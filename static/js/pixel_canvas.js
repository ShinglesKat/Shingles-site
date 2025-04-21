/**
 * @type HTMLCanvasElement
 * CREDIT TO dcode ON YOUTUBE FOR PIXEL ART CANVAS TUTORIAL
 */

let isDrawing = false;
const canvas = document.getElementById("canvas")
const guide = document.getElementById("guide")
const colourInput = document.getElementById("colourInput")
const toggleGuide = document.getElementById("toggleGuide")

const drawingContext = canvas.getContext("2d");
const CELL_SIDE_COUNT = 50;
const cellPixelLength = canvas.width/ CELL_SIDE_COUNT;
const colourHistory = {};

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

fetch("/api/canvas")
    .then(res => res.json())
    .then(data => {
        for (let y = 0; y < CELL_SIDE_COUNT; y++) {
            for (let x = 0; x < CELL_SIDE_COUNT; x++) {
                const colour = data[y][x];
                if (colour) {
                    const startX = x * cellPixelLength;
                    const startY = y * cellPixelLength;

                    drawingContext.fillStyle = colour;
                    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
                    colourHistory[`${x}_${y}`] = colour;
                }
            }
        }
    });

document.querySelectorAll(".colour-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const {colour} = btn.dataset;
        colourInput.value = colour;
    });
});

//Setup the guide
{
    guide.style.width = `${canvas.width}px`;
    guide.style.height = `${canvas.height}px`;
    guide.style.gridTemplateColumns = `repeat(${CELL_SIDE_COUNT}, 1fr)`;
    guide.style.gridTemplateRows = `repeat(${CELL_SIDE_COUNT}, 1fr)`;

    [...Array(CELL_SIDE_COUNT ** 2)].forEach(() => guide.insertAdjacentHTML("beforeend", "<div></div>"));
}

function handleCanvasMousedown(e){
    //Ensure user is using primary mouse button.
    if(e.button !== 0){
        return;
    }

    const canvasBoundingRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasBoundingRect.left;
    const y = e.clientY - canvasBoundingRect.top;
    const cellX = Math.floor(x / cellPixelLength);
    const cellY = Math.floor(y / cellPixelLength);

    if(cellX < 0 || cellY < 0 || cellX >= CELL_SIDE_COUNT || cellY >= CELL_SIDE_COUNT){
        return;
    }

    const currentColour = colourHistory[`${cellX}_${cellY}`];
    
    if(e.ctrlKey){
        if(currentColour){
            colourInput.value = currentColour;
        }
    }else{
        fillCell(cellX, cellY);
    }

    console.log(x, y);
}
function handleToggleGuideChange(){
    guide.style.display = toggleGuide.checked ? null : "none";
}

function fillCell(cellX, cellY){
    const startX = cellX * cellPixelLength;
    const startY = cellY * cellPixelLength;

    drawingContext.fillStyle = colourInput.value;
    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
    colourHistory[`${cellX}_${cellY}`] = colourInput.value;

    fetch("/canvas/updatePixel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({x : cellX, y: cellY, colour:colourInput.value}),
    });
}

function refreshCanvasFromServer() {
    if (isDrawing) {
        //Don't refresh while drawing
        return;
    }

    fetch("/api/canvas")
        .then(res => res.json())
        .then(data => {
            for (let y = 0; y < CELL_SIDE_COUNT; y++) {
                for (let x = 0; x < CELL_SIDE_COUNT; x++) {
                    const colour = data[y][x];
                    const key = `${x}_${y}`;

                    //Only update if the colour has changed
                    if (colour && colour !== colourHistory[key]) {
                        const startX = x * cellPixelLength;
                        const startY = y * cellPixelLength;

                        drawingContext.fillStyle = colour;
                        drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
                        colourHistory[key] = colour;
                    }
                }
            }
        })
        .catch(err => console.error("Error updating canvas:", err));
}

canvas.addEventListener("mousedown", (e) => {
    isDrawing = true;
    handleCanvasMousedown(e);
});
canvas.addEventListener("mousemove", (e) => {
    if(isDrawing){
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

//Poll server for update every second :>
setInterval(refreshCanvasFromServer, 1000);

//Admin stuff
const clearCanvasButton = document.getElementById("clearCanvasBtn");
if (clearCanvasButton) {
    clearCanvasButton.addEventListener("click", () => {
        clearCanvas();
    })
}

//clears the canvas on client side, make request to server
function clearCanvas() {
    for (let i = 0; i < CELL_SIDE_COUNT; i++) {
        for (let j = 0; j < CELL_SIDE_COUNT; j++) {
            colourHistory[`${i}_${j}`] = colourInput.value;
        }
    }

    fetch("/canvas/clear", {
        method: "POST"
    }).then(res => res.json())
    .then(data => {
        console.log("Canvas cleared on server:", data);
        refreshCanvasFromServer();
    }).catch(err => console.error("Error clearing canvas on server:", err));
}
