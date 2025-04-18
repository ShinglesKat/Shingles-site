/**
 * @type HTMLCanvasElement
 * CREDIT TO dcode ON YOUTUBE FOR PIXEL ART CANVAS TUTORIAL
 */
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
}

canvas.addEventListener("mousedown", handleCanvasMousedown);
toggleGuide.addEventListener("change", handleToggleGuideChange);