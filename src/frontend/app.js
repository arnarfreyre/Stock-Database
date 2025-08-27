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
let originalCanvasDimensions = {}; // Store original canvas dimensions for fullscreen restoration
let resizableChart = null; // ResizableChart instance for fullscreen mode

// ResizableChart class for handling resize and drag functionality in fullscreen
class ResizableChart {
    constructor(containerId, chart) {
        this.container = document.getElementById(containerId);
        this.chart = chart; // Chart.js instance (priceChart or volumeChart)
        this.wrapper = null;
        this.isResizing = false;
        this.isDragging = false;
        this.currentHandle = null;
        this.startX = 0;
        this.startY = 0;
        this.startWidth = 0;
        this.startHeight = 0;
        this.startLeft = 0;
        this.startTop = 0;
        
        // Constraints
        this.minWidth = 400;
        this.minHeight = 300;
        this.maxWidthPercent = 0.95;
        this.maxHeightPercent = 0.95;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Create wrapper for the chart
        this.createWrapper();
        // Add resize handles
        this.createResizeHandles();
        // Set up event listeners
        this.setupEventListeners();
        // Position the wrapper initially (centered, 80% size)
        this.setInitialPosition();
    }
    
    createWrapper() {
        const formulaBox = this.container.querySelector('.formula-box');
        
        // Create wrapper div
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'resizable-chart-wrapper';
        
        // Move the formula box inside the wrapper
        this.wrapper.appendChild(formulaBox);
        
        // Add wrapper to container
        if (this.container.classList.contains('fullscreen') || 
            this.container.matches(':fullscreen') || 
            this.container.matches(':-webkit-full-screen')) {
            this.container.appendChild(this.wrapper);
        }
    }
    
    createResizeHandles() {
        // Define handle positions
        const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
        
        handles.forEach(position => {
            const handle = document.createElement('div');
            handle.className = `resize-handle resize-handle-${position}`;
            handle.dataset.position = position;
            this.wrapper.appendChild(handle);
        });
    }
    
    setupEventListeners() {
        // Resize handles
        const handles = this.wrapper.querySelectorAll('.resize-handle');
        handles.forEach(handle => {
            handle.addEventListener('mousedown', this.startResize.bind(this));
            handle.addEventListener('touchstart', this.startResize.bind(this), { passive: false });
        });
        
        // Drag functionality (on the chart area)
        const formulaBox = this.wrapper.querySelector('.formula-box');
        formulaBox.addEventListener('mousedown', this.startDrag.bind(this));
        formulaBox.addEventListener('touchstart', this.startDrag.bind(this), { passive: false });
        
        // Global mouse/touch events
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        document.addEventListener('touchmove', this.handleMouseMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleMouseUp.bind(this));
    }
    
    setInitialPosition() {
        const containerRect = this.container.getBoundingClientRect();
        const sidebarWidth = 250; // Sidebar width in fullscreen
        const availableWidth = containerRect.width - sidebarWidth;
        
        // Set initial size (80% of available space)
        const initialWidth = availableWidth * 0.8;
        const initialHeight = containerRect.height * 0.8;
        
        // Center the wrapper
        const left = (availableWidth - initialWidth) / 2;
        const top = (containerRect.height - initialHeight) / 2;
        
        this.wrapper.style.width = `${initialWidth}px`;
        this.wrapper.style.height = `${initialHeight}px`;
        this.wrapper.style.left = `${left}px`;
        this.wrapper.style.top = `${top}px`;
        
        // Update chart size
        this.updateChartSize();
    }
    
    startResize(e) {
        e.preventDefault();
        e.stopPropagation();
        
        this.isResizing = true;
        this.currentHandle = e.target.dataset.position;
        
        const touch = e.touches ? e.touches[0] : e;
        this.startX = touch.clientX;
        this.startY = touch.clientY;
        
        const rect = this.wrapper.getBoundingClientRect();
        this.startWidth = rect.width;
        this.startHeight = rect.height;
        this.startLeft = parseInt(this.wrapper.style.left || 0);
        this.startTop = parseInt(this.wrapper.style.top || 0);
        
        this.wrapper.classList.add('resizing');
    }
    
