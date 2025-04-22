async function add_message(event){
    event.preventDefault();

    const username = document.getElementById('nameInput').value;
    const content = document.getElementById('messageInput').value;

    try {
        const response = await fetch("/message/post_message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${encodeURIComponent(username)}&content=${encodeURIComponent(content)}`
        });

        // Check if response is successful
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        // Parse the JSON response
        const result = await response.json();
        console.log(result);

        // Clear form after submission
        document.getElementById('commentForm').reset();

        // Show success message and hide after 3 seconds
        document.getElementById("successMessage").style.display = "block";
        setTimeout(() => { 
            document.getElementById("successMessage").style.display = "none"; 
        }, 3000);

        // Retrieve updated messages
        retrieve_messages();

    } catch (error) {
        console.error("Error adding message:", error.message);
        showAlert(`Error adding message: ${error.message}`);
    }
}

async function retrieve_messages(){
    try {
        const response = await fetch("/message.html");

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const json = await response.json();

        const messageList = document.getElementById('messageList');
        messageList.innerHTML = '';

        //Loop through each message and create a list item for it
        json.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = `${msg.name}: ${msg.message}`;
            messageList.appendChild(li);
        });
    } catch (error) {
        console.error(error.message);
    }
}
document.addEventListener('DOMContentLoaded', () => {
    fetchMessages();
    setInterval(fetchMessages, 1000); //poll every second
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

                // If current session is admin, show delete button
                if (msg.can_delete) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = `/delete/${msg.id}`;
                    const btn = document.createElement('button');
                    btn.type = 'submit';
                    btn.textContent = 'Delete Message';
                    form.appendChild(btn);
                    li.appendChild(form);
                }

                messageList.appendChild(li);
            });
        })
        .catch(err => console.error('Error fetching messages:', err));
}
//Call retrieve_messages when the page loads
window.onload = retrieve_messages;