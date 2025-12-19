/**
 * @type HTMLCanvasElement
 * CREDIT TO dcode ON YOUTUBE FOR PIXEL ART CANVAS TUTORIAL
 */

let isDrawing = false;
let isBanned = false;

const canvas = document.getElementById("canvas")
const guide = document.getElementById("guide")
const colourInput = document.getElementById("colourInput")
const toggleGuide = document.getElementById("toggleGuide")

const drawingContext = canvas.getContext("2d");
const CELL_SIDE_COUNT = 50;
const cellPixelLength = canvas.width / CELL_SIDE_COUNT;
const colourHistory = {};
const ipHistory = {};
const pendingUpdates = {};

let lastHoveredCell = { x: -1, y: -1 }; // To keep track of the previously hovered cell

//Set default colour
colourInput.value = "#009578";

//Init canvas background colour
drawingContext.fillStyle = "#ffffff";
drawingContext.fillRect(0, 0, canvas.width, canvas.height);
for (let i = 0; i < CELL_SIDE_COUNT; i++) {
    for (let j = 0; j < CELL_SIDE_COUNT; j++) {
        colourHistory[`${i}_${j}`] = "#ffffff";
        ipHistory[`${i}_${j}`] = null;
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

fetch("/multiplayer/canvas")
    .then(res => res.json())
    .then(data => {
        for (let y = 0; y < CELL_SIDE_COUNT; y++) {
            for (let x = 0; x < CELL_SIDE_COUNT; x++) {
                const pixelData = data[y][x];
                if (pixelData) {
                    const {colour} = pixelData;
                    const ip = pixelData.ip_address;
                    
                    const startX = x * cellPixelLength;
                    const startY = y * cellPixelLength;

                    drawingContext.fillStyle = colour;
                    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
                    colourHistory[`${x}_${y}`] = colour;
                    ipHistory[`${x}_${y}`] = ip;
                }
            }
        }
    });

document.addEventListener("DOMContentLoaded", () => {
    fetch('/check_ban_status')
    .then(res => res.json())
    .then(data => {
        if (data.banned) {
            isBanned = true;
            let banMessage = "You have been banned from drawing on the canvas.";
            if (data.reason) {
                banMessage += `\nReason: ${data.reason}`;
            }
            if (data.expires_at) {
                const expiryDate = new Date(data.expires_at);
                banMessage += `\nThis ban expires on: ${expiryDate.toLocaleString()}`;
            }
            alert(banMessage);
        }
    })
    .catch(err => {
        console.error("Error checking ban status:", err);
    });
});

document.querySelectorAll(".colour-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const { colour } = btn.dataset;
        colourInput.value = colour;
    });
});

{
    guide.style.gridTemplateColumns = `repeat(${CELL_SIDE_COUNT}, 1fr)`;
    guide.style.gridTemplateRows = `repeat(${CELL_SIDE_COUNT}, 1fr)`;

    [...Array(CELL_SIDE_COUNT ** 2)].forEach(() => guide.insertAdjacentHTML("beforeend", "<div></div>"));
}

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

canvas.addEventListener("contextmenu", (e) => {
    e.preventDefault();

    const { cellX, cellY } = getCellCoordinates(e);

    if (cellX < 0 || cellY < 0 || cellX >= CELL_SIDE_COUNT || cellY >= CELL_SIDE_COUNT) {
        return;
    }
    const currentColour = colourHistory[`${cellX}_${cellY}`];
    const currentIp = ipHistory[`${cellX}_${cellY}`];

    showTooltip(
        `Cell (${cellX}, ${cellY})<br>Colour: ${currentColour}`,
        e.clientX,
        e.clientY,
        currentIp
    );
});

function handleCanvasMousedown(e) {
    if (isBanned) {
        return;
    }

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

function fillCell(cellX, cellY) {
    if (isBanned) {
        return;
    }

    const startX = cellX * cellPixelLength;
    const startY = cellY * cellPixelLength;
    const key = `${cellX}_${cellY}`;

    drawingContext.fillStyle = colourInput.value;
    drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
    colourHistory[key] = colourInput.value;

    pendingUpdates[key] = colourInput.value;

    fetch("/multiplayer/canvas/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x: cellX, y: cellY, colour: colourInput.value }),
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(errorData => {
                throw new Error(errorData.error || `Failed to update canvas cell. Status: ${res.status}`);
            });
        }
        return res.json();
    })
    .then(data => {
        console.log("Pixel updated successfully");
        delete pendingUpdates[key];
    })
    .catch(err => {
        console.error("Error updating cell:", err);
        delete pendingUpdates[key];
        
        if (err.message.includes("banned") || err.message.includes("Ban")) {
            isBanned = true;
            
            const originalColour = "#ffffff";
            drawingContext.fillStyle = originalColour;
            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
            colourHistory[`${cellX}_${cellY}`] = originalColour;
            
            alert(err.message);
        } else {
            //For other errors, also revert the change
            refreshCanvasFromServer();
        }
    });
}

function refreshCanvasFromServer() {
    if (isDrawing) {
        //Don't refresh while drawing
        return;
    }

    fetch("/multiplayer/canvas")
        .then(res => res.json())
        .then(data => {
            for (let y = 0; y < CELL_SIDE_COUNT; y++) {
                for (let x = 0; x < CELL_SIDE_COUNT; x++) {
                    const pixelData = data[y][x];
                    const key = `${x}_${y}`;

                    if (pixelData && pixelData.colour !== undefined) {
                        const {colour} = pixelData;
                        const ip = pixelData.ip_address;

                        // Don't overwrite pending updates or hovered cells
                        if (colour !== colourHistory[key] && 
                            !pendingUpdates[key] && 
                            !(x === lastHoveredCell.x && y === lastHoveredCell.y)) {
                            const startX = x * cellPixelLength;
                            const startY = y * cellPixelLength;

                            drawingContext.fillStyle = colour;
                            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
                            colourHistory[key] = colour;
                            ipHistory[key] = ip;
                        }
                    }
                }
            }
        })
        .catch(err => console.error("Error updating canvas:", err));
}

