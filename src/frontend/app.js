// Stock Price Visualization Application
// Main JavaScript file for handling chart rendering and API interactions

const API_BASE_URL = 'http://localhost:5001/api';

// Global variables
let priceChart = null;
let volumeChart = null;
let currentStockData = null;
let searchTimeout = null;
let selectedSearchIndex = -1;
let allDatasets = {}; // Store all datasets for toggling
let chartUpdateTimeout = null; // Debouncing for chart updates
let isChartReady = false; // Flag to track if chart is ready for updates

// Centralized chart style configuration
const CHART_STYLES = {
    price: {
        borderColor: '#e74c3c',
        backgroundColor: 'rgba(231, 76, 60, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        tension: 0.1
    },
    ma5: {
        borderColor: '#3498db',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        borderDash: [5, 5]
    },
    ma20: {
        borderColor: '#27ae60',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        borderDash: [5, 5]
    },
    ma40: {
        borderColor: '#9b59b6',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        borderDash: [5, 5]
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    // Set default dates (last 6 months)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6);
    
    document.getElementById('startDate').value = formatDate(startDate);
    document.getElementById('endDate').value = formatDate(endDate);
    
    // Set up event listeners for search
    setupSearchFunctionality();
    
    // Set up other event listeners
    document.getElementById('loadDataBtn').addEventListener('click', loadStockData);
    document.getElementById('loadYahooDataBtn').addEventListener('click', loadYahooData);
    document.getElementById('updateDataBtn').addEventListener('click', updateStockData);
    
    // Chart line toggle listeners - reactive updates with debouncing
    document.getElementById('stockPrice').addEventListener('change', () => reactiveToggleDataset('price'));
    document.getElementById('ma5').addEventListener('change', () => reactiveToggleDataset('ma5'));
    document.getElementById('ma20').addEventListener('change', () => reactiveToggleDataset('ma20'));
    document.getElementById('ma40').addEventListener('change', () => reactiveToggleDataset('ma40'));
}

function setupSearchFunctionality() {
    const searchInput = document.getElementById('stockSearch');
    const searchResults = document.getElementById('searchResults');
    
    // Search input event listener with debouncing
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 1) {
            searchResults.style.display = 'none';
            searchResults.innerHTML = '';
            document.getElementById('selectedTicker').value = '';
            return;
        }
        
        // Debounce search requests (300ms)
        searchTimeout = setTimeout(() => searchTickers(query), 300);
    });
    
    // Handle keyboard navigation in search results
    searchInput.addEventListener('keydown', function(e) {
        const results = document.querySelectorAll('.search-result-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedSearchIndex = Math.min(selectedSearchIndex + 1, results.length - 1);
            updateSelectedResult(results);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedSearchIndex = Math.max(selectedSearchIndex - 1, -1);
            updateSelectedResult(results);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedSearchIndex >= 0 && results[selectedSearchIndex]) {
                selectStock(results[selectedSearchIndex].dataset.symbol, 
                          results[selectedSearchIndex].dataset.name);
            }
        } else if (e.key === 'Escape') {
            searchResults.style.display = 'none';
            selectedSearchIndex = -1;
        }
    });
    
    // Click outside to close search results
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
            selectedSearchIndex = -1;
        }
    });
}

