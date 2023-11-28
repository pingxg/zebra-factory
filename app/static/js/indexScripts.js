document.addEventListener('DOMContentLoaded', function() {
    flatpickr("#selected_date", {
        dateFormat: "Y-m-d",
    });
});


function showOrders(productType) {
    // Hide all order contents
    var contents = document.getElementsByClassName('orders-content');
    for (var i = 0; i < contents.length; i++) {
        contents[i].style.display = 'none';
    }

    // Show the selected product's orders
    var selectedContent = document.getElementById(productType + 'Orders');
    selectedContent.style.display = 'block';
}