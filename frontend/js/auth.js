document.addEventListener('DOMContentLoaded', () => {
    // SECURITY AUTO-REDIRECT: If a token exists, the user is already logged in.
    // Skip the login page and go straight to dashboard.
    if (localStorage.getItem('token')) {
        window.location.href = 'dashboard.html';
        return;
    }

    // --- DOM Element Selection ---
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegisterBtn = document.getElementById('showRegister');
    const showLoginBtn = document.getElementById('showLogin');
    const loginBox = document.getElementById('loginBox');
    const registerBox = document.getElementById('registerBox');

    // --- Form Toggling Logic ---
    // Swaps between Login and Register views without a page reload.
    showRegisterBtn.addEventListener('click', (e) => {
        e.preventDefault();
        loginBox.classList.add('hidden');
        registerBox.classList.remove('hidden');
    });

    showLoginBtn.addEventListener('click', (e) => {
        e.preventDefault();
        registerBox.classList.add('hidden');
        loginBox.classList.remove('hidden');
    });

    // --- Login Form Submission ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const errorMsg = document.getElementById('loginError');
        const submitBtn = loginForm.querySelector('button[type="submit"]');

        try {
            // UI State: Indicate loading
            submitBtn.textContent = 'Logging in...';
            submitBtn.disabled = true;
            errorMsg.classList.add('hidden');

            // API Call: Fetch JWT from Backend
            const response = await API.login(email, password);

            // Persist the token so it survives page refreshes
            localStorage.setItem('token', response.access_token);

            // Navigate to protected area
            window.location.href = 'dashboard.html';
        } catch (error) {
            // Display human-readable error (e.g., 'Incorrect password')
            errorMsg.textContent = error.message || 'Login failed';
            errorMsg.classList.remove('hidden');
        } finally {
            // Re-enable UI
            submitBtn.textContent = 'Login';
            submitBtn.disabled = false;
        }
    });

    // --- Registration Form Submission ---
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        const errorMsg = document.getElementById('regError');
        const submitBtn = registerForm.querySelector('button[type="submit"]');

        // Validation: Passwords must match before we even talk to the server
        if (password !== confirmPassword) {
            errorMsg.textContent = "Passwords do not match";
            errorMsg.classList.remove('hidden');
            return;
        }

        try {
            submitBtn.textContent = 'Creating Account...';
            submitBtn.disabled = true;
            errorMsg.classList.add('hidden');

            // 1. Create the account
            await API.register(email, password, fullName);

            // 2. Auto-login Flow: Log the user in immediately after successful signup
            const loginRes = await API.login(email, password);
            localStorage.setItem('token', loginRes.access_token);
            window.location.href = 'dashboard.html';
        } catch (error) {
            errorMsg.textContent = error.message || 'Registration failed';
            errorMsg.classList.remove('hidden');
        } finally {
            submitBtn.textContent = 'Create Account';
            submitBtn.disabled = false;
        }
    });
});
