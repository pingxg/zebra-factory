document.addEventListener('DOMContentLoaded', (event) => {
    let customerNameSpan = document.querySelector(".customer-name");
    let containerWidth = customerNameSpan.parentElement.offsetWidth;

    while (customerNameSpan.offsetWidth > containerWidth && parseInt(window.getComputedStyle(customerNameSpan).fontSize) > 10) {
        let currentSize = parseInt(window.getComputedStyle(customerNameSpan).fontSize);
        customerNameSpan.style.fontSize = (currentSize - 1) + "px";
    }
});


document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('addReading');
    if (!form) return;

    const submitBtn = document.getElementById('submitBtn');
    const scaleInput = document.getElementById('scale_reading');
    const batchInput = document.getElementById('batch_number');
    const statusMessage = document.getElementById('addReadingStatus');

    const isFloatValue = (value) => {
        if (!value) return false;
        const normalized = value.trim();
        if (normalized === '') return false;
        const numericValue = Number(normalized);
        return !Number.isNaN(numericValue) && Number.isFinite(numericValue);
    };

    const isBatchValue = (value) => /^[A-Za-z]+[0-9]+$/.test((value || '').trim());

    const showStatus = (message) => {
        if (!statusMessage) return;
        statusMessage.textContent = message;
        statusMessage.classList.remove('hidden');
    };

    const hideStatus = () => {
        if (!statusMessage) return;
        statusMessage.textContent = '';
        statusMessage.classList.add('hidden');
    };

    const validateInputs = () => {
        const scaleReading = scaleInput ? scaleInput.value.trim() : '';
        const batchNumber = batchInput ? batchInput.value.trim() : '';

        if (batchInput && batchNumber) {
            batchInput.value = batchNumber.toUpperCase();
        }

        if (!scaleReading && !batchNumber) {
            showStatus('Please provide both weight and batch number.');
            return false;
        }
        if (!scaleReading) {
            showStatus('Weight is missing. Scan or enter a float value.');
            return false;
        }
        if (!batchNumber) {
            showStatus('Batch number is missing. Scan or enter letters followed by numbers.');
            return false;
        }
        if (!isFloatValue(scaleReading)) {
            showStatus('Weight format is invalid. Use a float value.');
            return false;
        }
        if (!isBatchValue(batchNumber)) {
            showStatus('Batch format is invalid. Expected letters followed by numbers, e.g. AB123.');
            return false;
        }

        hideStatus();
        return true;
    };

    if (scaleInput) {
        scaleInput.addEventListener('input', validateInputs);
    }
    if (batchInput) {
        batchInput.addEventListener('input', validateInputs);
        batchInput.addEventListener('blur', () => {
            if (batchInput.value.trim()) {
                batchInput.value = batchInput.value.trim().toUpperCase();
            }
            validateInputs();
        });
    }

    form.onsubmit = function () {
        if (!validateInputs()) {
            return false;
        }

        submitBtn.disabled = true;
        submitBtn.innerText = 'Processing...';
        return true;
    };
});


