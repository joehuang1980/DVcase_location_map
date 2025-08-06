document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([22.99, 120.21], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var geoJsonLayer = L.geoJson().addTo(map);

    var datePicker = document.getElementById('date-picker');

    // Fetch available dates and populate the date picker
    fetch('/api/dates')
        .then(response => response.json())
        .then(dates => {
            dates.forEach(date => {
                var option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                datePicker.appendChild(option);
            });

            // Load data for the first date by default
            if (dates.length > 0) {
                loadDataForDate(dates[0]);
            }
        });

    datePicker.addEventListener('change', function() {
        loadDataForDate(this.value);
    });

    function loadDataForDate(date) {
        fetch(`/api/data?date=${date}`)
            .then(response => response.json())
            .then(geoJsonData => {
                geoJsonLayer.clearLayers();
                geoJsonLayer.addData(JSON.parse(geoJsonData));
            });
    }
});