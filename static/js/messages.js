async function add_message(event){
    event.preventDefault();

    const username = document.getElementById('nameInput').value;
    const content = document.getElementById('messageInput').value;

    try {
        const banStatus = await fetch("/api/check_ban_status");
        const banData = await banStatus.json();

        if (banData.banned) {
            let banMessage = "You are banned from posting messages.";
            if (banData.reason) banMessage += `\nReason: ${banData.reason}`;
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
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        console.log(result);
        document.getElementById('commentForm').reset();
        document.getElementById("successMessage").style.display = "block";
        setTimeout(() => {
            document.getElementById("successMessage").style.display = "none";
        }, 3000);
        retrieve_messages();
    } catch (error) {
        console.error("Error adding message:", error.message);
        showAlert(`Error adding message: ${error.message}`);
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

function fetchMessages() {
    if (!messageList) {
        console.log("Not on message");
        return;
    }
    fetch('/api/get_messages')
        .then(response => response.json())
        .then(data => {
            const messageList = document.getElementById('messageList');
            messageList.innerHTML = '';
            data.forEach(msg => {
                const li = document.createElement('li');
                li.innerHTML = `
                    ${msg.username}: ${msg.content} <br> ${msg.created}
                `;
                
                const buttonContainer = document.createElement('div');
                buttonContainer.style.marginTop = '5px';
                
                if (msg.can_delete) {
                    const deleteForm = document.createElement('form');
                    deleteForm.method = 'POST';
                    deleteForm.action = `/delete/${msg.id}`;
                    deleteForm.style.display = 'inline';
                    deleteForm.style.marginRight = '10px';
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.type = 'submit';
                    deleteBtn.textContent = 'Delete Message';
                    deleteBtn.style.backgroundColor = '#dc3545';
                    deleteBtn.style.color = 'white';
                    deleteBtn.style.border = 'none';
                    deleteBtn.style.padding = '5px 10px';
                    deleteBtn.style.cursor = 'pointer';
                    
                    deleteForm.appendChild(deleteBtn);
                    buttonContainer.appendChild(deleteForm);
                }
                
                if (msg.can_ban && msg.ip_address) {
                    const banBtn = document.createElement('button');
                    banBtn.textContent = 'Ban User';
                    banBtn.style.backgroundColor = '#fd7e14';
                    banBtn.style.color = 'white';
                    banBtn.style.border = 'none';
                    banBtn.style.padding = '5px 10px';
                    banBtn.style.cursor = 'pointer';
                    banBtn.onclick = () => banUserFromMessage(msg.ip_address);
                    
                    buttonContainer.appendChild(banBtn);
                }
                
                if (buttonContainer.children.length > 0) {
                    li.appendChild(buttonContainer);
                }
                
                messageList.appendChild(li);
            });
        })
        .catch(err => console.error('Error fetching messages:', err));
}

window.onload = retrieve_messages;