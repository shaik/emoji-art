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

// Color matching optimization
const colorCache = new Map();
const labCache = new Map();  // Cache for RGB to LAB conversions
const COLOR_BUCKETS = 32; // Number of buckets per channel

function getColorKey(r, g, b) {
    // More precise key than quantized version
    return `${r},${g},${b}`;
}

function getQuantizedKey(r, g, b) {
    const qr = Math.floor(r / 256 * COLOR_BUCKETS);
    const qg = Math.floor(g / 256 * COLOR_BUCKETS);
    const qb = Math.floor(b / 256 * COLOR_BUCKETS);
    return `${qr},${qg},${qb}`;
}

function rgbToLabCached(r, g, b) {
    const key = getColorKey(r, g, b);
    if (labCache.has(key)) {
        return labCache.get(key);
    }
    
    const lab = rgbToLab(r, g, b);
    labCache.set(key, lab);
    return lab;
}

function quantizeColor(r, g, b) {
    const qr = Math.floor(r / 256 * COLOR_BUCKETS);
    const qg = Math.floor(g / 256 * COLOR_BUCKETS);
    const qb = Math.floor(b / 256 * COLOR_BUCKETS);
    return `${qr},${qg},${qb}`;
}

// Initialize KD-tree with emoji database
function initializeEmojiKDTree() {
    if (emojiKDTree) return;
    
    // Convert emoji colors to LAB space using cached conversion
    const emojiLabData = emojiDatabase.map(emoji => ({
        emoji: emoji.emoji,
        lab: rgbToLabCached(emoji.color.r, emoji.color.g, emoji.color.b)
    }));
    
    // Create and build KD-tree
    emojiKDTree = new ColorKDTree();
    emojiKDTree.buildTree(emojiLabData);
}

function findClosestEmoji(color) {
    if (!emojiDatabase.length) return '⬜';
    
    // Try exact cache first
    const exactKey = getColorKey(color.r, color.g, color.b);
    if (colorCache.has(exactKey)) {
        return colorCache.get(exactKey);
    }
    
    // Try quantized cache next
    const quantizedKey = getQuantizedKey(color.r, color.g, color.b);
    if (colorCache.has(quantizedKey)) {
        return colorCache.get(quantizedKey);
    }
    
    // Initialize KD-tree if needed
    initializeEmojiKDTree();
    
    // Convert target color to LAB using cached conversion
    const targetLab = rgbToLabCached(color.r, color.g, color.b);
    
    // Find nearest emoji using KD-tree
    const closestEmoji = emojiKDTree.findNearest(targetLab);
    
    // Cache the result in both exact and quantized caches
    colorCache.set(exactKey, closestEmoji);
    colorCache.set(quantizedKey, closestEmoji);
    
    return closestEmoji || '⬜';
}

function clearColorCache() {
    colorCache.clear();
    labCache.clear();
    emojiKDTree = null;
}

function rgbToLab(r, g, b) {
    // Convert RGB to XYZ
    const rgb = [r / 255, g / 255, b / 255].map(v => 
        v > 0.04045 ? Math.pow((v + 0.055) / 1.055, 2.4) : v / 12.92
    );
    
    // Scale for XYZ conversion
    const [rx, gx, bx] = rgb.map(v => v * 100);
    
    // Convert to XYZ
    const x = rx * 0.4124 + gx * 0.3576 + bx * 0.1805;
    const y = rx * 0.2126 + gx * 0.7152 + bx * 0.0722;
    const z = rx * 0.0193 + gx * 0.1192 + bx * 0.9505;
    
    // XYZ to Lab
    const eps = 0.008856;
    const kappa = 903.3;
    const ref = [95.047, 100.000, 108.883]; // D65 illuminant
    
    const f = [x, y, z].map((v, i) => {
        const vr = v / ref[i];
        return vr > eps ? Math.pow(vr, 1/3) : (kappa * vr + 16) / 116;
    });
    
    return [
        (116 * f[1]) - 16,     // L
        500 * (f[0] - f[1]),   // a
        200 * (f[1] - f[2])    // b
    ];
}

