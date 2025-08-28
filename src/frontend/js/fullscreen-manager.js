// fullscreen-manager.js - Modular fullscreen functionality for charts

/**
 * ResizableChart class for handling resize and drag functionality in fullscreen
 */
class ResizableChart {
    constructor(containerId, chart, plotConfig) {
        this.container = document.getElementById(containerId);
        this.chart = chart; // Chart.js instance
        this.plotConfig = plotConfig || {};
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
        if (!this.container) {
            console.error('Container not found for ResizableChart');
            return;
        }
        
        // Create wrapper for the chart
        this.createWrapper();
        // Add resize handles
        this.createResizeHandles();
        // Set up event listeners
        this.setupEventListeners();
        // Position the wrapper initially
        this.setInitialPosition();
    }
    
    createWrapper() {
        const formulaBox = this.container.querySelector('.formula-box');
        if (!formulaBox) {
            console.error('Formula box not found in container');
            return;
        }
        
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
        if (formulaBox) {
            formulaBox.addEventListener('mousedown', this.startDrag.bind(this));
            formulaBox.addEventListener('touchstart', this.startDrag.bind(this), { passive: false });
        }
        
        // Global mouse/touch events
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        document.addEventListener('touchmove', this.handleMouseMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleMouseUp.bind(this));
    }
    
    setInitialPosition() {
        const containerRect = this.container.getBoundingClientRect();
        const sidebarWidth = this.plotConfig.sidebar?.width || 250;
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
        // Don't start drag if clicking on interactive elements
        if (e.target.closest('button') || 
            e.target.closest('input') || 
            e.target.closest('.resize-handle') ||
            e.target.closest('.exit-fullscreen-btn')) {
            return;
        }
        
        // Don't drag if it's a chart interaction
        if (e.target.tagName === 'CANVAS') {
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
        const sidebarWidth = this.plotConfig.sidebar?.width || 250;
        const maxWidth = (containerRect.width - sidebarWidth) * this.maxWidthPercent;
        const maxHeight = containerRect.height * this.maxHeightPercent;
        
        let newWidth = this.startWidth;
        let newHeight = this.startHeight;
        let newLeft = this.startLeft;
        let newTop = this.startTop;
        
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
        const sidebarWidth = this.plotConfig.sidebar?.width || 250;
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
            this.updateChartSize();
        }
        
        if (this.isDragging) {
            this.isDragging = false;
            this.wrapper.classList.remove('dragging');
        }
    }
    
    throttledUpdateChart() {
        if (!this.updateTimeout) {
            this.updateTimeout = setTimeout(() => {
                this.updateChartSize();
                this.updateTimeout = null;
            }, 50);
        }
    }
    
    updateChartSize() {
        if (this.chart) {
            requestAnimationFrame(() => {
                this.chart.resize();
            });
        }
    }
    
    destroy() {
        // Clean up event listeners
        if (this.wrapper) {
            const handles = this.wrapper.querySelectorAll('.resize-handle');
            handles.forEach(handle => {
                handle.removeEventListener('mousedown', this.startResize.bind(this));
                handle.removeEventListener('touchstart', this.startResize.bind(this));
            });
            
            const formulaBox = this.wrapper.querySelector('.formula-box');
            if (formulaBox) {
                formulaBox.removeEventListener('mousedown', this.startDrag.bind(this));
                formulaBox.removeEventListener('touchstart', this.startDrag.bind(this));
                
                // Move formula box back to container
                if (this.container) {
                    this.container.appendChild(formulaBox);
                }
            }
            
            // Remove wrapper
            if (this.wrapper.parentNode) {
                this.wrapper.remove();
            }
        }
    }
}

/**
 * FullscreenManager class for managing fullscreen charts with plot configurations
 */
class FullscreenManager {
    constructor() {
        this.activeInstance = null;
        this.originalCanvasDimensions = {};
        this.fullscreenListeners = new Map();
    }

