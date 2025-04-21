async function register_account(event){
    event.preventDefault();
    const submittedUsernameAttempt = document.getElementById('registerUsernameInput').value
    const submittedPasswordAttempt = document.getElementById('registerPasswordInput').value

    try{
        const hashedPassword = await hashPassword(submittedPasswordAttempt);

        const response = await fetch("/register_account", {
            method: "POST",
            headers:{
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${encodeURIComponent(submittedUsernameAttempt)}&password=${encodeURIComponent(hashedPassword)}`
        });

        if (response.status === 200) {
            alert("Account created!");
        } else {
            const resData = await response.json();
            alert("Registration failed: " + (resData.error || "Unknown error"));
        }

    } catch (error) {
        console.error("Registration error:", error);
    }
}

async function attempt_login(event){
    event.preventDefault();
    const submittedUsernameAttempt = document.getElementById('loginUsernameInput').value;
    const submittedPasswordAttempt = document.getElementById('loginPasswordInput').value;

    const hashedPassword = await hashPassword(submittedPasswordAttempt);
    
    try{
        const response = await fetch("/login", {
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

async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
    return hashHex;
}
