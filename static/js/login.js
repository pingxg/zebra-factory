function showErrorToast() {
    const toast = document.getElementById('errorToast');
    const closeBtn = document.getElementById('errorToastClose');

    toast.style.opacity = '1';
    toast.style.transform = 'translate(-50%, 0)';
    
    closeBtn.onclick = function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translate(-50%, -100%)';
    };
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translate(-50%, -100%)';
    }, 3000);  // Toast will be visible for 3 seconds
}