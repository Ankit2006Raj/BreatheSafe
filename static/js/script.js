// Global variables
let currentAQI = 0;
let socket;
let realtimeChart;
let chartData = {
    labels: [],
    datasets: [{
        label: 'AQI',
        data: [],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        tension: 0.4,
        fill: true
    }]
};
let map;
let markers = [];

// Input parameters
const parameters = ['pm25', 'pm10', 'no2', 'o3', 'co', 'temperature', 'humidity', 'wind_speed'];

// Presets
const presets = {
    clean: { pm25: 15, pm10: 25, no2: 10, o3: 30, co: 0.3, temperature: 22, humidity: 50, wind_speed: 5 },
    moderate: { pm25: 60, pm10: 90, no2: 35, o3: 70, co: 1.0, temperature: 28, humidity: 60, wind_speed: 2 },
    polluted: { pm25: 180, pm10: 280, no2: 85, o3: 130, co: 3.5, temperature: 35, humidity: 70, wind_speed: 0.5 },
    random: null
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeSliders();
    initializeWebSocket();
    initializeChart();
    initializeMap();
    loadStatistics();
    setupDarkMode();
    createParticles();
    setupAlertForm();
    checkPWAInstall();
});

// Initialize WebSocket connection
function initializeWebSocket() {
    socket = io();

    socket.on('connect', function () {
        console.log('WebSocket connected');
        showConnectionStatus('connected');
        socket.emit('request_realtime_data', { location: 'New York', lat: 40.7128, lon: -74.0060 });
    });

    socket.on('disconnect', function () {
        console.log('WebSocket disconnected');
        showConnectionStatus('disconnected');
    });

    socket.on('realtime_update', function (data) {
        console.log('Real-time update received:', data);
        updateRealtimeDisplay(data);
    });

    socket.on('global_update', function (data) {
        console.log('Global update received:', data);
        updateHeroAQI(data.aqi);
        addChartData(data);

        // Update real-time cards with global data
        if (data.pm25) animateValue('realtimePM25', data.pm25);
        if (data.pm10) animateValue('realtimePM10', data.pm10);
        if (data.temperature) animateValue('realtimeTemp', data.temperature);
        if (data.humidity) animateValue('realtimeHumidity', data.humidity);

        // Update floating cards in hero
        const floatPM25 = document.getElementById('floatPM25');
        const floatTemp = document.getElementById('floatTemp');
        const floatHumidity = document.getElementById('floatHumidity');

        if (floatPM25 && data.pm25) floatPM25.textContent = data.pm25;
        if (floatTemp && data.temperature) floatTemp.textContent = data.temperature + '°C';
        if (floatHumidity && data.humidity) floatHumidity.textContent = data.humidity + '%';

        // Update data source indicator
        updateDataSourceIndicator(data.source);
    });

    // Request updates every 5 seconds
    setInterval(() => {
        if (socket.connected) {
            socket.emit('request_realtime_data', { location: 'New York', lat: 40.7128, lon: -74.0060 });
        }
    }, 5000);
}

// Show connection status
function showConnectionStatus(status) {
    let existingStatus = document.querySelector('.connection-status');
    if (existingStatus) {
        existingStatus.remove();
    }

    const statusDiv = document.createElement('div');
    statusDiv.className = `connection-status ${status}`;

    const icon = status === 'connected' ? 'bi-wifi' : 'bi-wifi-off';
    const text = status === 'connected' ? 'Connected' : 'Disconnected';

    statusDiv.innerHTML = `<i class="bi ${icon}"></i> ${text}`;
    document.body.appendChild(statusDiv);

    setTimeout(() => {
        statusDiv.style.opacity = '0';
        statusDiv.style.transition = 'opacity 0.5s';
        setTimeout(() => statusDiv.remove(), 500);
    }, 3000);
}

// Update real-time display
function updateRealtimeDisplay(data) {
    animateValue('realtimePM25', data.pm25);
    animateValue('realtimePM10', data.pm10);
    animateValue('realtimeTemp', data.temperature);
    animateValue('realtimeHumidity', data.humidity);

    // Update data source indicator
    updateDataSourceIndicator(data.source);
}