function labDistance(lab1, lab2) {
    return Math.sqrt(
        Math.pow(lab1[0] - lab2[0], 2) +
        Math.pow(lab1[1] - lab2[1], 2) +
        Math.pow(lab1[2] - lab2[2], 2)
    );
}

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

    // Update handle positions
    const handles = [
        { class: 'top-left', x: -10, y: -10 },
        { class: 'top-right', x: selection.width - 10, y: -10 },
        { class: 'bottom-left', x: -10, y: selection.height - 10 },
        { class: 'bottom-right', x: selection.width - 10, y: selection.height - 10 }
    ];

    // Clear existing handles
    const existingHandles = selectionBox.querySelectorAll('.resize-handle');
    existingHandles.forEach(handle => handle.remove());

    // Create new handles
    handles.forEach(handle => {
        const div = document.createElement('div');
        div.className = `resize-handle ${handle.class}`;
        div.style.left = `${handle.x}px`;
        div.style.top = `${handle.y}px`;
        div.style.width = '20px';
        div.style.height = '20px';
        div.style.position = 'absolute';
        div.style.backgroundColor = 'white';
        div.style.border = '2px solid #007bff';
        div.style.borderRadius = '50%';
        div.style.cursor = 'pointer';
        div.style.zIndex = '1000';
        div.style.touchAction = 'none';
        selectionBox.appendChild(div);
    });
}

function handleSelectionStart(e) {
    const img = imagePreview.querySelector('img');
    if (!img) return;

    const rect = img.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    // Check if clicking on a handle
    const handleSize = 20;
    const handles = [
        { name: 'top-left', x: selection.x - handleSize/2, y: selection.y - handleSize/2 },
        { name: 'top-right', x: selection.x + selection.width - handleSize/2, y: selection.y - handleSize/2 },
        { name: 'bottom-left', x: selection.x - handleSize/2, y: selection.y + selection.height - handleSize/2 },
        { name: 'bottom-right', x: selection.x + selection.width - handleSize/2, y: selection.y + selection.height - handleSize/2 }
    ];

    for (const handle of handles) {
        if (Math.abs(x - handle.x) < handleSize && Math.abs(y - handle.y) < handleSize) {
            isResizing = true;
            currentHandle = handle.name;
            break;
        }
    }

    if (!isResizing) {
        isDragging = true;
        dragStart = { x: x - selection.x, y: y - selection.y };
    }

    e.preventDefault();
}

function handleSelectionMove(e) {
    if (!isDragging && !isResizing) return;

    const img = imagePreview.querySelector('img');
    if (!img) return;

    const rect = img.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const maxX = rect.width;
    const maxY = rect.height;

    if (isResizing) {
        const newX = clientX - rect.left;
        const newY = clientY - rect.top;

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
        selection.x = Math.max(0, Math.min(clientX - dragStart.x - rect.left, maxX - selection.width));
        selection.y = Math.max(0, Math.min(clientY - dragStart.y - rect.top, maxY - selection.height));
    }

    updateSelectionBox();
    
    // Debounce the processing to avoid too frequent updates
    clearTimeout(window.selectionTimeout);
    window.selectionTimeout = setTimeout(() => {
        requestAnimationFrame(updateEmojiArt);
    }, CONFIG.UPDATE_DELAY);

    e.preventDefault();
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
    const scale = currentImage.naturalWidth / img.offsetWidth;
    
    // Calculate dimensions for the selected area
    const dimensions = calculateDimensions(currentImage);
    
    // Set canvas dimensions based on selection
    previewCanvas.width = selection.width * scale;
    previewCanvas.height = selection.height * scale;

    // Clear the canvas
    previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);

    // Draw only the selected portion of the image
    previewCtx.drawImage(
        currentImage,
        selection.x * scale,
        selection.y * scale,
        selection.width * scale,
        selection.height * scale,
        0,
        0,
        previewCanvas.width,
        previewCanvas.height
    );

    // Process the grid
    const gridData = processGrid(previewCanvas, dimensions);
    renderEmojiGrid(gridData);
}

function processGrid(canvas, dimensions) {
    const ctx = canvas.getContext('2d');
    
    // Calculate cell dimensions
    const cellWidth = Math.floor(canvas.width / dimensions.width);
    const cellHeight = Math.floor(canvas.height / dimensions.height);
    
    const grid = {
        width: dimensions.width,
        height: dimensions.height,
        data: []
    };
    
    // Process each cell
    for (let y = 0; y < dimensions.height; y++) {
        const row = [];
        for (let x = 0; x < dimensions.width; x++) {
            const startX = x * cellWidth;
            const startY = y * cellHeight;
            
            // Get average color for this cell
            const color = getAverageColor(startX, startY, cellWidth, cellHeight);
            const emoji = findClosestEmoji(color);
            row.push(emoji);
        }
        grid.data.push(row);
    }
    
    return grid;
}

