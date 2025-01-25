// KD-Tree implementation for fast nearest neighbor search in LAB color space

class KDNode {
    constructor(emoji, lab) {
        this.emoji = emoji;        // The emoji character
        this.lab = lab;           // LAB color values
        this.left = null;
        this.right = null;
    }
}

class ColorKDTree {
    constructor() {
        this.root = null;
    }

    // Build tree from emoji database
    buildTree(emojiData) {
        const points = emojiData.map(emoji => ({
            emoji: emoji.emoji,
            lab: emoji.lab
        }));
        this.root = this._buildTreeHelper(points, 0);
    }

    _buildTreeHelper(points, depth) {
        if (points.length === 0) return null;

        // Choose axis based on depth (cycle through L, a, b)
        const axis = depth % 3;

        // Sort points by the current axis
        points.sort((a, b) => a.lab[axis] - b.lab[axis]);

        // Choose median as pivot
        const medianIdx = Math.floor(points.length / 2);
        const medianPoint = points[medianIdx];

        // Create node and construct subtrees
        const node = new KDNode(medianPoint.emoji, medianPoint.lab);
        node.left = this._buildTreeHelper(points.slice(0, medianIdx), depth + 1);
        node.right = this._buildTreeHelper(points.slice(medianIdx + 1), depth + 1);

        return node;
    }

    // Find nearest neighbor
    findNearest(targetLab) {
        if (!this.root) return null;

        let best = {
            node: null,
            distance: Infinity
        };

        this._searchNearest(this.root, targetLab, 0, best);
        return best.node ? best.node.emoji : '⬜';
    }

    _searchNearest(node, target, depth, best) {
        if (!node) return;

        // Calculate distance to current node
        const distance = this._labDistance(target, node.lab);

        // Update best if current node is closer
        if (distance < best.distance) {
            best.node = node;
            best.distance = distance;
        }

        // Choose which subtree to search first based on splitting axis
        const axis = depth % 3;
        const axisDist = target[axis] - node.lab[axis];
        const firstBranch = axisDist < 0 ? node.left : node.right;
        const secondBranch = axisDist < 0 ? node.right : node.left;

        // Search the closer branch first
        this._searchNearest(firstBranch, target, depth + 1, best);

        // Only search the other branch if it could contain a closer point
        if (Math.abs(axisDist) < best.distance) {
            this._searchNearest(secondBranch, target, depth + 1, best);
        }
    }

    // Calculate Euclidean distance in LAB space
    _labDistance(lab1, lab2) {
        const dL = lab1[0] - lab2[0];
        const da = lab1[1] - lab2[1];
        const db = lab1[2] - lab2[2];
        return Math.sqrt(dL * dL + da * da + db * db);
    }
}

// Export for use in main.js
window.ColorKDTree = ColorKDTree;
