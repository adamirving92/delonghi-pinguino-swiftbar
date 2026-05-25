# De'Longhi Pinguino Aircon CLI + SwiftBar + Homebridge

Small unofficial Python CLI, SwiftBar widget, and Homebridge thermostat bridge for a De'Longhi Pinguino portable air conditioner using the De'Longhi Comfort cloud flow.

It gives you:

- `aircon status`, `on`, `off`, `temp`, `mode`, `fan`, `silent`, and `raw`
- `aircon doctor` to check local config without printing secrets
- a low-key macOS menu bar widget via SwiftBar
- a Homebridge plugin so Apple Home, Siri, and HomePod can control it as a thermostat
- room temperature, humidity, target temperature, mode, fan, silent, swing, and outdoor weather context
- a one-click "Cool to 22°C" preset in the widget
- optional Tapo/Kasa smart plug readings in the widget, including live watts and cost estimates

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
- `python-kasa` if you want optional Tapo/Kasa energy readings
- macOS + SwiftBar for the optional menu bar widget
- Node.js + Homebridge for the optional Apple Home/HomePod bridge. Homebridge 2 currently expects Node 22 or 24.

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
9. Install the Homebridge plugin if you want Apple Home/HomePod control.

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

# Optional Tapo/Kasa energy monitor for SwiftBar.
AIRCON_TAPO_HOST=
AIRCON_TAPO_OUTLET=1

# Optional all-in marginal electricity rate, in pence per kWh.
AIRCON_ELECTRICITY_RATE_P_PER_KWH=
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

### Optional Energy Cost Values

The SwiftBar widget can show live power draw and cost estimates when the aircon is plugged into a Tapo/Kasa energy-monitoring plug or power strip.

Use:

```env
AIRCON_TAPO_HOST=192.168.1.50
AIRCON_TAPO_OUTLET=3
AIRCON_ELECTRICITY_RATE_P_PER_KWH=30.00
```

For a strip, `AIRCON_TAPO_OUTLET` is the socket number, starting at `1`.

`AIRCON_ELECTRICITY_RATE_P_PER_KWH` should be your all-in marginal usage price in pence per kWh. Do not include standing charges or late-payment fees, because those are not caused by the aircon being on.

If your bill breaks out Climate Change Levy and VAT, you can let the widget calculate the all-in rate instead:

```env
AIRCON_ELECTRICITY_UNIT_RATE_P_PER_KWH=24.00
AIRCON_ELECTRICITY_CCL_P_PER_KWH=0.80
AIRCON_ELECTRICITY_VAT_PERCENT=20
```

With those example values, the widget uses `29.76p/kWh`.

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

If `AIRCON_TAPO_HOST` is configured, it also shows live watts, cost per hour, today/month kWh, and estimated cost. The Tapo integration needs `python-kasa` in the Python environment SwiftBar uses. On Apple Silicon Macs, the widget also tries `/opt/homebrew/bin/python3` as a fallback.

Menu bar format:

```text
❄ 24.5° -> 22° · 30p/h
```

That means current room temperature is 24.5°C, target is 22°C, and the live smart-plug reading currently works out at about 30p per hour.

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
- `python-kasa` is installed for a different Python, if energy readings are enabled
- SwiftBar does not have the same shell environment as Terminal

## Apple Home / HomePod via Homebridge

The Homebridge plugin exposes the Pinguino as a HomeKit thermostat. Once paired with Apple Home, you can control it from the Home app and with Siri on HomePod.

Expected Siri phrases:

```text
Hey Siri, turn on the office aircon.
Hey Siri, turn off the office aircon.
Hey Siri, set the office aircon to 22 degrees.
Hey Siri, what temperature is the office aircon set to?
```

HomeKit thermostat mapping:

| HomeKit | CLI action |
| --- | --- |
| Off | `aircon off` |
| Cool | `aircon mode cool` then `aircon on` |
| Target temperature | `aircon temp <value>` |
| Current temperature | `room_temp` from `aircon raw` |
| Humidity sensor | `room_hum` from `aircon raw` |

The plugin intentionally exposes only `Off` and `Cool` thermostat modes. Dehumidify, fan-only, fan speed, silent mode, and swing are still available through the CLI and SwiftBar widget. They can be added as separate HomeKit controls later, but the thermostat surface is the cleanest first HomePod integration.

### Install Homebridge

If you do not already have Homebridge:

```sh
npm install -g homebridge homebridge-config-ui-x
```

If you see a Homebridge warning about your Node.js version, switch to a Homebridge-supported Node release before running it long term. For Homebridge 2, use Node 22 or 24.

On a Mac mini, the simplest first test is to run Homebridge through the service runner. This starts both Homebridge and the web UI without installing a macOS service:

```sh
hb-service run -U "$HOME/.homebridge" --stdout
```

The web UI will normally be available at `http://localhost:8581`.

Installing Homebridge as a proper macOS service requires sudo:

```sh
sudo hb-service install --user "$USER" --port 8581 -U "$HOME/.homebridge"
```

### Install This Plugin Locally

From this repo:

```sh
npm link
```

`npm link` registers the plugin in your global npm package directory, which is where a global Homebridge install looks for plugins.

For a normal permanent install from GitHub:

```sh
npm install -g github:adamirving92/delonghi-pinguino-swiftbar
```

Make sure the `aircon` CLI works before starting Homebridge:

```sh
./aircon doctor
./aircon status
```

### Configure Homebridge

Add this to the `platforms` array in your Homebridge `config.json`:

```json
{
  "platform": "DelonghiPinguinoCli",
  "name": "Office Aircon",
  "airconPath": "/absolute/path/to/aircon",
  "refreshIntervalSeconds": 30,
  "commandTimeoutSeconds": 25,
  "minTemperature": 18,
  "maxTemperature": 32,
  "temperatureStep": 1,
  "turnOnWhenSettingTemperature": true
}
```

Use the real absolute path. Example:

```json
"airconPath": "/Users/adam/delonghi-pinguino-swiftbar/aircon"
```

If Homebridge runs from the same folder as this repo, `airconPath` can be omitted and the plugin will use the bundled `./aircon`.

`turnOnWhenSettingTemperature` defaults to `true`. That means a Siri request such as "set Office Aircon to 22 degrees" will set cool mode, set the target temperature, and turn the unit on. Set it to `false` if you want temperature changes to leave power state untouched.

### Pair With Apple Home

1. Start Homebridge.
2. Open the Home app on your iPhone.
3. Tap Add Accessory.
4. Scan the Homebridge QR code or enter its setup code.
5. Put the thermostat in the correct room.
6. Rename it if desired, for example `Office Aircon`.
7. Test from the Home app before using HomePod.

If Siri has trouble with the word "aircon", rename the accessory to `Office AC` or `Office Cooler` in the Home app.

### Homebridge Troubleshooting

Run the plugin smoke test:

```sh
npm test
```

Check the CLI from the same user that runs Homebridge:

```sh
/absolute/path/to/aircon doctor
/absolute/path/to/aircon status
```

Common issues:

- `airconPath` is relative and Homebridge starts from another directory. Use an absolute path.
- `.env` is not next to the `aircon` script.
- `aircon` is not executable. Run `chmod +x aircon`.
- Python dependencies are installed for your Terminal user but not the Homebridge service user.
- The first login has not been completed. Run `aircon login` once manually.
- Siri does not hear the accessory name reliably. Rename it to something short in Apple Home.

## Security Notes

- Never commit `.env`.
- Never commit `.tokens.json`.
- Do not paste `.env` values into Homebridge config.
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