// Update data source indicator
function updateDataSourceIndicator(source) {
    const badge = document.getElementById('dataSourceBadge');
    const text = document.getElementById('dataSourceText');

    if (badge && text) {
        if (source === 'OpenWeatherMap' || source === 'AQICN' || source === 'API') {
            text.textContent = 'LIVE API';
            badge.style.background = 'rgba(16, 185, 129, 0.1)';
            badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            badge.style.color = '#10b981';
        } else {
            text.textContent = 'LIVE';
            badge.style.background = 'rgba(239, 68, 68, 0.1)';
            badge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            badge.style.color = '#ef4444';
        }
    }
}

// Update hero AQI
function updateHeroAQI(aqi) {
    const heroAQI = document.getElementById('heroAQI');
    if (heroAQI) {
        animateValue('heroAQI', Math.round(aqi));
        heroAQI.style.color = getAQIColor(aqi);
    }
}

// Get AQI color
function getAQIColor(aqi) {
    if (aqi <= 50) return '#10b981';
    if (aqi <= 100) return '#f59e0b';
    if (aqi <= 200) return '#f97316';
    if (aqi <= 300) return '#ef4444';
    return '#7c3aed';
}

// Initialize Chart.js
function initializeChart() {
    const ctx = document.getElementById('realtimeChart');
    if (!ctx) return;

    realtimeChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    borderRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 300,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    // Load initial historical data
    loadHistoricalData(24);
}

// Load historical data
async function loadHistoricalData(hours) {
    try {
        const response = await fetch(`/api/historical/${hours}`);
        const result = await response.json();

        chartData.labels = [];
        chartData.datasets[0].data = [];

        result.data.forEach(item => {
            const time = new Date(item.timestamp).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
            chartData.labels.push(time);
            chartData.datasets[0].data.push(item.aqi);
        });

        if (realtimeChart) {
            realtimeChart.update();
        }
    } catch (error) {
        console.error('Error loading historical data:', error);
    }
}

// Add data to chart
function addChartData(data) {
    const time = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    chartData.labels.push(time);
    chartData.datasets[0].data.push(data.aqi);

    // Keep only last 50 data points
    if (chartData.labels.length > 50) {
        chartData.labels.shift();
        chartData.datasets[0].data.shift();
    }

    if (realtimeChart) {
        realtimeChart.update('none'); // Update without animation for smooth real-time
    }
}

// Set chart range
function setChartRange(hours) {
    loadHistoricalData(hours);

    // Update active button
    document.querySelectorAll('.btn-group button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Initialize Leaflet Map
function initializeMap() {
    const mapElement = document.getElementById('airQualityMap');
    if (!mapElement) return;

    map = L.map('airQualityMap').setView([20, 0], 2);

    // Modern dark theme map
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Load initial locations
    loadMapLocations();

    // Map Click Event
    map.on('click', async function(e) {
        fetchAndDisplayLocationData(e.latlng.lat, e.latlng.lng, "Selected Location");
    });

    // Search functionality
    const searchBtn = document.getElementById('mapSearchBtn');
    const searchInput = document.getElementById('mapSearchInput');
    
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => searchLocation(searchInput.value));
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchLocation(searchInput.value);
        });
    }

    // Locate Me functionality
    const locateBtn = document.getElementById('locateMeBtn');
    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            if (navigator.geolocation) {
                const icon = locateBtn.querySelector('i');
                icon.className = 'spinner-border spinner-border-sm text-primary';
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        icon.className = 'bi bi-geo-alt-fill text-primary';
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        fetchAndDisplayLocationData(lat, lng, "Your Location");
                    },
                    (error) => {
                        icon.className = 'bi bi-geo-alt-fill text-primary';
                        showNotification('Geolocation failed or denied', 'warning');
                    }
                );
            } else {
                showNotification('Geolocation is not supported by this browser', 'warning');
            }
        });
    }
}

