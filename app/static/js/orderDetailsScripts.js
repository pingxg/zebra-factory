document.addEventListener('DOMContentLoaded', (event) => {
    let customerNameSpan = document.querySelector(".customer-name");
    let containerWidth = customerNameSpan.parentElement.offsetWidth;

    while (customerNameSpan.offsetWidth > containerWidth && parseInt(window.getComputedStyle(customerNameSpan).fontSize) > 10) {
        let currentSize = parseInt(window.getComputedStyle(customerNameSpan).fontSize);
        customerNameSpan.style.fontSize = (currentSize - 1) + "px";
    }
});


document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('addReading'); // Make sure your form has this ID
    const submitBtn = document.getElementById('submitBtn');
    form.onsubmit = function () {
        submitBtn.disabled = true; // Disable the button
        submitBtn.innerText = 'Processing...'; // Optional: Change button text

    };
});


document.addEventListener('DOMContentLoaded', function () {
    const editBtns = document.querySelectorAll('.edit-btn');
    const editModal = document.getElementById('editModal');
    const editInput = document.getElementById('editWeightInput');
    const saveEditBtn = document.getElementById('saveEdit');
    const cancelEditBtn = document.getElementById('cancelEdit');
    let currentEditingWeightId = null;

    editBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            event.preventDefault();  // Prevent the default behavior
            currentEditingWeightId = this.getAttribute('data-weight-id');
            order_id = this.getAttribute('data-order-id');
            const currentWeight = this.getAttribute('data-current-weight');
            editInput.value = currentWeight;
            editModal.classList.remove('hidden');
        });
    });

    saveEditBtn.addEventListener('click', function () {
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

    cancelEditBtn.addEventListener('click', function () {
        editModal.classList.add('hidden');
    });
});



function showDeleteConfirmation(deleteUrl) {
    // Set the form's action to the provided delete URL
    document.getElementById('deleteForm').action = deleteUrl;

    // Show the delete confirmation modal
    document.getElementById('deleteConfirmationModal').classList.remove('hidden');
}

document.getElementById('cancelDelete').addEventListener('click', function () {
    // Hide the delete confirmation modal
    document.getElementById('deleteConfirmationModal').classList.add('hidden');
});



Dropzone.autoDiscover = false;

const uploader = new Dropzone("#upload-widget", {
    dictDefaultMessage: "Drop or click here to add files",
    url: "https://endpoint.s3.amazonaws.com/",  // will be overwritten dynamically
    method: "POST",
    timeout: 3600000,
    parallelUploads: 100,
    maxFilesize: 5,  // MB
    autoProcessQueue: false,
    addRemoveLinks: true,
    createImageThumbnails: false,
    accept: function (file, done) {
        const req = new XMLHttpRequest();
        req.onreadystatechange = () => {
            if (req.readyState === XMLHttpRequest.DONE) {
                if (req.status === 200) {
                    const signedPost = JSON.parse(req.responseText);
                    this.options.url = signedPost.url;
                    file.signedPost = signedPost;
                    done();
                } else {
                    done("Fail to get pre-signed url.");
                }
            }
        };
        req.open("POST", '/deliverynote/get-presigned-post');
        req.setRequestHeader("Content-type", "application/json; charset=UTF-8");

        // Add payload to request to include file information
        const payload = JSON.stringify({ filename: file.name, filetype: file.type });
        req.send(payload);
    },
});

uploader.on('sending', (file, xhr, formData) => {
    const fields = file.signedPost.fields;
    Object.keys(fields).forEach(k => formData.append(k, fields[k]));
    formData.append('Content-Type', file.type);  // Ensure Content-Type is set
});

uploader.on("success", (file, response) => {
    const imageUrl = file.signedPost.fields.key;
    // Store imageUrl in a global array
    uploadedImages.push(imageUrl);
});

uploader.on("queuecomplete", () => {
    fetch('/deliverynote/update-image-links', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            customer_name: customerName,
            date: date,
            image_urls: uploadedImages
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                flash(data.message);
                location.reload();  // Refresh the page upon success
            } else {
                alert('Failed to associate images with orders');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

    // Clear the uploadedImages array after processing
    uploadedImages = [];
});

document.querySelector("#dropzone-btn").addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    uploader.processQueue();
});

// Global array to store uploaded image URLs
let uploadedImages = [];




function showDeleteImageConfirmation(imageId, presignedUrl, deleteUrl) {
    if (confirm('Are you sure you want to delete this image?')) {
        fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image_id: imageId, presigned_url: presignedUrl })
        })
            .then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    response.json().then(data => {
                        alert('Error deleting the image: ' + data.error);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting the image.');
            });
    }
}


