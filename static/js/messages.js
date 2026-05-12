async function add_message(event) {
    event.preventDefault();

    const username = document.getElementById('nameInput').value;
    const content = document.getElementById('messageInput').value;
    try {
        const response = await fetch("/messages/post_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${encodeURIComponent(username)}&content=${encodeURIComponent(content)}`
        });

        if (!response.ok) {
            const errorData = await response.json();
            
            if (response.status === 403 && errorData.error && errorData.error.includes("banned")) {
                alert(errorData.error);
                return;
            } else {
                throw new Error(errorData.error || `Status: ${response.status}`);
            }
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
    fetch('/check_ban_status')
    .then(res => res.json())
    .then(data => {
        if (data.banned) {
            let banMessage = "You have been banned from posting messages.";
            if (data.reason) {
                banMessage += `\nReason: ${data.reason}`;
            }
            if (data.expires_at) {
                const expiryDate = new Date(data.expires_at);
                banMessage += `\nThis ban expires on: ${expiryDate.toLocaleString()}`;
            }
            alert(banMessage);
            window.location.reload();
        }
    })
    .catch(err => {
        console.error("Error checking ban status:", err);
    });
}, 5000);

async function banUserFromMessage(ip) {
    const session = await getSessionData();
    if (!session || session.accounttype !== 'admin') {
        alert('You do not have permission to ban users.');
        return;
    }
    banUserByIp(ip);
}

document.addEventListener('DOMContentLoaded', () => {
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', add_message);
    }
    
    fetchMessages();
    setInterval(fetchMessages, 1000);
});

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
            li = document.createElement('li');
            li.setAttribute('data-id', id);
            li.innerHTML = buildMessageHTML(msg);
            attachEventListeners(li, msg);
            
            messageList.prepend(li);
        } else {
            const temp = document.createElement('div');
            temp.innerHTML = buildMessageHTML(msg);
            if (li.innerHTML !== temp.innerHTML) {
                li.innerHTML = buildMessageHTML(msg);
                attachEventListeners(li, msg);
            }
        }
    });

    existing.forEach((li, id) => {
        if (!seen.has(id)) {
            li.remove();
        }
    });
}

function attachEventListeners(li, msg) {
    if (msg.can_ban && msg.ip_address) {
        const banBtn = li.querySelector('.ban-button');
        if (banBtn) {
            banBtn.addEventListener('click', function(e) {
                e.preventDefault();
                banUserFromMessage(msg.ip_address);
            });
        }
    }
}

function buildMessageHTML(msg) {
    const container = document.createElement('div');

    const messageText = document.createElement('div');
    messageText.textContent = `${msg.username}: ${msg.content}`;
    container.appendChild(messageText);

    const timestamp = document.createElement('div');
    timestamp.textContent = msg.created;
    timestamp.style.fontSize = '0.9em';
    timestamp.style.color = '#666';
    container.appendChild(timestamp);

    const buttons = document.createElement('div');
    buttons.style.marginTop = '5px';

    if (msg.can_delete) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/messages/delete_message/${msg.id}`;
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
        banBtn.type = 'button';
        banBtn.className = 'ban-button';
        banBtn.textContent = 'Ban User';
        banBtn.style.cssText = 'background-color:#fd7e14; color:white; border:none; padding:5px 10px; cursor:pointer; margin-left: 5px;';
        
        buttons.appendChild(banBtn);
    }

    if (buttons.childNodes.length > 0) {
        container.appendChild(buttons);
    }

    return container.innerHTML;
}

function fetchMessages() {
    fetch('/messages/get_messages')
        .then(response => response.json())
        .then(data => {
            diffMessages(data);
        })
        .catch(err => {
            console.error('Error fetching messages:', err);
        });
}