    startDrag(e) {
        // Don't start drag if clicking on a button, input, or resize handle
        if (e.target.closest('button') || 
            e.target.closest('input') || 
            e.target.closest('.resize-handle') ||
            e.target.closest('.exit-fullscreen-btn')) {
            return;
        }
        
        // Don't drag if it's a chart interaction (like tooltip)
        if (e.target.tagName === 'CANVAS') {
            // Allow chart interactions to work normally
            return;
        }
        
        e.preventDefault();
        this.isDragging = true;
        
        const touch = e.touches ? e.touches[0] : e;
        this.startX = touch.clientX;
        this.startY = touch.clientY;
        
        this.startLeft = parseInt(this.wrapper.style.left || 0);
        this.startTop = parseInt(this.wrapper.style.top || 0);
        
        this.wrapper.classList.add('dragging');
    }
    
    handleMouseMove(e) {
        if (!this.isResizing && !this.isDragging) return;
        
        const touch = e.touches ? e.touches[0] : e;
        const deltaX = touch.clientX - this.startX;
        const deltaY = touch.clientY - this.startY;
        
        if (this.isResizing) {
            this.performResize(deltaX, deltaY);
        } else if (this.isDragging) {
            this.performDrag(deltaX, deltaY);
        }
    }
    
    performResize(deltaX, deltaY) {
        const containerRect = this.container.getBoundingClientRect();
        const sidebarWidth = 250;
        const maxWidth = (containerRect.width - sidebarWidth) * this.maxWidthPercent;
        const maxHeight = containerRect.height * this.maxHeightPercent;
        
        let newWidth = this.startWidth;
        let newHeight = this.startHeight;
        let newLeft = this.startLeft;
        let newTop = this.startTop;
        
        // Handle resize based on handle position
        const handle = this.currentHandle;
        
        if (handle.includes('e')) {
            newWidth = Math.min(Math.max(this.startWidth + deltaX, this.minWidth), maxWidth);
        }
        if (handle.includes('w')) {
            newWidth = Math.min(Math.max(this.startWidth - deltaX, this.minWidth), maxWidth);
            newLeft = this.startLeft + (this.startWidth - newWidth);
        }
        if (handle.includes('s')) {
            newHeight = Math.min(Math.max(this.startHeight + deltaY, this.minHeight), maxHeight);
        }
        if (handle.includes('n')) {
            newHeight = Math.min(Math.max(this.startHeight - deltaY, this.minHeight), maxHeight);
            newTop = this.startTop + (this.startHeight - newHeight);
        }
        
        // Apply constraints to position
        newLeft = Math.max(0, Math.min(newLeft, containerRect.width - sidebarWidth - newWidth));
        newTop = Math.max(0, Math.min(newTop, containerRect.height - newHeight));
        
        // Apply new dimensions
        this.wrapper.style.width = `${newWidth}px`;
        this.wrapper.style.height = `${newHeight}px`;
        this.wrapper.style.left = `${newLeft}px`;
        this.wrapper.style.top = `${newTop}px`;
        
        // Update chart size with throttling
        this.throttledUpdateChart();
    }
    
    performDrag(deltaX, deltaY) {
        const containerRect = this.container.getBoundingClientRect();
        const sidebarWidth = 250;
        const wrapperRect = this.wrapper.getBoundingClientRect();
        
        let newLeft = this.startLeft + deltaX;
        let newTop = this.startTop + deltaY;
        
        // Apply constraints
        newLeft = Math.max(0, Math.min(newLeft, containerRect.width - sidebarWidth - wrapperRect.width));
        newTop = Math.max(0, Math.min(newTop, containerRect.height - wrapperRect.height));
        
        // Apply new position
        this.wrapper.style.left = `${newLeft}px`;
        this.wrapper.style.top = `${newTop}px`;
    }
    
    handleMouseUp(e) {
        if (this.isResizing) {
            this.isResizing = false;
            this.wrapper.classList.remove('resizing');
            this.currentHandle = null;
            
            // Final chart update
            this.updateChartSize();
        }
        
        if (this.isDragging) {
            this.isDragging = false;
            this.wrapper.classList.remove('dragging');
        }
    }
    
