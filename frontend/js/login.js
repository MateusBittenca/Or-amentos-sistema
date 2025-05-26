const API_URL = "http://localhost:10000";

// Form submission
const loginForm = document.getElementById('loginForm');
loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-circle-notch fa-spin mr-2"></i>Entrando...';
    submitButton.disabled = true;

    const nome = document.getElementById('nome').value;
    const password = document.getElementById('password').value;

    const formData = new URLSearchParams();
    formData.append('username', nome);  // <-- O FastAPI espera 'username'
    formData.append('password', password);

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Usuário ou senha inválidos');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        
        // Store user status in localStorage as backup
        if (data.status) {
            localStorage.setItem('user_status', data.status);
        }
        
        // Store username for display purposes
        if (data.user && data.user.nome) {
            localStorage.setItem('username', data.user.nome);
        }

        // Redirecionar para dashboard.html
        window.location.href = 'dashboard.html';

    } catch (error) {
        alert(error.message);
        console.error(error);
    } finally {
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Toggle password visibility
    const togglePassword = document.querySelector('.toggle-password');
    const passwordInput = document.getElementById('password');

    togglePassword.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Toggle icon
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });

    // Form submission
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Show loading state
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-circle-notch fa-spin mr-2"></i>Entrando...';
        submitButton.disabled = true;

        // Simulate API call

    });
});