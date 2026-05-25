'use strict';

const { execFile } = require('child_process');
const path = require('path');

const PLUGIN_NAME = 'homebridge-delonghi-pinguino-cli';
const PLATFORM_NAME = 'DelonghiPinguinoCli';

module.exports = (api) => {
  api.registerPlatform(PLUGIN_NAME, PLATFORM_NAME, DelonghiPinguinoPlatform);
};

class DelonghiPinguinoPlatform {
  constructor(log, config, api) {
    this.log = log;
    this.config = config || {};
    this.api = api;
    this.Service = api.hap.Service;
    this.Characteristic = api.hap.Characteristic;
    this.accessories = [];

    this.api.on('didFinishLaunching', () => {
      this.discoverDevices();
    });
  }

  configureAccessory(accessory) {
    this.accessories.push(accessory);
  }

  discoverDevices() {
    const name = this.config.name || 'Office Aircon';
    const uuid = this.api.hap.uuid.generate(`${PLUGIN_NAME}:${name}`);
    const existingAccessory = this.accessories.find((accessory) => accessory.UUID === uuid);

    if (existingAccessory) {
      this.log.info(`Restoring cached accessory: ${name}`);
      new PinguinoThermostatAccessory(this, existingAccessory);
      return;
    }

    this.log.info(`Adding accessory: ${name}`);
    const accessory = new this.api.platformAccessory(name, uuid);
    new PinguinoThermostatAccessory(this, accessory);
    this.api.registerPlatformAccessories(PLUGIN_NAME, PLATFORM_NAME, [accessory]);
  }
}

class PinguinoThermostatAccessory {
  constructor(platform, accessory) {
    this.platform = platform;
    this.accessory = accessory;
    this.log = platform.log;
    this.Service = platform.Service;
    this.Characteristic = platform.Characteristic;
    this.name = platform.config.name || 'Office Aircon';
    this.airconPath = resolveAirconPath(platform.config.airconPath);
    this.refreshMs = Math.max(Number(platform.config.refreshIntervalSeconds || 30), 5) * 1000;
    this.timeoutMs = Math.max(Number(platform.config.commandTimeoutSeconds || 25), 5) * 1000;
    this.minTemperature = Number(platform.config.minTemperature || 18);
    this.maxTemperature = Number(platform.config.maxTemperature || 32);
    this.temperatureStep = Number(platform.config.temperatureStep || 1);
    this.turnOnWhenSettingTemperature = platform.config.turnOnWhenSettingTemperature !== false;
    this.cache = null;
    this.cacheAt = 0;

    this.accessory
      .getService(this.Service.AccessoryInformation)
      .setCharacteristic(this.Characteristic.Manufacturer, "De'Longhi")
      .setCharacteristic(this.Characteristic.Model, 'Pinguino')
      .setCharacteristic(this.Characteristic.Name, this.name)
      .setCharacteristic(this.Characteristic.SerialNumber, 'configured-by-aircon-cli');

    this.thermostat =
      this.accessory.getService(this.Service.Thermostat) ||
      this.accessory.addService(this.Service.Thermostat, this.name);

    this.thermostat
      .setCharacteristic(this.Characteristic.Name, this.name)
      .setCharacteristic(this.Characteristic.TemperatureDisplayUnits, this.Characteristic.TemperatureDisplayUnits.CELSIUS);

    this.thermostat
      .getCharacteristic(this.Characteristic.TargetHeatingCoolingState)
      .setProps({
        validValues: [
          this.Characteristic.TargetHeatingCoolingState.OFF,
          this.Characteristic.TargetHeatingCoolingState.COOL,
        ],
      })
      .onGet(() => this.getTargetHeatingCoolingState())
      .onSet((value) => this.setTargetHeatingCoolingState(value));

    this.thermostat
      .getCharacteristic(this.Characteristic.CurrentHeatingCoolingState)
      .onGet(() => this.getCurrentHeatingCoolingState());

    this.thermostat
      .getCharacteristic(this.Characteristic.CurrentTemperature)
      .setProps({ minValue: -20, maxValue: 60, minStep: 0.1 })
      .onGet(() => this.getCurrentTemperature());

    this.thermostat
      .getCharacteristic(this.Characteristic.TargetTemperature)
      .updateValue(clamp(22, this.minTemperature, this.maxTemperature))
      .setProps({
        minValue: this.minTemperature,
        maxValue: this.maxTemperature,
        minStep: this.temperatureStep,
      })
      .onGet(() => this.getTargetTemperature())
      .onSet((value) => this.setTargetTemperature(value));

    this.humidity =
      this.accessory.getService(this.Service.HumiditySensor) ||
      this.accessory.addService(this.Service.HumiditySensor, `${this.name} Humidity`);

    this.humidity
      .getCharacteristic(this.Characteristic.CurrentRelativeHumidity)
      .onGet(() => this.getCurrentRelativeHumidity());

    this.log.info(`${this.name} will use CLI: ${this.airconPath}`);
  }