async function searchLocation(city) {
    if (!city) return;
    const btn = document.getElementById('mapSearchBtn');
    if(btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
        try {
            const geoResponse = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}`);
            const geoData = await geoResponse.json();
            
            if (geoData && geoData.length > 0) {
                const lat = parseFloat(geoData[0].lat);
                const lng = parseFloat(geoData[0].lon);
                const displayName = geoData[0].display_name.split(',')[0];
                
                fetchAndDisplayLocationData(lat, lng, displayName);
            } else {
                showNotification('City not found', 'warning');
            }
        } catch (error) {
            showNotification('Error searching location', 'danger');
        } finally {
            btn.innerHTML = originalText;
        }
    }
}

async function fetchAndDisplayLocationData(lat, lng, locationName) {
    try {
        const response = await fetch(`/api/air-quality/coordinates?lat=${lat}&lon=${lng}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            const aqi = data.aqi;
            const color = getAQIColor(aqi);
            
            // Fly to location
            map.flyTo([lat, lng], 10, { duration: 1.5 });
            
            // Add marker
            const marker = L.circleMarker([lat, lng], {
                radius: 12,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);
            
            marker.bindPopup(`
                <div class="map-popup">
                    <div class="map-popup-location">${locationName}</div>
                    <div class="map-popup-aqi" style="color: ${color}">${aqi}</div>
                    <div class="text-muted">AQI</div>
                    <div class="map-popup-details">
                        <span><i class="bi bi-thermometer-half"></i> ${data.temperature || '--'}°C</span>
                        <span><i class="bi bi-droplet"></i> ${data.humidity || '--'}%</span>
                    </div>
                </div>
            `).openPopup();
            
            markers.push(marker);
        } else {
            showNotification('Air quality data unavailable for this location', 'warning');
        }
    } catch (error) {
        console.error('Error fetching location data:', error);
        showNotification('Error fetching air quality data', 'danger');
    }
}

// Load map locations
async function loadMapLocations() {
    try {
        const response = await fetch('/api/locations');
        const result = await response.json();

        result.locations.forEach(location => {
            const color = getAQIColor(location.aqi);

            const marker = L.circleMarker([location.lat, location.lng], {
                radius: 12,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            marker.bindPopup(`
                <div class="map-popup">
                    <div class="map-popup-location">${location.name}</div>
                    <div class="map-popup-aqi" style="color: ${color}">${location.aqi}</div>
                    <div class="text-muted">AQI</div>
                </div>
            `);

            markers.push(marker);
        });
    } catch (error) {
        console.error('Error loading map locations:', error);
    }
}

// Initialize sliders
function initializeSliders() {
    parameters.forEach(param => {
        const slider = document.getElementById(param);
        const input = document.getElementById(param + 'Input');

        if (slider && input) {
            slider.addEventListener('input', function () {
                input.value = this.value;
            });

            input.addEventListener('input', function () {
                const value = parseFloat(this.value);
                const min = parseFloat(this.min);
                const max = parseFloat(this.max);

                if (value >= min && value <= max) {
                    slider.value = value;
                }
            });
        }
    });
}

// Load preset scenarios
function loadPreset(type) {
    if (type === 'random') {
        parameters.forEach(param => {
            const slider = document.getElementById(param);
            const input = document.getElementById(param + 'Input');
            const min = parseFloat(slider.min);
            const max = parseFloat(slider.max);
            const step = parseFloat(slider.step) || 1;

            const randomValue = Math.random() * (max - min) + min;
            const roundedValue = Math.round(randomValue / step) * step;

            slider.value = roundedValue;
            input.value = roundedValue;
        });
    } else if (presets[type]) {
        Object.keys(presets[type]).forEach(param => {
            const slider = document.getElementById(param);
            const input = document.getElementById(param + 'Input');

            if (slider && input) {
                slider.value = presets[type][param];
                input.value = presets[type][param];
            }
        });
    }

    showNotification(`Loaded ${type} scenario`, 'success');
}

// Handle form submission
document.getElementById('aqiForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('resultContent').classList.add('d-none');
    document.getElementById('predictionResult').classList.add('d-none');

    const formData = {};
    parameters.forEach(param => {
        formData[param] = parseFloat(document.getElementById(param).value);
    });

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            displayPrediction(result);
        } else {
            showNotification('Error: ' + result.error, 'danger');
        }
    } catch (error) {
        showNotification('Error making prediction: ' + error.message, 'danger');
    } finally {
        document.getElementById('loadingSpinner').classList.add('d-none');
    }
});