document.addEventListener('DOMContentLoaded', function () {
    // Handler for editing weight records
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function (event) {
            event.preventDefault();

            const weightId = this.getAttribute('data-weight-id');
            const currentWeight = this.getAttribute('data-current-weight');
            const currentBatchNumber = this.getAttribute('data-current-batch-number');

            // Prompt for new weight
            const newWeightStr = prompt("Enter the new weight (leave blank to keep current):", currentWeight);

            // If user did not cancel the weight prompt
            if (newWeightStr !== null) {
                // Prompt for new batch number
                const newBatchNumberStr = prompt("Enter the new batch number (leave blank to keep current):", currentBatchNumber);

                // If user did not cancel the batch number prompt
                if (newBatchNumberStr !== null) {
                    const newWeight = newWeightStr.trim();
                    const newBatchNumber = newBatchNumberStr.trim().toUpperCase();

                    const isWeightChanged = newWeight !== '' && newWeight !== currentWeight;
                    const isBatchChanged = newBatchNumber !== '' && newBatchNumber !== currentBatchNumber;

                    if (!isWeightChanged && !isBatchChanged) {
                        // No alert needed if nothing changed, just do nothing.
                        return;
                    }

                    // Validate weight if changed
                    if (isWeightChanged && isNaN(newWeight)) {
                        alert("Invalid input. Please enter a valid number for the weight.");
                        return;
                    }
                    if (isBatchChanged && !/^[A-Za-z]+[0-9]+$/.test(newBatchNumber)) {
                        alert("Invalid batch number. Use letters followed by numbers, e.g. AB123.");
                        return;
                    }

                    const payload = {};
                    if (isWeightChanged) payload.edit_weight = newWeight;
                    if (isBatchChanged) payload.edit_batch_number = newBatchNumber;

                    fetch(`/weight/edit/${weightId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                window.location.reload();
                            } else {
                                alert('Error updating record: ' + (data.error || 'Unknown error'));
                            }
                        })
                        .catch(error => {
                            console.error("Fetch error:", error);
                            alert('An error occurred while updating the record.');
                        });
                }
            }
        });
    });

    // Handler for deleting weight records
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function (event) {
            event.preventDefault();
            const deleteUrl = this.getAttribute('data-delete-url');

            if (confirm('Are you sure you want to delete this weight record?')) {
                // Create a temporary form to submit the DELETE request
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = deleteUrl;

                document.body.appendChild(form);
                form.submit();
            }
        });
    });
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
    // Check if the order is already complete
    if (typeof isOrderComplete !== 'undefined' && isOrderComplete) {
        showFlash('Order is already complete. Cannot add more readings.', 'error');
        return; // Stop the function from proceeding
    }

    // Clear previous scan data from session storage
    sessionStorage.removeItem('scannedWeight');
    sessionStorage.removeItem('scannedBatchNumber');

    // Create a modal for the QR scanner
    const scannerModal = document.createElement('div');
    scannerModal.innerHTML = `
        <div class="fixed z-50 inset-0 overflow-y-auto">
            <div class="flex items-center justify-center min-h-screen px-4">
                <div class="fixed inset-0 bg-gray-500 bg-opacity-75"></div>
                <div class="relative bg-white rounded-lg p-8 max-w-lg w-full">
                    <div id="reader"></div>

                    <div class="flex justify-around my-4">
                        <div id="weightIndicator" class="text-center">
                            <i class="fas fa-question-circle text-gray-400 text-4xl"></i>
                            <p class="text-gray-600">Weight</p>
                        </div>
                        <div id="batchIndicator" class="text-center">
                            <i class="fas fa-question-circle text-gray-400 text-4xl"></i>
                            <p class="text-gray-600">Batch Number</p>
                        </div>
                    </div>

                    <div id="scannerStatus" class="mt-2 text-center text-gray-600">Scan both QR codes (weight + batch number), any order.</div>
                    <button id="closeScanner" class="mt-4 w-full bg-red-500 text-white py-3 px-4 rounded-lg">
                        Close Scanner
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(scannerModal);

    const statusDiv = document.getElementById('scannerStatus');
    const weightIcon = document.querySelector('#weightIndicator i');
    const batchIcon = document.querySelector('#batchIndicator i');
    const scaleInput = document.getElementById('scale_reading');
    const batchNumberInput = document.getElementById('batch_number');

    const isPurelyNumeric = (str) => {
        const trimmedStr = (str || '').trim();
        if (trimmedStr === "") return false;
        const numericValue = Number(trimmedStr);
        return !Number.isNaN(numericValue) && Number.isFinite(numericValue);
    };

    const isBatchCode = (str) => /^[A-Za-z]+[0-9]+$/.test((str || '').trim());

    const updateIndicatorsAndStatus = () => {
        const weight = sessionStorage.getItem('scannedWeight');
        const batchNumber = sessionStorage.getItem('scannedBatchNumber');

        if (weight) {
            weightIcon.className = 'fas fa-check-circle text-green-500 text-4xl';
        }
        if (batchNumber) {
            batchIcon.className = 'fas fa-check-circle text-green-500 text-4xl';
        }

        if (!weight && !batchNumber) {
            statusDiv.textContent = 'Waiting for scan...';
            return;
        }
        if (!weight) {
            statusDiv.textContent = 'Batch number scanned. Please scan weight QR code.';
            return;
        }
        if (!batchNumber) {
            statusDiv.textContent = 'Weight scanned. Please scan batch number QR code.';
            return;
        }

        statusDiv.textContent = 'Weight and batch number scanned. Submitting...';
    };

    // Respect any manual values that are already present.
    if (scaleInput && isPurelyNumeric(scaleInput.value.trim())) {
        sessionStorage.setItem('scannedWeight', Number.parseFloat(scaleInput.value.trim()).toFixed(2));
    }
    if (batchNumberInput && isBatchCode(batchNumberInput.value.trim())) {
        sessionStorage.setItem('scannedBatchNumber', batchNumberInput.value.trim().toUpperCase());
    }
    updateIndicatorsAndStatus();

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
            fps: 30, // A balanced FPS for performance and battery life.
            qrbox: { width: 250, height: 250 }, // A square box is optimal for QR codes.
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            },
            formatsToSupport: [
                Html5QrcodeSupportedFormats.QR_CODE
            ],
            verbose: false,
            videoConstraints: {
                facingMode: "environment",
                width: { ideal: 640 }, // Lower resolution for faster processing.
                height: { ideal: 480 },
            }
        };

        html5QrCode.start(
            { facingMode: "environment" },
            config,
            (decodedText, decodedResult) => {
                console.log("Scanned Data:", decodedText);

                const scannedText = (decodedText || '').trim();
                if (isPurelyNumeric(scannedText)) {
                    sessionStorage.setItem('scannedWeight', Number.parseFloat(scannedText).toFixed(2));
                } else if (/^[A-Za-z]/.test(scannedText) && isBatchCode(scannedText)) {
                    sessionStorage.setItem('scannedBatchNumber', scannedText.toUpperCase());
                } else {
                    statusDiv.textContent = 'Unrecognized QR format. Batch must be letters+numbers, weight must be float.';
                    return;
                }

                const weight = sessionStorage.getItem('scannedWeight');
                const batchNumber = sessionStorage.getItem('scannedBatchNumber');

                updateIndicatorsAndStatus();

                if (weight && batchNumber) {
                    if (scaleInput) scaleInput.value = weight;
                    if (batchNumberInput) batchNumberInput.value = batchNumber;
                    html5QrCode.stop().then(() => {
                        document.body.removeChild(scannerModal);
                        sessionStorage.removeItem('scannedWeight');
                        sessionStorage.removeItem('scannedBatchNumber');
                        const form = document.getElementById('addReading');
                        if (form) {
                            form.submit();
                        }
                    });
                }
            },
            (errorMessage) => {
                // Non-critical errors can be logged without alerting the user
                if (!errorMessage.includes("code parse error")) {
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
                sessionStorage.removeItem('scannedWeight');
                sessionStorage.removeItem('scannedBatchNumber');
            }).catch((err) => {
                console.error("Stop failed:", err);
                document.body.removeChild(scannerModal);
            });
        });
    }

    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        statusDiv.textContent = "Camera access requires HTTPS. Please use a secure connection.";
        return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        statusDiv.textContent = "Sorry, your browser doesn't support camera access.";
        return;
    }

    if (sessionStorage.getItem('cameraPermission') === 'granted') {
        startScanner();
    } else {
        requestCameraPermission();
    }
}

// The following lines seem to be related to a webview and might not be used in a standard web browser context.
// If they cause errors, they might need to be removed or placed inside a condition that checks for the webview environment.
try {
    webView.getSettings().setJavaScriptEnabled(true);
    webView.getSettings().setMediaPlaybackRequiresUserGesture(false);
} catch (e) {
    console.log("Not in a webView environment or webView is not defined.");
}