  async getTargetHeatingCoolingState() {
    const state = await this.getState();
    return this.isOn(state)
      ? this.Characteristic.TargetHeatingCoolingState.COOL
      : this.Characteristic.TargetHeatingCoolingState.OFF;
  }

  async getCurrentHeatingCoolingState() {
    const state = await this.getState();
    return this.isOn(state)
      ? this.Characteristic.CurrentHeatingCoolingState.COOL
      : this.Characteristic.CurrentHeatingCoolingState.OFF;
  }

  async setTargetHeatingCoolingState(value) {
    if (Number(value) === this.Characteristic.TargetHeatingCoolingState.OFF) {
      await this.runCli(['off']);
    } else {
      await this.runCli(['mode', 'cool']);
      await this.runCli(['on']);
    }
    this.invalidateCache();
  }

  async getCurrentTemperature() {
    const state = await this.getState();
    return numberOrDefault(state.room_temp, 0);
  }

  async getTargetTemperature() {
    const state = await this.getState();
    return clamp(numberOrDefault(state.temp_setpoint, 22), this.minTemperature, this.maxTemperature);
  }

  async setTargetTemperature(value) {
    const temperature = clamp(Number(value), this.minTemperature, this.maxTemperature);
    if (this.turnOnWhenSettingTemperature) {
      await this.runCli(['mode', 'cool']);
    }
    await this.runCli(['temp', String(temperature)]);
    if (this.turnOnWhenSettingTemperature) {
      await this.runCli(['on']);
    }
    this.invalidateCache();
  }

  async getCurrentRelativeHumidity() {
    const state = await this.getState();
    return clamp(numberOrDefault(state.room_hum, 0), 0, 100);
  }

  async getState(force = false) {
    const now = Date.now();
    if (!force && this.cache && now - this.cacheAt < this.refreshMs) {
      return this.cache;
    }

    const stdout = await this.runCli(['raw']);
    const state = JSON.parse(stdout);
    this.cache = state;
    this.cacheAt = Date.now();

    this.updateCharacteristics(state);
    return state;
  }

  updateCharacteristics(state) {
    const currentMode = this.isOn(state)
      ? this.Characteristic.CurrentHeatingCoolingState.COOL
      : this.Characteristic.CurrentHeatingCoolingState.OFF;
    const targetMode = this.isOn(state)
      ? this.Characteristic.TargetHeatingCoolingState.COOL
      : this.Characteristic.TargetHeatingCoolingState.OFF;

    this.thermostat.updateCharacteristic(this.Characteristic.CurrentHeatingCoolingState, currentMode);
    this.thermostat.updateCharacteristic(this.Characteristic.TargetHeatingCoolingState, targetMode);
    this.thermostat.updateCharacteristic(this.Characteristic.CurrentTemperature, numberOrDefault(state.room_temp, 0));
    this.thermostat.updateCharacteristic(
      this.Characteristic.TargetTemperature,
      clamp(numberOrDefault(state.temp_setpoint, 22), this.minTemperature, this.maxTemperature),
    );
    this.humidity.updateCharacteristic(
      this.Characteristic.CurrentRelativeHumidity,
      clamp(numberOrDefault(state.room_hum, 0), 0, 100),
    );
  }

  async runCli(args) {
    return new Promise((resolve, reject) => {
      execFile(this.airconPath, args, { timeout: this.timeoutMs }, (error, stdout, stderr) => {
        if (error) {
          const stderrText = stderr ? `: ${stderr.trim()}` : '';
          reject(new Error(`aircon ${args.join(' ')} failed${stderrText}`));
          return;
        }
        resolve(stdout.trim());
      });
    });
  }

  invalidateCache() {
    this.cache = null;
    this.cacheAt = 0;
  }

  isOn(state) {
    return Number(state.get_device_status) === 1;
  }
}

function resolveAirconPath(configuredPath) {
  if (!configuredPath || configuredPath === './aircon') {
    return path.join(__dirname, 'aircon');
  }
  return path.resolve(configuredPath);
}

function numberOrDefault(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
