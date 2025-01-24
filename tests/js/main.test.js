/**
 * @jest-environment jsdom
 */

describe('Image Processing Functions', () => {
    let mainModule;

    beforeEach(() => {
        // Set up document body
        document.body.innerHTML = `
            <div id="dragDropArea"></div>
            <input type="file" id="fileInput">
            <div id="imagePreview"></div>
            <canvas id="previewCanvas"></canvas>
            <canvas id="gridCanvas"></canvas>
            <button id="processImage"></button>
            <select id="gridSize">
                <option value="32">32x32</option>
                <option value="64">64x64</option>
            </select>
            <select id="aspectRatio">
                <option value="1:1">1:1</option>
                <option value="16:9">16:9</option>
            </select>
            <div id="errorMessage"></div>
            <div id="processingStatus"></div>
        `;

        // Mock canvas context
        const mockContext = {
            drawImage: jest.fn(),
            clearRect: jest.fn(),
            beginPath: jest.fn(),
            moveTo: jest.fn(),
            lineTo: jest.fn(),
            stroke: jest.fn(),
            fillStyle: '',
            fillRect: jest.fn(),
            strokeStyle: '',
            lineWidth: 0,
            getImageData: jest.fn().mockReturnValue({
                data: new Uint8ClampedArray([255, 0, 0, 255])  // Red pixel
            })
        };

        // Mock canvas getContext
        HTMLCanvasElement.prototype.getContext = jest.fn(() => mockContext);

        // Reset the module before each test
        jest.resetModules();
        mainModule = require('../../static/js/main.js');
    });

    test('calculateDimensions maintains aspect ratio', () => {
        const img = { width: 1000, height: 500 };
        const dimensions = mainModule.calculateDimensions(img);
        
        expect(dimensions.width).toBeLessThanOrEqual(800);
        expect(dimensions.height).toBeLessThanOrEqual(800);
        expect(dimensions.width / dimensions.height).toBeCloseTo(2, 1);
    });

    test('getAverageColor returns correct RGB values', () => {
        const color = mainModule.getAverageColor(0, 0, 10, 10);
        
        expect(color).toEqual({
            r: 255,
            g: 0,
            b: 0
        });
    });

    test('grid size is set correctly', () => {
        const gridSize = document.getElementById('gridSize');
        gridSize.value = '32';
        
        const event = new Event('change');
        gridSize.dispatchEvent(event);
        
        expect(mainModule.currentGridSize).toBe(32);
    });

    test('showError displays error message', () => {
        const message = 'Test error message';
        mainModule.showError(message);
        
        const errorElement = document.getElementById('errorMessage');
        expect(errorElement.textContent).toBe(message);
        expect(errorElement.style.display).toBe('block');
    });

    test('handleAspectRatioChange updates currentAspectRatio', () => {
        const select = document.getElementById('aspectRatio');
        select.value = '16:9';
        select.dispatchEvent(new Event('change'));
        
        expect(mainModule.currentAspectRatio).toBe('16:9');
    });

    test('debug mode can be toggled', () => {
        expect(mainModule.debugMode).toBeFalsy();
        
        mainModule.toggleDebugMode();
        expect(mainModule.debugMode).toBeTruthy();
        
        mainModule.toggleDebugMode();
        expect(mainModule.debugMode).toBeFalsy();
    });

    test('file validation rejects non-image files', () => {
        const file = new File(['test'], 'test.txt', { type: 'text/plain' });
        mainModule.processFile(file);
        
        const errorElement = document.getElementById('errorMessage');
        expect(errorElement.textContent).toBe('Please upload an image file');
    });

    test('file validation accepts image files', () => {
        // Create a mock Image class
        const mockImage = {
            onload: null,
            src: '',
            width: 100,
            height: 100
        };
        global.Image = jest.fn(() => mockImage);

        // Create a test file
        const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
        const processImageSpy = jest.spyOn(mainModule, 'processImage');
        
        mainModule.processFile(file);
        
        // Wait for FileReader to complete and trigger Image onload
        return new Promise(resolve => {
            // FileReader onload will set the Image src
            setTimeout(() => {
                // Manually trigger Image onload
                mockImage.onload();
                resolve();
            }, 100);
        }).then(() => {
            expect(processImageSpy).toHaveBeenCalled();
        });
    });
});