async function searchTickers(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/search/tickers?q=${encodeURIComponent(query)}&limit=20`);
        const data = await response.json();
        
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '';
        selectedSearchIndex = -1;
        
        if (data.success && data.results.length > 0) {
            data.results.forEach(stock => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';
                resultItem.dataset.symbol = stock.symbol;
                resultItem.dataset.name = stock.name;
                
                // Highlight matching text
                const highlightedSymbol = highlightText(stock.symbol, query);
                const highlightedName = highlightText(stock.name, query);
                
                resultItem.innerHTML = `
                    <span class="search-result-symbol">${highlightedSymbol}</span>
                    <span class="search-result-name">${highlightedName}</span>
                    <span class="search-result-sector">${stock.sector}</span>
                `;
                
                resultItem.addEventListener('click', function() {
                    selectStock(stock.symbol, stock.name);
                });
                
                searchResults.appendChild(resultItem);
            });
            
            searchResults.style.display = 'block';
        } else if (data.results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">No results found</div>';
            searchResults.style.display = 'block';
        } else {
            searchResults.style.display = 'none';
        }
    } catch (error) {
        console.error('Search error:', error);
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '<div class="search-no-results">Error searching stocks</div>';
        searchResults.style.display = 'block';
    }
}

function highlightText(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<span class="search-highlight">$1</span>');
}

function updateSelectedResult(results) {
    results.forEach((result, index) => {
        if (index === selectedSearchIndex) {
            result.classList.add('selected');
            result.scrollIntoView({ block: 'nearest' });
        } else {
            result.classList.remove('selected');
        }
    });
}

function selectStock(symbol, name) {
    document.getElementById('stockSearch').value = `${symbol} - ${name}`;
    document.getElementById('selectedTicker').value = symbol;
    document.getElementById('searchResults').style.display = 'none';
    selectedSearchIndex = -1;
    
    // Load stock info for the selected ticker
    onStockSelected(symbol);
}

async function onStockSelected(ticker = null) {
    ticker = ticker || document.getElementById('selectedTicker').value;
    if (ticker) {
        // Check if stock has data
        try {
            const response = await fetch(`${API_BASE_URL}/stock/${ticker}/check`);
            const data = await response.json();
            
            if (data.success) {
                const loadDataBtn = document.getElementById('loadDataBtn');
                const loadYahooBtn = document.getElementById('loadYahooDataBtn');
                const updateBtn = document.getElementById('updateDataBtn');
                const noDataMsg = document.getElementById('noDataMessage');
                
                if (data.has_data) {
                    // Stock has data - show normal buttons
                    loadDataBtn.style.display = 'inline-block';
                    loadYahooBtn.style.display = 'none';
                    updateBtn.style.display = 'inline-block';
                    noDataMsg.style.display = 'none';
                    
                    // Update date range to match available data
                    if (data.data_info && data.data_info.date_range_start && data.data_info.date_range_end) {
                        document.getElementById('startDate').value = data.data_info.date_range_start;
                        document.getElementById('endDate').value = data.data_info.date_range_end;
                    }
                } else {
                    // Stock doesn't have data - show load from Yahoo button
                    loadDataBtn.style.display = 'none';
                    loadYahooBtn.style.display = 'inline-block';
                    updateBtn.style.display = 'none';
                    noDataMsg.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Error checking stock data:', error);
        }
    }
}

async function loadStockData() {
    const ticker = document.getElementById('selectedTicker').value;
    
    if (!ticker) {
        showError('Please select a stock ticker');
        return;
    }
    
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    try {
        showLoading(true);
        hideMessages();
        
        // Reset chart ready flag
        isChartReady = false;
        
        // Fetch stock info
        const infoResponse = await fetch(`${API_BASE_URL}/stock/${ticker}/info`);
        const infoData = await infoResponse.json();
        
        if (!infoData.success) {
            showError(infoData.error || 'Failed to load stock information');
            return;
        }
        
        // Fetch price data
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const priceResponse = await fetch(`${API_BASE_URL}/stock/${ticker}/prices?${params}`);
        const priceData = await priceResponse.json();
        
        if (!priceData.success) {
            showError(priceData.error || 'Failed to load price data');
            return;
        }
        
        // Store data globally
        currentStockData = priceData.data;
        
        // Display stock information
        displayStockInfo(infoData.info);
        
        // Display charts
        displayPriceChart(priceData.data);
        displayVolumeChart(priceData.data);
        
        // Display statistics
        displayStatistics(priceData.data);
        
        // Mark chart as ready for reactive updates
        isChartReady = true;
        
        // Ensure chart style consistency after initial load
        ensureChartStyleConsistency();
        
        // Show sections
        document.getElementById('stockInfo').style.display = 'block';
        document.getElementById('chartSection').style.display = 'block';
        document.getElementById('volumeSection').style.display = 'block';
        document.getElementById('statsSection').style.display = 'block';
        
        showSuccess(`Loaded ${priceData.data.total_points} data points for ${ticker}`);
        
    } catch (error) {
        showError('Error loading stock data: ' + error.message);
        // Reset chart ready flag on error
        isChartReady = false;
    } finally {
        showLoading(false);
    }
}

async function loadYahooData() {
    const ticker = document.getElementById('selectedTicker').value;
    
    if (!ticker) {
        showError('Please search and select a stock ticker');
        return;
    }
    
    try {
        showLoading(true);
        hideMessages();
        
        const response = await fetch(`${API_BASE_URL}/stock/${ticker}/load`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ period: 'max' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            
            // Update UI to show normal buttons
            document.getElementById('loadDataBtn').style.display = 'inline-block';
            document.getElementById('loadYahooDataBtn').style.display = 'none';
            document.getElementById('updateDataBtn').style.display = 'inline-block';
            document.getElementById('noDataMessage').style.display = 'none';
            
            // Check stock info to update date ranges
            await onStockSelected(ticker);
            
            // Automatically load the chart
            setTimeout(() => loadStockData(), 500);
        } else {
            showError(data.error || 'Failed to load stock data from Yahoo Finance');
        }
        
    } catch (error) {
        showError('Error loading stock data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function updateStockData() {
    const ticker = document.getElementById('selectedTicker').value;
    
    if (!ticker) {
        showError('Please select a stock ticker');
        return;
    }
    
    try {
        showLoading(true);
        hideMessages();
        
        const response = await fetch(`${API_BASE_URL}/stock/${ticker}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ period: 'max' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            // Reload the chart with updated data
            setTimeout(() => loadStockData(), 1000);
        } else {
            showError(data.error || 'Failed to update stock data');
        }
        
    } catch (error) {
        showError('Error updating stock data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayStockInfo(info) {
    document.getElementById('stockName').textContent = info.company_name;
    document.getElementById('infoTicker').textContent = info.ticker;
    document.getElementById('infoSector').textContent = info.sector;
    document.getElementById('infoExchange').textContent = info.exchange;
    document.getElementById('infoDataPoints').textContent = info.total_records;
    document.getElementById('infoDateRange').textContent = 
        `${info.date_range_start} to ${info.date_range_end}`;
    document.getElementById('infoLastUpdated').textContent = 
        new Date(info.last_updated).toLocaleString();
}

function displayPriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (priceChart) {
        priceChart.destroy();
        priceChart = null;
    }
    
    // Set initial canvas background to prevent white flash
    const canvas = document.getElementById('priceChart');
    if (canvas) {
        canvas.style.backgroundColor = 'transparent';
    }
    
    // Prepare all datasets using centralized style configuration
    allDatasets = {
        price: {
            label: 'Close Price',
            data: data.prices,
            ...CHART_STYLES.price,
            hidden: !document.getElementById('stockPrice').checked  // Respect checkbox state
        },
        ma5: {
            label: '5-Day MA',
            data: data.ma_5,
            ...CHART_STYLES.ma5,
            hidden: !document.getElementById('ma5').checked  // Respect checkbox state
        },
        ma20: {
            label: '20-Day MA',
            data: data.ma_20,
            ...CHART_STYLES.ma20,
            hidden: !document.getElementById('ma20').checked  // Respect checkbox state
        },
        ma40: {
            label: '40-Day MA',
            data: data.ma_40,
            ...CHART_STYLES.ma40,
            hidden: !document.getElementById('ma40').checked  // Respect checkbox state
        }
    };
    
    // Build datasets array - always include all datasets
    const datasets = [allDatasets.price];
    
    // Add MA datasets if they exist in the data
    if (data.ma_5) datasets.push(allDatasets.ma5);
    if (data.ma_20) datasets.push(allDatasets.ma20);
    if (data.ma_40) datasets.push(allDatasets.ma40);
    
    // Create chart
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                onComplete: function() {
                    // Ensure dark backgrounds are maintained after chart completion
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: `${data.ticker} - Historical Prices with Moving Averages`,
                    font: {
                        size: 16,
                        family: 'Georgia, serif'
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            family: 'Georgia, serif'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += '$' + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            family: 'Georgia, serif'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        font: {
                            family: 'Georgia, serif'
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price ($)',
                        font: {
                            family: 'Georgia, serif'
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        },
                        font: {
                            family: 'Georgia, serif'
                        }
                    }
                }
            }
        }
    });
}

