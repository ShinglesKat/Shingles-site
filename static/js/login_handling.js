async function register_account(event) {
    event.preventDefault();
    const username = document.getElementById('registerUsernameInput').value.trim();
    const password = document.getElementById('registerPasswordInput').value.trim();

    if (!username || !password) {
        alert("Please fill in both username and password");
        return;
    }

    try {
        const response = await fetch("/api/register_account", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })  // send raw password
        });

        if (response.ok) {
            const resData = await response.json();
            alert("Account created!");
            document.getElementById('registerUsernameInput').value = '';
            document.getElementById('registerPasswordInput').value = '';
        } else {
            const resData = await response.json();
            alert("Registration failed: " + (resData.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Registration error:", error);
        alert("Registration failed: " + error.message);
    }
}

async function attempt_login(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsernameInput').value.trim();
    const password = document.getElementById('loginPasswordInput').value.trim();

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const resText = await response.text();
            alert("Login failed: " + resText);
        }
    } catch (err) {
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
