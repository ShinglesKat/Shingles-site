/**
 * @type HTMLCanvasElement
 * CREDIT TO dcode ON YOUTUBE FOR PIXEL ART CANVAS TUTORIAL
 */
import { buildMiniCanvas } from './minicanvas_helper.js';

let isDrawing = false;
let lastHoveredCell = { x: -1, y: -1 };

const canvas = document.getElementById("canvas");
const guide = document.getElementById("guide");
const colourInput = document.getElementById("colourInput");
const toggleGuide = document.getElementById("toggleGuide");

const drawingContext = canvas.getContext("2d");
const CELL_SIDE_COUNT = 50;
const cellPixelLength = canvas.width / CELL_SIDE_COUNT;
const colourHistory = {};
let drawnCells = [];

// Set default colour
colourInput.value = "#009578";

// Init canvas background colour
drawingContext.fillStyle = "#ffffff";
drawingContext.fillRect(0, 0, canvas.width, canvas.height);

// Initialize colourHistory to white for every cell
for (let i = 0; i < CELL_SIDE_COUNT; i++) {
    for (let j = 0; j < CELL_SIDE_COUNT; j++) {
        colourHistory[`${i}_${j}`] = "#ffffff";
    }
}

function getCanvasCoordinates(e) {
    const canvasBoundingRect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / canvasBoundingRect.width;
    const scaleY = canvas.height / canvasBoundingRect.height;
    
    const x = (e.clientX - canvasBoundingRect.left) * scaleX;
    const y = (e.clientY - canvasBoundingRect.top) * scaleY;
    
    return { x, y };
}

function getCellCoordinates(e) {
    const { x, y } = getCanvasCoordinates(e);
    const cellX = Math.floor(x / cellPixelLength);
    const cellY = Math.floor(y / cellPixelLength);
    
    return { cellX, cellY };
}

function fillCell(cellX, cellY) {
    const startX = cellX * cellPixelLength;
    const startY = cellY * cellPixelLength;
    const colour = colourInput.value;

    drawingContext.fillStyle = colour;
    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
    colourHistory[`${cellX}_${cellY}`] = colour;

    // Remove any existing entry for this cell before adding the new one
    drawnCells = drawnCells.filter(cell => !(cell.x === cellX && cell.y === cellY));
    drawnCells.push({ x: cellX, y: cellY, colour: colour });

    saveCanvasState();  // Save after each draw
}

function saveCanvasState() {
    // Save the current state of drawn cells to localStorage
    localStorage.setItem('canvasState', JSON.stringify(drawnCells));
}

function loadCanvasState() {
    const savedState = localStorage.getItem('canvasState');
    if (savedState) {
        drawnCells = JSON.parse(savedState);

        // Redraw the canvas based on the saved state
        drawnCells.forEach(cell => {
            const { x, y, colour } = cell;
            const startX = x * cellPixelLength;
            const startY = y * cellPixelLength;

            drawingContext.fillStyle = colour;
            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
            colourHistory[`${x}_${y}`] = colour; // Also update colourHistory
        });
    }
}

// Setup the guide - FIXED VERSION
{
    guide.style.width = `${canvas.width}px`;
    guide.style.height = `${canvas.height}px`;
    guide.style.gridTemplateColumns = `repeat(${CELL_SIDE_COUNT}, 1fr)`;
    guide.style.gridTemplateRows = `repeat(${CELL_SIDE_COUNT}, 1fr)`;

    [...Array(CELL_SIDE_COUNT ** 2)].forEach(() => guide.insertAdjacentHTML("beforeend", "<div></div>"));
}

// Prevent dragging and text selection
canvas.addEventListener('dragstart', (e) => {
    e.preventDefault();
    return false;
});

canvas.addEventListener('selectstart', (e) => {
    e.preventDefault();
    return false;
});

guide.addEventListener('dragstart', (e) => {
    e.preventDefault();
    return false;
});

function handleCanvasMousedown(e) {
    // Ensure user is using primary mouse button.
    if (e.button !== 0) {
        return;
    }

    const { cellX, cellY } = getCellCoordinates(e);

    if (cellX < 0 || cellY < 0 || cellX >= CELL_SIDE_COUNT || cellY >= CELL_SIDE_COUNT) {
        return;
    }

    const currentColour = colourHistory[`${cellX}_${cellY}`];

    if (e.ctrlKey) {
        if (currentColour) {
            colourInput.value = currentColour;
        }
    } else {
        fillCell(cellX, cellY);
    }

    console.log(`Cell: (${cellX}, ${cellY})`);
}

