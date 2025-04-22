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
            <label>Account Type:</label>
            <input type="text" id="editUserType" value="${user.userType}"><br>
            <button onclick="saveUserChanges()">Save Changes</button>
        `;
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

async function saveUserChanges(){
    const id = document.getElementById('editUserId').value;
    const username = document.getElementById('editUsername').value;
    const userType = document.getElementById('editUserType').value;

    try {
        const response = await fetch('/api/update_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, username, userType })
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

