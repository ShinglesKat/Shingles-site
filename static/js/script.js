function showAlert(){
    alert("HeeHee");
}

async function retrieve_messages(){
    try {
        // Make a GET request to fetch messages
        const response = await fetch("/message.html");

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        // Parse the JSON response
        const json = await response.json();

        // Clear any existing messages in the message list
        const messageList = document.getElementById('messageList');
        messageList.innerHTML = ''; // Clears the list before appending new messages

        // Loop through each message and create a list item for it
        json.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = `${msg.name}: ${msg.message}`;  // Customize this depending on the structure of your data
            messageList.appendChild(li);
        });
    } catch (error) {
        console.error(error.message);
    }
}

// Call retrieve_messages when the page loads
window.onload = retrieve_messages;
