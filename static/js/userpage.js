const userID = document.getElementById('loginUsernameInput').value;

async function fetchUserDrawings(){
    try{
        const response = await fetch(`api/get_user_drawings/${userID}`);
        if(!response.ok){
            console.error('Failed to fetch drawings: ', response.statusText);
            return;
        }
        const drawings = await response.json();
        const drawingsContainer = document.getElementById('drawings')
        drawingsContainer.innerHTML = '';
        drawings.forEach(drawing => {
            console.log("Drawing Content", drawing.content)
            createCanvas(drawing, drawingsContainer)
        });
    }catch(error){
        console.error('Error fetching drawings!', error)
    }
}

function createCanvas(drawing, container) {
    const drawingLink = document.createElement('a');
    drawingLink.href = `/drawing?id=${drawing.id}`;
    drawingLink.target = "_blank";
    
    const drawingContainer = document.createElement('div');
    drawingContainer.classList.add('drawing-container');

    const miniCanvas = document.createElement('canvas');
    const miniCanvasSize = 150;
    miniCanvas.width = miniCanvasSize;
    miniCanvas.height = miniCanvasSize;
    const ctx = miniCanvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, miniCanvas.width, miniCanvas.height);

    const cells = drawing.drawing_content_json;
    const cellPixelLength = miniCanvasSize / 50;

    cells.forEach(cell => {
        const { x, y, colour } = cell;
        ctx.fillStyle = colour;
        ctx.fillRect(x * cellPixelLength, y * cellPixelLength, cellPixelLength, cellPixelLength);
    });

    drawingLink.appendChild(miniCanvas);

    const nameLabel = document.createElement('p');
    nameLabel.textContent = drawing.piece_name;
    nameLabel.classList.add('drawing-name');

    drawingContainer.appendChild(drawingLink);
    drawingContainer.appendChild(nameLabel);

    container.appendChild(drawingContainer); // Add to the main container
}
window.onload = fetchUserDrawings;