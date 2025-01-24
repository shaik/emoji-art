// Main JavaScript file for Emoji Art application

// Debug mode flag
let debugMode = false;

// Debug logging function
function debugLog(...args) {
    if (debugMode) {
        console.debug('[EmojiArt]', ...args);
    }
}

// DOM Elements
const fileInput = document.getElementById('fileInput');
const dragDropArea = document.getElementById('dragDropArea');
const imagePreview = document.getElementById('imagePreview');
const previewCanvas = document.getElementById('previewCanvas');
const gridCanvas = document.getElementById('gridCanvas');
const processImageBtn = document.getElementById('processImage');
const gridSizeSelect = document.getElementById('gridSize');
const errorMessage = document.getElementById('errorMessage');
const aspectRatioSelect = document.getElementById('aspectRatio');
const uploadForm = document.getElementById('uploadForm');

// Canvas contexts
const previewCtx = previewCanvas?.getContext('2d', { willReadFrequently: true });
const gridCtx = gridCanvas?.getContext('2d', { willReadFrequently: true });

// State
let currentImage = null;
let currentGridSize = parseInt(gridSizeSelect?.value || '32');
let currentAspectRatio = aspectRatioSelect?.value || '1:1';
let emojiDatabase = [];

// Load emoji database
async function loadEmojiDatabase() {
    try {
        debugLog('Loading emoji database...');
        const response = await fetch('/data/emoji_data.csv');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const csvText = await response.text();
        debugLog('Received emoji data:', csvText.substring(0, 100) + '...');
        
        // Parse CSV
        const lines = csvText.split('\n').filter(line => line.trim());
        // Skip header row if it exists
        const startIndex = lines[0].includes('Emoji,ASCII Code,Hex Color') ? 1 : 0;
        
        emojiDatabase = lines.slice(startIndex).map(line => {
            const [emoji, _, hexColor] = line.split(',');
            // Convert hex color to RGB
            const r = parseInt(hexColor.substring(1, 3), 16);
            const g = parseInt(hexColor.substring(3, 5), 16);
            const b = parseInt(hexColor.substring(5, 7), 16);
            return {
                emoji: emoji.trim(),
                color: { r, g, b }
            };
        });
        
        debugLog(`Loaded ${emojiDatabase.length} emojis from database`);
    } catch (error) {
        console.error('Error loading emoji database:', error);
        debugLog('Error loading emoji database, using fallback');
        // Fallback to basic emoji set if loading fails
        emojiDatabase = [
            { emoji: '⬜', color: { r: 255, g: 255, b: 255 } }, // White
            { emoji: '⬛', color: { r: 0, g: 0, b: 0 } },       // Black
            { emoji: '🟨', color: { r: 255, g: 255, b: 0 } },   // Yellow
            { emoji: '🟦', color: { r: 0, g: 0, b: 255 } },     // Blue
            { emoji: '🟥', color: { r: 255, g: 0, b: 0 } },     // Red
            { emoji: '🟩', color: { r: 0, g: 255, b: 0 } },     // Green
            { emoji: '🟧', color: { r: 255, g: 165, b: 0 } },   // Orange
            { emoji: '🟫', color: { r: 139, g: 69, b: 19 } },   // Brown
            { emoji: '🟪', color: { r: 128, g: 0, b: 128 } },   // Purple
        ];
    }
}

// Event Listeners
function initializeEventListeners() {
    fileInput?.addEventListener('change', handleFileSelect);
    dragDropArea?.addEventListener('dragover', handleDragOver);
    dragDropArea?.addEventListener('drop', handleDrop);
    dragDropArea?.addEventListener('click', () => fileInput.click());
    gridSizeSelect?.addEventListener('change', handleGridSizeChange);
    aspectRatioSelect?.addEventListener('change', handleAspectRatioChange);
    
    // Prevent form submission and handle process image click
    uploadForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        if (currentImage) {
            processImage(currentImage);
        } else {
            showError('Please upload an image first');
        }
    });
}

if (typeof window !== 'undefined') {
    initializeEventListeners();
    loadEmojiDatabase();
    document.documentElement.style.setProperty('--grid-size', currentGridSize);
}

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDrop(event) {
    event.preventDefault();
    dragDropArea.classList.remove('drag-over');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    dragDropArea.classList.add('drag-over');
}

function handleGridSizeChange(event) {
    const newSize = parseInt(event.target.value);
    if (!isNaN(newSize) && newSize > 0) {
        currentGridSize = newSize;
        document.documentElement.style.setProperty('--grid-size', newSize);
        if (currentImage) {
            processImage(currentImage);
        }
    }
}

function handleAspectRatioChange(event) {
    const select = document.getElementById('aspectRatio');
    const newRatio = select.value;
    if (newRatio) {
        currentAspectRatio = newRatio;
        debugLog('Aspect ratio changed:', currentAspectRatio);
        if (currentImage) {
            processImage(currentImage);
        }
    }
}

// Image processing functions
function processFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        showError('Please upload an image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            currentImage = img;
            processImageBtn.disabled = false; // Enable the button when image is loaded
            processImage(img);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function processImage(img) {
    if (!img) {
        showError('No image loaded');
        return;
    }

    const dimensions = calculateDimensions(img);
    const canvas = document.getElementById('previewCanvas');
    if (!canvas) return;

    canvas.width = dimensions.width;
    canvas.height = dimensions.height;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return;

    ctx.drawImage(img, 0, 0, dimensions.width, dimensions.height);
    drawGrid(ctx, dimensions.width, dimensions.height, currentGridSize);
    debugLog('Image processed with grid size:', currentGridSize);
    renderEmojiGrid();
    debugLog('Image processed and emoji art rendered');
}

function calculateDimensions(img) {
    const maxWidth = 800;
    const maxHeight = 800;
    let width = img.width;
    let height = img.height;

    // First, scale down if too large while maintaining original aspect ratio
    if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
    }

    return { width, height };
}

