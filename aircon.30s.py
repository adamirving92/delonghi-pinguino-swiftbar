#!/usr/bin/env python3
# <bitbar.title>Aircon</bitbar.title>
# <bitbar.version>v1.1</bitbar.version>
# <bitbar.author>Adam</bitbar.author>
# <bitbar.desc>Control De'Longhi Pinguino over WiFi.</bitbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>false</swiftbar.hideSwiftBar>

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = str(Path(__file__).resolve().parent)
AIRCON = os.environ.get("AIRCON_CLI") or str(Path(PROJECT_DIR) / "aircon")
ENV_PATH = Path(os.environ.get("AIRCON_ENV") or Path(PROJECT_DIR) / ".env")
MODE_LABEL = {1: "cool", 2: "dry", 3: "fan"}
MODE_EMOJI = {1: "❄", 2: "💧", 3: "🌀"}
FAN_LABEL = {1: "low", 2: "mid", 3: "high", 4: "auto"}
POWER_LABEL = {1: "ON", 2: "OFF"}
COLOR_BLUE = "#2F80ED"
COLOR_GREEN = "#2F855A"
COLOR_AMBER = "#B7791F"
COLOR_RED = "#C53030"
COLOR_MUTED = "gray"


def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def env_value(env, *keys, default=None):
    for key in keys:
        if key in os.environ and os.environ[key] != "":
            return os.environ[key]
        if key in env and env[key] != "":
            return env[key]
    return default


def env_float(env, *keys, default=None):
    value = env_value(env, *keys)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def env_int(env, *keys, default=None):
    value = env_value(env, *keys)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fetch_state():
    try:
        r = subprocess.run([AIRCON, "raw"], capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return None, r.stderr or r.stdout or "unknown error"
        return json.loads(r.stdout), None
    except Exception as e:
        return None, str(e)


def swift_escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def attr_string(**attrs):
    parts = []
    for key, value in attrs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f"{key}={str(value).lower()}")
        elif isinstance(value, (int, float)):
            parts.append(f"{key}={value}")
        else:
            parts.append(f'{key}="{swift_escape(value)}"')
    return " ".join(parts)


def menu_line(text, **attrs):
    attrs_s = attr_string(**attrs)
    return f"{text} | {attrs_s}" if attrs_s else text


def action_line(text, action, **attrs):
    attrs_s = attr_string(**attrs)
    suffix = " ".join(part for part in [attrs_s, action] if part)
    return f"{text} | {suffix}" if suffix else text


def cmd(*args):
    """Return a SwiftBar param-string that runs `aircon <args>` and refreshes."""
    parts = [f'shell="{swift_escape(AIRCON)}"']
    for i, a in enumerate(args):
        parts.append(f'param{i}="{swift_escape(a)}"')
    parts.append("terminal=false")
    parts.append("refresh=true")
    return " ".join(parts)


def preset_cmd(*commands):
    """Run several aircon commands from one SwiftBar menu item."""
    script = " && ".join(
        " ".join(shlex.quote(str(part)) for part in (AIRCON, *args))
        for args in commands
    )
    parts = [
        'shell="/bin/zsh"',
        'param0="-lc"',
        f'param1="{swift_escape(script)}"',
        "terminal=false",
        "refresh=true",
    ]
    return " ".join(parts)


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def temp(value, decimals=1, unit="°C"):
    value = as_float(value)
    if value is None:
        return "?"
    return f"{value:.{decimals}f}{unit}"


def whole_temp(value):
    value = as_float(value)
    if value is None:
        return "?"
    return f"{value:.0f}°C"


def menu_temp(value):
    value = as_float(value)
    if value is None:
        return "?°"
    return f"{value:.1f}°"


def pct(value):
    value = as_float(value)
    if value is None:
        return "?"
    return f"{value:.0f}%"


def format_watts(value):
    value = as_float(value)
    if value is None:
        return "?"
    if abs(value) >= 1000:
        return f"{value / 1000:.2f} kW"
    return f"{value:.0f} W"


def format_kwh(value):
    value = as_float(value)
    if value is None:
        return "?"
    if abs(value) < 1:
        return f"{value:.3f} kWh"
    return f"{value:.2f} kWh"


def format_money_pence(value):
    value = as_float(value)
    if value is None:
        return "?"
    if abs(value) < 10:
        return f"{value:.1f}p"
    if abs(value) < 100:
        return f"{value:.0f}p"
    return f"£{value / 100:.2f}"