function displayVolumeChart(data) {
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (volumeChart) {
        volumeChart.destroy();
    }
    
    // Create volume chart
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Volume',
                data: data.volumes,
                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                borderColor: '#3498db',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${data.ticker} - Trading Volume`,
                    font: {
                        size: 16,
                        family: 'Georgia, serif'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Volume: ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            family: 'Georgia, serif'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        font: {
                            family: 'Georgia, serif'
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Volume',
                        font: {
                            family: 'Georgia, serif'
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        },
                        font: {
                            family: 'Georgia, serif'
                        }
                    }
                }
            }
        }
    });
}

function displayStatistics(data) {
    // Calculate statistics
    const prices = data.prices.filter(p => p !== null);
    const currentPrice = prices[prices.length - 1];
    const previousPrice = prices[prices.length - 2];
    const dailyChange = currentPrice - previousPrice;
    const dailyChangePercent = (dailyChange / previousPrice * 100).toFixed(2);
    
    const periodHigh = Math.max(...prices);
    const periodLow = Math.min(...prices);
    
    const volumes = data.volumes.filter(v => v !== null && v > 0);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    
    // Calculate volatility (standard deviation of daily returns)
    const returns = [];
    for (let i = 1; i < prices.length; i++) {
        returns.push((prices[i] - prices[i-1]) / prices[i-1]);
    }
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance * 252) * 100; // Annualized volatility
    
    // Update display
    document.getElementById('currentPrice').textContent = currentPrice.toFixed(2);
    
    const changeElement = document.getElementById('dailyChange');
    changeElement.textContent = `${dailyChange >= 0 ? '+' : ''}${dailyChange.toFixed(2)} (${dailyChangePercent}%)`;
    changeElement.style.color = dailyChange >= 0 ? '#27ae60' : '#e74c3c';
    
    document.getElementById('periodHigh').textContent = periodHigh.toFixed(2);
    document.getElementById('periodLow').textContent = periodLow.toFixed(2);
    document.getElementById('avgVolume').textContent = formatNumber(avgVolume);
    document.getElementById('volatility').textContent = volatility.toFixed(2);
}

function toggleDataset(datasetType) {
    if (!priceChart) return;
    
    // Find the dataset index based on label
    const datasetLabels = {
        'price': 'Close Price',
        'ma5': '5-Day MA',
        'ma20': '20-Day MA',
        'ma40': '40-Day MA'
    };
    
    const label = datasetLabels[datasetType];
    const datasetIndex = priceChart.data.datasets.findIndex(ds => ds.label === label);
    
    if (datasetIndex !== -1) {
        // Get the dataset and ensure consistent styling
        const dataset = priceChart.data.datasets[datasetIndex];
        
        // Restore original styling to prevent Chart.js from modifying it
        Object.assign(dataset, CHART_STYLES[datasetType]);
        
        // Toggle the visibility
        const isHidden = priceChart.getDatasetMeta(datasetIndex).hidden;
        priceChart.getDatasetMeta(datasetIndex).hidden = !isHidden;
        
        // Update the chart with consistent styling
        priceChart.update('none'); // 'none' animation mode for instant update
    }
}

/**
 * Reactive toggle function with debouncing and visual feedback
 * Updates chart immediately when checkbox state changes
 * @param {string} datasetType - Type of dataset to toggle (price, ma5, ma20, ma40)
 */
function reactiveToggleDataset(datasetType) {
    // Don't react if chart isn't ready yet
    if (!isChartReady || !priceChart) return;
    
    // Clear any pending chart updates to debounce rapid toggles
    if (chartUpdateTimeout) {
        clearTimeout(chartUpdateTimeout);
    }
    
    // Show visual feedback immediately
    showChartUpdateFeedback();
    
    // Debounce chart updates (100ms delay)
    chartUpdateTimeout = setTimeout(() => {
        performReactiveToggle(datasetType);
        hideChartUpdateFeedback();
        chartUpdateTimeout = null;
    }, 100);
}

/**
 * Perform the actual dataset toggle with consistent styling and white flash prevention
 * @param {string} datasetType - Type of dataset to toggle
 */
function performReactiveToggle(datasetType) {
    if (!priceChart) return;
    
    // Preserve dark background during toggle in fullscreen
    
    // Find the dataset index based on label
    const datasetLabels = {
        'price': 'Close Price',
        'ma5': '5-Day MA',
        'ma20': '20-Day MA',
        'ma40': '40-Day MA'
    };
    
    const label = datasetLabels[datasetType];
    const datasetIndex = priceChart.data.datasets.findIndex(ds => ds.label === label);
    
    if (datasetIndex !== -1) {
        // Get current checkbox state
        const checkbox = document.getElementById(getCheckboxId(datasetType));
        if (!checkbox) return;
        
        // Get the dataset and ensure consistent styling
        const dataset = priceChart.data.datasets[datasetIndex];
        
        // Restore original styling to prevent Chart.js from modifying it
        Object.assign(dataset, CHART_STYLES[datasetType]);
        
        // Toggle the visibility based on checkbox state
        priceChart.getDatasetMeta(datasetIndex).hidden = !checkbox.checked;
        
        // Update chart with 'none' animation mode to prevent style changes
        priceChart.update('none');
        
        // Re-apply dark backgrounds after update to prevent white flash
        setTimeout(() => {
                }, 10);
        
        // Sync with fullscreen sidebar checkboxes if they exist
        syncFullscreenCheckboxes(datasetType, checkbox.checked);
    }
}


/**
 * Get checkbox ID for dataset type
 * @param {string} datasetType - Type of dataset
 * @returns {string} Checkbox element ID
 */
function getCheckboxId(datasetType) {
    const checkboxIds = {
        'price': 'stockPrice',
        'ma5': 'ma5',
        'ma20': 'ma20',
        'ma40': 'ma40'
    };
    return checkboxIds[datasetType];
}

/**
 * Sync fullscreen sidebar checkboxes with main form checkboxes
 * @param {string} datasetType - Type of dataset
 * @param {boolean} checked - Checkbox state
 */
function syncFullscreenCheckboxes(datasetType, checked) {
    // Look for fullscreen sidebar checkboxes
    const fsCheckboxSelectors = [
        `#fs-${getCheckboxId(datasetType)}-priceChartContainer`,
        `#fs-${getCheckboxId(datasetType)}-price`,
        `#fs-${getCheckboxId(datasetType)}-stock-prices`
    ];
    
    fsCheckboxSelectors.forEach(selector => {
        const fsCheckbox = document.querySelector(selector);
        if (fsCheckbox && fsCheckbox.checked !== checked) {
            fsCheckbox.checked = checked;
        }
    });
}

