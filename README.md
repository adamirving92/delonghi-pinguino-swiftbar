# De'Longhi Pinguino Aircon CLI + SwiftBar Widget

Small unofficial Python CLI and SwiftBar widget for a De'Longhi Pinguino portable air conditioner using the De'Longhi Comfort cloud flow.

It gives you:

- `aircon status`, `on`, `off`, `temp`, `mode`, `fan`, `silent`, and `raw`
- a low-key macOS menu bar widget via SwiftBar
- room temperature, humidity, target temperature, mode, fan, silent, swing, and outdoor weather context
- a one-click "Cool to 22°C" preset in the widget

## Important

This is unofficial and not affiliated with De'Longhi, Kenwood, Pinguino, Ayla Networks, or SwiftBar. It relies on private cloud endpoints and can break if the vendor changes their app flow.

This repository deliberately does **not** include account credentials, token files, device serials/DSNs, or vendor app identifiers. Keep `.env` and `.tokens.json` private.

## Requirements

- Python 3.10+
- `requests`
- SwiftBar for the optional menu bar widget

```sh
python3 -m pip install -r requirements.txt
```

## Setup

Copy the example config and fill it in:

```sh
cp .env.example .env
chmod 600 .env
```

Required values:

- `DELONGHI_EMAIL`
- `DELONGHI_PASSWORD`
- `DELONGHI_API_KEY`
- `DELONGHI_CLIENT_ID`
- `DELONGHI_CLIENT_SECRET`
- `DELONGHI_APP_ID`
- `DELONGHI_APP_SECRET`

Optional:

- `DELONGHI_DSN` if your account has more than one device

The CLI caches access tokens in `.tokens.json`.

## CLI

```sh
./aircon status
./aircon on
./aircon off
./aircon temp 22
./aircon mode cool
./aircon fan auto
./aircon silent off
./aircon raw
```

## SwiftBar Widget

Put `aircon.30s.py` in your SwiftBar plugin folder. The widget expects the `aircon` CLI to be next to it by default.

If the CLI lives somewhere else, set:

```sh
export AIRCON_CLI="/path/to/aircon"
```

The widget refreshes every 30 seconds and uses restrained colour cues:

- blue: actively cooling
- muted: off
- amber/red: room is above target
- green: close to target

## Notes

Power status uses `get_device_status == 1` for on and `2` for off, matching the observed De'Longhi/Ayla property values for an EL110 unit.
