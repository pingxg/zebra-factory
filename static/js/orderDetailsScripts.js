function validateForm() {
    var scaleReading = document.getElementById("scale_reading").value;
    if (scaleReading === "" || scaleReading === null) {
        showErrorToast();
        return false; // This will prevent the form from submitting
    }
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
        flatpickr("#selected_date", {
            dateFormat: "Y-m-d",
        });
    });


function showToast() {
    const toast = document.getElementById('toast');
    const closeBtn = document.getElementById('toastClose');
    
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
function showPrintToast() {
    const toast = document.getElementById('printToast');
    const closeBtn = document.getElementById('printToastClose');
    
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

document.addEventListener('DOMContentLoaded', (event) => {
    let customerNameSpan = document.querySelector(".customer-name");
    let containerWidth = customerNameSpan.parentElement.offsetWidth;
    
    while(customerNameSpan.offsetWidth > containerWidth && parseInt(window.getComputedStyle(customerNameSpan).fontSize) > 10) {
        let currentSize = parseInt(window.getComputedStyle(customerNameSpan).fontSize);
        customerNameSpan.style.fontSize = (currentSize - 1) + "px";
    }
});




document.addEventListener('DOMContentLoaded', function() {
    const editBtns = document.querySelectorAll('.edit-btn');
    const editModal = document.getElementById('editModal');
    const editInput = document.getElementById('editWeightInput');
    const saveEditBtn = document.getElementById('saveEdit');
    const cancelEditBtn = document.getElementById('cancelEdit');
    let currentEditingWeightId = null;

    editBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            event.preventDefault();  // Prevent the default behavior
            currentEditingWeightId = this.getAttribute('data-weight-id');
            order_id = this.getAttribute('data-order-id');
            const currentWeight = this.getAttribute('data-current-weight');
            editInput.value = currentWeight;
            editModal.classList.remove('hidden');
        });
    });

    saveEditBtn.addEventListener('click', function() {
        console.log("Save button clicked");  // Add this line

            const newValue = editInput.value;
            console.log("Sending fetch request");  // Add this line
            fetch(`/weight/${currentEditingWeightId}/edit?order_id=${order_id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `edit_weight=${newValue}`,
            })
            .then(response => {
                console.log("Received response");  // Add this line
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log("Processed data:", data);
                if (data.success) {
                    window.location.reload();  // Refresh the page to show the updated value
                } else {
                    alert('Error updating weight.');
                }
            })
            .catch(error => {
                console.log("Fetch error:", error);  // Log the error
            });
        });

    cancelEditBtn.addEventListener('click', function() {
        editModal.classList.add('hidden');
    });
});



function showDeleteConfirmation(deleteUrl) {
    // Set the form's action to the provided delete URL
    document.getElementById('deleteForm').action = deleteUrl;
    
    // Show the delete confirmation modal
    document.getElementById('deleteConfirmationModal').classList.remove('hidden');
}

document.getElementById('cancelDelete').addEventListener('click', function() {
    // Hide the delete confirmation modal
    document.getElementById('deleteConfirmationModal').classList.add('hidden');
});