function handleCanvasMousemove(e) {
    const { cellX, cellY } = getCellCoordinates(e);

    if (cellX < 0 || cellY < 0 || cellX >= CELL_SIDE_COUNT || cellY >= CELL_SIDE_COUNT) {
        if (lastHoveredCell.x !== -1) {
            const prevX = lastHoveredCell.x;
            const prevY = lastHoveredCell.y;
            const originalColour = colourHistory[`${prevX}_${prevY}`];
            const startX = prevX * cellPixelLength;
            const startY = prevY * cellPixelLength;

            drawingContext.fillStyle = originalColour;
            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
            lastHoveredCell = { x: -1, y: -1 };
        }
        return;
    }

    if (cellX !== lastHoveredCell.x || cellY !== lastHoveredCell.y) {
        if (lastHoveredCell.x !== -1) {
            const prevX = lastHoveredCell.x;
            const prevY = lastHoveredCell.y;
            const originalColour = colourHistory[`${prevX}_${prevY}`];
            const startX = prevX * cellPixelLength;
            const startY = prevY * cellPixelLength;

            drawingContext.fillStyle = originalColour;
            drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
        }

        const startX = cellX * cellPixelLength;
        const startY = cellY * cellPixelLength;

        drawingContext.fillStyle = colourInput.value;
        drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);

        lastHoveredCell = { x: cellX, y: cellY };
    }

    if (isDrawing) {
        handleCanvasMousedown(e);
    }
}

canvas.addEventListener("mousedown", (e) => {
    if (isBanned) {
        return;
    }
    isDrawing = true;
    handleCanvasMousedown(e);
});
canvas.addEventListener("mousemove", handleCanvasMousemove);
canvas.addEventListener("mouseup", () => {
    isDrawing = false;
});
canvas.addEventListener("mouseleave", () => {
    isDrawing = false;
    if (lastHoveredCell.x !== -1) {
        const prevX = lastHoveredCell.x;
        const prevY = lastHoveredCell.y;
        const originalColour = colourHistory[`${prevX}_${prevY}`];
        const startX = prevX * cellPixelLength;
        const startY = prevY * cellPixelLength;

        drawingContext.fillStyle = originalColour;
        drawingContext.fillRect(startX, startY, cellPixelLength, cellPixelLength);
        lastHoveredCell = { x: -1, y: -1 };
    }
});

toggleGuide.addEventListener("change", handleToggleGuideChange);

//Poll server for update every second and half :>
setInterval(refreshCanvasFromServer, 1500);

//Admin stuff
const clearCanvasButton = document.getElementById("clearCanvasBtn");
if (clearCanvasButton) {
    clearCanvasButton.addEventListener("click", () => {
        clearCanvas();
    })
}

//init tooltip for pixels
const tooltip = document.getElementById("tooltip");

let sessionCache = null;

function showTooltip(content, clientX, clientY, ip) {
    const renderTooltip = (isAdmin) => {
        tooltip.innerHTML = `
            <div>${content}</div>
            ${isAdmin ? `<div>IP: ${ip}</div>` : ''}
            ${isAdmin ? `<button id="tooltip-btn">Ban user</button>` : ''}
        `;
        tooltip.style.display = "block";
        tooltip.style.left = `${clientX + 10}px`;
        tooltip.style.top = `${clientY + 10}px`;

        if (isAdmin) {
            document.getElementById("tooltip-btn").addEventListener("click", () => {
                const duration = prompt("How long should the user be banned for? ('1h', '24h', '7d'):");
                if (!duration) {
                    return;
                }

                const message = prompt("Enter a reason for the ban:");
                if (message === null) {
                    return;
                }

                fetch("/admin/ban_ip", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ip, reason: message, ban_duration: duration })
                })
                .then(res => {
                    if (res.ok) {
                        alert("User banned successfully.");
                    } else {
                        alert("Failed to ban user.");
                    }
                })
                .catch(err => {
                    console.error("Ban error:", err);
                    alert("Error banning user.");
                });
            });
        }
    };

    if (sessionCache) {
        renderTooltip(sessionCache.accounttype === 'admin');
    } else {
        fetch('/get_session_data')
            .then(res => res.ok ? res.json() : Promise.reject('Not logged in'))
            .then(data => {
                sessionCache = data;
                renderTooltip(data.accounttype === 'admin');
            })
            .catch(err => {
                console.warn("Could not fetch session data:", err);
                renderTooltip(false);
            });
    }
}

function hideTooltip() {
    tooltip.style.display = "none";
}
//Hide tooltip on load
hideTooltip()
//clears the canvas on client side, make request to server
function clearCanvas() {
    drawingContext.fillStyle = "#ffffff";
    drawingContext.fillRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < CELL_SIDE_COUNT; i++) {
        for (let j = 0; j < CELL_SIDE_COUNT; j++) {
            colourHistory[`${i}_${j}`] = "#ffffff";
        }
    }

    fetch("/multiplayer/canvas/clear", {
        method: "POST"
    }).then(res => res.json())
        .then(data => {
            console.log("Canvas cleared on server:", data);
            refreshCanvasFromServer();
        }).catch(err => console.error("Error clearing canvas on server:", err));
}

window.addEventListener('resize', () => {
    setTimeout(() => {
        refreshCanvasFromServer();
    }, 100);
});