/**
 * Show visual feedback during chart updates
 */
function showChartUpdateFeedback() {
    // Add a subtle overlay to indicate chart is updating
    const chartContainer = document.getElementById('priceChartContainer');
    if (!chartContainer) return;
    
    let overlay = chartContainer.querySelector('.chart-update-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'chart-update-overlay';
        overlay.innerHTML = '<div class="update-spinner"></div>';
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 5;
            pointer-events: none;
            transition: opacity 0.2s ease;
        `;
        
        // Add spinner styles
        const style = document.createElement('style');
        style.textContent = `
            .update-spinner {
                width: 24px;
                height: 24px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #e74c3c;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            .chart-update-overlay {
                opacity: 0;
                transition: opacity 0.2s ease;
            }
            .chart-update-overlay.visible {
                opacity: 1;
            }
        `;
        
        if (!document.querySelector('#chart-update-styles')) {
            style.id = 'chart-update-styles';
            document.head.appendChild(style);
        }
        
        chartContainer.appendChild(overlay);
    }
    
    // Show overlay
    requestAnimationFrame(() => {
        overlay.classList.add('visible');
    });
}

/**
 * Hide visual feedback after chart updates
 */
function hideChartUpdateFeedback() {
    const chartContainer = document.getElementById('priceChartContainer');
    if (!chartContainer) return;
    
    const overlay = chartContainer.querySelector('.chart-update-overlay');
    if (overlay) {
        overlay.classList.remove('visible');
        // Remove overlay after transition
        setTimeout(() => {
            if (overlay.parentNode && !overlay.classList.contains('visible')) {
                overlay.remove();
            }
        }, 200);
    }
}

/**
 * Ensure chart style consistency across all datasets
 * Call this after any operation that might affect chart styling
 */
function ensureChartStyleConsistency() {
    if (!priceChart || !priceChart.data || !priceChart.data.datasets) return;
    
    const datasetTypeMap = {
        'Close Price': 'price',
        '5-Day MA': 'ma5',
        '20-Day MA': 'ma20',
        '40-Day MA': 'ma40'
    };
    
    let stylesApplied = 0;
    
    priceChart.data.datasets.forEach(dataset => {
        const datasetType = datasetTypeMap[dataset.label];
        if (datasetType && CHART_STYLES[datasetType]) {
            // Preserve data and visibility state
            const originalData = dataset.data;
            const originalHidden = dataset.hidden;
            const originalLabel = dataset.label;
            
            // Check if style correction is needed (prevents Chart.js from adding dots/circles)
            const needsCorrection = dataset.pointRadius !== CHART_STYLES[datasetType].pointRadius ||
                                  dataset.borderWidth !== CHART_STYLES[datasetType].borderWidth ||
                                  dataset.borderColor !== CHART_STYLES[datasetType].borderColor;
            
            if (needsCorrection) {
                // Apply consistent styling
                Object.assign(dataset, CHART_STYLES[datasetType]);
                stylesApplied++;
                
                // Restore critical properties
                dataset.data = originalData;
                dataset.hidden = originalHidden;
                dataset.label = originalLabel;
            }
        }
    });
    
    // Only update if styles were actually corrected
    if (stylesApplied > 0) {
        // Update chart without animation to preserve styling
        priceChart.update('none');
    }
}

// Make CHART_STYLES and dark background preservation globally available
if (typeof window !== 'undefined') {
    window.CHART_STYLES = CHART_STYLES;
    window.ensureChartStyleConsistency = ensureChartStyleConsistency;
}

// Date range preset function with consistent chart styling
function setDateRange(value, unit) {
    const endDate = new Date();
    const startDate = new Date();
    
    if (value === 'all') {
        // Set start date to 10 years ago for "ALL" option
        startDate.setFullYear(startDate.getFullYear() - 10);
    } else {
        // Calculate the start date based on the period
        if (unit === 'months') {
            startDate.setMonth(startDate.getMonth() - value);
        } else if (unit === 'year') {
            startDate.setFullYear(startDate.getFullYear() - value);
        } else if (unit === 'years') {
            startDate.setFullYear(startDate.getFullYear() - value);
        }
    }
    
    // Update the date inputs
    document.getElementById('startDate').value = formatDate(startDate);
    document.getElementById('endDate').value = formatDate(endDate);
    
    // If chart exists, preserve style consistency after date change
    if (priceChart) {
        ensureChartStyleConsistency();
    }
}

// Utility functions
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatNumber(num) {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(0);
}


function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
}

function showError(message) {
    document.getElementById('errorText').textContent = message;
    document.getElementById('errorMessage').style.display = 'block';
    setTimeout(hideMessages, 5000);
}

function showSuccess(message) {
    document.getElementById('successText').textContent = message;
    document.getElementById('successMessage').style.display = 'block';
    setTimeout(hideMessages, 5000);
}

function hideMessages() {
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('successMessage').style.display = 'none';
}

// ==========================================================================
// Stock Viewer Modal Functionality
// ==========================================================================

// Global variables for stock viewer
let availableStocksData = [];
let loadedStocksData = [];
let filteredAvailableStocks = [];
let filteredLoadedStocks = [];

/**
 * Initialize stock viewer functionality
 */
function initializeStockViewer() {
    const stockViewerBtn = document.getElementById('stockViewerBtn');
    const closeBtn = document.getElementById('closeStockViewerBtn');
    const modal = document.getElementById('stockViewerModal');
    const availableSearch = document.getElementById('availableStocksSearch');
    const loadedSearch = document.getElementById('loadedStocksSearch');

    // Event listeners
    if (stockViewerBtn) {
        stockViewerBtn.addEventListener('click', openStockViewer);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeStockViewer);
    }

    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeStockViewer();
            }
        });
    }

    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
            closeStockViewer();
        }
    });

    // Search functionality
    if (availableSearch) {
        availableSearch.addEventListener('input', (e) => {
            filterAvailableStocks(e.target.value);
        });
    }

    if (loadedSearch) {
        loadedSearch.addEventListener('input', (e) => {
            filterLoadedStocks(e.target.value);
        });
    }
}

/**
 * Open the stock viewer modal
 */
async function openStockViewer() {
    const modal = document.getElementById('stockViewerModal');
    if (modal) {
        modal.classList.add('active');

        // Reset search inputs
        document.getElementById('availableStocksSearch').value = '';
        document.getElementById('loadedStocksSearch').value = '';

        // Load data
        await loadStockViewerData();
    }
}

/**
 * Close the stock viewer modal
 */
function closeStockViewer() {
    const modal = document.getElementById('stockViewerModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Load data for both available and loaded stocks
 */
async function loadStockViewerData() {
    await Promise.all([
        loadAvailableStocks(),
        loadLoadedStocks()
    ]);
}

/**
 * Load available stocks from the API
 */
async function loadAvailableStocks() {
    const loadingElement = document.getElementById('availableStocksLoading');
    const errorElement = document.getElementById('availableStocksError');
    const tableElement = document.getElementById('availableStocksTable');

    try {
        // Show loading state
        showElement(loadingElement);
        hideElement(errorElement);
        hideElement(tableElement);

        const response = await fetch(`${API_BASE_URL}/available-stocks`);

        if (!response.ok) {
            throw new Error(`Failed to load available stocks: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            availableStocksData = data.available_stocks || [];
            filteredAvailableStocks = [...availableStocksData];
            renderAvailableStocks();

            hideElement(loadingElement);
            showElement(tableElement);
        } else {
            throw new Error(data.error || 'Failed to load available stocks');
        }
    } catch (error) {
        console.error('Error loading available stocks:', error);

        hideElement(loadingElement);
        hideElement(tableElement);
        showElement(errorElement);

        errorElement.textContent = `Error: ${error.message}`;

        if (error.message.includes('nasdaq_screener.csv')) {
            errorElement.innerHTML = `
                <strong>Error:</strong> nasdaq_screener.csv not found.<br>
                <small>Run <code>python src/utils/get-tickers.py</code> to download the stock data file.</small>
            `;
        }
    }
}