def electricity_rate_p_per_kwh(env):
    direct = env_float(
        env,
        "AIRCON_ELECTRICITY_RATE_P_PER_KWH",
        "ELECTRICITY_RATE_P_PER_KWH",
    )
    if direct is not None:
        return direct

    unit = env_float(
        env,
        "AIRCON_ELECTRICITY_UNIT_RATE_P_PER_KWH",
        "ELECTRICITY_UNIT_RATE_P_PER_KWH",
    )
    if unit is None:
        return None

    ccl = env_float(
        env,
        "AIRCON_ELECTRICITY_CCL_P_PER_KWH",
        "ELECTRICITY_CCL_P_PER_KWH",
        default=0,
    )
    vat = env_float(
        env,
        "AIRCON_ELECTRICITY_VAT_PERCENT",
        "ELECTRICITY_VAT_PERCENT",
        default=0,
    )
    return (unit + ccl) * (1 + vat / 100)


def _feature_value(device, key):
    feature = getattr(device, "features", {}).get(key)
    if feature is None:
        return None
    return getattr(feature, "value", None)


async def _fetch_tapo_energy_async(host, outlet, timeout):
    from kasa import Discover

    dev = None
    try:
        dev = await Discover.discover_single(
            host,
            discovery_timeout=int(timeout),
            timeout=int(timeout),
        )
        if dev is None:
            raise RuntimeError(f"no Tapo device found at {host}")
        await dev.update()
        target = dev
        children = getattr(dev, "children", []) or []
        if children:
            index = outlet - 1
            if index < 0 or index >= len(children):
                raise RuntimeError(f"Tapo outlet {outlet} not found")
            target = children[index]
            await target.update()

        return {
            "host": host,
            "model": getattr(dev, "model", None),
            "alias": getattr(target, "alias", None),
            "outlet": outlet if children else None,
            "is_on": bool(getattr(target, "is_on", False)),
            "watts": _feature_value(target, "current_consumption"),
            "today_kwh": _feature_value(target, "consumption_today"),
            "month_kwh": _feature_value(target, "consumption_this_month"),
        }
    finally:
        close = getattr(dev, "disconnect", None) or getattr(dev, "close", None)
        if close:
            result = close()
            if hasattr(result, "__await__"):
                await result


def _fetch_tapo_energy_current_python(host, outlet, timeout):
    import asyncio

    return asyncio.run(_fetch_tapo_energy_async(host, outlet, timeout))


TAPO_HELPER = r"""
import asyncio
import json
import sys


def feature_value(device, key):
    feature = getattr(device, "features", {}).get(key)
    if feature is None:
        return None
    return getattr(feature, "value", None)


async def main():
    from kasa import Discover

    host = sys.argv[1]
    outlet = int(sys.argv[2])
    timeout = int(float(sys.argv[3]))
    dev = None
    try:
        dev = await Discover.discover_single(host, discovery_timeout=timeout, timeout=timeout)
        if dev is None:
            raise RuntimeError(f"no Tapo device found at {host}")
        await dev.update()
        target = dev
        children = getattr(dev, "children", []) or []
        if children:
            index = outlet - 1
            if index < 0 or index >= len(children):
                raise RuntimeError(f"Tapo outlet {outlet} not found")
            target = children[index]
            await target.update()
        print(json.dumps({
            "host": host,
            "model": getattr(dev, "model", None),
            "alias": getattr(target, "alias", None),
            "outlet": outlet if children else None,
            "is_on": bool(getattr(target, "is_on", False)),
            "watts": feature_value(target, "current_consumption"),
            "today_kwh": feature_value(target, "consumption_today"),
            "month_kwh": feature_value(target, "consumption_this_month"),
        }))
    finally:
        close = getattr(dev, "disconnect", None) or getattr(dev, "close", None)
        if close:
            result = close()
            if hasattr(result, "__await__"):
                await result


asyncio.run(main())
"""


def _fetch_tapo_energy_helper(host, outlet, timeout):
    candidates = [
        env for env in [os.environ.get("AIRCON_TAPO_PYTHON")] if env
    ]
    candidates.extend([
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
    ])
    seen = {sys.executable}
    last_error = None
    for python in candidates:
        if not python or python in seen or not Path(python).exists():
            continue
        seen.add(python)
        try:
            result = subprocess.run(
                [python, "-c", TAPO_HELPER, host, str(outlet), str(timeout)],
                capture_output=True,
                text=True,
                timeout=float(timeout) + 3,
            )
        except Exception as exc:
            last_error = str(exc)
            continue
        if result.returncode == 0:
            return json.loads(result.stdout)
        last_error = (result.stderr or result.stdout).strip()
    if last_error:
        raise RuntimeError(last_error[:180])
    raise RuntimeError("python-kasa is not available")


