async function add_message(event) {
    event.preventDefault();

    const username = document.getElementById('nameInput').value;
    const content = document.getElementById('messageInput').value;

    try {
        const banStatus = await fetch("/api/check_ban_status");
        const banData = await banStatus.json();

        if (banData.banned) {
            let banMessage = "You are banned from posting messages.";
            if (banData.reason) {
                banMessage += `\nReason: ${banData.reason}`;
            }
            if (banData.expires_at) {
                const expiry = new Date(banData.expires_at).toLocaleString();
                banMessage += `\nBan expires: ${expiry}`;
            }
            alert(banMessage);
            return;
        }

        const response = await fetch("/message/post_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${encodeURIComponent(username)}&content=${encodeURIComponent(content)}`
        });

        if (!response.ok) {
            throw new Error(`Status: ${response.status}`);
        }

        await response.json();

        document.getElementById('commentForm').reset();

        const msg = document.getElementById("successMessage");
        msg.classList.add("show");
        setTimeout(() => {
            msg.classList.remove("show");
        }, 3000);
        
    } catch (error) {
        console.error("Error adding message:", error.message);
    }
}

setInterval(() => {
    fetch('/api/check_ban_status')
    .then(res => res.json())
    .then(data => {
        if (data.banned) {
        alert('You have been banned! The page will refresh.');
        window.location.reload();
        }
    });
}, 5000);
async function retrieve_messages(){
    try {
        const response = await fetch("/api/get_messages");
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        const messageList = document.getElementById('messageList');
        messageList.innerHTML = '';
        json.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = `${msg.username}: ${msg.content}`;
            messageList.appendChild(li);
        });
    } catch (error) {
        console.error("Error retrieving messages:", error.message);
    }
}

let sessionCache = null;

function banUserFromMessage(ip) {
    const duration = prompt("How long should the user be banned for? ('1h', '24h', '7d'):");
    if (!duration) {
        return;
    }

    const message = prompt("Enter a reason for the ban:");
    if (message === null) {
        return;
    }

    fetch("/ban_ip", {
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
}

document.addEventListener('DOMContentLoaded', () => {
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', add_message);
    }
    
    fetchMessages();
    setInterval(fetchMessages, 1000);
});

function showLoadingMessage() {
    const messageList = document.getElementById('messageList');
    messageList.innerHTML = '<li>Loading messages...</li>';
}

function diffMessages(newMessages) {
    const messageList = document.getElementById('messageList');
    if (!messageList) {
        return;
    }

    const existing = new Map();
    messageList.querySelectorAll('li[data-id]').forEach(li => {
        existing.set(li.getAttribute('data-id'), li);
    });

    const seen = new Set();

    newMessages.slice().reverse().forEach(msg => {
        const id = `message-${msg.id}`;
        seen.add(id);

        let li = existing.get(id);
        if (!li) {
            // Add new message
            li = document.createElement('li');
            li.setAttribute('data-id', id);
            li.innerHTML = buildMessageHTML(msg);
            messageList.prepend(li);
        } else {
            // Check if content changed
            const temp = document.createElement('div');
            temp.innerHTML = buildMessageHTML(msg);
            if (li.innerHTML !== temp.innerHTML) {
                li.innerHTML = buildMessageHTML(msg);
            }
        }
    });

    // Remove messages no longer present
    existing.forEach((li, id) => {
        if (!seen.has(id)) {
            li.remove();
        }
    });
}

function buildMessageHTML(msg) {
    const container = document.createElement('div');

    // Message text (username + message content)
    const messageText = document.createElement('div');
    messageText.textContent = `${msg.username}: ${msg.content}`;
    container.appendChild(messageText);

    // Timestamp on its own line
    const timestamp = document.createElement('div');
    timestamp.textContent = msg.created;
    timestamp.style.fontSize = '0.9em';
    timestamp.style.color = '#666';
    container.appendChild(timestamp);

    // Buttons container
    const buttons = document.createElement('div');
    buttons.style.marginTop = '5px';

    if (msg.can_delete) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete/${msg.id}`;
        form.style.display = 'inline';
        form.style.marginRight = '10px';

        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'submit';
        deleteBtn.textContent = 'Delete Message';
        deleteBtn.style.cssText = 'background-color:#dc3545; color:white; border:none; padding:5px 10px; cursor:pointer;';

        form.appendChild(deleteBtn);
        buttons.appendChild(form);
    }

    if (msg.can_ban && msg.ip_address) {
        const banBtn = document.createElement('button');
        banBtn.textContent = 'Ban User';
        banBtn.style.cssText = 'background-color:#fd7e14; color:white; border:none; padding:5px 10px; cursor:pointer;';
        banBtn.onclick = () => banUserFromMessage(msg.ip_address);
        buttons.appendChild(banBtn);
    }

    if (buttons.childNodes.length > 0) {
        container.appendChild(buttons);
    }

    return container.innerHTML;
}


function fetchMessages() {
    fetch('/api/get_messages')
        .then(response => response.json())
        .then(data => {
            diffMessages(data);
        })
        .catch(err => {
            console.error('Error fetching messages:', err);
        });
}