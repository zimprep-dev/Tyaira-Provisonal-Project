// Custom Modal System - Platform Wide
// Replaces ugly browser alerts with beautiful modals

const Modal = {
    // Show alert modal
    alert: function(message, type = 'info', title = null) {
        const types = {
            success: { icon: 'check-circle', title: 'Success' },
            error: { icon: 'x-circle', title: 'Error' },
            warning: { icon: 'alert-triangle', title: 'Warning' },
            info: { icon: 'info', title: 'Information' }
        };

        const config = types[type] || types.info;
        const modalTitle = title || config.title;

        return new Promise((resolve) => {
            this.show({
                type: type,
                icon: config.icon,
                title: modalTitle,
                message: message,
                buttons: [
                    {
                        text: 'OK',
                        class: 'btn-primary',
                        onClick: () => {
                            this.close();
                            resolve(true);
                        }
                    }
                ]
            });
        });
    },

    // Show confirm modal
    confirm: function(message, title = 'Confirm', options = {}) {
        return new Promise((resolve) => {
            this.show({
                type: options.type || 'warning',
                icon: options.icon || 'alert-circle',
                title: title,
                message: message,
                buttons: [
                    {
                        text: options.cancelText || 'Cancel',
                        class: 'btn-outline',
                        onClick: () => {
                            this.close();
                            resolve(false);
                        }
                    },
                    {
                        text: options.confirmText || 'Confirm',
                        class: options.confirmClass || 'btn-primary',
                        onClick: () => {
                            this.close();
                            resolve(true);
                        }
                    }
                ]
            });
        });
    },

    // Show custom modal
    show: function(config) {
        // Remove existing modal if any
        const existingModal = document.querySelector('.modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }

        // Create modal
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-container">
                <div class="modal-header ${config.type || 'info'}">
                    <div class="modal-icon ${config.type || 'info'}">
                        <i data-feather="${config.icon || 'info'}"></i>
                    </div>
                    <div class="modal-title">
                        <h3>${config.title || 'Notification'}</h3>
                    </div>
                </div>
                <div class="modal-body">
                    ${typeof config.message === 'string' 
                        ? `<p>${config.message}</p>` 
                        : config.message}
                </div>
                <div class="modal-footer">
                    ${config.buttons ? config.buttons.map(btn => `
                        <button class="modal-btn ${btn.class || 'btn-secondary'}" data-action="${btn.text}">
                            ${btn.text}
                        </button>
                    `).join('') : ''}
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Initialize feather icons if available
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Add button click handlers
        if (config.buttons) {
            config.buttons.forEach((btn, index) => {
                const button = overlay.querySelector(`[data-action="${btn.text}"]`);
                if (button && btn.onClick) {
                    button.addEventListener('click', btn.onClick);
                }
            });
        }

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.close();
            }
        });

        // Show modal
        setTimeout(() => {
            overlay.classList.add('active');
        }, 10);
    },

    // Close modal
    close: function() {
        const overlay = document.querySelector('.modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }
};

// Override window.alert to use custom modal
window.alert = function(message) {
    Modal.alert(message, 'info');
};

// Override window.confirm to use custom modal
window.confirm = function(message) {
    return Modal.confirm(message);
};

// Show success toast
function showToast(message, type = 'success') {
    Modal.alert(message, type);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Modal;
}
