'use strict';

const registerPlugin = require('../index');

let registered = null;
const api = {
  registerPlatform(pluginName, platformName, constructor) {
    registered = { pluginName, platformName, constructor };
  },
};

registerPlugin(api);

if (!registered) {
  throw new Error('Plugin did not register a Homebridge platform');
}

if (registered.pluginName !== 'homebridge-delonghi-pinguino-cli') {
  throw new Error(`Unexpected plugin name: ${registered.pluginName}`);
}

if (registered.platformName !== 'DelonghiPinguinoCli') {
  throw new Error(`Unexpected platform name: ${registered.platformName}`);
}

if (typeof registered.constructor !== 'function') {
  throw new Error('Registered platform is not a constructor');
}

console.log('homebridge plugin smoke test: ok');
