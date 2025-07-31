
const selectFieldsDataCache = {
    customers: null,
    products: null,
    fishSizes: null,

};

async function populateSelectFields() {
    const fieldConfigs = [{
        key: 'customers',
        endpoint: '/customer/get-active-customers',
        elementId: 'customersSelect',
        isDatalist: true
    }, {
        key: 'products',
        endpoint: '/product/get-active-products',
        elementId: 'productsSelect'
    }, {
        key: 'customers',
        endpoint: '/customer/get-active-customers',
        elementId: 'updateCustomersSelect',
        isDatalist: true,
        cacheKey: 'customers'
    }, {
        key: 'products',
        endpoint: '/product/get-active-products',
        elementId: 'updateProductsSelect',
        cacheKey: 'products'
    }];

    for (const config of fieldConfigs) {
        const cacheKey = config.cacheKey || config.key;
        if (!selectFieldsDataCache[cacheKey]) {
            try {
                const response = await fetch(config.endpoint);
                selectFieldsDataCache[cacheKey] = await response.json();
            } catch (error) {
                console.error(`Failed to fetch ${cacheKey}:`, error);
            }
        }

        const data = selectFieldsDataCache[cacheKey];
        if (!data) continue;

        const element = document.getElementById(config.elementId);

        if (config.isDatalist) {
            const datalistId = element.getAttribute('list');
            const datalist = document.getElementById(datalistId);
            datalist.innerHTML = '';
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item;
                datalist.appendChild(option);
            });
        } else {
            element.innerHTML = '';
            const defaultOption = new Option('Select', '');
            element.appendChild(defaultOption);
            data.forEach(item => {
                const option = new Option(item);
                element.appendChild(option);
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    populateSelectFields();
});



// Function to fetch order details and then open the modal with populated data
async function populateUpdateModal(orderId) {
    try {
        const response = await fetch(`/order/get/${orderId}`)

        // Get the JSON data from the response
        const orderDetails = await response.json();
        document.getElementById('hiddenOrderID').value = orderDetails.id;
        document.getElementById('updateCustomersSelect').value = orderDetails.customer;
        document.getElementById('updateOrderDateInput').value = orderDetails.date;
        document.getElementById('updateProductsSelect').value = orderDetails.product;
        document.getElementById('updateOrderPriceInput').value = parseFloat(orderDetails.price).toFixed(2);
        document.getElementById('updateOrderQuantityInput').value = parseFloat(orderDetails.quantity).toFixed(2);
        document.getElementById('noteInput').value = orderDetails.note;

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


function populateAddOrderModal(date = null, customer = null) {
    // Fetch order details if an orderId is provided, otherwise set defaults
    // Set default values for date and customer if provided
    populateSelectFields(); // Populate select fields when opening the modal
    if (date) document.getElementById('addOrderDateInput').value = date;
    if (customer) document.getElementById('customersSelect').value = customer;
    // Handle enabling/disabling or showing/hiding fields as needed
    openModal('addOrderModal'); // Open the modal
}



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



document.addEventListener('DOMContentLoaded', function () {
    const updateOrderForm = document.getElementById('updateOrderForm');
    const deleteOrderBtn = document.getElementById('deleteOrderBtn');
    const saveOrderUpdateBtn = document.getElementById('saveOrderUpdateBtn');
    const saveEditOrderUpdateBtn = document.getElementById('saveEditOrderUpdateBtn');

    saveOrderUpdateBtn.addEventListener('click', function () {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        const formData = new FormData(updateOrderForm);
        const orderData = {
            id: parseInt(formData.get('id')),
            customer: formData.get('customer'),
            date: formData.get('date'),
            product: formData.get('product'),
            price: parseFloat(formData.get('price')),
            quantity: parseFloat(formData.get('quantity')),
            fish_size: formData.get('fishSize'),
            note: formData.get('note'),
        };
        fetch(`/order/update/${parseInt(formData.get('id'))}`, {
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
                    console.log('Error updating order.');
                    window.location.reload();
                }
            })
            .catch(error => {
                console.log("Fetch error:", error);  // Log the error
            });
    });


    saveEditOrderUpdateBtn.addEventListener('click', function () {
        const formData = new FormData(updateOrderForm);
        window.location.href = `/order/${parseInt(formData.get('id'))}`; // Redirect to the order detail page
    });

    deleteOrderBtn.addEventListener('click', function (event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        // Show confirmation dialog
        const userConfirmed = confirm("Are you sure you want to delete this order?\nAll weight details will be lost!");
        if (!userConfirmed) {
            return; // User clicked Cancel, so do not proceed with deletion
        }

        const formData = new FormData(updateOrderForm);
        fetch(`/order/delete/${parseInt(formData.get('id'))}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then(data => {
                console.log(data);
                if (data.status === 200) {
                    window.location.reload();  // Refresh the page to show the updated value
                } else if (data.status === 403) {
                    console.log('Failed to delete order.', 'error');
                    toastr.error('Access denied. You do not have permission to add an order.');
                    window.location.reload();
                }
            })
            .catch(error => {
                console.log("Fetch error:", error);  // Log the error
            });
    });
});



document.getElementById('addOrderForm').addEventListener('submit', async function (event) {
    event.preventDefault(); // Prevent the default form submission

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    try {
        fetch(`/order/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
            .then(data => {
                const response = data.json();
                if (data.status === 200) {
                    window.location.reload();  // Refresh the page to show the updated value
                } else {
                    console.log('Failed to add order.', 'error');
                    window.location.reload();
                }
            })
            .catch(error => {
                console.log("Fetch error:", error);  // Log the error
            });
        closeModal('addOrderModal'); // Assuming closeModal is your function to close the modal

    } catch (error) {
        console.error('Error adding order:', error);
    }
});


function checkFormInputs() {
    const fields = document.querySelectorAll('#addOrderForm .required');
    let allFilled = true;
    fields.forEach(field => {
        if (!field.value) {
            allFilled = false;
        }
    });
    document.getElementById('addOrderBtn').disabled = !allFilled;
}

document.addEventListener('DOMContentLoaded', () => {
    const fields = document.querySelectorAll('#addOrderForm .required');
    fields.forEach(field => {
        field.addEventListener('input', checkFormInputs);
        field.addEventListener('change', checkFormInputs);
    });
    // Initial check in case of pre-filled values
    checkFormInputs();
});

// DOMContentLoaded listener to setup event listeners once the document is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('cancelAddOrderBtn').addEventListener('click', function (event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        closeModal('addOrderModal');
    });
});

// DOMContentLoaded listener to setup event listeners once the document is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('cancelOrderUpdateBtn').addEventListener('click', function (event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        closeModal('updateOrderModal');
    });
});


// DOMContentLoaded listener to setup event listeners once the document is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    const productsSelect = document.getElementById('productsSelect');
    const fishSizesSelect = document.getElementById('fishSizesSelect');

    productsSelect.addEventListener('change', function (event) {
        // Assuming the presence of "lohi" is checked in the option's text
        const selectedOptionText = productsSelect.options[productsSelect.selectedIndex].text.toLowerCase();

        // Check if "lohi" is present in the selected option's text
        if (selectedOptionText.includes("lohi")) {
            fishSizesSelect.disabled = false; // Enable fishSizesSelect if "lohi" is present
        } else {
            fishSizesSelect.disabled = true; // Disable fishSizesSelect if "lohi" is not present
            fishSizesSelect.value = ''; // Optionally reset the value
        }
    });
});
