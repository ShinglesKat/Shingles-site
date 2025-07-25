async function register_account(event){
    event.preventDefault();
    const submittedUsernameAttempt = document.getElementById('registerUsernameInput').value.trim();
    const submittedPasswordAttempt = document.getElementById('registerPasswordInput').value.trim();
    
    if (!submittedUsernameAttempt || !submittedPasswordAttempt) {
        alert("Please fill in both username and password");
        return;
    }
    
    try{
        const hashedPassword = await hashPassword(submittedPasswordAttempt);
        const response = await fetch("/api/register_account", {
            method: "POST",
            headers:{
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                username: submittedUsernameAttempt,
                password: hashedPassword
            })
        });
        
        console.log("Response status:", response.status);
        console.log("Response ok:", response.ok);
        
        if (response.ok) {
            const resData = await response.json();
            alert("Account created!");
            // Clear the form
            document.getElementById('registerUsernameInput').value = '';
            document.getElementById('registerPasswordInput').value = '';
        } else {
            // Check if response is JSON or HTML
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const resData = await response.json();
                alert("Registration failed: " + (resData.error || "Unknown error"));
            } else {
                const resText = await response.text();
                console.log("Server returned HTML:", resText);
                alert("Registration failed: Server error (check console)");
            }
        }
    } catch (error) {
        console.error("Registration error:", error);
        alert("Registration failed: " + error.message);
    }
}

async function attempt_login(event){
    event.preventDefault();
    const submittedUsernameAttempt = document.getElementById('loginUsernameInput').value;
    const submittedPasswordAttempt = document.getElementById('loginPasswordInput').value;

    const hashedPassword = await hashPassword(submittedPasswordAttempt);
    
    try{
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${encodeURIComponent(submittedUsernameAttempt)}&password=${encodeURIComponent(hashedPassword)}`
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const resText = await response.text();
            alert("Login failed: " + resText);
            console.log("Server response:", resText);
        }
    } catch(err){
        console.error("Login error:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        loginForm.addEventListener('submit', attempt_login);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', register_account);
    }
});


async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
    return hashHex;
}
