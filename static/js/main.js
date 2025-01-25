// Main JavaScript file for Emoji Art application

// Debug mode flag
let debugMode = false;

// Debug logging function
function debugLog(...args) {
    if (debugMode) {
        console.debug('[EmojiArt]', ...args);
    }
}

// Configuration
const CONFIG = {
    UPDATE_DELAY: 500, // ms to wait after selection changes before updating
    MAX_CANVAS_SIZE: 800, // maximum canvas dimension
    MIN_SELECTION_SIZE: 10 // minimum selection dimension
};

// DOM Elements
const fileInput = document.getElementById('fileInput');
const dragDropArea = document.getElementById('dragDropArea');
const imagePreview = document.getElementById('imagePreview');
const previewCanvas = document.getElementById('previewCanvas');
const gridSizeSelect = document.getElementById('gridSize');
const errorMessage = document.getElementById('errorMessage');
const uploadForm = document.getElementById('uploadForm');
const increaseFontBtn = document.getElementById('increaseFontSize');
const decreaseFontBtn = document.getElementById('decreaseFontSize');
const fontSizeDisplay = document.getElementById('fontSizeDisplay');
const selectionBox = document.querySelector('.selection-box');
const selectionOverlay = document.getElementById('selectionOverlay');

// Canvas context
const previewCtx = previewCanvas?.getContext('2d', { willReadFrequently: true });

// State
let currentImage = null;
let currentGridSize = parseInt(gridSizeSelect?.value || '32');
let emojiDatabase = [];
let baseFontSize = 0;
let currentFontSizePercent = 100;
let selection = { x: 0, y: 0, width: 0, height: 0 };
let isDragging = false;
let isResizing = false;
let dragStart = { x: 0, y: 0 };
let currentHandle = null;

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

// Selection Functions
function initializeSelection() {
    if (!currentImage || !selectionBox || !selectionOverlay) return;
    
    const img = imagePreview.querySelector('img');
    if (!img) return;

    // Wait for image to be fully loaded
    if (!img.complete) {
        img.onload = () => initializeSelection();
        return;
    }

    const rect = img.getBoundingClientRect();
    
    // Set initial selection to full image
    selection = {
        x: 0,
        y: 0,
        width: rect.width,
        height: rect.height
    };

    // Show selection overlay and update its position
    selectionOverlay.style.display = 'block';
    selectionOverlay.style.width = `${rect.width}px`;
    selectionOverlay.style.height = `${rect.height}px`;
    updateSelectionBox();
}

function updateSelectionBox() {
    if (!selectionBox) return;
    
    selectionBox.style.left = `${selection.x}px`;
    selectionBox.style.top = `${selection.y}px`;
    selectionBox.style.width = `${selection.width}px`;
    selectionBox.style.height = `${selection.height}px`;
}

function handleSelectionStart(e) {
    if (!selectionBox) return;

    const target = e.target;
    const rect = selectionBox.getBoundingClientRect();
    
    if (target.classList.contains('resize-handle')) {
        isResizing = true;
        currentHandle = target.classList[1]; // get handle position (e.g., 'top-left')
    } else if (target === selectionBox || target.parentElement === selectionBox) {
        isDragging = true;
    } else {
        return;
    }

    dragStart = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };

    e.preventDefault();
}

function handleSelectionMove(e) {
    if (!isDragging && !isResizing) return;

    const img = imagePreview.querySelector('img');
    if (!img) return;

    const rect = img.getBoundingClientRect();
    const maxX = rect.width;
    const maxY = rect.height;

    if (isResizing) {
        const newX = e.clientX - rect.left;
        const newY = e.clientY - rect.top;

        if (currentHandle.includes('left')) {
            const newWidth = selection.x + selection.width - newX;
            if (newWidth > CONFIG.MIN_SELECTION_SIZE) {
                selection.width = newWidth;
                selection.x = Math.max(0, Math.min(newX, selection.x + selection.width - CONFIG.MIN_SELECTION_SIZE));
            }
        }
        if (currentHandle.includes('right')) {
            selection.width = Math.max(CONFIG.MIN_SELECTION_SIZE, Math.min(newX - selection.x, maxX - selection.x));
        }
        if (currentHandle.includes('top')) {
            const newHeight = selection.y + selection.height - newY;
            if (newHeight > CONFIG.MIN_SELECTION_SIZE) {
                selection.height = newHeight;
                selection.y = Math.max(0, Math.min(newY, selection.y + selection.height - CONFIG.MIN_SELECTION_SIZE));
            }
        }
        if (currentHandle.includes('bottom')) {
            selection.height = Math.max(CONFIG.MIN_SELECTION_SIZE, Math.min(newY - selection.y, maxY - selection.y));
        }
    } else if (isDragging) {
        selection.x = Math.max(0, Math.min(e.clientX - dragStart.x - rect.left, maxX - selection.width));
        selection.y = Math.max(0, Math.min(e.clientY - dragStart.y - rect.top, maxY - selection.height));
    }

    updateSelectionBox();
    
    // Debounce the processing to avoid too frequent updates
    clearTimeout(window.selectionTimeout);
    window.selectionTimeout = setTimeout(() => {
        requestAnimationFrame(updateEmojiArt);
    }, CONFIG.UPDATE_DELAY);
}

