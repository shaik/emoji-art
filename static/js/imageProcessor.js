if (typeof window === 'undefined') {
    global.window = {};
    global.document = {
        addEventListener: jest.fn(),
        getElementById: jest.fn()
    };
}

class ImageProcessor {
    constructor() {
        this.MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        this.SUPPORTED_TYPES = ['image/jpeg', 'image/png'];
        this.initializeElements();
        this.setupEventListeners();
        this.logger = new Logger();
    }

    initializeElements() {
        this.fileInput = document.getElementById('imageUpload');
        this.processButton = document.getElementById('processImage');
        this.aspectRatioSelect = document.getElementById('aspectRatio');
        this.gridSizeSelect = document.getElementById('gridSize');
        this.previewCanvas = document.getElementById('previewCanvas');
        this.gridCanvas = document.getElementById('gridCanvas');
        this.statusMessage = document.getElementById('processingStatus');
        
        this.previewCtx = this.previewCanvas.getContext('2d');
        this.gridCtx = this.gridCanvas.getContext('2d');
    }

    setupEventListeners() {
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.processButton.addEventListener('click', () => this.processImage());
        this.aspectRatioSelect.addEventListener('change', () => {
            if (this.currentImage) {
                this.drawPreview(this.currentImage);
            }
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.logger.info(`File selected: ${file.name} (${this.formatFileSize(file.size)})`);

        if (!this.validateFile(file)) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const image = new Image();
            image.onload = () => {
                this.currentImage = image;
                this.drawPreview(image);
                this.processButton.disabled = false;
                this.logger.info('Image loaded successfully');
            };
            image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    validateFile(file) {
        if (file.size > this.MAX_FILE_SIZE) {
            this.showError(`File too large. Maximum size is ${this.formatFileSize(this.MAX_FILE_SIZE)}`);
            return false;
        }

        if (!this.SUPPORTED_TYPES.includes(file.type)) {
            this.showError('Unsupported file type. Please upload a PNG or JPEG image.');
            return false;
        }

        return true;
    }

    drawPreview(image) {
        const aspectRatio = this.parseAspectRatio(this.aspectRatioSelect.value);
        const { width, height } = this.calculateDimensions(image, aspectRatio);

        this.previewCanvas.width = width;
        this.previewCanvas.height = height;

        this.logger.debug(`Canvas resized to: ${width}x${height}`);
        this.logger.debug(`Aspect ratio set to: ${aspectRatio.x}:${aspectRatio.y}`);

        // Clear canvas
        this.previewCtx.clearRect(0, 0, width, height);

        // Draw image with proper cropping
        const scale = Math.max(width / image.width, height / image.height);
        const scaledWidth = image.width * scale;
        const scaledHeight = image.height * scale;
        const x = (width - scaledWidth) / 2;
        const y = (height - scaledHeight) / 2;

        this.previewCtx.drawImage(image, x, y, scaledWidth, scaledHeight);
    }

    processImage() {
        if (!this.currentImage) return;

        const gridSize = parseInt(this.gridSizeSelect.value);
        this.logger.info(`Processing image with grid size: ${gridSize}x${gridSize}`);

        // Set up grid canvas
        const { width, height } = this.previewCanvas;
        this.gridCanvas.width = width;
        this.gridCanvas.height = height;

        // Copy preview canvas to grid canvas
        this.gridCtx.drawImage(this.previewCanvas, 0, 0);

        // Calculate cell dimensions
        const cellWidth = width / gridSize;
        const cellHeight = height / gridSize;
        this.logger.debug(`Grid cell size: ${cellWidth}x${cellHeight} pixels`);

        // Process each cell
        const gridData = [];
        for (let y = 0; y < gridSize; y++) {
            const row = [];
            for (let x = 0; x < gridSize; x++) {
                const cellData = this.processGridCell(x, y, cellWidth, cellHeight);
                row.push(cellData);
                this.logger.debug(`Cell (${x},${y}) average color: ${cellData.color}`);
            }
            gridData.push(row);
        }

        // Show grid overlay
        this.drawGridOverlay(gridSize);

        this.logger.info('Image processing completed');
        this.showSuccess('Image processed successfully');

        return gridData;
    }

    processGridCell(x, y, cellWidth, cellHeight) {
        const imageData = this.gridCtx.getImageData(
            x * cellWidth,
            y * cellHeight,
            cellWidth,
            cellHeight
        );

        const { r, g, b } = this.calculateAverageColor(imageData.data);
        const color = this.rgbToHex(r, g, b);

        return {
            position: { x, y },
            color: color,
            averageRGB: { r, g, b }
        };
    }

    calculateAverageColor(data) {
        let r = 0, g = 0, b = 0, count = 0;

        for (let i = 0; i < data.length; i += 4) {
            r += data[i];
            g += data[i + 1];
            b += data[i + 2];
            count++;
        }

        return {
            r: Math.round(r / count),
            g: Math.round(g / count),
            b: Math.round(b / count)
        };
    }

    drawGridOverlay(gridSize) {
        const { width, height } = this.gridCanvas;
        const cellWidth = width / gridSize;
        const cellHeight = height / gridSize;

        this.gridCtx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        this.gridCtx.lineWidth = 1;

        for (let x = 0; x <= width; x += cellWidth) {
            this.gridCtx.beginPath();
            this.gridCtx.moveTo(x, 0);
            this.gridCtx.lineTo(x, height);
            this.gridCtx.stroke();
        }

        for (let y = 0; y <= height; y += cellHeight) {
            this.gridCtx.beginPath();
            this.gridCtx.moveTo(0, y);
            this.gridCtx.lineTo(width, y);
            this.gridCtx.stroke();
        }
    }

    // Utility methods
    parseAspectRatio(ratio) {
        const [x, y] = ratio.split(':').map(Number);
        return { x, y };
    }

    calculateDimensions(image, aspectRatio) {
        const maxWidth = 800;
        const maxHeight = 600;

        let width = maxWidth;
        let height = (width / aspectRatio.x) * aspectRatio.y;

        if (height > maxHeight) {
            height = maxHeight;
            width = (height / aspectRatio.y) * aspectRatio.x;
        }

        return { width, height };
    }

    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB'];
        let size = bytes;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)}${units[unitIndex]}`;
    }

    showError(message) {
        const statusMessage = document.getElementById('processingStatus');
        if (statusMessage) {
            statusMessage.textContent = message;
            statusMessage.className = 'error';
            this.logger.error(message);
        }
    }

    showSuccess(message) {
        const statusMessage = document.getElementById('processingStatus');
        if (statusMessage) {
            statusMessage.textContent = message;
            statusMessage.className = 'success';
            this.logger.info(message);
        }
    }
}

class Logger {
    constructor() {
        this.LOG_LEVELS = {
            DEBUG: 0,
            INFO: 1,
            ERROR: 2
        };
        this.currentLevel = this.LOG_LEVELS.DEBUG;
    }

    debug(message) {
        if (this.currentLevel <= this.LOG_LEVELS.DEBUG) {
            console.debug(`[DEBUG] ${message}`);
        }
    }

    info(message) {
        if (this.currentLevel <= this.LOG_LEVELS.INFO) {
            console.info(`[INFO] ${message}`);
        }
    }

    error(message) {
        if (this.currentLevel <= this.LOG_LEVELS.ERROR) {
            console.error(`[ERROR] ${message}`);
        }
    }
}

if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        window.imageProcessor = new ImageProcessor();
    });
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ImageProcessor, Logger };
}
