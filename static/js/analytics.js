/**
 * Analytics Dashboard JavaScript
 * Handles data fetching, chart rendering, and user interactions
 */

let currentPeriod = 'day';
let charts = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function () {
    loadAnalytics();
});

/**
 * Change time period and reload data
 */
function changePeriod(period) {
    currentPeriod = period;

    // Update button states
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${period}`).classList.add('active');

    // Reload analytics
    loadAnalytics();
}

/**
 * Load all analytics data
 */
async function loadAnalytics() {
    try {
        // Load statistics
        await loadStats();

        // Load chart data
        await loadChartData();

        // Load recent activity
        await loadRecentActivity();

    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

/**
 * Load statistics summary
 */
async function loadStats() {
    try {
        const response = await fetch(`/analytics/api/stats?period=${currentPeriod}`);
        const result = await response.json();

        if (result.success) {
            const stats = result.data;

            // Update stat cards
            document.getElementById('stat-total').textContent = stats.total_usage || 0;
            document.getElementById('stat-success').textContent = `${stats.success_rate || 0}%`;
            document.getElementById('stat-categories').textContent = Object.keys(stats.categories || {}).length;

            // Update top feature
            if (stats.top_features && stats.top_features.length > 0) {
                const topFeature = stats.top_features[0];
                document.getElementById('stat-top-feature').textContent = formatFeatureName(topFeature.name);
                document.getElementById('stat-top-count').textContent = `${topFeature.count} uses`;
            } else {
                document.getElementById('stat-top-feature').textContent = '-';
                document.getElementById('stat-top-count').textContent = '0 uses';
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Load and render charts
 */
async function loadChartData() {
    try {
        const response = await fetch(`/analytics/api/data?period=${currentPeriod}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // Render trend chart
            renderTrendChart(data.daily_trend);

            // Load features for top features chart
            const featuresResponse = await fetch('/analytics/api/features');
            const featuresResult = await featuresResponse.json();

            if (featuresResult.success) {
                renderFeaturesChart(featuresResult.data);
            }

            // Render category chart
            const statsResponse = await fetch(`/analytics/api/stats?period=${currentPeriod}`);
            const statsResult = await statsResponse.json();

            if (statsResult.success) {
                renderCategoryChart(statsResult.data.categories);
            }
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

/**
 * Render usage trend chart
 */
function renderTrendChart(trendData) {
    const ctx = document.getElementById('trendChart');

    // Destroy existing chart
    if (charts.trend) {
        charts.trend.destroy();
    }

    const labels = trendData.map(d => formatDate(d.date));
    const data = trendData.map(d => d.count);

    charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Usage Count',
                data: data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#64748b'
                    },
                    grid: {
                        color: '#e2e8f0'
                    }
                },
                x: {
                    ticks: {
                        color: '#64748b'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Render top features chart
 */
function renderFeaturesChart(features) {
    const ctx = document.getElementById('featuresChart');

    // Destroy existing chart
    if (charts.features) {
        charts.features.destroy();
    }

    // Get top 10 features
    const topFeatures = features.slice(0, 10);
    const labels = topFeatures.map(f => formatFeatureName(f.name));
    const data = topFeatures.map(f => f.total_uses);

    const colors = [
        '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
        '#10b981', '#06b6d4', '#6366f1', '#f97316',
        '#14b8a6', '#a855f7'
    ];

    charts.features = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Uses',
                data: data,
                backgroundColor: colors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#64748b'
                    },
                    grid: {
                        color: '#e2e8f0'
                    }
                },
                y: {
                    ticks: {
                        color: '#64748b'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Render category distribution chart
 */
function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');

    // Destroy existing chart
    if (charts.category) {
        charts.category.destroy();
    }

    const labels = Object.keys(categories).map(c => formatCategoryName(c));
    const data = Object.values(categories);

    const colors = [
        '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
        '#10b981', '#06b6d4', '#6366f1', '#f97316'
    ];

    charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#64748b',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12
                }
            }
        }
    });
}

/**
 * Load recent activity
 */
async function loadRecentActivity() {
    try {
        const response = await fetch('/analytics/api/recent?limit=20');
        const result = await response.json();

        if (result.success) {
            const tbody = document.getElementById('recent-activity-body');

            if (result.data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-8 text-slate-500 dark:text-slate-400">
                            No activity yet. Start using features to see your usage history!
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = result.data.map(activity => `
                <tr>
                    <td class="font-medium text-slate-800 dark:text-slate-200">
                        ${formatFeatureName(activity.feature_name)}
                    </td>
                    <td>
                        <span class="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs font-medium">
                            ${formatCategoryName(activity.feature_category)}
                        </span>
                    </td>
                    <td class="text-slate-600 dark:text-slate-400">
                        ${formatTimestamp(activity.timestamp)}
                    </td>
                    <td>
                        <span class="status-badge ${activity.success ? 'status-success' : 'status-error'}">
                            ${activity.success ? '✓ Success' : '✗ Failed'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

/**
 * Format feature name for display
 */
function formatFeatureName(name) {
    if (!name) return '-';
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Format category name for display
 */
function formatCategoryName(category) {
    if (!category) return 'Other';
    return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }

    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }

    // Less than 1 day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }

    // More than 1 day
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
