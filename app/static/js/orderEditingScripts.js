
// document.addEventListener('DOMContentLoaded', () => {
//     const searchBtn = document.getElementById('search-btn');
//     const orderTable = document.getElementById('order-table');

//     // Function to populate the order table
//     function populateOrderTable(data) {
//         // Clear previous table content
//         orderTable.innerHTML = '';

//         // Create table headers based on selected dates
//         // Create table rows and cells based on order data
//         // Note: Full implementation will depend on your data structure
//     };


    // // Handle Search Button Click
    // searchBtn.addEventListener('click', () => {
    //     const dateRange = document.getElementById('date-range').value;
    //     // Fetch data based on the date range and populate the table
    //     // This is where you would make an AJAX call to your Flask backend
    //     // For demo purposes, let's call populateOrderTable with mock data
    //     populateOrderTable(mockData); // Replace mockData with actual data from AJAX call
    // });
    

    // Initialize the date picker to the current ISO week
    // You will need to write a function to calculate the current ISO week in JavaScript

    // Implement the functionality to toggle between quantity and price view
    // This may involve updating the table cells and re-rendering the table

    // Implement cell editing functionality
    // This could be complex and involve more in-depth JavaScript to handle inline editing, validation, and updating the backend
// });

// Function to open a modal
function openModal(modalID) {
    document.getElementById(modalID).classList.remove('hidden');
}

// Function to close a modal
function closeModal(modalID) {
    document.getElementById(modalID).classList.add('hidden');
}

// Function to fetch order details and then open the modal with populated data
async function populateUpdateModal(orderId) {
    try {
        const response = await fetch(`/get-order-info/${orderId}`);
        const orderDetails = await response.json();
        document.getElementById('customerSelect').value = orderDetails[1];
        document.getElementById('updateOrderDateInput').value = orderDetails[2];
        document.getElementById('productSelect').value = orderDetails[3];
        document.getElementById('updateOrderPriceInput').value = parseFloat(orderDetails[4]).toFixed(2);
        document.getElementById('updateOrderQuantityInput').value = parseFloat(orderDetails[5]).toFixed(2);
        document.getElementById('fishSizeSelect').value = orderDetails[6]
        openModal('updateOrderModal'); // Use this function to open the modal after populating it
    } catch (error) {
        console.error('Error fetching order details:', error);
    }
}

// DOMContentLoaded listener to setup event listeners once the document is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Assuming you have a trigger to open the modal, such as a button to edit an order
    // const editOrderButtons = document.querySelectorAll('.editOrderButton'); // Example class name for edit buttons
    // editOrderButtons.forEach(button => {
    //     button.addEventListener('click', function() {
    //         const orderId = this.getAttribute('data-order-id'); // Assuming button has data-order-id attribute
    //         populateUpdateModal(orderId);
    //     });
    // });

    document.getElementById('cancelOrderUpdateBtn').addEventListener('click', function(event) {
        event.preventDefault(); // Prevents the default action if it's a submit button.
        closeModal('updateOrderModal');
    });
    
});