function handleSelectionEnd() {
    isDragging = false;
    isResizing = false;
    currentHandle = null;
}

function updateEmojiArt() {
    if (!currentImage || !previewCanvas || !previewCtx) return;

    const img = imagePreview.querySelector('img');
    if (!img) return;

    // Calculate scale between displayed image and original image
    const scale = img.naturalWidth / img.offsetWidth;
    
    // Set canvas dimensions based on selection
    const dimensions = calculateDimensions(currentImage);
    previewCanvas.width = dimensions.canvasWidth;
    previewCanvas.height = dimensions.canvasHeight;

    // Create a temporary canvas for the selected portion
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = selection.width * scale;
    tempCanvas.height = selection.height * scale;

    // Draw only the selected portion
    tempCtx.drawImage(
        img,
        selection.x * scale,
        selection.y * scale,
        selection.width * scale,
        selection.height * scale,
        0,
        0,
        tempCanvas.width,
        tempCanvas.height
    );

    // Draw the selected portion to the preview canvas
    previewCtx.drawImage(
        tempCanvas,
        0,
        0,
        previewCanvas.width,
        previewCanvas.height
    );

    renderEmojiGrid();
}

// Event Listeners
function initializeEventListeners() {
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    if (dragDropArea) {
        dragDropArea.addEventListener('dragover', handleDragOver);
        dragDropArea.addEventListener('drop', handleDrop);
        dragDropArea.addEventListener('click', () => fileInput.click());
    }

    if (gridSizeSelect) {
        gridSizeSelect.addEventListener('change', () => {
            if (currentImage) {
                updateEmojiArt();
            }
        });
    }

    if (increaseFontBtn) {
        increaseFontBtn.addEventListener('click', () => {
            adjustFontSize(10); // Increase by 10%
        });
    }

    if (decreaseFontBtn) {
        decreaseFontBtn.addEventListener('click', () => {
            adjustFontSize(-10); // Decrease by 10%
        });
    }

    if (selectionBox) {
        selectionBox.addEventListener('mousedown', handleSelectionStart);
        document.addEventListener('mousemove', handleSelectionMove);
        document.addEventListener('mouseup', handleSelectionEnd);
    }
}

function adjustFontSize(change) {
    const emojiArt = document.getElementById('emojiArtOutput');
    if (!emojiArt) return;

    // Initialize base font size if not set
    if (!baseFontSize) {
        const computedStyle = window.getComputedStyle(emojiArt);
        baseFontSize = parseFloat(computedStyle.fontSize);
    }

    // Update percentage
    currentFontSizePercent = Math.max(50, Math.min(200, currentFontSizePercent + change));
    
    // Update display
    if (fontSizeDisplay) {
        fontSizeDisplay.textContent = `${currentFontSizePercent}%`;
    }

    // Apply new font size
    const newSize = (baseFontSize * currentFontSizePercent / 100);
    emojiArt.style.fontSize = `${newSize}px`;
}

function updateEmojiArtFontSize() {
    const emojiArt = document.getElementById('emojiArtOutput');
    if (emojiArt) {
        const baseSize = parseInt(window.getComputedStyle(emojiArt).fontSize);
        emojiArt.style.fontSize = `${baseSize * currentFontSizePercent / 100}px`;
    }
}

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file');
            return;
        }
        processImage(file);
    }
}

function handleDrop(event) {
    event.preventDefault();
    dragDropArea.classList.remove('dragover');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file');
            return;
        }
        processImage(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    dragDropArea.classList.add('dragover');
}

// Image processing functions
function processFile(file) {
    if (!file || !(file instanceof Blob)) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // Update preview
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Uploaded image">`;
            currentImage = img;

            // Initialize selection after image is loaded
            setTimeout(() => {
                initializeSelection();
                updateEmojiArt();
            }, 100);
        };
        img.src = e.target.result;
        
        // Show preview
        imagePreview.innerHTML = '';
        const preview = new Image();
        preview.src = e.target.result;
        preview.className = 'preview-image';
        imagePreview.appendChild(preview);
    };
    reader.readAsDataURL(file);
}

