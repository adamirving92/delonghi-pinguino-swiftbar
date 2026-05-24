# De'Longhi Pinguino Aircon CLI + SwiftBar Widget

Small unofficial Python CLI and SwiftBar widget for a De'Longhi Pinguino portable air conditioner using the De'Longhi Comfort cloud flow.

It gives you:

- `aircon status`, `on`, `off`, `temp`, `mode`, `fan`, `silent`, and `raw`
- `aircon doctor` to check local config without printing secrets
- a low-key macOS menu bar widget via SwiftBar
- room temperature, humidity, target temperature, mode, fan, silent, swing, and outdoor weather context
- a one-click "Cool to 22°C" preset in the widget

## Important

This is unofficial and not affiliated with De'Longhi, Kenwood, Pinguino, Ayla Networks, or SwiftBar. It relies on private cloud endpoints and can break if the vendor changes their app flow.

This repository deliberately does **not** include account credentials, token files, device serials/DSNs, or vendor app identifiers. Keep `.env` and `.tokens.json` private.

Why the app identifiers are not bundled:

- They are not user account secrets, but they are still client configuration for a proprietary mobile app flow.
- Shipping copied vendor identifiers in a public repo is brittle and may violate terms for some users.
- Keeping them in `.env` makes it clear what is user-provided and keeps the public repo clean.

## Requirements

- Python 3.10+
- `requests`
- macOS + SwiftBar for the optional menu bar widget

Install Python dependencies:

```sh
python3 -m pip install -r requirements.txt
```

If your system Python warns about LibreSSL, the CLI can still work. To avoid that warning, use a newer Python from Homebrew or pyenv:

```sh
brew install python
python3 -m pip install -r requirements.txt
```

## Setup Overview

1. Clone the repo.
2. Install Python dependencies.
3. Copy `.env.example` to `.env`.
4. Fill in your De'Longhi account details and app/client identifiers.
5. Run `./aircon doctor`.
6. Run `./aircon devices`.
7. Run `./aircon status`.
8. Install `aircon.30s.py` into SwiftBar if you want the menu bar widget.

## Clone

```sh
git clone https://github.com/adamirving92/delonghi-pinguino-swiftbar.git
cd delonghi-pinguino-swiftbar
python3 -m pip install -r requirements.txt
```

## Configure `.env`

Copy the example config:

```sh
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

```env
DELONGHI_EMAIL=you@example.com
DELONGHI_PASSWORD=your-password
DELONGHI_DSN=

DELONGHI_API_KEY=
DELONGHI_CLIENT_ID=
DELONGHI_CLIENT_SECRET=
DELONGHI_APP_ID=
DELONGHI_APP_SECRET=
```

### Required Values

`DELONGHI_EMAIL`

Your De'Longhi Comfort account email.

`DELONGHI_PASSWORD`

Your De'Longhi Comfort account password. If your account uses a provider login instead of a password login, this script may not work without changes.

`DELONGHI_API_KEY`

The Gigya/FIDM API key used by the De'Longhi Comfort app flow.

`DELONGHI_CLIENT_ID`

The OAuth client ID used by the De'Longhi Comfort app flow.

`DELONGHI_CLIENT_SECRET`

The OAuth client secret paired with the client ID.

`DELONGHI_APP_ID`

The Ayla application ID used for `token_sign_in`.

`DELONGHI_APP_SECRET`

The Ayla application secret paired with the app ID.

### Optional Value

`DELONGHI_DSN`

The device serial/DSN to control. Leave it blank if the account only has one device or if you are happy to use the first device returned by the API.

To find it after the rest of the config is working:

```sh
./aircon devices
```

Then copy the DSN into `.env`:

```env
DELONGHI_DSN=AC000W000000000
```

## Getting App/Client Identifiers

This project cannot publish copied vendor app identifiers. You need to provide values from a De'Longhi/Ayla client configuration you are allowed to use.

Practical ways people usually source these values:

- from an existing local/private script you already run
- from environment variables or secret storage used by your own integration
- from another maintained integration that documents compatible De'Longhi/Ayla client settings
- from your own authorized inspection of the De'Longhi Comfort app/network flow, subject to your local law and account terms

The names in `.env.example` map directly to the code:

| `.env` key | Used for |
| --- | --- |
| `DELONGHI_API_KEY` | Gigya/FIDM authorize, login, user-info requests |
| `DELONGHI_CLIENT_ID` | OAuth authorize and consent |
| `DELONGHI_CLIENT_SECRET` | OAuth token exchange basic auth |
| `DELONGHI_APP_ID` | Ayla `token_sign_in` |
| `DELONGHI_APP_SECRET` | Ayla `token_sign_in` |

Do not commit these values. Keep them in `.env`, a shell profile, a password manager, or your own secret manager.

## Check Config

Run:

```sh
./aircon doctor
```

Expected healthy shape:

```text
Config
  .env:        present (.../.env)
  .env mode:   600 (ok)
  DELONGHI_EMAIL: set
  DELONGHI_PASSWORD: set
  DELONGHI_API_KEY: set
  DELONGHI_CLIENT_ID: set
  DELONGHI_CLIENT_SECRET: set
  DELONGHI_APP_ID: set
  DELONGHI_APP_SECRET: set
  DELONGHI_DSN: not set; first device will be used

