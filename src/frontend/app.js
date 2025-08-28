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
    
    // Chart line toggle listeners - they toggle visibility without reloading data
    document.getElementById('stockPrice').addEventListener('change', () => toggleDataset('price'));
    document.getElementById('ma5').addEventListener('change', () => toggleDataset('ma5'));
    document.getElementById('ma20').addEventListener('change', () => toggleDataset('ma20'));
    document.getElementById('ma40').addEventListener('change', () => toggleDataset('ma40'));
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
        
        // Show sections
        document.getElementById('stockInfo').style.display = 'block';
        document.getElementById('chartSection').style.display = 'block';
        document.getElementById('volumeSection').style.display = 'block';
        document.getElementById('statsSection').style.display = 'block';
        
        showSuccess(`Loaded ${priceData.data.total_points} data points for ${ticker}`);
        
    } catch (error) {
        showError('Error loading stock data: ' + error.message);
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
    }
    
    // Prepare all datasets - load them all but control visibility
    allDatasets = {
        price: {
            label: 'Close Price',
            data: data.prices,
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231, 76, 60, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 5,
            tension: 0.1,
            hidden: !document.getElementById('stockPrice').checked  // Respect checkbox state
        },
        ma5: {
            label: '5-Day MA',
            data: data.ma_5,
            borderColor: '#3498db',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            borderDash: [5, 5],
            hidden: !document.getElementById('ma5').checked  // Respect checkbox state
        },
        ma20: {
            label: '20-Day MA',
            data: data.ma_20,
            borderColor: '#27ae60',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            borderDash: [5, 5],
            hidden: !document.getElementById('ma20').checked  // Respect checkbox state
        },
        ma40: {
            label: '40-Day MA',
            data: data.ma_40,
            borderColor: '#9b59b6',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            borderDash: [5, 5],
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
        // Toggle the visibility
        const isHidden = priceChart.getDatasetMeta(datasetIndex).hidden;
        priceChart.getDatasetMeta(datasetIndex).hidden = !isHidden;
        
        // Update the chart to show/hide the dataset
        priceChart.update('none'); // 'none' animation mode for instant update
    }
}

// Date range preset function
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