function getAverageColor(x, y, width, height) {
    if (!previewCtx) {
        return { r: 0, g: 0, b: 0 };
    }

    const imageData = previewCtx.getImageData(x, y, width, height);
    const data = imageData.data;
    let r = 0, g = 0, b = 0;
    const pixels = data.length / 4;

    for (let i = 0; i < data.length; i += 4) {
        r += data[i];
        g += data[i + 1];
        b += data[i + 2];
    }

    return {
        r: Math.round(r / pixels),
        g: Math.round(g / pixels),
        b: Math.round(b / pixels)
    };
}

function drawGrid(ctx, width, height, gridSize) {
    if (!gridCtx) return;

    const cellWidth = width / gridSize;
    const cellHeight = height / gridSize;

    gridCanvas.width = width;
    gridCanvas.height = height;

    gridCtx.clearRect(0, 0, gridCanvas.width, gridCanvas.height);

    // Draw cells
    for (let y = 0; y < gridSize; y++) {
        for (let x = 0; x < gridSize; x++) {
            const color = getAverageColor(
                Math.floor(x * cellWidth),
                Math.floor(y * cellHeight),
                Math.ceil(cellWidth),
                Math.ceil(cellHeight)
            );
            gridCtx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`;
            gridCtx.fillRect(
                x * cellWidth,
                y * cellHeight,
                cellWidth,
                cellHeight
            );
        }
    }

    // Draw grid lines
    gridCtx.strokeStyle = '#ccc';
    gridCtx.lineWidth = 1;

    // Vertical lines
    for (let x = 0; x <= gridSize; x++) {
        gridCtx.beginPath();
        gridCtx.moveTo(x * cellWidth, 0);
        gridCtx.lineTo(x * cellWidth, gridCanvas.height);
        gridCtx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= gridSize; y++) {
        gridCtx.beginPath();
        gridCtx.moveTo(0, y * cellHeight);
        gridCtx.lineTo(gridCanvas.width, y * cellHeight);
        gridCtx.stroke();
    }
}

function showError(message) {
    debugLog('Error:', message);
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 3000);
    }
}

function findClosestEmoji(color) {
    debugLog(`Finding closest emoji for color: rgb(${color.r}, ${color.g}, ${color.b})`);
    
    let minDistance = Infinity;
    let closestEmoji = emojiDatabase[0];

    for (const emojiData of emojiDatabase) {
        const distance = Math.sqrt(
            Math.pow(color.r - emojiData.color.r, 2) +
            Math.pow(color.g - emojiData.color.g, 2) +
            Math.pow(color.b - emojiData.color.b, 2)
        );

        if (distance < minDistance) {
            minDistance = distance;
            closestEmoji = emojiData;
        }
    }

    debugLog(`Selected emoji: ${closestEmoji.emoji} with distance: ${minDistance.toFixed(2)}`);
    return closestEmoji.emoji;
}

function renderEmojiGrid() {
    const startTime = performance.now();
    debugLog('Starting emoji grid rendering');

    const emojiArtOutput = document.getElementById('emojiArtOutput');
    if (!emojiArtOutput) {
        console.error('Could not find emoji art output element');
        return;
    }

    let emojiArt = '';
    const cellWidth = previewCanvas.width / currentGridSize;
    const cellHeight = previewCanvas.height / currentGridSize;

    // Create emoji grid
    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            const color = getAverageColor(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
            const emoji = findClosestEmoji(color);
            emojiArt += `<span>${emoji}</span>`;
        }
    }

    // Set the emoji art
    emojiArtOutput.innerHTML = emojiArt;
    
    const endTime = performance.now();
    debugLog(`Emoji grid rendered in ${(endTime - startTime).toFixed(2)}ms`);
}

// Initialize debug mode from localStorage or URL parameter
function initDebugMode() {
    const urlParams = new URLSearchParams(window.location?.search);
    const debugParam = urlParams.get('debug');
    const storedDebug = localStorage?.getItem('debugMode');

    if (debugParam === 'true' || storedDebug === 'true') {
        debugMode = true;
        debugLog('Debug mode: enabled');
    }
}

// Toggle debug mode
function toggleDebugMode() {
    debugMode = !debugMode;
    localStorage?.setItem('debugMode', debugMode);
    debugLog('Debug mode:', debugMode ? 'enabled' : 'disabled');
}

// Placeholder for future functionality
const EmojiArt = {
    init() {
        debugLog('Initializing EmojiArt');
    },

    createArt() {
        debugLog('Creating emoji art');
    },

    saveArt() {
        debugLog('Saving emoji art');
    }
};

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculateDimensions,
        getAverageColor,
        drawGrid,
        showError,
        handleGridSizeChange,
        handleAspectRatioChange,
        toggleDebugMode,
        processFile,
        processImage,
        get debugMode() { return debugMode; },
        set debugMode(value) { debugMode = value; },
        get currentGridSize() { return currentGridSize; },
        set currentGridSize(value) { currentGridSize = parseInt(value) || 32; },
        get currentAspectRatio() { return currentAspectRatio; },
        set currentAspectRatio(value) { currentAspectRatio = value || '1:1'; },
        initDebugMode,
        EmojiArt
    };
}
