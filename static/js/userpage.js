import { buildMiniCanvas } from './minicanvas_helper.js';

const userID = document.getElementById('loginUsernameInput').value;

async function fetchUserDrawings() {
    try {
        const response = await fetch(`api/get_user_drawings/${userID}`);
        if (!response.ok) {
            console.error('Failed to fetch drawings:', response.statusText);
            return;
        }

        const drawings = await response.json();
        const drawingsContainer = document.getElementById('drawings');
        drawingsContainer.innerHTML = '';

        drawings.forEach(drawing => {
            createCanvas(drawing, drawingsContainer);
        });
    } catch (error) {
        console.error('Error fetching drawings!', error);
    }
}

function createCanvas(drawing, container) {
    const drawingLink = document.createElement('a');
    drawingLink.href = `/drawing?id=${drawing.id}`;
    drawingLink.target = "_blank";

    const miniCanvas = buildMiniCanvas(drawing, { size: 150 });
    drawingLink.appendChild(miniCanvas);

    const nameLabel = document.createElement('p');
    nameLabel.textContent = drawing.piece_name;
    nameLabel.classList.add('drawing-name');

    const drawingContainer = document.createElement('div');
    drawingContainer.classList.add('drawing-container');
    drawingContainer.appendChild(drawingLink);
    drawingContainer.appendChild(nameLabel);

    container.appendChild(drawingContainer);
}

window.onload = fetchUserDrawings;
