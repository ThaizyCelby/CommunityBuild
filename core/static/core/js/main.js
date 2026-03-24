// main.js

// Live search for professionals
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('professionalSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.professional-card');
            cards.forEach(card => {
                const name = card.querySelector('.card-title').textContent.toLowerCase();
                const profession = card.querySelector('.profession').textContent.toLowerCase();
                if (name.includes(searchTerm) || profession.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Login modal trigger for protected links
    const protectedLinks = document.querySelectorAll('.needs-login');
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));

    protectedLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            // Store the intended URL to redirect after login
            const destination = this.getAttribute('href');
            document.getElementById('loginRedirect').value = destination;
            loginModal.show();
        });
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            bootstrap.Alert.getOrCreateInstance(alert).close();
        });
    }, 5000);
});