function scanQRCode() {
    // Create a modal for the QR scanner
    const scannerModal = document.createElement('div');
    scannerModal.innerHTML = `
        <div class="fixed z-50 inset-0 overflow-y-auto">
            <div class="flex items-center justify-center min-h-screen px-4">
                <div class="fixed inset-0 bg-gray-500 bg-opacity-75"></div>
                <div class="relative bg-white rounded-lg p-8 max-w-lg w-full">
                    <div id="reader"></div>
                    <div id="scannerStatus" class="mt-2 text-center text-gray-600"></div>
                    <button id="closeScanner" class="mt-4 w-full bg-red-500 text-white py-3 px-4 rounded-lg">
                        Close Scanner
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(scannerModal);

    const statusDiv = document.getElementById('scannerStatus');

    // Modified permission handling
    async function requestCameraPermission() {
        try {
            const constraints = {
                video: {
                    facingMode: { exact: "environment" },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            // Stop the stream right away
            stream.getTracks().forEach(track => track.stop());
            sessionStorage.setItem('cameraPermission', 'granted');
            startScanner();
        } catch (err) {
            // If environment camera fails, try with any camera
            try {
                const fallbackConstraints = {
                    video: true
                };
                const fallbackStream = await navigator.mediaDevices.getUserMedia(fallbackConstraints);
                fallbackStream.getTracks().forEach(track => track.stop());
                sessionStorage.setItem('cameraPermission', 'granted');
                startScanner();
            } catch (fallbackErr) {
                console.error("Camera permission error:", fallbackErr);
                sessionStorage.removeItem('cameraPermission');
                statusDiv.textContent = "Camera permission denied. Please check your browser settings and try again.";
            }
        }
    }

    function startScanner() {
        const html5QrCode = new Html5Qrcode("reader");
        const config = {
            fps: 10, // Reduced FPS for better performance
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0,
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            },
            formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
            verbose: false,
            videoConstraints: {
                facingMode: "environment",
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 } // Reduced frame rate
            }
        };

        html5QrCode.start(
            { facingMode: "environment" },
            config,
            (decodedText) => {
                try {
                    const scannedValue = parseFloat(decodedText);
                    if (!isNaN(scannedValue)) {
                        const formattedValue = scannedValue.toFixed(2);
                        document.getElementById('scale_reading').value = formattedValue;

                        html5QrCode.stop().then(() => {
                            document.body.removeChild(scannerModal);

                            // Set flag before submitting
                            sessionStorage.setItem('scannerActive', 'true');

                            const form = document.getElementById('addReading');
                            const submitBtn = document.getElementById('submitBtn');
                            if (form && submitBtn) {
                                submitBtn.click();
                            }
                        });
                    } else {
                        statusDiv.textContent = 'Invalid number format scanned. Please try again.';
                    }
                } catch (error) {
                    console.error('Error processing scanned value:', error);
                    statusDiv.textContent = 'Error processing scanned value. Please try again.';
                }
            },
            (errorMessage) => {
                if (!errorMessage.includes("QR code parse error")) {
                    console.log("QR Error:", errorMessage);
                    if (errorMessage.includes("permission")) {
                        sessionStorage.removeItem('cameraPermission');
                    }
                }
            }
        ).catch((err) => {
            console.error("Start failed:", err);
            if (err.message && err.message.includes("permission")) {
                sessionStorage.removeItem('cameraPermission');
            }
            statusDiv.textContent = `Error starting scanner: ${err.message || 'Please check camera permissions'}`;
        });

        document.getElementById('closeScanner').addEventListener('click', () => {
            html5QrCode.stop().then(() => {
                document.body.removeChild(scannerModal);
                sessionStorage.removeItem('scannerActive');
            }).catch((err) => {
                console.error("Stop failed:", err);
                // Ensure the modal is removed even if stopping fails
                document.body.removeChild(scannerModal);
            });
        });
    }

    // Check if HTTPS is being used
    if (window.location.protocol !== 'https:') {
        statusDiv.textContent = "Camera access requires HTTPS. Please use a secure connection.";
        return;
    }

    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        statusDiv.textContent = "Sorry, your browser doesn't support camera access.";
        return;
    }

    // Initialize the scanner
    if (sessionStorage.getItem('cameraPermission') === 'granted') {
        startScanner();
    } else {
        requestCameraPermission();
    }
}

// Auto-reopen scanner after page refresh if it was active
document.addEventListener('DOMContentLoaded', () => {
    if (sessionStorage.getItem('scannerActive') === 'true') {
        scanQRCode();
    }
});

webView.getSettings().setJavaScriptEnabled(true);
webView.getSettings().setMediaPlaybackRequiresUserGesture(false);