def fetch_energy(env):
    host = env_value(env, "AIRCON_TAPO_HOST", "TAPO_HOST")
    if not host:
        return None, None
    outlet = env_int(env, "AIRCON_TAPO_OUTLET", "TAPO_OUTLET", default=1)
    timeout = env_float(env, "AIRCON_TAPO_TIMEOUT_SECONDS", "TAPO_TIMEOUT_SECONDS", default=4)

    try:
        try:
            energy = _fetch_tapo_energy_current_python(host, outlet, timeout)
        except ModuleNotFoundError:
            energy = _fetch_tapo_energy_helper(host, outlet, timeout)
    except Exception as exc:
        return None, str(exc)

    rate = electricity_rate_p_per_kwh(env)
    energy["rate_p_per_kwh"] = rate
    watts = as_float(energy.get("watts"))
    today_kwh = as_float(energy.get("today_kwh"))
    month_kwh = as_float(energy.get("month_kwh"))
    if rate is not None and watts is not None:
        energy["cost_per_hour_p"] = watts / 1000 * rate
    if rate is not None and today_kwh is not None:
        energy["cost_today_p"] = today_kwh * rate
    if rate is not None and month_kwh is not None:
        energy["cost_month_p"] = month_kwh * rate
    return energy, None


def gap_value(room, setpoint):
    room = as_float(room)
    setpoint = as_float(setpoint)
    if room is None or setpoint is None:
        return None
    return room - setpoint


def target_gap(room, setpoint):
    gap = gap_value(room, setpoint)
    if gap is None:
        return None
    if abs(gap) < 0.2:
        return "at target"
    if gap > 0:
        return f"{gap:.1f}°C above target"
    return f"{abs(gap):.1f}°C below target"


def gap_color(room, setpoint):
    gap = gap_value(room, setpoint)
    if gap is None:
        return COLOR_MUTED
    if abs(gap) < 0.5:
        return COLOR_GREEN
    if gap > 3:
        return COLOR_RED
    if gap > 0.8:
        return COLOR_AMBER
    return COLOR_BLUE


def status_color(on, mode):
    if not on:
        return COLOR_MUTED
    if mode == 1:
        return COLOR_BLUE
    if mode == 2:
        return "#3B7C8C"
    return COLOR_GREEN


def temp_bar(room, setpoint, low=18, high=32, width=18):
    room = as_float(room)
    setpoint = as_float(setpoint)
    if room is None or setpoint is None:
        return None

    def pos(value):
        clamped = min(max(value, low), high)
        return round((clamped - low) / (high - low) * (width - 1))

    bar = ["─"] * width
    target_pos = pos(setpoint)
    room_pos = pos(room)
    bar[target_pos] = "┆"
    bar[room_pos] = "●" if room_pos != target_pos else "◆"
    return f"{low}° {''.join(bar)} {high}°"