// Display prediction results
function displayPrediction(result) {
    currentAQI = result.aqi;

    document.getElementById('resultContent').classList.add('d-none');
    const predictionDiv = document.getElementById('predictionResult');
    predictionDiv.classList.remove('d-none');

    const aqiValueElement = document.getElementById('aqiValue');
    aqiValueElement.style.color = result.color;
    animateValue('aqiValue', result.aqi, 0, 1500);

    const iconElement = document.getElementById('categoryIcon');
    iconElement.className = result.icon + ' display-4';
    iconElement.style.color = result.color;

    const categoryElement = document.getElementById('categoryName');
    categoryElement.textContent = result.category;
    categoryElement.style.color = result.color;

    const adviceBox = document.getElementById('adviceBox');
    adviceBox.className = 'alert alert-' + result.level;
    document.getElementById('adviceText').textContent = result.advice;

    updateAQIMarker(result.aqi);

    if (result.aqi <= 50) {
        createConfetti();
    }

    predictionDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Animate number counting
function animateValue(elementId, end, start = 0, duration = 1500) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }

        if (elementId.includes('realtime')) {
            element.textContent = Math.round(current * 10) / 10;
            element.classList.add('updating');
            setTimeout(() => element.classList.remove('updating'), 500);
        } else {
            element.textContent = Math.round(current);
        }
    }, 16);
}

// Update AQI marker position
function updateAQIMarker(aqi) {
    const marker = document.getElementById('aqiMarker');
    if (!marker) return;

    const maxAQI = 500;
    const percentage = Math.min((aqi / maxAQI) * 100, 100);
    marker.style.left = percentage + '%';
}

// Create confetti effect
function createConfetti() {
    const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];
    const confettiCount = 80;

    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.width = Math.random() * 10 + 5 + 'px';
            confetti.style.height = confetti.style.width;
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * window.innerWidth + 'px';
            confetti.style.top = '-20px';
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            confetti.style.transition = 'all 3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';

            document.body.appendChild(confetti);

            setTimeout(() => {
                confetti.style.top = window.innerHeight + 100 + 'px';
                confetti.style.transform = `rotate(${Math.random() * 720}deg)`;
                confetti.style.opacity = '0';
            }, 10);

            setTimeout(() => confetti.remove(), 3000);
        }, i * 20);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();

        document.getElementById('modelAccuracy').textContent = stats.model_metrics.accuracy + '%';
        if (document.getElementById('subtitleAccuracy')) {
            document.getElementById('subtitleAccuracy').textContent = stats.model_metrics.accuracy + '%';
        }
        if (document.getElementById('footerAccuracy')) {
            document.getElementById('footerAccuracy').textContent = stats.model_metrics.accuracy + '%';
        }
        displayStatsCards(stats);
        displayFeatureImportance(stats.feature_importance);
        displayAQIDistribution(stats.aqi_distribution);

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Display stats cards
function displayStatsCards(stats) {
    const container = document.getElementById('statsCards');
    container.innerHTML = `
        <div class="col-md-3 mb-4">
            <div class="stats-card">
                <i class="bi bi-database display-4 text-primary"></i>
                <h3>${stats.total_records.toLocaleString()}</h3>
                <p class="text-muted mb-0">Training Records</p>
            </div>
        </div>
        <div class="col-md-3 mb-4">
            <div class="stats-card">
                <i class="bi bi-graph-up display-4 text-success"></i>
                <h3>${stats.avg_aqi}</h3>
                <p class="text-muted mb-0">Average AQI</p>
            </div>
        </div>
        <div class="col-md-3 mb-4">
            <div class="stats-card">
                <i class="bi bi-bullseye display-4 text-info"></i>
                <h3>${stats.model_metrics.accuracy}%</h3>
                <p class="text-muted mb-0">Model Accuracy</p>
            </div>
        </div>
        <div class="col-md-3 mb-4">
            <div class="stats-card">
                <i class="bi bi-speedometer2 display-4 text-warning"></i>
                <h3>${stats.model_metrics.r2_score}</h3>
                <p class="text-muted mb-0">R² Score</p>
            </div>
        </div>
    `;
}

