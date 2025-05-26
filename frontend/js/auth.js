// auth.js - Handle authentication and user permissions

/**
 * Parse JWT token to get user information
 * @param {string} token - JWT token
 * @returns {Object} - Decoded token payload
 */
function parseJwt(token) {
    try {
        console.log('Attempting to parse JWT token');
        
        // Get the payload part of the JWT (second part)
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const payload = JSON.parse(jsonPayload);
        console.log('JWT payload parsed successfully:', payload);
        return payload;
    } catch (e) {
        console.error('Error parsing JWT token', e);
        return null;
    }
}

/**
 * Check if the current user has admin status
 * @returns {boolean} - True if user is admin, false otherwise
 */
function isAdmin() {
    // Check JWT token first
    const token = localStorage.getItem('access_token');
    if (token) {
        const payload = parseJwt(token);
        if (payload && payload.status === 'ADM') {
            return true;
        }
    }
    
    // Fallback to localStorage if JWT parsing fails
    const userStatus = localStorage.getItem('user_status');
    return userStatus === 'ADM';
}

/**
 * Get current user information from token
 * @returns {Object|null} - User information or null if not logged in
 */
function getCurrentUser() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    return parseJwt(token);
}

/**
 * Apply permission-based UI restrictions
 */
function applyPermissions() {
    try {
        // Handle the activity form visibility
        const formContainer = document.querySelector('form#addActivityForm');
        if (formContainer) {
            const parentContainer = formContainer.closest('.bg-white.rounded-lg.shadow-md.p-4');
            
            if (parentContainer) {
                // Only show the add activity form for admins
                if (!isAdmin()) {
                    parentContainer.style.display = 'none';
                    
                    // Adjust the grid layout since we're hiding an element
                    const topSection = document.querySelector('.top-section');
                    if (topSection) {
                        topSection.style.gridTemplateColumns = '1fr';
                    }
                } else {
                    console.log('User is admin, showing activity form');
                }
            }
        } else {
            console.warn('Add activity form not found in the DOM');
        }
        
        // Hide admin-only elements for non-admin users
        if (!isAdmin()) {
            const adminOnlyElements = document.querySelectorAll('.admin-only-element');
            adminOnlyElements.forEach(element => {
                element.style.display = 'none';
            });
        }
        
        // Display user info in the UI
        displayUserInfo();
        
        // You can add more permission-based UI adjustments here
    } catch (error) {
        console.error('Error applying permissions:', error);
    }
}

/**
 * Display user information in the UI
 */
function displayUserInfo() {
    const username = localStorage.getItem('username') || 'Usuário';
    const isUserAdmin = isAdmin();
    
    // Find the navigation container
    const navContainer = document.querySelector('.nav-container');
    if (navContainer) {
        // Create user info element
        const userInfoElement = document.createElement('div');
        userInfoElement.className = 'flex items-center ml-auto mr-4 text-sm user-info';
        userInfoElement.innerHTML = `
            <i class="fas fa-user-circle text-xl mr-2"></i>
            <span>${username}</span>
            ${isUserAdmin ? '<span class="ml-2 bg-green-500 text-white text-xs px-2 py-1 rounded">ADM</span>' : ''}
        `;
        
        // Insert before the nav-buttons
        const navButtons = navContainer.querySelector('.nav-buttons');
        if (navButtons) {
            navContainer.insertBefore(userInfoElement, navButtons);
        } else {
            navContainer.appendChild(userInfoElement);
        }
    }
}

// Apply permissions when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    
    // Debug user information
    debugUserInfo();
    
    // Apply permissions based on user role
    applyPermissions();
});

/**
 * Debug function to display user information in the console
 */
function debugUserInfo() {
    const token = localStorage.getItem('access_token');
    const userStatus = localStorage.getItem('user_status');
    const username = localStorage.getItem('username');
    
    console.group('User Authentication Debug Info');
    console.log('Username:', username);
    console.log('User status from localStorage:', userStatus);
    
    if (token) {
        const payload = parseJwt(token);
        console.log('JWT payload:', payload);
        console.log('Is admin based on JWT:', payload && payload.status === 'ADM');
    } else {
        console.log('No token found');
    }
    
    console.log('Final isAdmin() result:', isAdmin());
    console.groupEnd();
}

// Export functions for use in other scripts
window.auth = {
    isAdmin,
    getCurrentUser,
    parseJwt
}; 