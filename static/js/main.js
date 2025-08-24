/**
 * Main JavaScript file for Financial Report Analyzer
 */

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    // Check if it's a timestamp in milliseconds
    if (!isNaN(dateString) && dateString.toString().length >= 13) {
        dateString = parseInt(dateString);
    }
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        return dateString;
    }
    
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show toast notification
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'fixed bottom-4 right-4 z-50';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    
    // Set toast classes based on type
    let bgColor, textColor, borderColor;
    switch (type) {
        case 'success':
            bgColor = 'bg-success-50';
            textColor = 'text-success-800';
            borderColor = 'border-success-200';
            break;
        case 'error':
        case 'danger':
            bgColor = 'bg-danger-50';
            textColor = 'text-danger-800';
            borderColor = 'border-danger-200';
            break;
        case 'warning':
            bgColor = 'bg-warning-50';
            textColor = 'text-warning-800';
            borderColor = 'border-warning-200';
            break;
        case 'info':
        default:
            bgColor = 'bg-primary-50';
            textColor = 'text-primary-800';
            borderColor = 'border-primary-200';
            break;
    }
    
    toast.className = `${bgColor} ${textColor} ${borderColor} border rounded-lg shadow-lg p-4 mb-3 flex items-center animate-fade-in`;
    
    // Create toast content
    let icon;
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle text-success-500 mr-3 text-xl"></i>';
            break;
        case 'error':
        case 'danger':
            icon = '<i class="fas fa-exclamation-circle text-danger-500 mr-3 text-xl"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle text-warning-500 mr-3 text-xl"></i>';
            break;
        case 'info':
        default:
            icon = '<i class="fas fa-info-circle text-primary-500 mr-3 text-xl"></i>';
            break;
    }
    
    toast.innerHTML = `
        <div class="flex-1">
            ${icon}
            <span>${message}</span>
        </div>
        <button type="button" class="ml-4 text-secondary-400 hover:text-secondary-600" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Auto-remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0');
        toast.style.transition = 'opacity 0.5s ease-out';
        
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 3000);
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast('已复制到剪贴板', 'success');
        })
        .catch(err => {
            console.error('复制失败:', err);
            showToast('复制失败', 'danger');
        });
}

// Create and render charts
function createChart(elementId, type, data, options = {}) {
    if (!document.getElementById(elementId)) return;
    
    const defaultOptions = {
        chart: {
            type: type,
            height: 350,
            fontFamily: 'Inter, sans-serif',
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800,
                animateGradually: {
                    enabled: true,
                    delay: 150
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 350
                }
            }
        },
        colors: ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7'],
        grid: {
            borderColor: '#e2e8f0',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: false
                }
            }
        },
        tooltip: {
            theme: 'light',
            x: {
                show: true
            }
        }
    };
    
    // Merge default options with provided options
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        chart: {
            ...defaultOptions.chart,
            ...options.chart,
            type: type
        }
    };
    
    const chart = new ApexCharts(document.getElementById(elementId), {
        ...mergedOptions,
        series: data
    });
    
    chart.render();
    return chart;
}

// Create financial ratio charts
function createFinancialCharts(financialData) {
    if (!financialData) return;
    
    // Profitability chart
    if (financialData.profitability && document.getElementById('profitability-chart')) {
        const profitabilityData = [
            {
                name: '盈利能力指标',
                data: [
                    financialData.profitability.roe || 0,
                    financialData.profitability.roa || 0,
                    financialData.profitability.gross_margin || 0,
                    financialData.profitability.net_margin || 0
                ]
            }
        ];
        
        createChart('profitability-chart', 'bar', profitabilityData, {
            chart: {
                height: 300
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: false
            },
            xaxis: {
                categories: ['净资产收益率(ROE)', '总资产收益率(ROA)', '毛利率', '净利率'],
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            yaxis: {
                title: {
                    text: '百分比(%)',
                    style: {
                        color: '#64748b'
                    }
                },
                labels: {
                    formatter: function(val) {
                        return val.toFixed(2) + '%';
                    },
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            fill: {
                opacity: 1,
                type: 'gradient',
                gradient: {
                    shade: 'light',
                    type: 'vertical',
                    shadeIntensity: 0.4,
                    opacityFrom: 0.9,
                    opacityTo: 0.6,
                    stops: [0, 90, 100]
                }
            },
            tooltip: {
                y: {
                    formatter: function(val) {
                        return val.toFixed(2) + '%';
                    }
                }
            }
        });
    }
    
    // Expense ratios chart
    if (financialData.expense_ratios && document.getElementById('expense-chart')) {
        const expenseData = [];
        const expenseLabels = [];
        
        if (financialData.expense_ratios.sales_expense_ratio !== null) {
            expenseData.push(financialData.expense_ratios.sales_expense_ratio);
            expenseLabels.push('销售费用');
        }
        
        if (financialData.expense_ratios.admin_expense_ratio !== null) {
            expenseData.push(financialData.expense_ratios.admin_expense_ratio);
            expenseLabels.push('管理费用');
        }
        
        if (financialData.expense_ratios.rd_expense_ratio !== null) {
            expenseData.push(financialData.expense_ratios.rd_expense_ratio);
            expenseLabels.push('研发费用');
        }
        
        if (financialData.expense_ratios.financial_expense_ratio !== null) {
            expenseData.push(financialData.expense_ratios.financial_expense_ratio);
            expenseLabels.push('财务费用');
        }
        
        if (expenseData.length > 0) {
            createChart('expense-chart', 'pie', expenseData, {
                chart: {
                    height: 300
                },
                labels: expenseLabels,
                responsive: [{
                    breakpoint: 480,
                    options: {
                        chart: {
                            width: 300
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }],
                dataLabels: {
                    enabled: true,
                    formatter: function(val, opts) {
                        return opts.w.config.labels[opts.seriesIndex] + ': ' + val.toFixed(1) + '%';
                    }
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '50%'
                        }
                    }
                },
                legend: {
                    position: 'bottom',
                    horizontalAlign: 'center'
                }
            });
        }
    }
    
    // Cash flow chart
    if (financialData.cash_flow && document.getElementById('cash-flow-chart')) {
        const cashFlowData = [
            {
                name: '现金流量',
                data: [
                    financialData.cash_flow.operating || 0,
                    financialData.cash_flow.investing || 0,
                    financialData.cash_flow.financing || 0
                ]
            }
        ];
        
        createChart('cash-flow-chart', 'bar', cashFlowData, {
            chart: {
                height: 300
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    barHeight: '50%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: false
            },
            xaxis: {
                categories: ['经营活动', '投资活动', '筹资活动'],
                labels: {
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            yaxis: {
                title: {
                    text: '金额(元)',
                    style: {
                        color: '#64748b'
                    }
                },
                labels: {
                    formatter: function(val) {
                        return formatLargeNumber(val);
                    },
                    style: {
                        colors: '#64748b'
                    }
                }
            },
            colors: ['#0ea5e9', '#ef4444', '#f59e0b'],
            fill: {
                opacity: 1,
                type: 'gradient',
                gradient: {
                    shade: 'light',
                    type: 'horizontal',
                    shadeIntensity: 0.4,
                    opacityFrom: 0.9,
                    opacityTo: 0.6,
                    stops: [0, 90, 100]
                }
            },
            tooltip: {
                y: {
                    formatter: function(val) {
                        return formatLargeNumber(val) + ' 元';
                    }
                }
            }
        });
    }
}

// Format large numbers for display
function formatLargeNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    
    if (Math.abs(num) >= 100000000) {
        return (num / 100000000).toFixed(2) + '亿';
    } else if (Math.abs(num) >= 10000) {
        return (num / 10000).toFixed(2) + '万';
    } else {
        return num.toFixed(2);
    }
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to all code blocks
    document.querySelectorAll('pre').forEach(block => {
        if (!block.classList.contains('no-copy')) {
            const button = document.createElement('button');
            button.className = 'absolute top-2 right-2 bg-secondary-700 hover:bg-secondary-600 text-white rounded p-1 text-xs';
            button.innerHTML = '<i class="fas fa-copy"></i>';
            button.title = '复制到剪贴板';
            
            button.addEventListener('click', function() {
                copyToClipboard(block.textContent);
                button.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
            
            // Make the pre position relative for absolute positioning of the button
            if (window.getComputedStyle(block).position === 'static') {
                block.style.position = 'relative';
            }
            block.appendChild(button);
        }
    });
    
    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        if (tooltipText) {
            element.classList.add('custom-tooltip');
            
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip-text';
            tooltip.textContent = tooltipText;
            
            element.appendChild(tooltip);
        }
    });
    
    // Add print functionality
    const printButtons = document.querySelectorAll('.print-button');
    if (printButtons.length > 0) {
        printButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                window.print();
            });
        });
    }
    
    // Add export to PDF functionality
    const exportPdfButtons = document.querySelectorAll('.export-pdf-button');
    if (exportPdfButtons.length > 0 && typeof html2pdf !== 'undefined') {
        exportPdfButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const elementId = button.getAttribute('data-target');
                const element = document.getElementById(elementId);
                
                if (element) {
                    const opt = {
                        margin: 10,
                        filename: '财报分析_' + new Date().toISOString().slice(0, 10) + '.pdf',
                        image: { type: 'jpeg', quality: 0.98 },
                        html2canvas: { scale: 2 },
                        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                    };
                    
                    html2pdf().set(opt).from(element).save();
                }
            });
        });
    }
    
    // Add export to Excel functionality
    const exportExcelButtons = document.querySelectorAll('.export-excel-button');
    if (exportExcelButtons.length > 0 && typeof XLSX !== 'undefined') {
        exportExcelButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const tableId = button.getAttribute('data-target');
                const table = document.getElementById(tableId);
                
                if (table) {
                    const wb = XLSX.utils.table_to_book(table);
                    XLSX.writeFile(wb, '财报数据_' + new Date().toISOString().slice(0, 10) + '.xlsx');
                }
            });
        });
    }
});

// Function to toggle dark mode
function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    
    // Save preference to localStorage
    const isDarkMode = document.documentElement.classList.contains('dark');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
    
    // Update charts if they exist
    if (window.charts) {
        for (const chartId in window.charts) {
            if (window.charts[chartId]) {
                window.charts[chartId].updateOptions({
                    theme: {
                        mode: isDarkMode ? 'dark' : 'light'
                    }
                });
            }
        }
    }
}

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'enabled') {
    document.documentElement.classList.add('dark');
}