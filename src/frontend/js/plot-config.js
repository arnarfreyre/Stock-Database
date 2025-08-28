// plot-config.js - Centralized configuration for all plot types and their options

/**
 * Plot Configuration System
 * Defines available plot types, their fullscreen capabilities, and configurable options
 */
const plotConfigs = {
    'stock-prices': {
        id: 'stock-prices',
        title: 'Stock Prices',
        fullscreenEnabled: true,
        resizable: true,  // Enable chart resizing in fullscreen
        chartVariable: 'priceChart',  // Global variable name for the chart instance
        chartType: 'line',
        options: {
            movingAverages: {
                enabled: true,
                label: 'Data Series',
                controls: [
                    { id: 'stockPrice', label: 'Stock Price', defaultEnabled: true, color: '#e74c3c' },
                    { id: 'ma5', label: '5-Day MA', defaultEnabled: true, color: '#3498db' },
                    { id: 'ma20', label: '20-Day MA', defaultEnabled: true, color: '#27ae60' },
                    { id: 'ma40', label: '40-Day MA', defaultEnabled: true, color: '#9b59b6' }
                ]
            },
            dateRange: {
                enabled: true,
                label: 'Date Range',
                presets: [
                    { id: '3months', label: '3M', value: 3, unit: 'months' },
                    { id: '6months', label: '6M', value: 6, unit: 'months' },
                    { id: '1year', label: '1Y', value: 1, unit: 'year' },
                    { id: '2years', label: '2Y', value: 2, unit: 'years' },
                    { id: '5years', label: '5Y', value: 5, unit: 'years' },
                    { id: 'max', label: 'MAX', value: 'all', unit: null }
                ],
                customEnabled: true
            },
            technicalIndicators: {
                enabled: false, // Future expansion
                label: 'Technical Indicators',
                controls: []
            }
        },
        sidebar: {
            width: 250,
            backgroundColor: 'linear-gradient(to bottom, rgba(20, 20, 20, 0.95), rgba(30, 30, 30, 0.95))'
        }
    },

    'volume': {
        id: 'volume',
        title: 'Trading Volume', 
        fullscreenEnabled: true,
        resizable: true,  // Enable chart resizing in fullscreen
        chartVariable: 'volumeChart',  // Global variable name for the chart instance
        chartType: 'bar',
        options: {
            movingAverages: {
                enabled: false // No moving averages for volume charts
            },
            dateRange: {
                enabled: true,
                label: 'Date Range',
                presets: [
                    { id: '3months', label: '3M', value: 3, unit: 'months' },
                    { id: '6months', label: '6M', value: 6, unit: 'months' },
                    { id: '1year', label: '1Y', value: 1, unit: 'year' },
                    { id: '2years', label: '2Y', value: 2, unit: 'years' },
                    { id: '5years', label: '5Y', value: 5, unit: 'years' },
                    { id: 'max', label: 'MAX', value: 'all', unit: null }
                ],
                customEnabled: true
            },
            volumeIndicators: {
                enabled: true,
                label: 'Display Options',
                controls: [
                    { id: 'volumeBars', label: 'Volume Bars', defaultEnabled: true, color: '#3498db' },
                    { id: 'avgVolume', label: 'Average Volume Line', defaultEnabled: false, color: '#e67e22', disabled: true }
                ]
            },
            technicalIndicators: {
                enabled: false, // Future expansion
                label: 'Volume Indicators',
                controls: []
            }
        },
        sidebar: {
            width: 250,
            backgroundColor: 'linear-gradient(to bottom, rgba(20, 20, 20, 0.95), rgba(30, 30, 30, 0.95))'
        }
    },

    'cumulative-returns': {
        id: 'cumulative-returns',
        title: 'Cumulative Returns',
        fullscreenEnabled: true,
        resizable: true,  // Disable chart resizing in fullscreen
        chartVariable: 'returnsChart',  // Global variable name for the chart instance
        chartType: 'line',
        options: {
            movingAverages: {
                enabled: false // Not applicable for returns analysis
            },
            dateRange: {
                enabled: true,
                label: 'Date Range',
                presets: [
                    { id: '3months', label: '3M', value: 3, unit: 'months' },
                    { id: '6months', label: '6M', value: 6, unit: 'months' },
                    { id: '1year', label: '1Y', value: 1, unit: 'year' },
                    { id: '2years', label: '2Y', value: 2, unit: 'years' },
                    { id: '5years', label: '5Y', value: 5, unit: 'years' },
                    { id: 'max', label: 'MAX', value: 'all', unit: null }
                ],
                customEnabled: true
            },
            returnTypes: {
                enabled: true,
                label: 'Return Types',
                controls: [
                    { id: 'overnight', label: 'Overnight (Close → Open)', defaultEnabled: true, color: '#3498db' },
                    { id: 'intraday', label: 'Intraday (Open → Close)', defaultEnabled: true, color: '#f39c12' },
                    { id: 'combined', label: 'Combined Returns', defaultEnabled: false, color: '#27ae60' }
                ]
            },
            performanceMetrics: {
                enabled: false, // Future expansion
                label: 'Performance Metrics',
                controls: []
            }
        },
        sidebar: {
            width: 250,
            backgroundColor: 'linear-gradient(to bottom, rgba(20, 20, 20, 0.95), rgba(30, 30, 30, 0.95))'
        }
    },

    'volatility': {
        id: 'volatility',
        title: 'Volatility Analysis',
        fullscreenEnabled: true,
        resizable: false,  // Disable chart resizing in fullscreen
        chartVariable: 'termStructureChart',  // Global variable name for the chart instance
        chartType: 'line',
        options: {
            movingAverages: {
                enabled: false
            },
            dateRange: {
                enabled: true,
                label: 'Date Range', 
                presets: [
                    { id: '3months', label: '3M', value: 3, unit: 'months' },
                    { id: '6months', label: '6M', value: 6, unit: 'months' },
                    { id: '1year', label: '1Y', value: 1, unit: 'year' },
                    { id: '2years', label: '2Y', value: 2, unit: 'years' },
                    { id: '5years', label: '5Y', value: 5, unit: 'years' },
                    { id: 'max', label: 'MAX', value: 'all', unit: null }
                ],
                customEnabled: true
            },
            volatilityTypes: {
                enabled: true,
                label: 'Volatility Measures',
                controls: [
                    { id: 'dailyVol', label: 'Daily Volatility', defaultEnabled: true, color: '#e74c3c' },
                    { id: 'weeklyVol', label: 'Weekly Volatility', defaultEnabled: false, color: '#3498db' },
                    { id: 'monthlyVol', label: 'Monthly Volatility', defaultEnabled: false, color: '#27ae60' },
                    { id: 'annualizedVol', label: 'Annualized Volatility', defaultEnabled: true, color: '#9b59b6' }
                ]
            }
        },
        sidebar: {
            width: 250,
            backgroundColor: 'linear-gradient(to bottom, rgba(20, 20, 20, 0.95), rgba(30, 30, 30, 0.95))'
        }
    }
};