def main():
    env = load_env()
    state, err = fetch_state()
    if state is None:
        print("⚠️ aircon")
        print("---")
        print(f"Error: {err.strip()[:200] if err else 'unknown'}")
        print(f"Retry | refresh=true")
        return
    energy, energy_err = fetch_energy(env)

    power = state.get("get_device_status")
    on = power == 1
    setpoint = state.get("temp_setpoint")
    room = state.get("room_temp")
    room_h = state.get("room_hum")
    mode = state.get("get_device_mode")
    fan = state.get("get_int_fan_speed")
    silent = state.get("get_silent_function") == 1
    swing = state.get("get_swing_function") == 1
    out_t = state.get("outdoor_temp")
    out_h = state.get("outdoor_hum")
    weather = state.get("outdoor_Weather_condition") or "?"

    mode_lbl = MODE_LABEL.get(mode, "?")
    fan_lbl = FAN_LABEL.get(fan, "?")
    emoji = MODE_EMOJI.get(mode, "❄")
    gap = target_gap(room, setpoint)
    gap_colour = gap_color(room, setpoint)
    state_colour = status_color(on, mode)
    status_dot = "●" if on else "○"
    status_text = POWER_LABEL.get(power, f"UNKNOWN {power}")
    visual_bar = temp_bar(room, setpoint)

    # ---------- menu bar title ----------
    energy_title = ""
    if on and energy and energy.get("cost_per_hour_p") is not None:
        energy_title = f" · {format_money_pence(energy.get('cost_per_hour_p'))}/h"
    if on:
        print(f"{emoji} {menu_temp(room)} → {temp(setpoint, 0, '°')}{energy_title} | color={state_colour}")
    else:
        print(f"○ {menu_temp(room)} | color={COLOR_MUTED}")

    # ---------- dropdown ----------
    print("---")
    print(menu_line("Office Aircon", size=13))
    print(menu_line("Pinguino EL110", size=10, color=COLOR_MUTED))
    print("---")
    print(menu_line(f"{status_dot} {status_text} · {mode_lbl} · fan {fan_lbl}", size=13, color=state_colour))
    if gap:
        print(menu_line(f"Target {whole_temp(setpoint)} · {gap}", size=12, color=gap_colour))
    else:
        print(menu_line(f"Target {whole_temp(setpoint)}", size=12, color=COLOR_MUTED))
    if visual_bar:
        print(menu_line(visual_bar, size=11, font="Menlo", color=gap_colour))
        print(menu_line("◆ at target  ● room  ┆ target", size=10, color=COLOR_MUTED))
    print("---")
    print(menu_line(f"Room      {temp(room)} · {pct(room_h)} humidity", size=12))
    print(menu_line(f"Outside   {temp(out_t)} · {pct(out_h)} · {weather}", size=12, color=COLOR_MUTED))
    print(menu_line(f"Updated   {datetime.now().strftime('%H:%M:%S')}", size=10, color=COLOR_MUTED))
    if energy:
        cost_per_hour = energy.get("cost_per_hour_p")
        energy_colour = COLOR_GREEN if as_float(energy.get("watts")) == 0 else state_colour
        print("---")
        if cost_per_hour is not None:
            print(menu_line(
                f"Energy    {format_watts(energy.get('watts'))} · {format_money_pence(cost_per_hour)}/h",
                size=12,
                color=energy_colour,
            ))
        else:
            print(menu_line(f"Energy    {format_watts(energy.get('watts'))}", size=12, color=energy_colour))
        today_line = f"Today     {format_kwh(energy.get('today_kwh'))}"
        if energy.get("cost_today_p") is not None:
            today_line += f" · {format_money_pence(energy.get('cost_today_p'))}"
        print(menu_line(today_line, size=11, color=COLOR_MUTED))
        month_line = f"Month     {format_kwh(energy.get('month_kwh'))}"
        if energy.get("cost_month_p") is not None:
            month_line += f" · {format_money_pence(energy.get('cost_month_p'))}"
        print(menu_line(month_line, size=11, color=COLOR_MUTED))
        if energy.get("rate_p_per_kwh") is not None:
            print(menu_line(
                f"Tariff    {energy.get('rate_p_per_kwh'):.2f}p/kWh all-in",
                size=10,
                color=COLOR_MUTED,
            ))
        outlet = energy.get("outlet")
        tapo_label = f"Tapo      outlet {outlet}" if outlet else "Tapo      device"
        tapo_label += f" · {'on' if energy.get('is_on') else 'off'}"
        print(menu_line(tapo_label, size=10, color=COLOR_MUTED))
    elif energy_err:
        print("---")
        print(menu_line("Energy    not available", size=12, color=COLOR_AMBER))
        print(menu_line(energy_err[:120], size=10, color=COLOR_MUTED))
    print("---")

    print(action_line("Cool to 22°C", preset_cmd(('mode', 'cool'), ('fan', 'auto'), ('temp', 22), ('on',)), color=COLOR_BLUE))
    if on:
        print(action_line("Turn off", cmd('off'), color=COLOR_MUTED))
    else:
        print(action_line("Turn on", cmd('on'), color=COLOR_BLUE))

    print("---")

    # Temperature submenu (18–32°C; EL110 minimum is 18)
    print(menu_line(f"Temperature · target {whole_temp(setpoint)}"))
    for t in range(18, 33):
        mark = " ✓" if int(as_float(setpoint) or 0) == t else ""
        print(f"--{t}°C{mark} | {cmd('temp', t)}")

    # Mode submenu
    print(menu_line(f"Mode · {mode_lbl}"))
    for m, label, em in [("cool", "Cool", "❄"), ("dry", "Dry", "💧"), ("fan", "Fan", "🌀")]:
        mark = " ✓" if mode_lbl == m else ""
        print(f"--{em} {label}{mark} | {cmd('mode', m)}")

    # Fan submenu
    print(menu_line(f"Fan · {fan_lbl}"))
    for f in ["low", "mid", "high", "auto"]:
        mark = " ✓" if fan_lbl == f else ""
        print(f"--{f.capitalize()}{mark} | {cmd('fan', f)}")

    # Silent toggle
    silent_lbl = "on" if silent else "off"
    silent_next = "off" if silent else "on"
    print(action_line(f"Silent · {silent_lbl}", cmd('silent', silent_next)))

    print("---")
    print("Refresh | refresh=true")
    print(menu_line(f"Swing · {'on' if swing else 'off'}", size=11, color=COLOR_MUTED))
    open_project = f'shell="open" param0="{swift_escape(PROJECT_DIR)}" terminal=false'
    print(action_line("Open project folder", open_project, color=COLOR_MUTED))


if __name__ == "__main__":
    main()
