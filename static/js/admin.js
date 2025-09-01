// Admin Panel JavaScript
class AdminPanel {
    constructor() {
        this.initializeSorting();
        this.initializeGenerateButtons();
    }
    
    initializeSorting() {
        // Add event listeners for sorting buttons if they exist
        const sortButtons = document.querySelectorAll('[onclick*="sortTable"]');
        sortButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const sortType = button.getAttribute('onclick').includes('discrimination') ? 'discrimination' : 'difficulty';
                this.sortTable(sortType);
            });
        });
    }
    
    initializeGenerateButtons() {
        // Add generate question buttons for each prerequisite
        const generateButtons = document.querySelectorAll('[data-generate-prerequisite]');
        generateButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const prerequisite = button.getAttribute('data-generate-prerequisite');
                this.generateQuestions(prerequisite);
            });
        });
    }
    
    sortTable(sortBy) {
        const table = document.getElementById('questions-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        let sortIndex;
        let isNumeric = true;
        
        switch (sortBy) {
            case 'discrimination':
                sortIndex = 7; // Discrimination index column
                break;
            case 'difficulty':
                sortIndex = 6; // Difficulty percentage column
                break;
            default:
                return;
        }
        
        rows.sort((a, b) => {
            let aVal = a.cells[sortIndex].textContent.trim();
            let bVal = b.cells[sortIndex].textContent.trim();
            
            // Handle special cases for discrimination index
            if (sortBy === 'discrimination') {
                if (aVal === 'محاسبه نشده') aVal = '-999';
                if (bVal === 'محاسبه نشده') bVal = '-999';
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else if (sortBy === 'difficulty') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }
            
            // Sort in descending order (highest first)
            return bVal - aVal;
        });
        
        // Clear tbody and append sorted rows
        tbody.innerHTML = '';
        rows.forEach((row, index) => {
            row.cells[0].textContent = index + 1; // Update row numbers
            tbody.appendChild(row);
        });
        
        // Show feedback
        this.showAlert(`جدول بر اساس ${sortBy === 'discrimination' ? 'شاخص تمایز' : 'درصد سختی'} مرتب شد`, 'success');
    }
    
    async generateQuestions(prerequisite) {
        if (!prerequisite) {
            this.showAlert('پیش‌نیاز مشخص نشده', 'danger');
            return;
        }
        
        // Show loading state
        const button = document.querySelector(`[data-generate-prerequisite="${prerequisite}"]`);
        if (button) {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>در حال تولید...';
            button.disabled = true;
        }
        
        try {
            const response = await fetch('/admin/generate_questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prerequisite })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message || 'سوالات با موفقیت تولید شدند', 'success');
                // Refresh page after a short delay
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                this.showAlert(data.error || 'خطا در تولید سوالات', 'danger');
            }
        } catch (error) {
            console.error('Error generating questions:', error);
            this.showAlert('خطا در ارتباط با سرور', 'danger');
        } finally {
            // Restore button state
            if (button) {
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Utility function to highlight quality indicators
    highlightQualityIndicators() {
        const discriminationCells = document.querySelectorAll('[data-discrimination-index]');
        
        discriminationCells.forEach(cell => {
            const value = parseFloat(cell.getAttribute('data-discrimination-index'));
            
            if (!isNaN(value)) {
                if (value >= 0.4) {
                    cell.classList.add('quality-excellent');
                } else if (value >= 0.2) {
                    cell.classList.add('quality-acceptable');
                } else {
                    cell.classList.add('quality-poor');
                }
            }
        });
    }
    
    // Format numbers for better display
    formatNumbers() {
        // Format discrimination indices
        const discriminationElements = document.querySelectorAll('.discrimination-index');
        discriminationElements.forEach(el => {
            const value = parseFloat(el.textContent);
            if (!isNaN(value)) {
                el.textContent = value.toFixed(3);
            }
        });
        
        // Format difficulty percentages
        const difficultyElements = document.querySelectorAll('.difficulty-percentage');
        difficultyElements.forEach(el => {
            const value = parseFloat(el.textContent);
            if (!isNaN(value)) {
                el.textContent = value.toFixed(1) + '%';
            }
        });
    }
}

// Global functions for backward compatibility
window.sortTable = function(sortBy) {
    if (window.adminPanel) {
        window.adminPanel.sortTable(sortBy);
    }
};

window.generateQuestions = function(prerequisite) {
    if (window.adminPanel) {
        window.adminPanel.generateQuestions(prerequisite);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
    
    // Apply formatting
    window.adminPanel.formatNumbers();
    window.adminPanel.highlightQualityIndicators();
});

// Analytics Chart Helper (if Chart.js is available)
if (typeof Chart !== 'undefined') {
    class AnalyticsCharts {
        constructor() {
            this.initializeCharts();
        }
        
        initializeCharts() {
            this.createQualityDistributionChart();
            this.createPrerequisitePerformanceChart();
        }
        
        createQualityDistributionChart() {
            const ctx = document.getElementById('qualityChart');
            if (!ctx) return;
            
            // Get data from the page
            const excellent = document.querySelectorAll('[data-quality="excellent"]').length;
            const acceptable = document.querySelectorAll('[data-quality="acceptable"]').length;
            const poor = document.querySelectorAll('[data-quality="poor"]').length;
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['عالی', 'قابل قبول', 'ضعیف'],
                    datasets: [{
                        data: [excellent, acceptable, poor],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(220, 53, 69, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'توزیع کیفیت سوالات'
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        createPrerequisitePerformanceChart() {
            const ctx = document.getElementById('prerequisiteChart');
            if (!ctx) return;
            
            // This would need actual data from the server
            // For now, it's a placeholder
        }
    }
    
    // Initialize charts when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
        new AnalyticsCharts();
    });
}
