window.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById("drawingCanvas");
    const ctx = canvas.getContext("2d");

    // Read drawing content from data attribute
    const drawingContent = JSON.parse(canvas.dataset.drawingContent);

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cellPixelLength = canvas.width / 50;

    drawingContent.forEach(({x, y, colour}) => {
        ctx.fillStyle = colour;
        ctx.fillRect(x * cellPixelLength, y * cellPixelLength, cellPixelLength, cellPixelLength);
    });
});
