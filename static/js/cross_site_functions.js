// ─── Logout ──────────────────────────────────────────────────────────────────

function confirmLogout() {
    return confirm("Are you sure you want to log out?");
}

// Prevent multiple event listeners from being added
if (!window.logoutListenerAdded) {
    window.logoutListenerAdded = true;

    // Use event delegation on document - only needs to run once
    document.addEventListener('click', (event) => {
        if (event.target.matches('a.logout-link')) {
            event.preventDefault();

            if (confirmLogout()) {
                fetch('/account/logout', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Logout failed');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(data.message);
                    window.location.href = '/';
                })
                .catch(error => {
                    console.error('Error during logout:', error);
                    alert('An error occurred during logout.');
                });
            }
        }
    });
}

// ─── Session ─────────────────────────────────────────────────────────────────

// undefined  = not yet fetched
// null       = fetched but not logged in / error
// object     = active session data
var sessionCache = undefined;

async function getSessionData() {
    if (sessionCache !== undefined) {
        return sessionCache;
    }
    try {
        const response = await fetch('/get_session_data');
        if (response.ok) {
            sessionCache = await response.json();
            console.log('Session cached:', sessionCache);
        } else if (response.status === 401) {
            console.log('User not logged in');
            sessionCache = null;
        } else {
            console.log('Session check failed, assuming no admin privileges');
            sessionCache = null;
        }
    } catch (error) {
        console.error('Error checking session:', error);
        sessionCache = null;
    }
    return sessionCache;
}

// ─── Password hashing ────────────────────────────────────────────────────────

async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

// ─── Ban user by IP ──────────────────────────────────────────────────────────

function banUserByIp(ip) {
    const duration = prompt("How long should the user be banned for? ('1h', '24h', '7d'):");
    if (!duration) {
        console.log('Ban cancelled - no duration provided');
        return;
    }

    const message = prompt("Enter a reason for the ban:");
    if (message === null) {
        console.log('Ban cancelled - no reason provided');
        return;
    }

    console.log('Sending ban request:', { ip, reason: message, ban_duration: duration });

    fetch("/admin/ban_ip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip, reason: message, ban_duration: duration })
    })
    .then(res => {
        console.log('Ban response status:', res.status);
        if (res.ok) {
            return res.json().then(data => {
                console.log('Ban success:', data);
                alert("User banned successfully.");
            });
        } else {
            return res.json().then(data => {
                console.error('Ban failed:', data);
                alert(`Failed to ban user: ${data.error || 'Unknown error'}`);
            }).catch(() => {
                alert(`Failed to ban user. Status: ${res.status}`);
            });
        }
    })
    .catch(err => {
        console.error("Ban error:", err);
        alert("Error banning user: " + err.message);
    });
}