    throttledUpdateChart() {
        // Throttle chart updates for performance
        if (!this.updateTimeout) {
            this.updateTimeout = setTimeout(() => {
                this.updateChartSize();
                this.updateTimeout = null;
            }, 50);
        }
    }
    
    updateChartSize() {
        if (this.chart) {
            // Use requestAnimationFrame for smooth updates
            requestAnimationFrame(() => {
                this.chart.resize();
            });
        }
    }
    
    destroy() {
        // Clean up event listeners
        const handles = this.wrapper.querySelectorAll('.resize-handle');
        handles.forEach(handle => {
            handle.removeEventListener('mousedown', this.startResize.bind(this));
            handle.removeEventListener('touchstart', this.startResize.bind(this));
        });
        
        const formulaBox = this.wrapper.querySelector('.formula-box');
        if (formulaBox) {
            formulaBox.removeEventListener('mousedown', this.startDrag.bind(this));
            formulaBox.removeEventListener('touchstart', this.startDrag.bind(this));
        }
        
        // Move formula box back to container
        if (formulaBox && this.container) {
            this.container.appendChild(formulaBox);
        }
        
        // Remove wrapper
        if (this.wrapper && this.wrapper.parentNode) {
            this.wrapper.remove();
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Fullscreen functionality
function toggleFullscreen(containerId) {
    const container = document.getElementById(containerId);
    
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        // Enter fullscreen
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            // Safari support
            container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
            // IE11 support
            container.msRequestFullscreen();
        }
        
        // Store original canvas dimensions and set fullscreen dimensions
        const canvas = container.querySelector('canvas');
        if (canvas) {
            originalCanvasDimensions[containerId] = {
                height: canvas.style.height || '',
                maxHeight: canvas.style.maxHeight || ''
            };
            // Set canvas to fill available height in fullscreen
            canvas.style.height = 'calc(100vh - 6rem)';
            canvas.style.maxHeight = 'calc(100vh - 6rem)';
        }
        
        // Set up fullscreen event listeners
        setupFullscreenListeners(containerId);
        
        // Initialize ResizableChart after a short delay to ensure fullscreen is active
        setTimeout(() => {
            // Determine which chart to make resizable
            const chart = containerId === 'priceChartContainer' ? priceChart : volumeChart;
            if (chart) {
                resizableChart = new ResizableChart(containerId, chart);
            }
            
            // Update charts to fit the new size
            if (priceChart) priceChart.resize();
            if (volumeChart) volumeChart.resize();
        }, 100);
    } else {
        // Exit fullscreen
        exitFullscreen();
    }
}

function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        // Safari support
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        // IE11 support
        document.msExitFullscreen();
    }
}

