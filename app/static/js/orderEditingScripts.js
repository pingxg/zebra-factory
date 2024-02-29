// Function to open a modal
function openModal(modalID) {
    document.getElementById(modalID).classList.remove('hidden');
}

// Function to close a modal
function closeModal(modalID) {
    document.getElementById(modalID).classList.add('hidden');
    const form = document.getElementById('updateOrderForm');
    saveButton = document.getElementById('saveOrderUpdateBtn');
    saveButton.disabled = true;
    saveButton.classList.add('bg-gray-400', 'text-gray-500', 'cursor-not-allowed');
    saveButton.classList.remove('bg-blue-600', 'hover:bg-blue-700', 'text-white');
}

// Function to fetch order details and then open the modal with populated data
async function populateUpdateModal(orderId) {
    try {
        const response = await fetch(`/get-order-info/${orderId}`);
        const orderDetails = await response.json();
        document.getElementById('hiddenOrderID').value = orderDetails.id;
        document.getElementById('displayCustomerName').textContent = orderDetails.customer;
        document.getElementById('displayOrderDate').textContent = orderDetails.date;
        document.getElementById('displayProductName').textContent = orderDetails.product;
        document.getElementById('updateOrderPriceInput').value = parseFloat(orderDetails.price).toFixed(2);
        document.getElementById('updateOrderQuantityInput').value = parseFloat(orderDetails.quantity).toFixed(2);
        // const selectedOption = document.getElementById('fishSizeSelect').querySelector(`option[value="${orderDetails.fish_size}"]`);
        // if (selectedOption) {
        //     selectedOption.selected = true;
        // } else {
        //   // Handle cases where the order's fish size isn't in the available options
        //     console.warn(`Fish size "${orderDetails.fish_size}" not found in select options`);
        // }
        const fishSizeSelect = document.getElementById('fishSizeSelect');

        if (!orderDetails.product.toLowerCase().includes("lohi")) {
            fishSizeSelect.disabled = true; // Disable the selector if product name does not include "lohi"
            fishSizeSelect.value = "";
        } else {
            fishSizeSelect.disabled = false; // Enable the selector if product name includes "lohi"
            const selectedOption = fishSizeSelect.querySelector(`option[value="${orderDetails.fish_size}"]`);
            if (selectedOption) {
                selectedOption.selected = true;
            } else {
                // Handle cases where the order's fish size isn't in the available options
                console.warn(`Fish size "${orderDetails.fish_size}" not found in select options`);
            }
        }
        openModal('updateOrderModal'); // Use this function to open the modal after populating it
    } catch (error) {
        console.error('Error fetching order details:', error);
    }
}




function initializeFishSizeSelect() {
    const fishSizes = ['大L', '小S']; // Define options
    const currentFishSize = ''; // Default selected value
    const fishSizeSelect = document.getElementById('fishSizeSelect');

    // Clear existing options
    fishSizeSelect.innerHTML = '';

    // Add options to the select
    fishSizes.forEach(size => {
        const option = document.createElement('option');
        option.value = size;
        option.textContent = size;
        if (size === currentFishSize) {
            option.selected = true; // Set default selected value
        }
        fishSizeSelect.appendChild(option);
    });
}
document.addEventListener('DOMContentLoaded', initializeFishSizeSelect);



document.addEventListener('DOMContentLoaded', () => {
    let initialFormData = {};
    const form = document.getElementById('updateOrderForm');
    saveOrderUpdateBtn = document.getElementById('saveOrderUpdateBtn');
    saveEditOrderUpdateBtn = document.getElementById('saveEditOrderUpdateBtn');

    // Store initial form data
    Array.from(form.elements).forEach(input => {
        if (input.name) { // Ensure the element has a name attribute
            initialFormData[input.name] = input.value;
        }
    });

    // Monitor form for changes
    form.addEventListener('input', () => {
        let isFormChanged = false;
        Array.from(form.elements).forEach(input => {
            if (input.name && initialFormData[input.name] !== input.value) {
                isFormChanged = true;
            }
        });

        saveOrderUpdateBtn.disabled = !isFormChanged;
        saveOrderUpdateBtn.classList.add('bg-blue-600', 'hover:bg-blue-700', 'text-white');
        saveOrderUpdateBtn.classList.remove('bg-gray-400', 'text-gray-500', 'cursor-not-allowed');
    });

    saveOrderUpdateBtn.disabled = true;
    saveOrderUpdateBtn.classList.add('bg-gray-400', 'text-gray-500', 'cursor-not-allowed');
    saveOrderUpdateBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700', 'text-white');
});


// DOMContentLoaded listener to setup event listeners once the document is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('cancelOrderUpdateBtn').addEventListener('click', function(event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        closeModal('updateOrderModal');
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const updateOrderForm = document.getElementById('updateOrderForm');
    const deleteOrderBtn = document.getElementById('deleteOrderBtn');
    const saveOrderUpdateBtn = document.getElementById('saveOrderUpdateBtn');
    const saveEditOrderUpdateBtn = document.getElementById('saveEditOrderUpdateBtn');

    saveOrderUpdateBtn.addEventListener('click', function() {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        const formData = new FormData(updateOrderForm);
        const orderData = {
            id: parseInt(formData.get('id')),
            price: parseFloat(formData.get('price')),
            quantity: parseFloat(formData.get('quantity')),
            fish_size: formData.get('fishSize')
        };
        fetch(`/update-order/${parseInt(formData.get('id'))}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData),
        })
        .then(data => {
            if (data.status === 200) {
                window.location.reload();  // Refresh the page to show the updated value
            } else {
                alert('Error updating order.');
            }
        })
        .catch(error => {
            console.log("Fetch error:", error);  // Log the error
        });
    });
    saveEditOrderUpdateBtn.addEventListener('click', function() {
        const formData = new FormData(updateOrderForm);
        window.location.href = `/order/${parseInt(formData.get('id'))}`; // Redirect to the order detail page
    });

    deleteOrderBtn.addEventListener('click', function(event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        // Show confirmation dialog
        const userConfirmed = confirm("Are you sure you want to delete this order?\nAll weight details will be lost!");
        
        if (!userConfirmed) {
            return; // User clicked Cancel, so do not proceed with deletion
        }

        const formData = new FormData(updateOrderForm);
        fetch(`/delete-order/${parseInt(formData.get('id'))}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(data => {
            if (data.status === 200) {
                window.location.reload();  // Refresh the page to show the updated value
            } else {
                alert('Error deleting order.');
            }
        })
        .catch(error => {
            console.log("Fetch error:", error);  // Log the error
        });
    });
});
