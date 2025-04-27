/**
 * @type HTMLCanvasElement
 * CREDIT TO dcode ON YOUTUBE FOR PIXEL ART CANVAS TUTORIAL
 */

let isDrawing = false;
const canvas = document.getElementById("canvas");
const guide = document.getElementById("guide");
const colourInput = document.getElementById("colourInput");
const toggleGuide = document.getElementById("toggleGuide");

const drawingContext = canvas.getContext("2d");
const CELL_SIDE_COUNT = 50;
const cellPixelLength = canvas.width / CELL_SIDE_COUNT;
const colourHistory = {};
let drawnCells = [];

//Set default colour
colourInput.value = "#009578";

//Init canvas background colour
drawingContext.fillStyle = "#ffffff";
drawingContext.fillRect(0, 0, canvas.width, canvas.height);

for (let i = 0; i < CELL_SIDE_COUNT; i++) {
    for (let j = 0; j < CELL_SIDE_COUNT; j++) {
        colourHistory[`${i}_${j}`] = "#ffffff";
    }
}

function fillCell(cellX, cellY) {
    const startX = cellX * cellPixelLength;
    const startY = cellY * cellPixelLength;
    const colour = colourInput.value;

    drawingContext.fillStyle = colour;
    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
    colourHistory[`${cellX}_${cellY}`] = colour;

    drawnCells.push({ x: cellX, y: cellY, colour: colour });

    saveCanvasState();  //Save after each draw
}

function saveCanvasState() {
    //Save the current state of drawn cells to localStorage
    localStorage.setItem('canvasState', JSON.stringify(drawnCells));
}

function loadCanvasState() {
    const savedState = localStorage.getItem('canvasState');
    if (savedState) {
        drawnCells = JSON.parse(savedState);

        //Redraw the canvas based on the saved state
        drawnCells.forEach(cell => {
            const { x, y, colour } = cell;
            const startX = x * cellPixelLength;
            const startY = y * cellPixelLength;

            drawingContext.fillStyle = colour;
            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
        });
    }
}

//Setup the guide
{
    guide.style.width = `${canvas.width}px`;
    guide.style.height = `${canvas.height}px`;
    guide.style.gridTemplateColumns = `repeat(${CELL_SIDE_COUNT}, 1fr)`;
    guide.style.gridTemplateRows = `repeat(${CELL_SIDE_COUNT}, 1fr)`;

    [...Array(CELL_SIDE_COUNT ** 2)].forEach(() => guide.insertAdjacentHTML("beforeend", "<div></div>"));
}

function handleCanvasMousedown(e) {
    // Ensure user is using primary mouse button.
    if (e.button !== 0) {
        return;
    }

    const canvasBoundingRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasBoundingRect.left;
    const y = e.clientY - canvasBoundingRect.top;
    const cellX = Math.floor(x / cellPixelLength);
    const cellY = Math.floor(y / cellPixelLength);

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

    console.log(x, y);
}

function handleToggleGuideChange() {
    guide.style.display = toggleGuide.checked ? null : "none";
}

canvas.addEventListener("mousedown", (e) => {
    isDrawing = true;
    handleCanvasMousedown(e);
});
canvas.addEventListener("mousemove", (e) => {
    if (isDrawing) {
        handleCanvasMousedown(e);
    }
});
canvas.addEventListener("mouseup", () => {
    isDrawing = false;
});
canvas.addEventListener("mouseleave", () => {
    isDrawing = false;
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
attachButtonListener(loadCanvasButton, "click", loadCanvasData);

function clearCanvas() {
    const yes = confirm("Are you sure?");

    if (!yes) return;
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

            if (pieceName.length < 3 || pieceName.length > 16) {
                alert("Name must be between 3 and 16 characters.");
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
        const response = await fetch('/get_session_data');
        if (!response.ok) throw new Error("You must be logged in to do that!");

        const result = await showNameModal();
        if (!result) return;

        const { pieceName, isPrivate } = result;
        const json = JSON.stringify(drawnCells);
        const sessionData = await response.json();
        const { userid, username } = sessionData;

        const dataToSend = {
            user_id: userid,
            username: username,
            piece_name: pieceName,
            content: json,
            private: isPrivate,
            piece_id: currentPieceId
        };

        const saveResponse = await fetch('/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataToSend)
        });

        if (!saveResponse.ok) throw new Error("Failed to save canvas");

        const canvasSaveResponse = await saveResponse.json();

        if (canvasSaveResponse.piece_id) {
            currentPieceId = canvasSaveResponse.piece_id;
        }

        alert(canvasSaveResponse.message || "Canvas saved successfully!");
    } catch (err) {
        console.error("Save error:", err);
        alert(err.message || "An error occurred while saving the canvas.");
    }
}

async function loadCanvasData(drawing, container) {
    const canvasContainer = document.createElement('div');
    canvasContainer.classList.add('drawing-container');

    const drawingLink = document.createElement('a');
    drawingLink.href = `/drawing?id=${drawing.id}`;
    drawingLink.target = "_blank";

    const miniCanvas = document.createElement('canvas');
    const miniCanvasSize = 150;
    miniCanvas.width = miniCanvasSize;
    miniCanvas.height = miniCanvasSize;
    const context = miniCanvas.getContext('2d');

    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, miniCanvas.width, miniCanvas.height);

    const cells = JSON.parse(drawing.content);
    const cellPixelLength = miniCanvasSize / 50;

    cells.forEach(cell => {
        const { x, y, colour } = cell;
        context.fillStyle = colour;
        context.fillRect(x * cellPixelLength, y * cellPixelLength, cellPixelLength, cellPixelLength);
    });

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

async function loadRecentDrawings() {
    try {
        const response = await fetch('/retrieve_latest');
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
            await loadCanvasData(drawing, drawingsContainer);
        }
    } catch (err) {
        console.error('Error loading recent drawings:', err);
    }
}
window.addEventListener('load', loadCanvasState);
loadRecentDrawings();