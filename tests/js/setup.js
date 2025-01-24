const { createCanvas, Image } = require('canvas');

// Mock canvas and context
global.HTMLCanvasElement.prototype.getContext = function() {
  return {
    clearRect: jest.fn(),
    drawImage: jest.fn(),
    getImageData: jest.fn(() => ({
      data: new Uint8ClampedArray([255, 0, 0, 255]) // Red pixel
    })),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    stroke: jest.fn()
  };
};

// Mock FileReader
global.FileReader = class {
  constructor() {
    this.DONE = 2;
    this.EMPTY = 0;
    this.LOADING = 1;
    this.readyState = 0;
  }

  readAsDataURL() {
    this.readyState = this.LOADING;
    setTimeout(() => {
      this.readyState = this.DONE;
      this.result = 'data:image/png;base64,test';
      this.onload && this.onload({
        target: this
      });
    }, 0);
  }
};

// Mock Image
global.Image = class {
  constructor() {
    setTimeout(() => {
      this.width = 100;
      this.height = 100;
      this.onload && this.onload();
    }, 0);
  }
};
