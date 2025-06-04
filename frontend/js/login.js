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

    // Forgot password link
    const forgotPasswordLink = document.querySelector('a[href="#"]');
    const forgotPasswordModal = document.getElementById('forgotPasswordModal');
    const closeForgotModal = document.getElementById('closeForgotModal');
    const forgotPasswordForm = document.getElementById('forgotPasswordForm');
    const resetSuccess = document.getElementById('resetSuccess');
    const resetError = document.getElementById('resetError');
    const resetSuccessMessage = document.getElementById('resetSuccessMessage');
    const resetErrorMessage = document.getElementById('resetErrorMessage');
    const passwordResetForm = document.getElementById('passwordResetForm');

    // Show forgot password modal
    forgotPasswordLink.addEventListener('click', function (e) {
        e.preventDefault();
        forgotPasswordModal.classList.remove('hidden');
        resetSuccess.classList.add('hidden');
        resetError.classList.add('hidden');
        forgotPasswordForm.reset();
        forgotPasswordForm.classList.remove('hidden');
        if (passwordResetForm) {
            passwordResetForm.reset();
        }
    });

    // Close forgot password modal
    closeForgotModal.addEventListener('click', function () {
        forgotPasswordModal.classList.add('hidden');
    });

    // Close modal when clicking outside
    forgotPasswordModal.addEventListener('click', function (e) {
        if (e.target === forgotPasswordModal) {
            forgotPasswordModal.classList.add('hidden');
        }
    });

    // Handle forgot password form submission
    forgotPasswordForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-circle-notch fa-spin mr-2"></i>Processando...';
        submitButton.disabled = true;

        const resetUsername = document.getElementById('resetUsername').value;

        try {
            // Send request to the password reset endpoint
            const response = await fetch(`${API_URL}/password/request-reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: resetUsername
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Erro ao processar solicitação.');
            }

            // Success scenario
            resetSuccess.classList.remove('hidden');
            resetError.classList.add('hidden');
            
            // In a real-world application, we wouldn't display the token to the user
            // This is just for demonstration purposes since we don't have an email system
            resetSuccessMessage.textContent = data.message;
            forgotPasswordForm.classList.add('hidden');
            
            // Store username for the reset form
            if (passwordResetForm) {
                passwordResetForm.dataset.username = resetUsername;
            }

        } catch (error) {
            // Error scenario
            resetError.classList.remove('hidden');
            resetSuccess.classList.add('hidden');
            resetErrorMessage.textContent = error.message || 'Erro ao processar a solicitação.';
            console.error(error);
        } finally {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    });

    // Handle password reset form submission
    if (passwordResetForm) {
        passwordResetForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-circle-notch fa-spin mr-2"></i>Processando...';
            submitButton.disabled = true;
            
            const resetToken = document.getElementById('resetToken').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const username = this.dataset.username;
            
            // Validation
            if (!username) {
                alert('Nome de usuário não encontrado. Por favor, tente novamente.');
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
                return;
            }
            
            if (newPassword !== confirmPassword) {
                alert('As senhas não coincidem. Por favor, verifique e tente novamente.');
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
                return;
            }
            
            try {
                // Send request to reset password
                const response = await fetch(`${API_URL}/password/reset`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        reset_token: resetToken,
                        new_password: newPassword
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Erro ao redefinir senha.');
                }
                
                if (data.success) {
                    // Hide reset form
                    this.classList.add('hidden');
                    
                    // Update success message
                    resetSuccessMessage.textContent = 'Senha redefinida com sucesso! Você pode fazer login agora.';
                    
                    // Close modal after delay
                    setTimeout(() => {
                        forgotPasswordModal.classList.add('hidden');
                        forgotPasswordForm.classList.remove('hidden');
                    }, 3000);
                } else {
                    throw new Error(data.message || 'Erro ao redefinir senha.');
                }
                
            } catch (error) {
                alert(error.message || 'Erro ao redefinir senha. Por favor, tente novamente.');
                console.error(error);
            } finally {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        });
    }
});