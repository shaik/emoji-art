// Grid processing Web Worker

// Color matching functions
function rgbToLab(r, g, b) {
    // First, convert RGB to XYZ
    let rr = r / 255;
    let gg = g / 255;
    let bb = b / 255;

    // Gamma correction
    rr = rr > 0.04045 ? Math.pow((rr + 0.055) / 1.055, 2.4) : rr / 12.92;
    gg = gg > 0.04045 ? Math.pow((gg + 0.055) / 1.055, 2.4) : gg / 12.92;
    bb = bb > 0.04045 ? Math.pow((bb + 0.055) / 1.055, 2.4) : bb / 12.92;

    // Convert to XYZ
    rr *= 100;
    gg *= 100;
    bb *= 100;

    const x = rr * 0.4124 + gg * 0.3576 + bb * 0.1805;
    const y = rr * 0.2126 + gg * 0.7152 + bb * 0.0722;
    const z = rr * 0.0193 + gg * 0.1192 + bb * 0.9505;

    // Then XYZ to Lab
    const xn = 95.047;
    const yn = 100.000;
    const zn = 108.883;

    const fx = x / xn > 0.008856 ? Math.pow(x / xn, 1/3) : (7.787 * x / xn) + 16/116;
    const fy = y / yn > 0.008856 ? Math.pow(y / yn, 1/3) : (7.787 * y / yn) + 16/116;
    const fz = z / zn > 0.008856 ? Math.pow(z / zn, 1/3) : (7.787 * z / zn) + 16/116;

    const L = (116 * fy) - 16;
    const a = 500 * (fx - fy);
    const b = 200 * (fy - fz);

    return [L, a, b];
}

function labDistance(lab1, lab2) {
    const dL = lab1[0] - lab2[0];
    const da = lab1[1] - lab2[1];
    const db = lab1[2] - lab2[2];
    return Math.sqrt(dL * dL + da * da + db * db);
}

function getAverageColor(imageData, x, y, width, height, cellWidth, cellHeight) {
    let r = 0, g = 0, b = 0;
    let count = 0;

    const startX = Math.floor(x * cellWidth);
    const startY = Math.floor(y * cellHeight);
    const endX = Math.min(Math.floor((x + 1) * cellWidth), width);
    const endY = Math.min(Math.floor((y + 1) * cellHeight), height);

    for (let py = startY; py < endY; py++) {
        for (let px = startX; px < endX; px++) {
            const i = (py * width + px) * 4;
            r += imageData.data[i];
            g += imageData.data[i + 1];
            b += imageData.data[i + 2];
            count++;
        }
    }

    return {
        r: Math.round(r / count),
        g: Math.round(g / count),
        b: Math.round(b / count)
    };
}

function findClosestEmoji(color, emojiDatabase) {
    const targetLab = rgbToLab(color.r, color.g, color.b);
    
    let minDistance = Infinity;
    let closestEmoji = null;
    
    for (const emoji of emojiDatabase) {
        const emojiLab = rgbToLab(emoji.color.r, emoji.color.g, emoji.color.b);
        const distance = labDistance(targetLab, emojiLab);
        
        if (distance < minDistance) {
            minDistance = distance;
            closestEmoji = emoji.emoji;
        }
    }
    
    return closestEmoji || '⬜';
}

// Process grid in chunks
function processGridChunk(imageData, startY, endY, width, height, cellWidth, cellHeight, emojiDatabase) {
    const chunk = [];
    
    for (let y = startY; y < endY; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            const color = getAverageColor(imageData, x, y, imageData.width, imageData.height, cellWidth, cellHeight);
            const emoji = findClosestEmoji(color, emojiDatabase);
            row.push(emoji);
        }
        chunk.push(row);
    }
    
    return chunk;
}

// Handle messages from main thread
self.onmessage = function(e) {
    const { imageData, dimensions, emojiDatabase } = e.data;
    
    const cellWidth = imageData.width / dimensions.width;
    const cellHeight = imageData.height / dimensions.height;
    
    // Process grid in chunks
    const CHUNK_SIZE = 10;
    const grid = {
        width: dimensions.width,
        height: dimensions.height,
        data: []
    };
    
    for (let y = 0; y < dimensions.height; y += CHUNK_SIZE) {
        const endY = Math.min(y + CHUNK_SIZE, dimensions.height);
        const chunk = processGridChunk(
            imageData,
            y,
            endY,
            dimensions.width,
            dimensions.height,
            cellWidth,
            cellHeight,
            emojiDatabase
        );
        grid.data.push(...chunk);
        
        // Report progress
        const progress = (endY / dimensions.height) * 100;
        self.postMessage({ type: 'progress', progress });
    }
    
    // Send completed grid back to main thread
    self.postMessage({ type: 'complete', grid });
};
