module.exports = {
  testEnvironment: 'jsdom',
  setupFiles: ['<rootDir>/tests/js/setup.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': '<rootDir>/tests/js/styleMock.js'
  },
  testMatch: [
    '<rootDir>/tests/js/**/*.test.js'
  ],
  transform: {
    '^.+\\.js$': 'babel-jest'
  }
};
