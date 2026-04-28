/**
 * CBMText Data Visualization Module
 * Provides visualization utilities for transit/route data
 */

// Data Visualization Configuration
const VisualizationConfig = {
    colors: {
        primary: '#2563eb',
        secondary: '#7c3aed',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        neutral: '#6b7280'
    },
    animationDuration: 300,
    defaultWidth: 800,
    defaultHeight: 400
};

/**
 * Route Timeline Visualization
 * Displays routes as a horizontal timeline with stops
 */
class RouteTimeline {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = { ...VisualizationConfig, ...options };
        this.routes = [];
    }

    /**
     * Load route data from Python-exported JSON
     * @param {Array} routesData - Array of route objects
     */
    loadData(routesData) {
        this.routes = routesData;
        this.render();
    }

    render() {
        if (!this.container) {
            console.error(`Container #${this.containerId} not found`);
            return;
        }

        this.container.innerHTML = '';
        const svg = this.createSVG();
        this.container.appendChild(svg);
    }

    createSVG() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', this.options.defaultHeight);
        svg.setAttribute('viewBox', `0 0 ${this.options.defaultWidth} ${this.options.defaultHeight}`);

        // Draw timeline for each route
        const routeHeight = this.options.defaultHeight / (this.routes.length + 1);
        
        this.routes.forEach((route, index) => {
            const y = routeHeight * (index + 1);
            this.drawRouteLine(svg, route, y);
        });

        return svg;
    }

    drawRouteLine(svg, route, y) {
        const padding = 50;
        const lineWidth = this.options.defaultWidth - (padding * 2);
        
        // Main timeline line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padding);
        line.setAttribute('y1', y);
        line.setAttribute('x2', padding + lineWidth);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', this.options.colors.primary);
        line.setAttribute('stroke-width', '3');
        svg.appendChild(line);

        // Route label
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', 10);
        label.setAttribute('y', y + 5);
        label.setAttribute('fill', '#374151');
        label.setAttribute('font-weight', 'bold');
        label.textContent = route.name;
        svg.appendChild(label);

        // Draw stops
        if (route.stops && route.stops.length > 0) {
            const stopSpacing = lineWidth / (route.stops.length + 1);
            
            route.stops.forEach((stop, stopIndex) => {
                const x = padding + (stopSpacing * (stopIndex + 1));
                
                // Stop marker
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '8');
                circle.setAttribute('fill', this.options.colors.secondary);
                circle.setAttribute('class', 'stop-marker');
                svg.appendChild(circle);

                // Stop label
                const stopLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                stopLabel.setAttribute('x', x);
                stopLabel.setAttribute('y', y + 25);
                stopLabel.setAttribute('text-anchor', 'middle');
                stopLabel.setAttribute('fill', '#6b7280');
                stopLabel.setAttribute('font-size', '12');
                stopLabel.textContent = stop.name;
                svg.appendChild(stopLabel);
            });
        }
    }
}

/**
 * Statistics Dashboard
 * Displays key metrics and statistics
 */
