function showAlert(text){
    alert(text);
}

//down here are jokes :)
let counter = 0;
function incrementBClicks(){
    counter++;

    if(counter === 5){
        showAlert("Brute is gae")

        fetch("/set_brute",{method: "POST", headers: { "Content-Type": "application/json"}}).then(res=>res.json()).then(data=>{console.log("session set to wade:", data)}).catch(err=>{console.error("Error setting to wade :(", err);});
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
