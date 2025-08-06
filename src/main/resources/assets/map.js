document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([22.99, 120.21], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var actualLayer = L.layerGroup().addTo(map);
    var predictedLayer = L.layerGroup().addTo(map);

    var datePicker = document.getElementById('date-picker');
    var actualCheckbox = document.getElementById('actual-layer-checkbox');
    var predictedCheckbox = document.getElementById('predicted-layer-checkbox');

    var data = [];

    fetch('/data')
        .then(response => response.json())
        .then(fetchedData => {
            data = fetchedData;
            // Set date picker to the first date in the data
            if (data.length > 0) {
                datePicker.value = data[0].date.split('T')[0];
                updateLayers();
            }
        });

    datePicker.addEventListener('change', updateLayers);
    actualCheckbox.addEventListener('change', updateLayers);
    predictedCheckbox.addEventListener('change', updateLayers);

    function updateLayers() {
        actualLayer.clearLayers();
        predictedLayer.clearLayers();

        var selectedDate = datePicker.value;

        var filteredData = data.filter(function (item) {
            return item.date.split('T')[0] === selectedDate;
        });

        if (actualCheckbox.checked) {
            filteredData.forEach(function (item) {
                if (item.case_lag_future_14 > 0) {
                    L.circle([item.latitude, item.longitude], {
                        color: 'red',
                        fillColor: '#f03',
                        fillOpacity: 0.5,
                        radius: item.case_lag_future_14 * 100
                    }).addTo(actualLayer);
                }
            });
        }

        if (predictedCheckbox.checked) {
            filteredData.forEach(function (item) {
                if (item.predicted_case_lag_future_14_binary > 0) {
                    L.circle([item.latitude, item.longitude], {
                        color: 'blue',
                        fillColor: '#30f',
                        fillOpacity: 0.5,
                        radius: 50
                    }).addTo(predictedLayer);
                }
            });
        }
    }
});