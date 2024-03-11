// Function to open a modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        // Add Escape key listener for this modal
        escapeKeyListener = function(event) {
            if (event.key === "Escape" || event.key === "Esc") {
                closeModal(modalId);
            }
        };
        document.addEventListener('keydown', escapeKeyListener);
    }
}

// Function to close a modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.removeEventListener('keydown', escapeKeyListener);
        // Reset the form within the modal
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}