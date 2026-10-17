const path = require('path');
module.exports = { testEnvironment: 'node', cacheDirectory: path.join(__dirname, 'tmp', 'jest-cache'), watchman: false };