/**
 * Utility functions for working with plot configurations
 */
const PlotConfig = {
    /**
     * Get configuration for a specific plot type
     * @param {string} plotId - The plot type identifier
     * @returns {Object|null} Plot configuration or null if not found
     */
    get(plotId) {
        return plotConfigs[plotId] || null;
    },

    /**
     * Check if a plot type supports fullscreen
     * @param {string} plotId - The plot type identifier  
     * @returns {boolean} True if fullscreen is enabled
     */
    isFullscreenEnabled(plotId) {
        const config = this.get(plotId);
        return config ? config.fullscreenEnabled : false;
    },

    /**
     * Get enabled options for a plot type
     * @param {string} plotId - The plot type identifier
     * @returns {Object} Enabled options object
     */
    getEnabledOptions(plotId) {
        const config = this.get(plotId);
        if (!config) return {};
        
        const enabledOptions = {};
        Object.keys(config.options).forEach(optionKey => {
            if (config.options[optionKey].enabled) {
                enabledOptions[optionKey] = config.options[optionKey];
            }
        });
        
        return enabledOptions;
    },

    /**
     * Get default control states for a plot type
     * @param {string} plotId - The plot type identifier
     * @returns {Object} Default states for all controls
     */
    getDefaultStates(plotId) {
        const config = this.get(plotId);
        if (!config) return {};
        
        const defaultStates = {};
        Object.keys(config.options).forEach(optionKey => {
            const option = config.options[optionKey];
            if (option.enabled && option.controls) {
                option.controls.forEach(control => {
                    defaultStates[control.id] = control.defaultEnabled || false;
                });
            }
        });
        
        return defaultStates;
    },

    /**
     * Generate HTML for fullscreen sidebar options
     * @param {string} plotId - The plot type identifier
     * @param {string} chartType - Chart identifier for unique element IDs
     * @returns {string} HTML string for sidebar options
     */
    generateSidebarHTML(plotId, chartType) {
        const config = this.get(plotId);
        if (!config) return '';
        
        let html = '';
        const enabledOptions = this.getEnabledOptions(plotId);
        
        Object.keys(enabledOptions).forEach(optionKey => {
            const option = enabledOptions[optionKey];
            
            if (optionKey === 'dateRange') {
                html += this._generateDateRangeHTML(option, chartType);
            } else if (option.controls && option.controls.length > 0) {
                html += this._generateControlsHTML(option, chartType);
            }
        });
        
        return html;
    },

    /**
     * Generate date range section HTML
     * @private
     */
    _generateDateRangeHTML(option, chartType) {
        let html = `
            <div class="sidebar-section">
                <h4 class="sidebar-section-title">${option.label}</h4>
                <div class="date-preset-buttons">`;
        
        option.presets.forEach(preset => {
            html += `<button class="date-preset-btn" onclick="PlotConfig.setDateRangeWithDarkPreservation('${preset.value}', '${preset.unit}', '${chartType}')">${preset.label}</button>`;
        });
        
        html += `</div>`;
        
        if (option.customEnabled) {
            html += `
                <div class="manual-date-selection">
                    <div class="date-input-group">
                        <label>From:</label>
                        <input type="date" id="fs-startDate-${chartType}" class="fs-date-input">
                    </div>
                    <div class="date-input-group">
                        <label>To:</label>
                        <input type="date" id="fs-endDate-${chartType}" class="fs-date-input">
                    </div>
                    <button class="apply-date-btn" onclick="PlotConfig.applyCustomDateRangeWithDarkPreservation('${chartType}')">Apply</button>
                </div>`;
        }
        
        html += `</div>`;
        return html;
    },

    /**
     * Generate controls section HTML
     * @private
     */
    _generateControlsHTML(option, chartType) {
        let html = `
            <div class="sidebar-section">
                <h4 class="sidebar-section-title">${option.label}</h4>
                <div class="sidebar-options">`;
        
        option.controls.forEach(control => {
            const checked = control.defaultEnabled ? 'checked' : '';
            const disabled = control.disabled ? 'disabled' : '';
            html += `
                <label class="sidebar-option">
                    <input type="checkbox" id="fs-${control.id}-${chartType}" ${checked} ${disabled}>
                    <span>${control.label}</span>
                </label>`;
        });
        
        html += `
                </div>
            </div>`;
        return html;
    },

    /**
     * Set date range with dark background preservation (called from generated buttons)
     * @param {string|number} value - Date range value
     * @param {string|null} unit - Date unit (months, years, etc.)
     * @param {string} chartType - Chart identifier
     */
    setDateRangeWithDarkPreservation(value, unit, chartType) {
        // Preserve dark backgrounds before and after date range change
        this._preserveDarkBackgroundDuringUpdate();
        
        this.setDateRange(value, unit, chartType);
        
        // Re-apply dark backgrounds after a short delay
        setTimeout(() => {
            this._preserveDarkBackgroundDuringUpdate();
        }, 100);
    },

    /**
     * Set date range (called from generated buttons)
     * @param {string|number} value - Date range value
     * @param {string|null} unit - Date unit (months, years, etc.)
     * @param {string} chartType - Chart identifier
     */
    setDateRange(value, unit, chartType) {
        const endDate = new Date();
        const startDate = new Date();
        
        if (value === 'all') {
            startDate.setFullYear(startDate.getFullYear() - 10);
        } else if (unit === 'months') {
            startDate.setMonth(startDate.getMonth() - value);
        } else if (unit === 'year') {
            startDate.setFullYear(startDate.getFullYear() - value);
        } else if (unit === 'years') {
            startDate.setFullYear(startDate.getFullYear() - value);
        }
        
        // Update fullscreen date inputs
        const startInput = document.getElementById(`fs-startDate-${chartType}`);
        const endInput = document.getElementById(`fs-endDate-${chartType}`);
        
        if (startInput && endInput) {
            startInput.value = this._formatDate(startDate);
            endInput.value = this._formatDate(endDate);
            
            // Update main date inputs if they exist
            const mainStartInput = document.getElementById('startDate');
            const mainEndInput = document.getElementById('endDate');
            if (mainStartInput && mainEndInput) {
                mainStartInput.value = this._formatDate(startDate);
                mainEndInput.value = this._formatDate(endDate);
            }
            
            // Trigger chart update
            this._triggerChartUpdate();
        }
    },

    /**
     * Apply custom date range with dark background preservation
     * @param {string} chartType - Chart identifier
     */
    applyCustomDateRangeWithDarkPreservation(chartType) {
        // Preserve dark backgrounds before and after date range change
        this._preserveDarkBackgroundDuringUpdate();
        
        this.applyCustomDateRange(chartType);
        
        // Re-apply dark backgrounds after a short delay
        setTimeout(() => {
            this._preserveDarkBackgroundDuringUpdate();
        }, 100);
    },

    /**
     * Apply custom date range
     * @param {string} chartType - Chart identifier
     */
    applyCustomDateRange(chartType) {
        const startInput = document.getElementById(`fs-startDate-${chartType}`);
        const endInput = document.getElementById(`fs-endDate-${chartType}`);
        
        if (startInput && endInput && startInput.value && endInput.value) {
            // Update main date inputs if they exist
            const mainStartInput = document.getElementById('startDate');
            const mainEndInput = document.getElementById('endDate');
            if (mainStartInput && mainEndInput) {
                mainStartInput.value = startInput.value;
                mainEndInput.value = endInput.value;
            }
            
            // Trigger chart update
            this._triggerChartUpdate();
        }
    },

    /**
     * Format date for input
     * @private
     */
    _formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    },

    /**
     * Trigger chart update with style consistency preservation and white flash prevention
     * @private
     */
    _triggerChartUpdate() {
        // Preserve dark backgrounds during update
        this._preserveDarkBackgroundDuringUpdate();
        
        // Look for common update functions in global scope
        if (typeof loadStockData === 'function') {
            loadStockData(); // For index.html
            
            // Ensure style consistency after reload
            setTimeout(() => {
                if (typeof ensureChartStyleConsistency === 'function') {
                    ensureChartStyleConsistency();
                }
                this._preserveDarkBackgroundDuringUpdate(); // Reapply after update
            }, 100);
        } else if (typeof calculateReturns === 'function') {
            calculateReturns(); // For cumulative-returns.html
        } else if (typeof updateChart === 'function') {
            updateChart(); // Generic fallback
        }
    },

    /**
     * Preserve dark backgrounds during chart updates but keep canvas white
     * @private
     */
    _preserveDarkBackgroundDuringUpdate() {
        // Find all fullscreen containers
        const fullscreenContainers = document.querySelectorAll('.chart-container:fullscreen, .chart-container:-webkit-full-screen');
        
        fullscreenContainers.forEach(container => {
            // Apply dark background to container
            container.style.background = '#1a1a1a';
            
            // Apply dark background to formula box
            const formulaBox = container.querySelector('.formula-box');
            if (formulaBox) {
                formulaBox.style.background = '#1a1a1a';
                formulaBox.style.transition = 'none';
            }
            
            // Keep canvas white - remove any dark background overrides
            const canvas = container.querySelector('canvas');
            if (canvas) {
                canvas.style.background = '';
                canvas.style.backgroundColor = '';
                canvas.style.transition = 'none';
            }
        });
    },

    /**
     * Trigger reactive chart option updates with consistent styling
     * @param {string} controlId - Control ID that was changed
     * @param {boolean} checked - New state of the control
     */
    triggerReactiveUpdate(controlId, checked) {
        // Map control IDs to dataset types for reactive updates
        const controlToDatasetMap = {
            'stockPrice': 'price',
            'ma5': 'ma5', 
            'ma20': 'ma20',
            'ma40': 'ma40'
        };
        
        const datasetType = controlToDatasetMap[controlId];
        if (datasetType && typeof reactiveToggleDataset === 'function') {
            reactiveToggleDataset(datasetType);
            
            // Ensure style consistency after reactive update
            setTimeout(() => {
                if (typeof ensureChartStyleConsistency === 'function') {
                    ensureChartStyleConsistency();
                }
            }, 50);
        }
    },

    /**
     * Get all available plot types
     * @returns {Array} Array of plot type IDs
     */
    getAllPlotTypes() {
        return Object.keys(plotConfigs);
    },

    /**
     * Validate plot configuration
     * @param {string} plotId - The plot type identifier
     * @returns {boolean} True if configuration is valid
     */
    validate(plotId) {
        const config = this.get(plotId);
        if (!config) return false;
        
        // Basic validation
        return !!(config.id && config.title && typeof config.fullscreenEnabled === 'boolean');
    }
};

// Make configs available globally
(function() {
    if (typeof window !== 'undefined') {
        // Using bracket notation to avoid linter false positives
        window['plotConfigs'] = plotConfigs;
        window['PlotConfig'] = PlotConfig;
    }
})();