function processImage(file) {
    if (!file || !(file instanceof Blob)) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // Update preview
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Uploaded image">`;
            currentImage = img;

            // Initialize selection after image is loaded
            setTimeout(() => {
                initializeSelection();
                updateEmojiArt();
            }, 100);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function calculateDimensions(img) {
    const gridWidth = parseInt(gridSizeSelect?.value || '32');
    const aspectRatio = img.height / img.width;
    const gridHeight = Math.round(gridWidth * aspectRatio);
    
    // Calculate canvas dimensions
    let canvasWidth = img.width;
    let canvasHeight = img.height;
    
    if (canvasWidth > CONFIG.MAX_CANVAS_SIZE || canvasHeight > CONFIG.MAX_CANVAS_SIZE) {
        const ratio = Math.min(CONFIG.MAX_CANVAS_SIZE / canvasWidth, CONFIG.MAX_CANVAS_SIZE / canvasHeight);
        canvasWidth = canvasWidth * ratio;
        canvasHeight = canvasHeight * ratio;
    }
    
    return {
        width: gridWidth,
        height: gridHeight,
        canvasWidth,
        canvasHeight
    };
}

function getAverageColor(x, y, width, height) {
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

function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 3000);
    }
}

function findClosestEmoji(color) {
    if (!emojiDatabase.length) return '⬜';
    
    let minDistance = Infinity;
    let closestEmoji = null;
    
    for (const emoji of emojiDatabase) {
        const emojiColor = emoji.color;
        const distance = Math.sqrt(
            Math.pow(color.r - emojiColor.r, 2) +
            Math.pow(color.g - emojiColor.g, 2) +
            Math.pow(color.b - emojiColor.b, 2)
        );
        
        if (distance < minDistance) {
            minDistance = distance;
            closestEmoji = emoji.emoji;
        }
    }
    
    return closestEmoji || '⬜';
}

function renderEmojiGrid() {
    const emojiArtOutput = document.getElementById('emojiArtOutput');
    if (!emojiArtOutput || !previewCtx || !currentImage) return;

    const dimensions = calculateDimensions(currentImage);
    const gridWidth = dimensions.width;
    const gridHeight = dimensions.height;
    
    const cellWidth = dimensions.canvasWidth / gridWidth;
    const cellHeight = dimensions.canvasHeight / gridHeight;

    let emojiGrid = '';
    
    // Set the data-grid-size attribute for responsive sizing
    emojiArtOutput.setAttribute('data-grid-width', gridWidth);
    emojiArtOutput.setAttribute('data-grid-height', gridHeight);

    // Set grid template columns
    emojiArtOutput.style.gridTemplateColumns = `repeat(${gridWidth}, 1fr)`;
    
    for (let y = 0; y < gridHeight; y++) {
        for (let x = 0; x < gridWidth; x++) {
            const color = getAverageColor(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
            const emoji = findClosestEmoji(color);
            emojiGrid += `<span>${emoji}</span>`;
        }
    }

    emojiArtOutput.innerHTML = emojiGrid;
    emojiArtOutput.style.fontSize = ''; // Reset font size to get proper base size
    
    // Reset base font size for new grid
    baseFontSize = parseFloat(window.getComputedStyle(emojiArtOutput).fontSize);
    
    // Reapply current font size percentage
    if (currentFontSizePercent !== 100) {
        const newSize = (baseFontSize * currentFontSizePercent / 100);
        emojiArtOutput.style.fontSize = `${newSize}px`;
    }
    
    // Adjust container width based on grid size
    const container = document.querySelector('.emoji-art-container');
    if (container) {
        if (gridWidth <= 32) {
            container.style.maxWidth = '800px';
        } else if (gridWidth <= 64) {
            container.style.maxWidth = '1000px';
        } else {
            container.style.maxWidth = '1200px';
        }
    }

    debugLog(`Grid rendered with dimensions: ${gridWidth}x${gridHeight}`);
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
        showError,
        handleGridSizeChange,
        toggleDebugMode,
        processFile,
        processImage,
        get debugMode() { return debugMode; },
        set debugMode(value) { debugMode = value; },
        get currentGridSize() { return currentGridSize; },
        set currentGridSize(value) { currentGridSize = parseInt(value) || 32; },
        initDebugMode,
        EmojiArt
    };
}

if (typeof window !== 'undefined') {
    initializeEventListeners();
    loadEmojiDatabase();
    document.documentElement.style.setProperty('--grid-size', currentGridSize);
}