function handleToggleGuideChange() {
    guide.style.display = toggleGuide.checked ? null : "none";
}

// New function to redraw the canvas from colourHistory
function redrawCanvasFromHistory() {
    drawingContext.fillStyle = "#ffffff"; // Clear the entire canvas
    drawingContext.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < CELL_SIDE_COUNT; i++) {
        for (let j = 0; j < CELL_SIDE_COUNT; j++) {
            const key = `${i}_${j}`;
            const colour = colourHistory[key];
            if (colour && colour !== "#ffffff") {
                const startX = i * cellPixelLength;
                const startY = j * cellPixelLength;
                drawingContext.fillStyle = colour;
                drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
            }
        }
    }
}

function handleCanvasMousemove(e) {
    const { cellX, cellY } = getCellCoordinates(e);

    // If mouse is outside canvas, reset lastHoveredCell and redraw if needed
    if (cellX < 0 || cellY < 0 || cellX >= CELL_SIDE_COUNT || cellY >= CELL_SIDE_COUNT) {
        if (lastHoveredCell.x !== -1) { // Only redraw if we were previously hovering over a cell
            redrawCanvasFromHistory();
            lastHoveredCell = { x: -1, y: -1 }; // Reset
        }
        return;
    }

    // Only update if the hovered cell has changed
    if (cellX !== lastHoveredCell.x || cellY !== lastHoveredCell.y) {
        redrawCanvasFromHistory(); // Redraw the canvas to clear previous hover effect

        // Apply the new hover effect
        const startX = cellX * cellPixelLength;
        const startY = cellY * cellPixelLength;
        drawingContext.fillStyle = colourInput.value;
        drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);

        // Update the last hovered cell
        lastHoveredCell = { x: cellX, y: cellY };
    }

    if (isDrawing) {
        handleCanvasMousedown(e);
    }
}

canvas.addEventListener("mousedown", (e) => {
    isDrawing = true;
    handleCanvasMousedown(e);
});

canvas.addEventListener("mousemove", handleCanvasMousemove);

canvas.addEventListener("mouseup", () => {
    isDrawing = false;
});

canvas.addEventListener("mouseleave", () => {
    isDrawing = false;
    // When the mouse leaves the canvas, restore the last hovered cell's color
    if (lastHoveredCell.x !== -1) {
        redrawCanvasFromHistory(); // Redraw to remove the hover effect
        lastHoveredCell = { x: -1, y: -1 }; // Reset
    }
});

toggleGuide.addEventListener("change", handleToggleGuideChange);

document.querySelectorAll(".colour-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const { colour } = btn.dataset;
        colourInput.value = colour;
    });
});

function attachButtonListener(button, eventType, callback) {
    if (button) {
        button.addEventListener(eventType, callback);
    }
}

const clearCanvasButton = document.getElementById("clearCanvasBtn");
const saveCanvasButton = document.getElementById("saveCanvasBtn");
const loadCanvasButton = document.getElementById("loadCanvasBtn"); 

attachButtonListener(clearCanvasButton, "click", clearCanvas);
attachButtonListener(saveCanvasButton, "click", saveCanvasData);
// attachButtonListener(loadCanvasButton, "click", showLoadDrawingModal);

function clearCanvas() {
    const yes = confirm("Are you sure?");

    if (!yes) {
        return;
    }
    drawingContext.fillStyle = "#ffffff";
    drawingContext.fillRect(0, 0, canvas.width, canvas.height);

    drawnCells = [];
    localStorage.removeItem('canvasState');

    for (let i = 0; i < CELL_SIDE_COUNT; i++) {
        for (let j = 0; j < CELL_SIDE_COUNT; j++) {
            colourHistory[`${i}_${j}`] = "#ffffff";
        }
    }
}

function showNameModal() {
    return new Promise((resolve, reject) => {
        const modal = document.getElementById("customModal");
        const nameInput = document.getElementById("canvasNameInput");
        const privateCheckbox = document.getElementById("privateCheckbox");
        const cancelBtn = document.getElementById("cancelModalBtn");
        const confirmBtn = document.getElementById("confirmModalBtn");

        modal.classList.remove("hidden");

        cancelBtn.onclick = () => {
            modal.classList.add("hidden");
            reject(null);
        };

        confirmBtn.onclick = () => {
            const pieceName = nameInput.value.trim();
            const isPrivate = privateCheckbox.checked;

            if (pieceName.length < 3 || pieceName.length > 30) {
                alert("Name must be between 3 and 30 characters.");
                return;
            }

            modal.classList.add("hidden");
            resolve({ pieceName, isPrivate });
        };
    });
}