    /**
     * Toggle fullscreen for a chart
     * @param {string} containerId - Container element ID
     * @param {string} plotId - Plot type ID from plot configuration
     * @param {Object} chart - Chart.js instance
     * @param {Object} options - Additional options
     */
    toggleFullscreen(containerId, plotId, chart, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
            this.enterFullscreen(containerId, plotId, chart, options);
        } else {
            this.exitFullscreen();
        }
    }

    /**
     * Enter fullscreen mode
     * @param {string} containerId - Container element ID
     * @param {string} plotId - Plot type ID
     * @param {Object} chart - Chart.js instance
     * @param {Object} options - Additional options
     */
    enterFullscreen(containerId, plotId, chart, options = {}) {
        const container = document.getElementById(containerId);
        const plotConfig = PlotConfig.get(plotId);
        
        if (!plotConfig || !plotConfig.fullscreenEnabled) {
            console.warn(`Fullscreen not enabled for plot type: ${plotId}`);
            return;
        }

        // Request fullscreen
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
            container.msRequestFullscreen();
        }

        // Store original canvas dimensions
        const canvas = container.querySelector('canvas');
        if (canvas) {
            this.originalCanvasDimensions[containerId] = {
                height: canvas.style.height || '',
                maxHeight: canvas.style.maxHeight || ''
            };
            canvas.style.height = 'calc(100vh - 6rem)';
            canvas.style.maxHeight = 'calc(100vh - 6rem)';
        }

        // Set up fullscreen-specific functionality
        setTimeout(() => {
            this.setupFullscreenUI(containerId, plotId, chart, options);
        }, 100);
    }

    /**
     * Set up fullscreen UI (sidebar, listeners, etc.)
     * @param {string} containerId - Container element ID
     * @param {string} plotId - Plot type ID
     * @param {Object} chart - Chart.js instance
     * @param {Object} options - Additional options
     */
    setupFullscreenUI(containerId, plotId, chart, options = {}) {
        const container = document.getElementById(containerId);
        const plotConfig = PlotConfig.get(plotId);
        
        if (!container || !plotConfig) return;

        // Create and populate sidebar
        this.createSidebar(container, plotId, containerId, options);
        
        // Initialize resizable chart only if enabled in configuration
        if (plotConfig.resizable === true) {
            this.activeInstance = new ResizableChart(containerId, chart, plotConfig);
        }
        
        // Set up fullscreen exit listener
        this.setupExitListener(containerId);
        
        // Resize chart
        if (chart) {
            setTimeout(() => chart.resize(), 50);
        }
    }

    /**
     * Create and populate fullscreen sidebar
     * @param {HTMLElement} container - Container element
     * @param {string} plotId - Plot type ID
     * @param {string} containerId - Container element ID for unique IDs
     * @param {Object} options - Additional options
     */
    createSidebar(container, plotId, containerId, options = {}) {
        // Check if sidebar already exists
        let sidebar = container.querySelector('.fullscreen-sidebar');
        if (!sidebar) {
            sidebar = document.createElement('div');
            sidebar.className = 'fullscreen-sidebar';
            sidebar.style.display = 'none';
            container.appendChild(sidebar);
        }

        // Generate exit button
        sidebar.innerHTML = `
            <button class="exit-fullscreen-btn" onclick="FullscreenManager.instance.exitFullscreen()" title="Exit Fullscreen">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                </svg>
            </button>
            <div class="sidebar-content">
                <h3>Chart Options</h3>
                ${PlotConfig.generateSidebarHTML(plotId, containerId)}
            </div>
        `;

        // Set up option listeners
        this.setupOptionListeners(sidebar, plotId, containerId, options);
        
        // Show sidebar in fullscreen
        if (container.matches(':fullscreen') || container.matches(':-webkit-full-screen')) {
            sidebar.style.display = 'block';
        }
    }

    /**
     * Set up event listeners for sidebar options
     * @param {HTMLElement} sidebar - Sidebar element
     * @param {string} plotId - Plot type ID
     * @param {string} containerId - Container element ID
     * @param {Object} options - Additional options including callbacks
     */
    setupOptionListeners(sidebar, plotId, containerId, options = {}) {
        const plotConfig = PlotConfig.get(plotId);
        if (!plotConfig) return;

        // Sync with existing form inputs if they exist
        this.syncWithMainInputs(sidebar, containerId);

        // Set up control listeners with reactive updates
        const enabledOptions = PlotConfig.getEnabledOptions(plotId);
        
        Object.keys(enabledOptions).forEach(optionKey => {
            const option = enabledOptions[optionKey];
            
            if (option.controls && option.controls.length > 0) {
                option.controls.forEach(control => {
                    const checkbox = sidebar.querySelector(`#fs-${control.id}-${containerId}`);
                    if (checkbox) {
                        checkbox.addEventListener('change', () => {
                            // Sync with main checkbox if it exists
                            const mainCheckbox = document.getElementById(control.id);
                            if (mainCheckbox) {
                                mainCheckbox.checked = checkbox.checked;
                                
                                // Trigger reactive update if function exists
                                this.triggerReactiveUpdate(control.id, checkbox.checked);
                            }
                            
                            // Call custom callback if provided
                            if (options.onControlChange) {
                                options.onControlChange(control.id, checkbox.checked, optionKey);
                            }
                        });
                    }
                });
            }
        });
    }

    /**
     * Trigger reactive chart update from fullscreen sidebar with consistent styling
     * @param {string} controlId - Control ID (e.g., 'stockPrice', 'ma5', etc.)
     * @param {boolean} checked - New checkbox state
     */
    triggerReactiveUpdate(controlId, checked) {
        // Map control IDs to dataset types
        const controlToDatasetMap = {
            'stockPrice': 'price',
            'ma5': 'ma5',
            'ma20': 'ma20',
            'ma40': 'ma40'
        };
        
        const datasetType = controlToDatasetMap[controlId];
        if (datasetType && typeof reactiveToggleDataset === 'function') {
            // Trigger the reactive update with style consistency
            reactiveToggleDataset(datasetType);
        } else if (datasetType && typeof priceChart !== 'undefined' && priceChart) {
            // Fallback: Direct chart update with style preservation
            this.updateChartDatasetDirectly(datasetType, checked);
        }
    }

    /**
     * Direct chart update with style preservation (fallback method)
     * @param {string} datasetType - Dataset type
     * @param {boolean} visible - Whether dataset should be visible
     */
    updateChartDatasetDirectly(datasetType, visible) {
        if (!priceChart) return;
        
        // Use global CHART_STYLES if available
        const styles = window.CHART_STYLES || {};
        
        const datasetLabels = {
            'price': 'Close Price',
            'ma5': '5-Day MA',
            'ma20': '20-Day MA',
            'ma40': '40-Day MA'
        };
        
        const label = datasetLabels[datasetType];
        const datasetIndex = priceChart.data.datasets.findIndex(ds => ds.label === label);
        
        if (datasetIndex !== -1) {
            const dataset = priceChart.data.datasets[datasetIndex];
            
            // Restore consistent styling
            if (styles[datasetType]) {
                Object.assign(dataset, styles[datasetType]);
            }
            
            // Set visibility
            priceChart.getDatasetMeta(datasetIndex).hidden = !visible;
            
            // Update without animation to preserve styling
            priceChart.update('none');
        }
    }

    /**
     * Sync sidebar inputs with main form inputs
     * @param {HTMLElement} sidebar - Sidebar element
     * @param {string} containerId - Container element ID
     */
    syncWithMainInputs(sidebar, containerId) {
        // Sync date inputs
        const fsStartDate = sidebar.querySelector(`#fs-startDate-${containerId}`);
        const fsEndDate = sidebar.querySelector(`#fs-endDate-${containerId}`);
        
        if (fsStartDate && fsEndDate) {
            const mainStartDate = document.getElementById('startDate');
            const mainEndDate = document.getElementById('endDate');
            
            if (mainStartDate && mainEndDate) {
                fsStartDate.value = mainStartDate.value;
                fsEndDate.value = mainEndDate.value;
            }
        }

        // Sync checkboxes - find all fullscreen checkboxes and sync with main ones
        const fsCheckboxes = sidebar.querySelectorAll('input[type="checkbox"]');
        fsCheckboxes.forEach(fsCheckbox => {
            const id = fsCheckbox.id.replace(`fs-`, '').replace(`-${containerId}`, '');
            const mainCheckbox = document.getElementById(id);
            if (mainCheckbox) {
                fsCheckbox.checked = mainCheckbox.checked;
            }
        });
    }

    /**
     * Set up fullscreen exit listener
     * @param {string} containerId - Container element ID
     */
    setupExitListener(containerId) {
        const fullscreenChangeHandler = () => {
            if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                this.cleanup(containerId);
                document.removeEventListener('fullscreenchange', fullscreenChangeHandler);
                document.removeEventListener('webkitfullscreenchange', fullscreenChangeHandler);
                this.fullscreenListeners.delete(containerId);
            }
        };

        document.addEventListener('fullscreenchange', fullscreenChangeHandler);
        document.addEventListener('webkitfullscreenchange', fullscreenChangeHandler);
        this.fullscreenListeners.set(containerId, fullscreenChangeHandler);
    }

    /**
     * Exit fullscreen mode
     */
    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }

    /**
     * Clean up fullscreen resources
     * @param {string} containerId - Container element ID
     */
    cleanup(containerId) {
        // Destroy resizable chart instance
        if (this.activeInstance) {
            this.activeInstance.destroy();
            this.activeInstance = null;
        }

        // Restore canvas dimensions
        const container = document.getElementById(containerId);
        if (container) {
            const canvas = container.querySelector('canvas');
            if (canvas && this.originalCanvasDimensions[containerId]) {
                canvas.style.height = this.originalCanvasDimensions[containerId].height || '300px';
                canvas.style.maxHeight = this.originalCanvasDimensions[containerId].maxHeight || '';
                delete this.originalCanvasDimensions[containerId];
            }

            // Hide sidebar
            const sidebar = container.querySelector('.fullscreen-sidebar');
            if (sidebar) {
                sidebar.style.display = 'none';
            }
        }

        // Trigger chart resize
        setTimeout(() => {
            // Look for chart instances in common global variables
            if (typeof priceChart !== 'undefined' && priceChart) priceChart.resize();
            if (typeof volumeChart !== 'undefined' && volumeChart) volumeChart.resize();
            if (typeof returnsChart !== 'undefined' && returnsChart) returnsChart.resize();
        }, 100);
    }

    /**
     * Create fullscreen button HTML
     * @param {string} containerId - Container element ID
     * @param {string} plotId - Plot type ID
     * @returns {string} HTML for fullscreen button
     */
    static createFullscreenButton(containerId, plotId) {
        return `
            <button class="fullscreen-btn" onclick="FullscreenManager.instance.toggleFullscreen('${containerId}', '${plotId}', window.${plotId === 'stock-prices' ? 'priceChart' : plotId === 'volume' ? 'volumeChart' : 'chart'})" title="Fullscreen">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                </svg>
            </button>
        `;
    }
}

// Create global instance
const fullscreenManagerInstance = new FullscreenManager();

// Export for browser use
if (typeof window !== 'undefined') {
    window.ResizableChart = ResizableChart;
    window.FullscreenManager = FullscreenManager;
    window.FullscreenManager.instance = fullscreenManagerInstance;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ResizableChart, FullscreenManager };
}