function showAlert(){
    alert("HeeHee");
}

async function add_message(event){
    event.preventDefault();

    const username = document.getElementById('nameInput').value;
    const content = document.getElementById('messageInput').value;

    try {
        const response = await fetch("/message.html", {
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

        //clear form after submission
        document.getElementById('commentForm').reset();

        document.getElementById("successMessage").style.display = "block";
        retrieve_messages();

    } catch (error) {
        console.error("Error adding message:", error.message);
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

async function attempt_login(event){
    event.preventDefault();
    const submittedPasswordAttempt = document.getElementById('passwordInput').value

    try{
        const response = await fetch("/login.html", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `password=${encodeURIComponent(submittedPasswordAttempt)}`
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const resText = await response.text();
            alert("Login failed or error occurred.");
            console.log("Server response:", resText);
        }
    } catch(err){
        console.error("Login error:", err);
    }
}

//Call retrieve_messages when the page loads
window.onload = retrieve_messages;
