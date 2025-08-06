document.addEventListener('DOMContentLoaded', function () {
    // Initialize map centered on Tainan
    var map = L.map('map').setView([22.99, 120.21], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var geoJsonLayer = L.geoJson().addTo(map);
    var availableDates = [];
    var currentDateIndex = 0;
    var isPlaying = false;
    var playInterval;
    
    // Timeline controls
    var timelineSlider = document.getElementById('timeline-slider');
    var playPauseBtn = document.getElementById('play-pause');
    var currentDateSpan = document.getElementById('current-date');
    var statsPanel = document.getElementById('stats-panel');

    // Polygon styling function
    function getPolygonStyle(feature) {
        const actualCase = feature.properties.case_lag_future_14;
        const predictedBinary = feature.properties.predicted_case_lag_future_14_binary;
        const predictedPercentage = feature.properties.predicted_case_lag_future_14_percentage || 0;
        
        return {
            fillColor: predictedBinary === 1 ? 'lightblue' : 'white',
            fillOpacity: predictedBinary === 1 ? 0.6 : 0.1,
            color: actualCase === 1 ? 'red' : '#666',
            weight: actualCase === 1 ? 3 : 1,
            opacity: 0.8
        };
    }

    // Popup content function
    function getPopupContent(feature) {
        const props = feature.properties;
        const actualCase = props.case_lag_future_14;
        const predictedBinary = props.predicted_case_lag_future_14_binary;
        const predictedValue = props.predicted_case_lag_future_14 || 0;
        const predictedPercentage = props.predicted_case_lag_future_14_percentage || 0;
        
        return `
            <div class="popup-content">
                <h3>${props.town || 'Unknown Area'}</h3>
                <p><strong>Region ID:</strong> ${props.townvill}</p>
                <p><strong>Date:</strong> ${props.date}</p>
                <hr>
                <p><strong>Actual Cases:</strong> ${actualCase} ${actualCase === 1 ? '🔴' : '✅'}</p>
                <p><strong>Predicted Binary:</strong> ${predictedBinary} ${predictedBinary === 1 ? '🔵' : '✅'}</p>
                <p><strong>Prediction Value:</strong> ${predictedValue.toFixed(4)}</p>
                <p><strong>Risk Percentage:</strong> ${predictedPercentage.toFixed(2)}%</p>
            </div>
        `;
    }

    // Update statistics panel
    function updateStats(geoJsonData) {
        if (!statsPanel || !geoJsonData.features) return;
        
        const features = geoJsonData.features;
        const totalRegions = features.length;
        const actualCases = features.filter(f => f.properties.case_lag_future_14 === 1).length;
        const predictedCases = features.filter(f => f.properties.predicted_case_lag_future_14_binary === 1).length;
        const highRisk = features.filter(f => (f.properties.predicted_case_lag_future_14_percentage || 0) >= 50).length;
        const mediumRisk = features.filter(f => {
            const pct = f.properties.predicted_case_lag_future_14_percentage || 0;
            return pct >= 20 && pct < 50;
        }).length;
        
        statsPanel.innerHTML = `
            <h4>Statistics</h4>
            <div class="stat-item">
                <span class="stat-label">Total Regions:</span>
                <span class="stat-value">${totalRegions}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Actual Cases:</span>
                <span class="stat-value actual-cases">${actualCases}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Predicted Cases:</span>
                <span class="stat-value predicted-cases">${predictedCases}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">High Risk (≥50%):</span>
                <span class="stat-value high-risk">${highRisk}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Medium Risk (20-50%):</span>
                <span class="stat-value medium-risk">${mediumRisk}</span>
            </div>
        `;
    }

    // Load data for specific date
    function loadDataForDate(date) {
        fetch(`/api/data?date=${date}`)
            .then(response => response.json())
            .then(geoJsonData => {
                geoJsonLayer.clearLayers();
                
                // Apply styling and popups to each feature
                const styledGeoJson = L.geoJson(geoJsonData, {
                    style: getPolygonStyle,
                    onEachFeature: function(feature, layer) {
                        layer.bindPopup(getPopupContent(feature));
                    }
                });
                
                geoJsonLayer.addLayer(styledGeoJson);
                updateStats(geoJsonData);
                currentDateSpan.textContent = date;
            })
            .catch(error => {
                console.error('Error loading data:', error);
                currentDateSpan.textContent = `Error loading ${date}`;
            });
    }

    // Timeline controls
    function playTimeline() {
        if (isPlaying) return;
        
        isPlaying = true;
        playPauseBtn.textContent = '⏸️';
        
        playInterval = setInterval(function() {
            if (currentDateIndex < availableDates.length - 1) {
                currentDateIndex++;
                timelineSlider.value = currentDateIndex;
                loadDataForDate(availableDates[currentDateIndex]);
            } else {
                pauseTimeline();
            }
        }, 1000); // Change date every second
    }

    function pauseTimeline() {
        isPlaying = false;
        playPauseBtn.textContent = '▶️';
        if (playInterval) {
            clearInterval(playInterval);
        }
    }

    // Initialize application
    fetch('/api/dates')
        .then(response => response.json())
        .then(dates => {
            availableDates = dates;
            
            // Set up timeline slider
            timelineSlider.max = dates.length - 1;
            timelineSlider.value = 0;
            
            // Timeline slider event
            timelineSlider.addEventListener('input', function() {
                currentDateIndex = parseInt(this.value);
                loadDataForDate(availableDates[currentDateIndex]);
                
                // Pause if playing
                if (isPlaying) {
                    pauseTimeline();
                }
            });
            
            // Play/pause button event
            playPauseBtn.addEventListener('click', function() {
                if (isPlaying) {
                    pauseTimeline();
                } else {
                    playTimeline();
                }
            });
            
            // Load first date
            if (dates.length > 0) {
                loadDataForDate(dates[0]);
            }
        })
        .catch(error => {
            console.error('Error loading dates:', error);
        });
});