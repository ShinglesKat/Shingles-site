function confirmLogout() {
    return confirm("Are you sure you want to log out?");
}

// Prevent multiple event listeners from being added
if (!window.logoutListenerAdded) {
    window.logoutListenerAdded = true;
    
    // Use event delegation on document - only needs to run once
    document.addEventListener('click', (event) => {
    // Check if clicked element is a logout link
    if (event.target.matches('a.logout-link')) {
        event.preventDefault();
        
        if (confirmLogout()) {
            fetch('/api/logout', {
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
});}