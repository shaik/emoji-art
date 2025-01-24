const { ImageProcessor, Logger } = require('../../static/js/imageProcessor');

describe('ImageProcessor', () => {
    let imageProcessor;
    let mockFile;

    beforeEach(() => {
        // Set up DOM elements
        document.body.innerHTML = `
            <input type="file" id="imageUpload" />
            <button id="processImage">Process Image</button>
            <select id="aspectRatio">
                <option value="1:1">1:1</option>
            </select>
            <select id="gridSize">
                <option value="16">16x16</option>
            </select>
            <canvas id="previewCanvas"></canvas>
            <canvas id="gridCanvas"></canvas>
            <div id="processingStatus"></div>
        `;

        // Mock getElementById
        document.getElementById = jest.fn((id) => {
            const element = document.querySelector(`#${id}`);
            if (id.includes('Canvas')) {
                Object.defineProperty(element, 'getContext', {
                    value: () => ({
                        clearRect: jest.fn(),
                        drawImage: jest.fn(),
                        getImageData: jest.fn(() => ({
                            data: new Uint8ClampedArray([255, 0, 0, 255])
                        })),
                        beginPath: jest.fn(),
                        moveTo: jest.fn(),
                        lineTo: jest.fn(),
                        stroke: jest.fn()
                    })
                });
            }
            return element;
        });

        // Initialize ImageProcessor
        imageProcessor = new ImageProcessor();

        // Mock file
        mockFile = new File([''], 'test.png', { type: 'image/png' });
    });

    describe('File Validation', () => {
        test('should validate correct file type', () => {
            expect(imageProcessor.validateFile(mockFile)).toBe(true);
        });

        test('should reject oversized files', () => {
            const largeFile = new File([''], 'large.png', {
                type: 'image/png'
            });
            Object.defineProperty(largeFile, 'size', { value: 20 * 1024 * 1024 });
            expect(imageProcessor.validateFile(largeFile)).toBe(false);
        });

        test('should reject unsupported file types', () => {
            const gifFile = new File([''], 'test.gif', { type: 'image/gif' });
            expect(imageProcessor.validateFile(gifFile)).toBe(false);
        });
    });

    describe('Image Processing', () => {
        test('should calculate correct dimensions for aspect ratio', () => {
            const image = { width: 1000, height: 1000 };
            const aspectRatio = { x: 16, y: 9 };
            const dimensions = imageProcessor.calculateDimensions(image, aspectRatio);
            
            expect(dimensions.width).toBeLessThanOrEqual(800);
            expect(dimensions.height).toBeLessThanOrEqual(600);
            expect(dimensions.width / dimensions.height).toBeCloseTo(16/9, 2);
        });

        test('should calculate average color correctly', () => {
            const data = new Uint8ClampedArray([
                255, 0, 0, 255,  // Red pixel
                0, 255, 0, 255,  // Green pixel
                0, 0, 255, 255,  // Blue pixel
                255, 255, 255, 255  // White pixel
            ]);

            const avgColor = imageProcessor.calculateAverageColor(data);
            expect(avgColor).toEqual({
                r: 128,
                g: 128,
                b: 128
            });
        });

        test('should convert RGB to hex correctly', () => {
            expect(imageProcessor.rgbToHex(255, 0, 0)).toBe('#ff0000');
            expect(imageProcessor.rgbToHex(0, 255, 0)).toBe('#00ff00');
            expect(imageProcessor.rgbToHex(0, 0, 255)).toBe('#0000ff');
        });
    });

    describe('UI Interaction', () => {
        test('should enable process button after loading image', (done) => {
            const event = { target: { files: [mockFile] } };
            imageProcessor.handleFileSelect(event);

            setTimeout(() => {
                expect(imageProcessor.processButton.disabled).toBe(false);
                done();
            }, 100);
        });

        test('should show error for invalid file', () => {
            const invalidFile = new File([''], 'test.gif', { type: 'image/gif' });
            const event = { target: { files: [invalidFile] } };
            imageProcessor.handleFileSelect(event);

            const statusMessage = document.getElementById('processingStatus');
            expect(statusMessage.className).toContain('error');
        });
    });

    describe('Grid Processing', () => {
        test('should generate correct grid data', () => {
            // Mock the current image
            imageProcessor.currentImage = new Image();
            imageProcessor.currentImage.width = 100;
            imageProcessor.currentImage.height = 100;

            // Process the image
            const gridData = imageProcessor.processImage();

            expect(gridData).toBeDefined();
            expect(gridData.length).toBe(16); // 16x16 grid
            expect(gridData[0].length).toBe(16);
            expect(gridData[0][0]).toHaveProperty('color');
            expect(gridData[0][0]).toHaveProperty('position');
        });
    });
});

describe('Logger', () => {
    let logger;
    let consoleDebugSpy;
    let consoleInfoSpy;
    let consoleErrorSpy;

    beforeEach(() => {
        logger = new Logger();
        consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation();
        consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation();
        consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
        consoleDebugSpy.mockRestore();
        consoleInfoSpy.mockRestore();
        consoleErrorSpy.mockRestore();
    });

    test('should log debug messages', () => {
        logger.debug('test debug');
        expect(consoleDebugSpy).toHaveBeenCalledWith('[DEBUG] test debug');
    });

    test('should log info messages', () => {
        logger.info('test info');
        expect(consoleInfoSpy).toHaveBeenCalledWith('[INFO] test info');
    });

    test('should log error messages', () => {
        logger.error('test error');
        expect(consoleErrorSpy).toHaveBeenCalledWith('[ERROR] test error');
    });
});