// Display feature importance
function displayFeatureImportance(importance) {
    const container = document.getElementById('featureImportanceChart');
    const sortedFeatures = Object.entries(importance).sort((a, b) => b[1] - a[1]);
    const maxImportance = Math.max(...Object.values(importance));

    let html = '';
    sortedFeatures.forEach(([feature, value]) => {
        const percentage = (value / maxImportance) * 100;
        const displayName = feature.toUpperCase().replace('_', ' ');
        const displayValue = (value * 100).toFixed(1);

        html += `
            <div class="feature-bar-container">
                <div class="feature-bar-label">
                    <span>${displayName}</span>
                    <span class="text-primary fw-bold">${displayValue}%</span>
                </div>
                <div class="feature-bar-bg">
                    <div class="feature-bar-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Display AQI distribution
function displayAQIDistribution(distribution) {
    const container = document.getElementById('aqiDistributionChart');
    const categories = [
        { key: 'good', label: 'Good', color: '#10b981' },
        { key: 'moderate', label: 'Moderate', color: '#f59e0b' },
        { key: 'unhealthy_sensitive', label: 'Unhealthy (Sensitive)', color: '#f97316' },
        { key: 'unhealthy', label: 'Unhealthy', color: '#ef4444' },
        { key: 'hazardous', label: 'Hazardous', color: '#7c3aed' }
    ];

    let html = '';
    categories.forEach(cat => {
        const count = distribution[cat.key] || 0;
        html += `
            <div class="distribution-item">
                <div class="distribution-color" style="background: ${cat.color}"></div>
                <div class="distribution-info">
                    <div class="distribution-label">${cat.label}</div>
                    <div class="distribution-count">${count.toLocaleString()}</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Show detailed recommendations
async function showDetailedRecommendations() {
    const modal = new bootstrap.Modal(document.getElementById('recommendationsModal'));
    const content = document.getElementById('recommendationsContent');

    content.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
    modal.show();

    try {
        const response = await fetch(`/api/recommendations/${Math.round(currentAQI)}`);
        const data = await response.json();

        let html = '';

        if (data.general && data.general.length > 0) {
            html += `
                <div class="recommendation-section">
                    <h6><i class="bi bi-info-circle me-2"></i>General Information</h6>
                    <ul class="recommendation-list">
                        ${data.general.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (data.sensitive_groups && data.sensitive_groups.length > 0) {
            html += `
                <div class="recommendation-section">
                    <h6><i class="bi bi-heart-pulse me-2"></i>Sensitive Groups</h6>
                    <ul class="recommendation-list">
                        ${data.sensitive_groups.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (data.outdoor_activities) {
            html += `
                <div class="recommendation-section">
                    <h6><i class="bi bi-bicycle me-2"></i>Outdoor Activities</h6>
                    <div class="alert alert-info">${data.outdoor_activities}</div>
                </div>
            `;
        }

        if (data.protective_measures && data.protective_measures.length > 0) {
            html += `
                <div class="recommendation-section">
                    <h6><i class="bi bi-shield-check me-2"></i>Protective Measures</h6>
                    <ul class="recommendation-list">
                        ${data.protective_measures.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        content.innerHTML = html;

    } catch (error) {
        content.innerHTML = '<div class="alert alert-danger">Failed to load recommendations</div>';
    }
}

// Save result
function saveResult() {
    const result = {
        timestamp: new Date().toISOString(),
        aqi: currentAQI,
        parameters: {}
    };

    parameters.forEach(param => {
        result.parameters[param] = parseFloat(document.getElementById(param).value);
    });

    // Save to localStorage
    let savedResults = JSON.parse(localStorage.getItem('aqiResults') || '[]');
    savedResults.push(result);
    localStorage.setItem('aqiResults', JSON.stringify(savedResults));

    showNotification('Result saved successfully!', 'success');
}

// Export data
async function exportData(format) {
    try {
        const response = await fetch(`/api/export/${format}`);

        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'aqi_data.csv';
            a.click();
        } else if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'aqi_data.json';
            a.click();
        }

        showNotification(`Data exported as ${format.toUpperCase()}`, 'success');
    } catch (error) {
        showNotification('Export failed: ' + error.message, 'danger');
    }
}

// Generate report
function generateReport() {
    showNotification('Report generation feature coming soon!', 'info');
}

// Setup alert form
function setupAlertForm() {
    const form = document.getElementById('alertForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const threshold = document.getElementById('alertThreshold').value;
        const email = document.getElementById('alertEmail').value;

        try {
            const response = await fetch('/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ threshold, email })
            });

            const result = await response.json();

            if (result.success) {
                showNotification('Alert set successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('alertModal')).hide();
            }
        } catch (error) {
            showNotification('Failed to set alert', 'danger');
        }
    });
}

// Setup dark mode
function setupDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    const savedMode = localStorage.getItem('darkMode');

    if (savedMode === 'enabled') {
        document.body.classList.add('dark-mode');
        toggle.querySelector('i').classList.replace('bi-moon-stars', 'bi-sun');
    }

    toggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const icon = this.querySelector('i');

        if (document.body.classList.contains('dark-mode')) {
            icon.classList.replace('bi-moon-stars', 'bi-sun');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            icon.classList.replace('bi-sun', 'bi-moon-stars');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
}

// Create particles
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        container.appendChild(particle);
    }
}

// Check PWA install
function checkPWAInstall() {
    let deferredPrompt;

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;

        const installPrompt = document.createElement('div');
        installPrompt.className = 'pwa-install-prompt';
        installPrompt.innerHTML = `
            <div class="d-flex align-items-center gap-3">
                <div>
                    <strong>Install BreatheSafe AI</strong>
                    <p class="mb-0 small">Get quick access and offline support</p>
                </div>
                <button class="btn btn-light btn-sm" id="installBtn">Install</button>
                <button class="btn btn-link text-white btn-sm" id="dismissBtn">×</button>
            </div>
        `;

        document.body.appendChild(installPrompt);

        document.getElementById('installBtn').addEventListener('click', async () => {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response: ${outcome}`);
            installPrompt.remove();
        });

        document.getElementById('dismissBtn').addEventListener('click', () => {
            installPrompt.remove();
        });
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `toast-notification ${type}`;
    notification.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'x-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offset = 80;
            const targetPosition = target.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Parallax effect
window.addEventListener('scroll', function () {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero-section');
    if (hero && scrolled < window.innerHeight) {
        hero.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});


// Share result function
function shareResult() {
    if (navigator.share) {
        navigator.share({
            title: 'BreatheSafe AI - AQI Prediction',
            text: `Current AQI: ${currentAQI}. Check air quality with BreatheSafe AI!`,
            url: window.location.href
        }).then(() => {
            showNotification('Shared successfully!', 'success');
        }).catch(() => {
            copyToClipboard();
        });
    } else {
        copyToClipboard();
    }
}

// Copy to clipboard
function copyToClipboard() {
    const text = `Current AQI: ${currentAQI} - Check it out at ${window.location.href}`;
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Link copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy link', 'danger');
    });
}


// Newsletter subscription
function subscribeNewsletter(event) {
    event.preventDefault();
    const email = event.target.querySelector('input[type="email"]').value;

    // Simulate subscription
    showNotification('Thanks for subscribing! 🎉', 'success');
    event.target.reset();
}

// Back to top functionality
window.addEventListener('scroll', function () {
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        if (window.pageYOffset > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    }
});

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}


// Setup theme toggle (Dark/Light Mode)
function setupThemeToggle() {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;

    const savedMode = localStorage.getItem('themeMode');

    // Apply saved theme or default to dark
    if (savedMode === 'light') {
        document.body.classList.add('light-mode');
        toggle.querySelector('i').classList.replace('bi-moon-stars', 'bi-sun-fill');
    }

    toggle.addEventListener('click', function () {
        document.body.classList.toggle('light-mode');
        const icon = this.querySelector('i');

        if (document.body.classList.contains('light-mode')) {
            // Switch to light mode
            icon.classList.replace('bi-moon-stars', 'bi-sun-fill');
            localStorage.setItem('themeMode', 'light');
            showNotification('Light mode activated ☀️', 'info');
        } else {
            // Switch to dark mode
            icon.classList.replace('bi-sun-fill', 'bi-moon-stars');
            localStorage.setItem('themeMode', 'dark');
            showNotification('Dark mode activated 🌙', 'info');
        }
    });
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function () {
    setupThemeToggle();
});


// ========================================
// GEMINI AI FEATURES
// ========================================

// Show AI-powered insights
async function showAIInsights() {
    const modal = new bootstrap.Modal(document.getElementById('aiInsightsModal') || createAIModal());
    const content = document.getElementById('aiInsightsContent');

    if (!content) return;

    content.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p class="mt-3">Generating AI insights...</p></div>';
    modal.show();

    try {
        const response = await fetch('/api/ai/health-recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                aqi: currentAQI,
                pm25: parseFloat(document.getElementById('pm25').value),
                location: 'your area'
            })
        });

        const result = await response.json();

        if (result.success && result.recommendations) {
            displayAIRecommendations(result.recommendations);
        } else {
            content.innerHTML = '<div class="alert alert-warning">AI insights not available. Please configure Gemini API key.</div>';
        }
    } catch (error) {
        content.innerHTML = '<div class="alert alert-danger">Failed to load AI insights</div>';
    }
}