function setupFullscreenListeners(containerId) {
    // Determine which chart we're working with
    const isPriceChart = containerId === 'priceChartContainer';
    const chartType = isPriceChart ? 'price' : 'volume';
    
    // Sync date inputs with main date inputs
    const startDateInput = document.getElementById(`fs-startDate-${chartType}`);
    const endDateInput = document.getElementById(`fs-endDate-${chartType}`);
    if (startDateInput && endDateInput) {
        startDateInput.value = document.getElementById('startDate').value;
        endDateInput.value = document.getElementById('endDate').value;
    }
    
    // Set up sidebar checkbox listeners for the specific chart
    if (isPriceChart) {
        // Price chart toggles
        const stockPriceCheckbox = document.getElementById('fs-stockPrice-price');
        const ma5Checkbox = document.getElementById('fs-ma5-price');
        const ma20Checkbox = document.getElementById('fs-ma20-price');
        const ma40Checkbox = document.getElementById('fs-ma40-price');
        
        // Sync with main checkboxes
        stockPriceCheckbox.checked = document.getElementById('stockPrice').checked;
        ma5Checkbox.checked = document.getElementById('ma5').checked;
        ma20Checkbox.checked = document.getElementById('ma20').checked;
        ma40Checkbox.checked = document.getElementById('ma40').checked;
        
        // Add event listeners
        stockPriceCheckbox.onchange = function() {
            document.getElementById('stockPrice').checked = this.checked;
            toggleDataset('price');
        };
        
        ma5Checkbox.onchange = function() {
            document.getElementById('ma5').checked = this.checked;
            toggleDataset('ma5');
        };
        
        ma20Checkbox.onchange = function() {
            document.getElementById('ma20').checked = this.checked;
            toggleDataset('ma20');
        };
        
        ma40Checkbox.onchange = function() {
            document.getElementById('ma40').checked = this.checked;
            toggleDataset('ma40');
        };
    } else {
        // Volume chart toggles (for future use)
        const volumeBarsCheckbox = document.getElementById('fs-volume-bars');
        if (volumeBarsCheckbox) {
            volumeBarsCheckbox.onchange = function() {
                // Future implementation for volume chart options
                if (volumeChart && this.checked === false) {
                    volumeChart.data.datasets[0].hidden = true;
                    volumeChart.update('none');
                } else if (volumeChart) {
                    volumeChart.data.datasets[0].hidden = false;
                    volumeChart.update('none');
                }
            };
        }
    }
    
    // Listen for fullscreen exit to clean up
    const fullscreenChangeHandler = function() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
            // Clean up event listeners when exiting fullscreen
            document.removeEventListener('fullscreenchange', fullscreenChangeHandler);
            document.removeEventListener('webkitfullscreenchange', fullscreenChangeHandler);
            
            // Destroy ResizableChart instance
            if (resizableChart) {
                resizableChart.destroy();
                resizableChart = null;
            }
            
            // Restore original canvas dimensions
            const canvas = document.getElementById(containerId).querySelector('canvas');
            if (canvas && originalCanvasDimensions[containerId]) {
                canvas.style.height = originalCanvasDimensions[containerId].height || '300px';
                canvas.style.maxHeight = originalCanvasDimensions[containerId].maxHeight || '';
                delete originalCanvasDimensions[containerId];
            }
            
            // Resize charts back to normal
            setTimeout(() => {
                if (priceChart) priceChart.resize();
                if (volumeChart) volumeChart.resize();
            }, 100);
        }
    };
    
    document.addEventListener('fullscreenchange', fullscreenChangeHandler);
    document.addEventListener('webkitfullscreenchange', fullscreenChangeHandler);
}

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

// Fullscreen date range functions
function setDateRangeFullscreen(value, unit, chartType) {
    const endDate = new Date();
    const startDate = new Date();
    
    if (value === 'all') {
        // Set start date to 10 years ago for "MAX" option
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
    
    // Update the fullscreen date inputs
    const startDateInput = document.getElementById(`fs-startDate-${chartType}`);
    const endDateInput = document.getElementById(`fs-endDate-${chartType}`);
    
    if (startDateInput && endDateInput) {
        startDateInput.value = formatDate(startDate);
        endDateInput.value = formatDate(endDate);
        
        // Also update the main date inputs
        document.getElementById('startDate').value = formatDate(startDate);
        document.getElementById('endDate').value = formatDate(endDate);
        
        // Reload the chart with new dates
        loadStockData();
    }
    
    // Update active state on preset buttons
    updatePresetButtonStates(chartType);
}

function applyCustomDateRange(chartType) {
    const startDateInput = document.getElementById(`fs-startDate-${chartType}`);
    const endDateInput = document.getElementById(`fs-endDate-${chartType}`);
    
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        // Update the main date inputs
        document.getElementById('startDate').value = startDateInput.value;
        document.getElementById('endDate').value = endDateInput.value;
        
        // Reload the chart with new dates
        loadStockData();
        
        // Clear active state from preset buttons
        updatePresetButtonStates(chartType);
    }
}

function updatePresetButtonStates(chartType) {
    // This would update the visual state of preset buttons to show which is active
    // For now, we'll just clear all active states when custom dates are applied
    const container = chartType === 'price' ? 
        document.getElementById('priceChartContainer') : 
        document.getElementById('volumeChartContainer');
    
    if (container) {
        const buttons = container.querySelectorAll('.date-preset-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
    }
}