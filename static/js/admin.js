async function fetch_user(event){
    event.preventDefault();

    const userId = document.getElementById('loginUsernameInput').value;

    try {
        const response = await fetch(`/api/userinfo?id=${encodeURIComponent(userId)}`);
        if (!response.ok) throw new Error('User not found');

        const user = await response.json();
        const display = document.getElementById('userDisplay');

        display.innerHTML = `
            <h3>Editing User ID: ${user.id}</h3>
            <input type="hidden" id="editUserId" value="${user.id}">
            <label>Username:</label>
            <input type="text" id="editUsername" value="${user.username}"><br>
            <label>Password:</label>
            <input type="password" id="editPassword" value=""><br>  <!-- Empty password field -->
            <input type="hidden" id="originalHashedPassword" value="${user.password}">
            <label>Account Type:</label>
            <input type="text" id="editUserType" value="${user.userType}"><br>
            <label>Created pixel drawing IDs:</label>
            <input type="text" id="editDrawings" value="${user.creationsIDs}"><br>
            <button id="saveUserButton">Save Changes</button>
        `;

        document.getElementById('saveUserButton').addEventListener('click', saveUserChanges);
        
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}


async function saveUserChanges() {
    const id = document.getElementById('editUserId').value;
    const username = document.getElementById('editUsername').value;
    const password = document.getElementById('editPassword').value;
    const userType = document.getElementById('editUserType').value;
    const userDrawings = document.getElementById('editDrawings').value;

    const originalHashedPassword = document.getElementById('originalHashedPassword').value;
    let hashed_password;

    if (password !== "") {
        hashed_password = await hashPassword(password);
    } else {
        hashed_password = originalHashedPassword;
    }

    try {
        const response = await fetch('/api/update_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, username, hashed_password, userType, userDrawings })
        });

        const result = await response.json();
        if (response.ok) {
            alert('User updated successfully!');
        } else {
            throw new Error(result.error || "Unknown error");
        }
    } catch (err) {
        alert(`Failed to update user: ${err.message}`);
    }
}


async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('userInfo').addEventListener('submit', fetch_user);
});