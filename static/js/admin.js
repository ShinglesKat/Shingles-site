async function fetchUserData(event) {
    event.preventDefault();
    const userId = document.getElementById('IDInput').value.trim();
    const userUsername = document.getElementById('loginUsernameInput').value.trim();
    try {
        let response;
        if (userId) {
            // Fetch by ID
            response = await fetch(`/admin/userinfo?id=${encodeURIComponent(userId)}`);
            if (!response.ok) {
                throw new Error('ID not found');
            }
        } else if (userUsername) {
            response = await fetch(`/admin/userinfo?username=${encodeURIComponent(userUsername)}`);
            if (!response.ok) {
                throw new Error('Username not found');
            }
        } else {
            throw new Error('Please provide either a User ID or Username');
        }
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
        const response = await fetch('/admin/update_user', {
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

async function getAllBannedUsers(){
    try {
        const response = await fetch('/admin/all_banned_users');

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Status: ${response.status}`);
        }

        const data = await response.json();
        renderBannedUsers(data);

    } catch (error) {
        console.error('Error fetching banned users:', error.message);
    }
}

function renderBannedUsers(bans) {
    const container = document.getElementById('messageList');
    container.innerHTML = '';

    if (bans.length === 0) {
        container.textContent = 'No banned IPs.';
        return;
    }

    bans.forEach(ban => {
        const row = document.createElement('div');

        const text = document.createElement('span');
        text.textContent = `${ban.ip} - ${ban.reason} - (expires: ${ban.ban_expires_at})`;
        row.appendChild(text);

        const unbanBtn = document.createElement('button');
        unbanBtn.type = 'button';
        unbanBtn.textContent = 'Cleanse ban';
        unbanBtn.style.marginLeft = '10px';
        unbanBtn.addEventListener('click', () => unbanIp(ban.ip));
        row.appendChild(unbanBtn);

        container.appendChild(row);
    });
}

function confirmUnban(ip) {
    return confirm(`Are you sure you want to unban ${ip}?`);
}

async function unbanIp(ip) {
    if (!confirmUnban(ip)) {
        return;
    }

    try {
        const response = await fetch('/admin/unban_ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Status: ${response.status}`);
        }

        await response.json();
        getAllBannedUsers(); // refresh the list so the removed row disappears

    } catch (error) {
        console.error('Error unbanning IP:', error.message);
        alert('Failed to unban: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('userInfo').addEventListener('submit', fetchUserData);

    document.getElementById('banBtn').addEventListener('click', () => {
        banUserByIp(null); // triggers the prompt() fallback for IP
    });

    document.getElementById('getAllBannedUsersBtn').addEventListener('click', () => {
        getAllBannedUsers();
    });
});