function calculateDimensions(img) {
    const gridSize = parseInt(gridSizeSelect?.value || '32');
    
    // Calculate scale between displayed image and original image
    const scale = img.naturalWidth / imagePreview.querySelector('img').offsetWidth;
    
    // Get selection dimensions in original image coordinates
    const selectionWidth = selection.width * scale;
    const selectionHeight = selection.height * scale;
    
    // Calculate grid dimensions maintaining aspect ratio
    let gridWidth = gridSize;
    let gridHeight = Math.round(gridSize * (selectionHeight / selectionWidth));
    
    // Calculate canvas dimensions
    let canvasWidth = Math.min(selectionWidth, CONFIG.MAX_CANVAS_SIZE);
    let canvasHeight = Math.round(canvasWidth * (selectionHeight / selectionWidth));
    
    // Adjust if height exceeds max
    if (canvasHeight > CONFIG.MAX_CANVAS_SIZE) {
        canvasHeight = CONFIG.MAX_CANVAS_SIZE;
        canvasWidth = Math.round(canvasHeight * (selectionWidth / selectionHeight));
    }
    
    return {
        width: gridWidth,
        height: gridHeight,
        canvasWidth,
        canvasHeight
    };
}

function renderEmojiGrid(grid) {
    const emojiArtOutput = document.getElementById('emojiArtOutput');
    if (!emojiArtOutput) return;

    // Clear any existing content
    emojiArtOutput.innerHTML = '';
    
    // Set grid dimensions
    emojiArtOutput.style.display = 'grid';
    emojiArtOutput.style.gridTemplateColumns = `repeat(${grid.width}, 1fr)`;
    emojiArtOutput.style.gap = '0';
    emojiArtOutput.style.width = '100%';
    emojiArtOutput.style.maxWidth = '100%';
    
    // Create and append emoji elements
    for (let y = 0; y < grid.height; y++) {
        for (let x = 0; x < grid.width; x++) {
            const span = document.createElement('span');
            span.textContent = grid.data[y][x];
            span.style.display = 'inline-block';
            span.style.lineHeight = '1';
            emojiArtOutput.appendChild(span);
        }
    }
    
    // Adjust container width based on grid size
    const container = document.querySelector('.emoji-art-container');
    if (container) {
        if (grid.width <= 32) {
            container.style.maxWidth = '800px';
        } else if (grid.width <= 64) {
            container.style.maxWidth = '1000px';
        } else {
            container.style.maxWidth = '1200px';
        }
    }
}

function processImage(file) {
    if (!file || !(file instanceof Blob)) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // Clear previous state
            clearColorCache();
            
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

function getAverageColor(x, y, width, height) {
    try {
        const imageData = previewCtx.getImageData(
            Math.floor(x),
            Math.floor(y),
            Math.min(Math.ceil(width), previewCanvas.width - Math.floor(x)),
            Math.min(Math.ceil(height), previewCanvas.height - Math.floor(y))
        );
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
    } catch (error) {
        console.error('Error getting average color:', error);
        return { r: 255, g: 255, b: 255 }; // Default to white on error
    }
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
        
        // Touch events
        selectionBox.addEventListener('touchstart', handleSelectionStart, { passive: false });
        document.addEventListener('touchmove', handleSelectionMove, { passive: false });
        document.addEventListener('touchend', handleSelectionEnd);
        document.addEventListener('touchcancel', handleSelectionEnd);
    }
    
    // Prevent default touch behavior to avoid scrolling while dragging
    document.addEventListener('touchmove', function(e) {
        if (isDragging || isResizing) {
            e.preventDefault();
        }
    }, { passive: false });
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

// Load emoji database
async function loadEmojiDatabase() {
    try {
        debugLog('Loading emoji database...');
        const response = await fetch('/static/data/emoji_data.csv');
        
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
    function initializeApp() {
        initializeEventListeners();
        loadEmojiDatabase();
        document.documentElement.style.setProperty('--grid-size', currentGridSize);
    }

    document.addEventListener('DOMContentLoaded', initializeApp);
}
