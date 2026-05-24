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
from datetime import datetime
from pathlib import Path

PROJECT_DIR = str(Path(__file__).resolve().parent)
AIRCON = os.environ.get("AIRCON_CLI") or str(Path(__file__).with_name("aircon"))
MODE_LABEL = {1: "cool", 2: "dry", 3: "fan"}
MODE_EMOJI = {1: "❄", 2: "💧", 3: "🌀"}
FAN_LABEL = {1: "low", 2: "mid", 3: "high", 4: "auto"}
POWER_LABEL = {1: "ON", 2: "OFF"}
COLOR_BLUE = "#2F80ED"
COLOR_GREEN = "#2F855A"
COLOR_AMBER = "#B7791F"
COLOR_RED = "#C53030"
COLOR_MUTED = "gray"


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
    state, err = fetch_state()
    if state is None:
        print("⚠️ aircon")
        print("---")
        print(f"Error: {err.strip()[:200] if err else 'unknown'}")
        print(f"Retry | refresh=true")
        return

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
    if on:
        print(f"{emoji} {menu_temp(room)} → {temp(setpoint, 0, '°')} | color={state_colour}")
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