let currentPieceId = null;

async function saveCanvasData() {
    if (!drawnCells || drawnCells.length === 0) {
        alert("cmon bruh at least try draw something");
        return;
    }

    try {
        const response = await fetch('/api/get_session_data');
        if (!response.ok) {
            throw new Error("You must be logged in to do that!");
        }

        const result = await showNameModal();
        if (!result) {
            return;
        }

        const { pieceName, isPrivate } = result;
        const json = JSON.stringify(drawnCells);
        const sessionData = await response.json();
        const { userid, username } = sessionData;

        const dataToSend = {
            piece_name: pieceName,
            content: json,
            private: isPrivate,
            piece_id: currentPieceId
        };

        const saveResponse = await fetch('/api/save_drawing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataToSend)
        });

        if (!saveResponse.ok) {
            throw new Error("Failed to save drawing");
        }

        const saveResult = await saveResponse.json();

        if (saveResult && saveResult.id) {
            currentPieceId = saveResult.id;
            alert("Drawing saved!");
        }
    } catch (err) {
        alert(err.message);
    }
}

async function loadRecentDrawings() {
    try {
        const response = await fetch('/api/retrieve_drawings?limit=5');
        const drawings = await response.json();

        if (!Array.isArray(drawings)) {
            console.error('Unexpected response format:', drawings);
            return;
        }

        const drawingsContainer = document.getElementById('recentDrawings');
        drawingsContainer.innerHTML = '';

        if (drawings.length === 0) {
            drawingsContainer.innerHTML = '<p>No recent drawings found.</p>';
            return;
        }

        for (const drawing of drawings) {
            await renderDrawingOnMiniCanvas(drawing, drawingsContainer);
        }
    } catch (err) {
        console.error('Error loading recent drawings:', err);
    }
}

async function loadAllDrawings() {
    try {
        const response = await fetch('/api/retrieve_drawings'); // all drawings, newest first
        const drawings = await response.json();

        if (!Array.isArray(drawings) || drawings.length === 0) {
            alert('No drawings found.');
            return;
        }

        // Show newest 5 in #recentDrawings
        const recentContainer = document.getElementById('recentDrawings');
        recentContainer.innerHTML = '';
        const newestDrawings = drawings.slice(0, 5);
        for (const drawing of newestDrawings) {
            await renderDrawingOnMiniCanvas(drawing, recentContainer);
        }

        // Show the rest in a new container below the button
        const olderContainer = document.getElementById('allOlderDrawings');

        // Clear older drawings but keep the header
        olderContainer.innerHTML = '';

        const olderDrawings = drawings.slice(5);
        if (olderDrawings.length === 0) {
            olderContainer.innerHTML += '<p>No older drawings.</p>';
        } else {
            for (const drawing of olderDrawings) {
                await renderDrawingOnMiniCanvas(drawing, olderContainer);
            }
        }
    } catch (err) {
        console.error('Failed to load drawings:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('loadAllDrawingsBtn').addEventListener('click', loadAllDrawings);
});

async function renderDrawingOnMiniCanvas(drawing, container) {
    const canvasContainer = document.createElement('div');
    canvasContainer.classList.add('drawing-container');

    const drawingLink = document.createElement('a');
    drawingLink.href = `/drawing?id=${drawing.id}`;
    drawingLink.target = "_blank";

    const miniCanvas = buildMiniCanvas(drawing, { size: 150 });
    drawingLink.appendChild(miniCanvas);

    const nameLabel = document.createElement('p');
    nameLabel.textContent = drawing.piece_name;
    nameLabel.classList.add('drawing-name');

    const userLabel = document.createElement('a');
    userLabel.textContent = `by ${drawing.username}`;
    userLabel.classList.add('drawing-user');
    userLabel.href = `/user?id=${drawing.user_id}`;
    userLabel.target = "_blank";

    canvasContainer.appendChild(drawingLink);
    canvasContainer.appendChild(nameLabel);
    canvasContainer.appendChild(userLabel);

    container.appendChild(canvasContainer);
}

// Add window resize handler for proper canvas rescaling
window.addEventListener('resize', () => {
    setTimeout(() => {
        redrawCanvasFromHistory();
    }, 100);
});

// Initial load from saved canvas state in localStorage
loadCanvasState();
loadRecentDrawings();