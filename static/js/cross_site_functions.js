// This is coming back to bite me in the ahh because I didnt realise inline js is baddd and I cba redoing it all for every button

function confirmLogout() {
    return confirm("Are you sure you want to log out?");
}

document.addEventListener('DOMContentLoaded', () => {
    const logoutLink = document.querySelector('a.logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', event => {
            if (!confirmLogout()) {
                event.preventDefault();
            }
        });
    }
});