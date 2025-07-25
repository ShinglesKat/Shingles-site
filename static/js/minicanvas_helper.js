//again shoutout chatgpt I do NOT know how to make this look nice

export function buildMiniCanvas(drawing, opts = {}) {
    const {
        size = 150,
        cellSideCount = 50,
        returnWrapper = false
    } = opts;

    // Accept several data shapes -------------------------------------------
    let cells;
    if (Array.isArray(drawing)) {            // already [{x,y,colour}]
        cells = drawing;
    } else if (drawing.content) {            // { content: '[{…}]' }
        cells = JSON.parse(drawing.content);
    } else if (drawing.drawing_content_json) {
        cells = drawing.drawing_content_json;
    } else {
        console.warn('buildMiniCanvas › unknown data shape', drawing);
        cells = [];
    }

    // Canvas ----------------------------------------------------------------
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = size;
    canvas.classList.add('mini-canvas');
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);

    // Cells
    const cellSize = size / cellSideCount;
    cells.forEach(({ x, y, colour }) => {
        ctx.fillStyle = colour;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
    });

    // Optional wrapper for nicer layout -------------------------------------
    if (returnWrapper) {
        const wrapper = document.createElement('div');
        wrapper.classList.add('mini-canvas-wrapper');
        wrapper.appendChild(canvas);
        return wrapper;
    }
    return canvas;
}
