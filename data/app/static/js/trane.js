// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refresh-btn');
    const lastUpdated = document.getElementById('last-updated');
    const currentTemp = document.getElementById('current-temp');
    const outdoorTemp = document.getElementById('outdoor-temp');
    const outdoorHumidity = document.getElementById('outdoor-humidity');
    const tempDifference = document.getElementById('temp-difference');
    const systemMode = document.getElementById('system-mode');
    const heatSetpoint = document.getElementById('heat-setpoint');
    const coolSetpoint = document.getElementById('cool-setpoint');
    const heatSetpointValue = document.getElementById('heat-setpoint-value');
    const coolSetpointValue = document.getElementById('cool-setpoint-value');
    const heatSetpointSlider = document.getElementById('heat-setpoint-slider');
    const coolSetpointSlider = document.getElementById('cool-setpoint-slider');
    const heatingDemand = document.getElementById('heating-demand');
    const coolingDemand = document.getElementById('cooling-demand');
    const heatingBar = document.getElementById('heating-bar');
    const coolingBar = document.getElementById('cooling-bar');
    const commStatus = document.getElementById('comm-status');
    const occupancyStatus = document.getElementById('occupancy-status');
    const diagnosticStatus = document.getElementById('diagnostic-status');
    const tempMarker = document.getElementById('temp-marker');
    const tempRange = document.getElementById('temp-range');
    const comfortModeSelect = document.getElementById('comfort-mode-select');
    const pointReaderForm = document.getElementById('point-reader-form');
    const pointResult = document.getElementById('point-result');
    
    // Tab Navigation
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show active tab content
            tabContents.forEach(content => {
                if (content.id === tabName) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
            
            // Initialize chart if history tab is selected
            if (tabName === 'history' && !window.tempChart) {
                initTempChart();
            }
        });
    });
    
    // Temperature Chart
    let tempChart;
    
    function initTempChart() {
        const ctx = document.getElementById('tempChart').getContext('2d');
        
        // Sample data - this would be replaced with actual API data
        const labels = Array.from({length: 24}, (_, i) => `${i}:00`);
        const indoorData = [72, 72.5, 73, 73.5, 74, 74.5, 74, 73.5, 73, 72.5, 72, 71.5, 71, 70.5, 70, 70.5, 71, 71.5, 72, 72.5, 73, 73.5, 73, 72.5];
        const outdoorData = [65, 64, 63, 62, 61, 60, 62, 65, 68, 72, 75, 78, 81, 83, 84, 85, 84, 82, 80, 77, 74, 71, 68, 66];
        
        tempChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Indoor Temperature',
                        data: indoorData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 2,
                        pointHoverRadius: 4
                    },
                    {
                        label: 'Outdoor Temperature',
                        data: outdoorData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 2,
                        pointHoverRadius: 4
                    }
                ]
            },
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
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw}°F`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        suggestedMin: 60,
                        suggestedMax: 90,
                        ticks: {
                            callback: function(value) {
                                return value + '°F';
                            }
                        }
                    }
                }
            }
        });
        
        window.tempChart = tempChart;
    }
    
    // Temperature Slider Controls
    heatSetpointSlider.addEventListener('input', function() {
        const value = parseFloat(this.value);
        const coolValue = parseFloat(coolSetpointSlider.value);
        
        // Ensure heat setpoint is at least 2 degrees below cool setpoint
        if (value > coolValue - 2) {
            this.value = coolValue - 2;
            return;
        }
        
        heatSetpointValue.textContent = `${value.toFixed(1)}°F`;
        heatSetpoint.textContent = `${value.toFixed(1)}°F`;
        updateTempRange();
    });
    
    coolSetpointSlider.addEventListener('input', function() {
        const value = parseFloat(this.value);
        const heatValue = parseFloat(heatSetpointSlider.value);
        
        // Ensure cool setpoint is at least 2 degrees above heat setpoint
        if (value < heatValue + 2) {
            this.value = heatValue + 2;
            return;
        }
        
        coolSetpointValue.textContent = `${value.toFixed(1)}°F`;
        coolSetpoint.textContent = `${value.toFixed(1)}°F`;
        updateTempRange();
    });
    
    // Apply setpoint buttons
    const applyHeatBtn = document.getElementById('apply-heat-btn');
    const applyCoolBtn = document.getElementById('apply-cool-btn');
    
    applyHeatBtn.addEventListener('click', function() {
        const value = parseFloat(heatSetpointSlider.value);
        setParameter('aV6_wJ8BLYdd', value);
    });
    
    applyCoolBtn.addEventListener('click', function() {
        const value = parseFloat(coolSetpointSlider.value);
        setParameter('aV6_wJ8BLYdc', value);
    });
    
    function updateTempRange() {
        const min = 60;
        const max = 90;
        const range = max - min;
        
        const heatValue = parseFloat(heatSetpointSlider.value);
        const coolValue = parseFloat(coolSetpointSlider.value);
        const currentValue = parseFloat(currentTemp.textContent.replace('°F', ''));
        
        // Calculate positions as percentages
        const heatPos = ((heatValue - min) / range) * 100;
        const coolPos = ((coolValue - min) / range) * 100;
        const currentPos = ((currentValue - min) / range) * 100;
        
        // Update visual elements
        tempRange.style.left = `${heatPos}%`;
        tempRange.style.right = `${100 - coolPos}%`;
        tempMarker.style.left = `${currentPos}%`;
    }
    
    // Comfort Mode Select
    comfortModeSelect.addEventListener('change', function() {
        const value = this.value.toLowerCase();
        
        // Send to API
        setParameter('aV6_wkNKKotN', value === 'comfort' ? 0 : 1);
    });
    
    // Point Reader Form
    pointReaderForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const pointType = document.getElementById('point-type').value;
        const pointId = document.getElementById('point-id').value;
        
        if (!pointId) {
            alert('Please enter a Point ID');
            return;
        }
        
        // Show loading state
        const resultPre = pointResult.querySelector('pre');
        resultPre.textContent = 'Loading...';
        pointResult.classList.remove('hidden');
        
        // Fetch point data from API
        fetch(`/ac/api/point?type=${pointType}&id=${pointId}`)
            .then(response => response.json())
            .then(data => {
                resultPre.textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => {
                resultPre.textContent = `Error: ${error.message}`;
            });
    });
    
    // API Functions
    function refreshData() {
        // Show loading state
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt animate-spin text-sm"></i><span>Updating...</span>';
        
        // Fetch data from API
        fetch('/ac/api/status')
            .then(response => response.json())
            .then(data => {
                updateUI(data);
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt text-sm"></i><span>Refresh</span>';
                
                // Update last updated time
                const now = new Date();
                const timeString = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
                lastUpdated.querySelector('span').textContent = timeString;
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt text-sm"></i><span>Refresh</span>';
            });
    }
    
    function updateUI(data) {
        // Update temperature values
        if (data['Space Temperature Active']) {
            const spaceTemp = parseFloat(data['Space Temperature Active'].value);
            currentTemp.textContent = data['Space Temperature Active'].displayValue;
            
            // Set color based on temperature
            if (spaceTemp < 68) {
                currentTemp.style.color = '#1d4ed8'; // Cooler blue
            } else if (spaceTemp > 76) {
                currentTemp.style.color = '#ef4444'; // Warmer red
            } else {
                currentTemp.style.color = '#60a5fa'; // Normal blue
            }
        }
        
        if (data['Outdoor Air Temperature']) {
            const outTemp = parseFloat(data['Outdoor Air Temperature'].value);
            outdoorTemp.textContent = data['Outdoor Air Temperature'].displayValue;
            
            // Set color based on temperature
            if (outTemp < 50) {
                outdoorTemp.style.color = '#1d4ed8'; // Cold blue
            } else if (outTemp > 80) {
                outdoorTemp.style.color = '#ef4444'; // Hot red
            } else {
                outdoorTemp.style.color = '#10b981'; // Mild green
            }
            
            // Calculate and display temperature difference
            if (data['Space Temperature Active']) {
                const spaceTemp = parseFloat(data['Space Temperature Active'].value);
                const diff = (spaceTemp - outTemp).toFixed(1);
                const sign = diff > 0 ? '+' : '';
                tempDifference.textContent = `${sign}${diff}°F`;
                
                // Set color based on difference
                if (diff > 0) {
                    tempDifference.style.color = '#ef4444'; // Warmer inside
                } else {
                    tempDifference.style.color = '#60a5fa'; // Cooler inside
                }
            }
        }
        
        if (data['Outdoor Humidity']) {
            outdoorHumidity.textContent = data['Outdoor Humidity'].displayValue.replace('%', '');
        }
        
        // Update setpoints
        if (data['Occupied Heat Setpoint']) {
            const heatValue = parseFloat(data['Occupied Heat Setpoint'].value);
            heatSetpoint.textContent = data['Occupied Heat Setpoint'].displayValue;
            heatSetpointValue.textContent = data['Occupied Heat Setpoint'].displayValue;
            heatSetpointSlider.value = heatValue;
        }
        
        if (data['Occupied Cool Setpoint']) {
            const coolValue = parseFloat(data['Occupied Cool Setpoint'].value);
            coolSetpoint.textContent = data['Occupied Cool Setpoint'].displayValue;
            coolSetpointValue.textContent = data['Occupied Cool Setpoint'].displayValue;
            coolSetpointSlider.value = coolValue;
        }
        
        // Update system mode
        if (data['Reversing Valve']) {
            const isCooling = data['Reversing Valve'].displayValue === 'Cooling';
            systemMode.className = isCooling ? 'status-badge status-cooling' : 'status-badge status-heating';
            systemMode.innerHTML = isCooling ? 
                '<i class="fas fa-snowflake"></i><span>Cooling</span>' : 
                '<i class="fas fa-sun"></i><span>Heating</span>';
        }
        
        // Update diagnostic status
        if (data['Diagnostic Present']) {
            const hasAlarm = data['Diagnostic Present'].displayValue === 'In Alarm';
            diagnosticStatus.className = hasAlarm ? 'status-badge status-danger' : 'status-badge status-normal';
            diagnosticStatus.innerHTML = hasAlarm ? 
                '<i class="fas fa-exclamation-triangle"></i><span>In Alarm</span>' : 
                '<i class="fas fa-check"></i><span>Normal</span>';
        }
        
        // Update communication status
        if (data['Communication Status']) {
            const commValue = data['Communication Status'].displayValue;
            if (commValue === 'Communicating') {
                commStatus.className = 'status-badge status-normal';
                commStatus.innerHTML = '<i class="fas fa-check"></i><span>Communicating</span>';
            } else if (commValue === 'Not Communicating') {
                commStatus.className = 'status-badge status-danger';
                commStatus.innerHTML = '<i class="fas fa-times"></i><span>Not Communicating</span>';
            } else {
                commStatus.className = 'status-badge status-warning';
                commStatus.innerHTML = `<i class="fas fa-exclamation"></i><span>${commValue}</span>`;
            }
        }
        
        // Update occupancy status
        if (data['Occupancy Status']) {
            const occValue = data['Occupancy Status'].displayValue;
            if (occValue === 'Occupied') {
                occupancyStatus.className = 'status-badge status-normal';
                occupancyStatus.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                occupancyStatus.style.color = '#3b82f6';
                occupancyStatus.innerHTML = '<i class="fas fa-user"></i><span>Occupied</span>';
            } else if (occValue === 'Unoccupied') {
                occupancyStatus.className = 'status-badge';
                occupancyStatus.style.backgroundColor = 'rgba(107, 114, 128, 0.1)';
                occupancyStatus.style.color = '#6b7280';
                occupancyStatus.innerHTML = '<i class="fas fa-user-slash"></i><span>Unoccupied</span>';
            } else {
                occupancyStatus.className = 'status-badge';
                occupancyStatus.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                occupancyStatus.style.color = '#3b82f6';
                occupancyStatus.innerHTML = `<i class="fas fa-clock"></i><span>${occValue}</span>`;
            }
        }
        
        // Update comfort mode
        if (data['Comfort Mode']) {
            const comfortMode = data['Comfort Mode'].displayValue;
            comfortModeSelect.value = comfortMode;
        }
        
        // Update heating/cooling demand
        if (data['PI Heating Demand']) {
            const heatDemand = parseFloat(data['PI Heating Demand'].value);
            heatingDemand.textContent = data['PI Heating Demand'].displayValue;
            heatingBar.style.width = `${heatDemand}%`;
        }
        
        if (data['PI Cooling Demand']) {
            const coolDemand = parseFloat(data['PI Cooling Demand'].value);
            coolingDemand.textContent = data['PI Cooling Demand'].displayValue;
            coolingBar.style.width = `${coolDemand}%`;
        }
        
        // Update temperature range visualization
        updateTempRange();
        
        // Update table values in diagnostics tab
        const paramValues = document.querySelectorAll('.param-value');
        paramValues.forEach(element => {
            const paramName = element.previousElementSibling.textContent.trim();
            
            // Match parameter name to data
            Object.entries(data).forEach(([key, value]) => {
                if (key === paramName) {
                    element.textContent = value.displayValue;
                }
            });
        });
    }
    
    function setParameter(keyName, value) {
        fetch('/ac/api/set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keyName, value }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Parameter set successfully:', data);
            // Refresh data after setting parameter
            setTimeout(refreshData, 1000);
        })
        .catch(error => {
            console.error('Error setting parameter:', error);
        });
    }
    
    // Initial data load
    refreshData();
    
    // Set up periodic refresh when tab is visible
    let refreshInterval;
    
    function startRefreshInterval() {
        if (!refreshInterval) {
            refreshInterval = setInterval(refreshData, 60000); // Refresh every minute
        }
    }
    
    function stopRefreshInterval() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            refreshData(); // Refresh immediately when page becomes visible
            startRefreshInterval();
        } else {
            stopRefreshInterval();
        }
    });
    
    // Start interval if page is visible
    if (document.visibilityState === 'visible') {
        startRefreshInterval();
    }
});
