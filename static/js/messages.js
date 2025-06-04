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

    newMessages.forEach(msg => {
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
    let html = `
        ${msg.username}: ${msg.content} <br> ${msg.created}
    `;

    let buttonHTML = '';

    if (msg.can_delete) {
        buttonHTML += `
            <form method="POST" action="/delete/${msg.id}" style="display:inline; margin-right:10px;">
                <button type="submit" style="background-color:#dc3545; color:white; border:none; padding:5px 10px; cursor:pointer;">
                    Delete Message
                </button>
            </form>
        `;
    }

    if (msg.can_ban && msg.ip_address) {
        buttonHTML += `
            <button onclick="banUserFromMessage('${msg.ip_address}')" style="background-color:#fd7e14; color:white; border:none; padding:5px 10px; cursor:pointer;">
                Ban User
            </button>
        `;
    }

    if (buttonHTML) {
        html += `<div style="margin-top: 5px;">${buttonHTML}</div>`;
    }

    return html;
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