Token cache
  .tokens.json: missing; it will be created after login

Next step
  Config has all required keys. Run: ./aircon devices
```

`doctor` does not contact De'Longhi or Ayla. It only checks local files and required config keys.

## First Login

List devices:

```sh
./aircon devices
```

If login succeeds, `.tokens.json` will be created with cached access/refresh tokens:

```sh
chmod 600 .tokens.json
```

Show current state:

```sh
./aircon status
```

Force a fresh login if tokens become stale or corrupted:

```sh
./aircon login
```

## CLI Usage

Show status:

```sh
./aircon status
```

Turn on/off:

```sh
./aircon on
./aircon off
```

Set temperature:

```sh
./aircon temp 22
```

The EL110 minimum observed by this script is 18°C.

Set mode:

```sh
./aircon mode cool
./aircon mode dry
./aircon mode fan
```

Set fan:

```sh
./aircon fan low
./aircon fan mid
./aircon fan high
./aircon fan auto
```

Silent mode:

```sh
./aircon silent on
./aircon silent off
```

Dump raw properties:

```sh
./aircon raw
```

`raw` is useful for debugging new models, but review it before sharing because it may contain device identifiers.

## SwiftBar Widget

Install SwiftBar:

```sh
brew install --cask swiftbar
```

Copy the widget into your SwiftBar plugin folder.

If you keep the CLI and widget together:

```sh
mkdir -p "$HOME/Library/Application Support/SwiftBar/Plugins"
cp aircon aircon.30s.py "$HOME/Library/Application Support/SwiftBar/Plugins/"
chmod +x "$HOME/Library/Application Support/SwiftBar/Plugins/aircon"
chmod +x "$HOME/Library/Application Support/SwiftBar/Plugins/aircon.30s.py"
```

Also copy your private `.env` next to the CLI:

```sh
cp .env "$HOME/Library/Application Support/SwiftBar/Plugins/.env"
chmod 600 "$HOME/Library/Application Support/SwiftBar/Plugins/.env"
```

If the CLI lives somewhere else, leave `aircon.30s.py` in the SwiftBar plugin folder and set `AIRCON_CLI` for SwiftBar's environment:

```sh
export AIRCON_CLI="/path/to/aircon"
```

The widget refreshes every 30 seconds and uses restrained colour cues:

- blue: actively cooling
- muted: off
- amber/red: room is above target
- green: close to target

Menu bar format:

```text
❄ 24.5° -> 22°
```

That means current room temperature is 24.5°C and target is 22°C.

## Troubleshooting

### `Missing /path/.env`

Create `.env` in the same folder as the `aircon` script:

```sh
cp .env.example .env
chmod 600 .env
./aircon doctor
```

### `Missing DELONGHI_*`

Run:

```sh
./aircon doctor
```

Fill in every missing required key in `.env`.

### Login Fails

Check:

- the De'Longhi email/password works in the official app
- every app/client identifier is present
- the account uses a password login rather than only social login
- your machine can reach `*.gigya.com`, `*.delonghigroup.com`, and `*.aylanetworks.com`

Then force a fresh login:

```sh
rm -f .tokens.json
./aircon login
```

### `401` or Stale Token

The script refreshes tokens automatically once. If it still fails:

```sh
rm -f .tokens.json
./aircon login
```

### More Than One Device

List devices:

```sh
./aircon devices
```

Set the chosen DSN in `.env`:

```env
DELONGHI_DSN=AC000W000000000
```

### SwiftBar Shows an Error

Run the plugin directly:

```sh
"$HOME/Library/Application Support/SwiftBar/Plugins/aircon.30s.py"
```

Then run the CLI directly from the same folder:

```sh
cd "$HOME/Library/Application Support/SwiftBar/Plugins"
./aircon doctor
./aircon status
```

Most SwiftBar issues are one of:

- `aircon` is not executable
- `.env` is not next to `aircon`
- `requests` is installed for a different Python
- SwiftBar does not have the same shell environment as Terminal

## Security Notes

- Never commit `.env`.
- Never commit `.tokens.json`.
- Treat `.tokens.json` like a password.
- Use `chmod 600 .env .tokens.json`.
- Review `./aircon raw` output before sharing it.
- If you accidentally publish credentials or tokens, rotate them immediately.

## Model Notes

This was tested against a De'Longhi Pinguino EL110.

Power status uses:

- `get_device_status == 1` for on
- `get_device_status == 2` for off

Commands write:

- `set_device_status = "1"` for on
- `set_device_status = "2"` for off
- `set_temp_setpoint` for temperature
- `set_device_mode` for mode
- `set_int_fan_speed` for fan speed
- `set_silent_function` for silent mode

Other models may expose different properties or value ranges. Use `./aircon raw` to inspect them.