class StatsDashboard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = { ...VisualizationConfig, ...options };
        this.stats = {};
    }

    /**
     * Update dashboard with new statistics
     * @param {Object} stats - Statistics object
     */
    update(stats) {
        this.stats = stats;
        this.render();
    }

    render() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="stats-grid">
                ${this.createStatCards()}
            </div>
        `;
    }

    createStatCards() {
        const cards = [];
        
        for (const [key, value] of Object.entries(this.stats)) {
            const label = this.formatLabel(key);
            const color = this.getStatColor(key);
            
            cards.push(`
                <div class="stat-card" style="border-left-color: ${color}">
                    <div class="stat-value" style="color: ${color}">${value}</div>
                    <div class="stat-label">${label}</div>
                </div>
            `);
        }
        
        return cards.join('');
    }

    formatLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    getStatColor(key) {
        const colorMap = {
            'routes': this.options.colors.primary,
            'stops': this.options.colors.secondary,
            'buses': this.options.colors.success,
            'delays': this.options.colors.danger,
            'passengers': this.options.colors.warning
        };
        return colorMap[key] || this.options.colors.neutral;
    }
}

/**
 * Bus Fleet Status Visualization
 * Shows current status of all buses
 */
class FleetStatus {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = { ...VisualizationConfig, ...options };
        this.buses = [];
    }

    /**
     * Load bus fleet data
     * @param {Array} busesData - Array of bus objects
     */
    loadData(busesData) {
        this.buses = busesData;
        this.render();
    }

    render() {
        if (!this.container) return;

        const statusCounts = this.getStatusCounts();
        
        this.container.innerHTML = `
            <div class="fleet-status">
                <h3>Fleet Status</h3>
                <div class="status-bars">
                    ${this.createStatusBars(statusCounts)}
                </div>
                <div class="bus-list">
                    ${this.createBusList()}
                </div>
            </div>
        `;
    }

    getStatusCounts() {
        const counts = { active: 0, idle: 0, maintenance: 0 };
        
        this.buses.forEach(bus => {
            const status = bus.status || 'idle';
            if (counts.hasOwnProperty(status)) {
                counts[status]++;
            } else {
                counts.idle++;
            }
        });
        
        return counts;
    }

    createStatusBars(counts) {
        const total = this.buses.length || 1;
        
        return `
            <div class="status-bar-container">
                <div class="status-bar active" style="width: ${(counts.active / total) * 100}%"></div>
                <div class="status-bar idle" style="width: ${(counts.idle / total) * 100}%"></div>
                <div class="status-bar maintenance" style="width: ${(counts.maintenance / total) * 100}%"></div>
            </div>
            <div class="status-legend">
                <span><span class="dot active"></span> Active: ${counts.active}</span>
                <span><span class="dot idle"></span> Idle: ${counts.idle}</span>
                <span><span class="dot maintenance"></span> Maintenance: ${counts.maintenance}</span>
            </div>
        `;
    }

    createBusList() {
        return this.buses.map(bus => `
            <div class="bus-item">
                <span class="bus-id">Bus #${bus.id || bus.bus_id}</span>
                <span class="bus-status ${bus.status || 'idle'}">${bus.status || 'idle'}</span>
                <span class="bus-route">${bus.route || 'Unassigned'}</span>
            </div>
        `).join('');
    }
}

/**
 * Export data to JSON for Python consumption
 */
const DataExporter = {
    /**
     * Export visualization data to JSON file
     * @param {Object} data - Data to export
     * @param {string} filename - Output filename
     */
    toJSON(data, filename) {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
    },

    /**
     * Import data from JSON file
     * @param {File} file - JSON file to import
     * @returns {Promise<Object>}
     */
    fromJSON(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    resolve(JSON.parse(e.target.result));
                } catch (err) {
                    reject(err);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }
};

// CSS Styles (inject into page)
const visualizationStyles = `
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        padding: 16px;
    }
    
    .stat-card {
        background: #fff;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: bold;
    }
    
    .stat-label {
        color: #6b7280;
        font-size: 14px;
        margin-top: 4px;
    }
    
    .fleet-status h3 {
        margin: 0 0 16px 0;
        color: #374151;
    }
    
    .status-bar-container {
        display: flex;
        height: 24px;
        border-radius: 4px;
        overflow: hidden;
        background: #e5e7eb;
    }
    
    .status-bar {
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .status-bar.active { background: #10b981; }
    .status-bar.idle { background: #6b7280; }
    .status-bar.maintenance { background: #f59e0b; }
    
    .status-legend {
        display: flex;
        gap: 16px;
        margin-top: 8px;
        font-size: 12px;
    }
    
    .dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 4px;
    }
    
    .dot.active { background: #10b981; }
    .dot.idle { background: #6b7280; }
    .dot.maintenance { background: #f59e0b; }
    
    .bus-list {
        margin-top: 16px;
    }
    
    .bus-item {
        display: flex;
        justify-content: space-between;
        padding: 8px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .bus-status {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    
    .bus-status.active { background: #d1fae5; color: #065f46; }
    .bus-status.idle { background: #f3f4f6; color: #374151; }
    .bus-status.maintenance { background: #fef3c7; color: #92400e; }
    
    .stop-marker {
        cursor: pointer;
        transition: r 0.2s ease;
    }
    
    .stop-marker:hover {
        r: 12;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = visualizationStyles;
document.head.appendChild(styleSheet);

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RouteTimeline, StatsDashboard, FleetStatus, DataExporter, VisualizationConfig };
}
