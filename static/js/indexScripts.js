var socket = io.connect('https://zebra-factory.onrender.com');
socket.on('refresh_data', function(data) {
    alert(data.message);
    // Optionally, you can refresh the page to get the latest data
    location.reload();
});


document.addEventListener('DOMContentLoaded', function() {
    flatpickr("#selected_date", {
        dateFormat: "Y-m-d",
    });
});