/**
 * Load loaded stocks from the API
 */
async function loadLoadedStocks() {
    const loadingElement = document.getElementById('loadedStocksLoading');
    const errorElement = document.getElementById('loadedStocksError');
    const tableElement = document.getElementById('loadedStocksTable');

    try {
        // Show loading state
        showElement(loadingElement);
        hideElement(errorElement);
        hideElement(tableElement);

        const response = await fetch(`${API_BASE_URL}/stocks`);

        if (!response.ok) {
            throw new Error(`Failed to load database stocks: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            loadedStocksData = data.stocks || [];
            filteredLoadedStocks = [...loadedStocksData];
            renderLoadedStocks();

            hideElement(loadingElement);
            showElement(tableElement);
        } else {
            throw new Error(data.error || 'Failed to load database stocks');
        }
    } catch (error) {
        console.error('Error loading database stocks:', error);

        hideElement(loadingElement);
        hideElement(tableElement);
        showElement(errorElement);

        errorElement.textContent = `Error: ${error.message}`;
    }
}

/**
 * Render available stocks table
 */
function renderAvailableStocks() {
    const tbody = document.querySelector('#availableStocksTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (filteredAvailableStocks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #666;">
                    ${availableStocksData.length === 0 ? 'No available stocks found' : 'No stocks match your search'}
                </td>
            </tr>
        `;
        return;
    }

    filteredAvailableStocks.forEach(stock => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="ticker">${stock.symbol || 'N/A'}</span></td>
            <td><span class="company-name">${stock.name || 'N/A'}</span></td>
            <td><span class="sector">${stock.sector || 'N/A'}</span></td>
            <td><span class="sector">${stock.industry || 'N/A'}</span></td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Render loaded stocks table
 */
function renderLoadedStocks() {
    const tbody = document.querySelector('#loadedStocksTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (filteredLoadedStocks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                    ${loadedStocksData.length === 0 ? 'No stocks loaded in database' : 'No stocks match your search'}
                </td>
            </tr>
        `;
        return;
    }

    filteredLoadedStocks.forEach(stock => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="ticker">${stock.ticker || 'N/A'}</span></td>
            <td><span class="company-name">${stock.company_name || 'N/A'}</span></td>
            <td><span class="sector">${stock.sector || 'N/A'}</span></td>
            <td><span class="sector">${stock.exchange || 'N/A'}</span></td>
            <td><span class="records-count">${formatNumber(stock.total_records || 0)}</span></td>
            <td><span class="date-range">${formatDateRange(stock.date_range_start, stock.date_range_end)}</span></td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Filter available stocks based on search term
 */
function filterAvailableStocks(searchTerm) {
    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        filteredAvailableStocks = [...availableStocksData];
    } else {
        filteredAvailableStocks = availableStocksData.filter(stock => {
            const symbol = (stock.symbol || '').toLowerCase();
            const name = (stock.name || '').toLowerCase();
            const sector = (stock.sector || '').toLowerCase();
            const industry = (stock.industry || '').toLowerCase();

            return symbol.includes(term) ||
                   name.includes(term) ||
                   sector.includes(term) ||
                   industry.includes(term);
        });
    }

    renderAvailableStocks();
}

/**
 * Filter loaded stocks based on search term
 */
function filterLoadedStocks(searchTerm) {
    const term = searchTerm.toLowerCase().trim();

    if (!term) {
        filteredLoadedStocks = [...loadedStocksData];
    } else {
        filteredLoadedStocks = loadedStocksData.filter(stock => {
            const ticker = (stock.ticker || '').toLowerCase();
            const name = (stock.company_name || '').toLowerCase();
            const sector = (stock.sector || '').toLowerCase();
            const exchange = (stock.exchange || '').toLowerCase();

            return ticker.includes(term) ||
                   name.includes(term) ||
                   sector.includes(term) ||
                   exchange.includes(term);
        });
    }

    renderLoadedStocks();
}

/**
 * Format date range for display
 */
function formatDateRange(startDate, endDate) {
    if (!startDate || !endDate) return 'N/A';

    const start = new Date(startDate).toLocaleDateString();
    const end = new Date(endDate).toLocaleDateString();

    return `${start} - ${end}`;
}

/**
 * Show element helper
 */
function showElement(element) {
    if (element) {
        element.style.display = 'block';
    }
}

/**
 * Hide element helper
 */
function hideElement(element) {
    if (element) {
        element.style.display = 'none';
    }
}

// Initialize stock viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeStockViewer();
});