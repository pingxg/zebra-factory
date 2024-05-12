// document.addEventListener('DOMContentLoaded', function() {
//         flatpickr("#selected_date", {
//             dateFormat: "Y-m-d",
//         });
//     });

function emitPrintZebra() {
    const orderId = "{{ order[0] }}"; 
    fetch('/print/emit_print_zebra', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ order_id: orderId })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'Print event (Zebra) emitted') {
            console.log("Print event (Zebra) successfully emitted");
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
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
    const form = document.getElementById('addReading'); // Make sure your form has this ID
    const submitBtn = document.getElementById('submitBtn');
    form.onsubmit = function() {
        submitBtn.disabled = true; // Disable the button
        submitBtn.innerText = 'Processing...'; // Optional: Change button text
        
    };
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
            const response = fetch(`/weight/edit/${currentEditingWeightId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ edit_weight: newValue }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                console.log("Response:", response);  // Log the response
                return response.json();
            })
            .then(data => {
                console.log("Data:", data);  // Log the data
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


Dropzone.options.fileDropzone = {
    url: '/deliverynote/upload_url',  // Initial URL to get the pre-signed URL
    method: 'POST', // POST to request the pre-signed URL from your Flask backend
    paramName: "file",
    maxFilesize: 5, // MB
    autoProcessQueue: false, // Don't process files automatically on drop/add
    dictDefaultMessage: "Drop files here or click to upload.",
    init: function() {
        var myDropzone = this;

        this.on("addedfile", function(file) {
            // Request a pre-signed URL with the filename and content type
            fetch(`/deliverynote/upload_url?filename=${encodeURIComponent(file.name)}&content_type=${encodeURIComponent(file.type)}`, {
                method: 'GET'  // Assuming your server expects a GET request
            })
            .then(response => response.json())
            .then(data => {
                // Use the pre-signed URL for the actual file upload
                myDropzone.options.url = data.url;
                myDropzone.processQueue(); // Process the queue once the URL is set
            })
            .catch(error => {
                console.error("Error getting the pre-signed URL:", error);
                alert("Failed to get upload URL.");
            });
        });

        this.on("sending", function(file, xhr, formData) {
            xhr.setRequestHeader('Content-Type', file.type);  // Set content type header for S3
        });

        this.on("success", function(file, response) {
            alert("File successfully uploaded");
        });

        this.on("error", function(file, response) {
            alert("Error in upload: " + response);
        });
    }
};