import { buildMiniCanvas } from './minicanvas_helper.js';

async function fetchUserDrawings() {
    const userID = document.getElementById('loginUsernameInput').value;
    try {
        const response = await fetch(`/account/get_user_drawings/${userID}`);
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
    const miniCanvasWrapper = buildMiniCanvas(drawing, { size: 150, returnWrapper: true });
    drawingLink.appendChild(miniCanvasWrapper);
    const nameLabel = document.createElement('p');
    nameLabel.textContent = drawing.piece_name;
    nameLabel.classList.add('drawing-name');
    const drawingContainer = document.createElement('div');
    drawingContainer.classList.add('drawing-container');
    drawingContainer.appendChild(drawingLink);
    drawingContainer.appendChild(nameLabel);
    container.appendChild(drawingContainer);
}

function handlePasswordReset() {
    const currentPassword = prompt("Please enter your current password:");
    if (!currentPassword) return;

    const newPassword = prompt("Please enter your new password (min 6 characters):");
    if (!newPassword) return;

    if (newPassword.length < 6) {
        alert("Error: New password must be at least 6 characters long.");
        return;
    }
    if (currentPassword === newPassword) {
        alert("Error: New password must be different from the current password.");
        return;
    }

    fetch('/account/reset_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'Password reset failed due to a server error.');
            });
        }
        return response.json();
    })
    .then(data => {
        alert(data.status || "Password successfully reset!");
        return fetch('/account/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    })
    .then(() => {
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Operation Error:', error);
        alert(`Failed to reset password or log out. ${error.message}`);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchUserDrawings();

    const resetPasswordButton = document.getElementById('resetPasswordButton');
    if (resetPasswordButton) {
        resetPasswordButton.addEventListener('click', handlePasswordReset);
    }
});