// Display AI recommendations
function displayAIRecommendations(recommendations) {
    const content = document.getElementById('aiInsightsContent');

    let html = '';

    // Assessment
    if (recommendations.assessment) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-clipboard-pulse me-2"></i>Health Impact Assessment</h6>
                <p class="ai-text">${recommendations.assessment}</p>
            </div>
        `;
    }

    // General Population
    if (recommendations.general_population && recommendations.general_population.length > 0) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-people me-2"></i>For General Population</h6>
                <ul class="ai-list">
                    ${recommendations.general_population.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Sensitive Groups
    if (recommendations.sensitive_groups && recommendations.sensitive_groups.length > 0) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-heart-pulse me-2"></i>For Sensitive Groups</h6>
                <ul class="ai-list">
                    ${recommendations.sensitive_groups.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Outdoor Activities
    if (recommendations.outdoor_activities) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-bicycle me-2"></i>Outdoor Activities</h6>
                <p class="ai-text">${recommendations.outdoor_activities}</p>
            </div>
        `;
    }

    // Indoor Tips
    if (recommendations.indoor_tips && recommendations.indoor_tips.length > 0) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-house me-2"></i>Indoor Air Quality Tips</h6>
                <ul class="ai-list">
                    ${recommendations.indoor_tips.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Protective Measures
    if (recommendations.protective_measures && recommendations.protective_measures.length > 0) {
        html += `
            <div class="ai-section">
                <h6><i class="bi bi-shield-check me-2"></i>Protective Measures</h6>
                <ul class="ai-list">
                    ${recommendations.protective_measures.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Medical Attention
    if (recommendations.medical_attention) {
        html += `
            <div class="ai-section alert alert-info">
                <h6><i class="bi bi-hospital me-2"></i>When to Seek Medical Attention</h6>
                <p class="mb-0">${recommendations.medical_attention}</p>
            </div>
        `;
    }

    // Source
    html += `
        <div class="text-center mt-3">
            <small class="text-muted">
                <i class="bi bi-stars"></i> Powered by ${recommendations.source || 'AI'}
            </small>
        </div>
    `;

    content.innerHTML = html;
}

// Create AI modal if it doesn't exist
function createAIModal() {
    const modalHTML = `
        <div class="modal fade" id="aiInsightsModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content modal-modern">
                    <div class="modal-header-modern">
                        <h5><i class="bi bi-stars me-2"></i>AI-Powered Insights</h5>
                        <button type="button" class="btn-close-modern" data-bs-dismiss="modal">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                    <div class="modal-body-modern" id="aiInsightsContent">
                        <div class="text-center">
                            <div class="spinner-border text-primary"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    return document.getElementById('aiInsightsModal');
}

// Get simple AI explanation
async function getSimpleExplanation(aqi, pm25) {
    try {
        const response = await fetch('/api/ai/explain-simple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aqi, pm25 })
        });

        const result = await response.json();

        if (result.success) {
            return result.explanation;
        }
    } catch (error) {
        console.error('Error getting simple explanation:', error);
    }

    return null;
}

// Check if Gemini AI is configured
async function checkAIStatus() {
    try {
        const response = await fetch('/api/check-api-status');
        const status = await response.json();

        if (status.gemini_configured) {
            // Show AI features
            document.querySelectorAll('.ai-feature').forEach(el => {
                el.style.display = 'block';
            });
        }
    } catch (error) {
        console.error('Error checking AI status:', error);
    }
}

// Initialize AI features on page load
document.addEventListener('DOMContentLoaded', function () {
    checkAIStatus();
});
