// Fotek Scraper Frontend JavaScript

class FotekScraperApp {
    constructor() {
        this.isRunning = false;
        this.statusCheckInterval = null;
        this.sampleUrls = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadSampleUrls();
        this.updateWorkersDisplay();
    }

    initializeElements() {
        // Form elements
        this.urlInput = document.getElementById('urlInput');
        this.maxWorkers = document.getElementById('maxWorkers');
        this.workersValue = document.getElementById('workersValue');
        
        // Buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.loadSampleBtn = document.getElementById('loadSampleBtn');
        this.clearUrlBtn = document.getElementById('clearUrlBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.addSelectedUrls = document.getElementById('addSelectedUrls');
        
        // Status elements
        this.statusBadge = document.getElementById('status-badge');
        this.progressBar = document.getElementById('progressBar');
        this.progressPercent = document.getElementById('progressPercent');
        this.currentTask = document.getElementById('currentTask');
        
        // Stats elements
        this.seriesCount = document.getElementById('seriesCount');
        this.productsCount = document.getElementById('productsCount');
        this.successCount = document.getElementById('successCount');
        this.errorCount = document.getElementById('errorCount');
        this.duration = document.getElementById('duration');
        
        // Result sections
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
        
        // Log container
        this.logContainer = document.getElementById('logContainer');
        
        // Modal elements
        this.sampleUrlsModal = new bootstrap.Modal(document.getElementById('sampleUrlsModal'));
        this.sampleUrlsList = document.getElementById('sampleUrlsList');
    }

    bindEvents() {
        // Button events
        this.startBtn.addEventListener('click', () => this.startScraping());
        this.stopBtn.addEventListener('click', () => this.stopScraping());
        this.loadSampleBtn.addEventListener('click', () => this.showSampleUrls());
        this.clearUrlBtn.addEventListener('click', () => this.clearUrls());
        this.downloadBtn.addEventListener('click', () => this.downloadResults());
        this.addSelectedUrls.addEventListener('click', () => this.addSelectedSampleUrls());
        
        // Range input
        this.maxWorkers.addEventListener('input', () => this.updateWorkersDisplay());
        
        // Auto-resize textarea
        this.urlInput.addEventListener('input', () => this.autoResizeTextarea());
    }

    updateWorkersDisplay() {
        const value = this.maxWorkers.value;
        this.workersValue.textContent = `${value} luồng`;
    }

    autoResizeTextarea() {
        this.urlInput.style.height = 'auto';
        this.urlInput.style.height = Math.max(120, this.urlInput.scrollHeight) + 'px';
    }

    async loadSampleUrls() {
        try {
            const response = await fetch('/api/sample_urls');
            this.sampleUrls = await response.json();
        } catch (error) {
            console.error('Error loading sample URLs:', error);
            this.addLog('Lỗi khi tải URL mẫu', 'error');
        }
    }

    showSampleUrls() {
        let html = '';
        
        this.sampleUrls.forEach((item, index) => {
            html += `
                <div class="sample-url-item" onclick="toggleSampleUrl(${index})">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="sample${index}">
                        <label class="form-check-label w-100" for="sample${index}">
                            <div class="sample-url-name">${item.name}</div>
                            <div class="sample-url-description">${item.description}</div>
                            <div class="sample-url-link">${item.url}</div>
                        </label>
                    </div>
                </div>
            `;
        });
        
        this.sampleUrlsList.innerHTML = html;
        this.sampleUrlsModal.show();
    }

    addSelectedSampleUrls() {
        const selectedUrls = [];
        
        this.sampleUrls.forEach((item, index) => {
            const checkbox = document.getElementById(`sample${index}`);
            if (checkbox && checkbox.checked) {
                selectedUrls.push(item.url);
            }
        });
        
        if (selectedUrls.length > 0) {
            const currentUrls = this.urlInput.value.trim();
            const newUrls = selectedUrls.join('\n');
            
            if (currentUrls) {
                this.urlInput.value = currentUrls + '\n' + newUrls;
            } else {
                this.urlInput.value = newUrls;
            }
            
            this.autoResizeTextarea();
            this.sampleUrlsModal.hide();
            this.addLog(`Đã thêm ${selectedUrls.length} URL mẫu`, 'success');
        } else {
            this.addLog('Vui lòng chọn ít nhất một URL', 'warning');
        }
    }

    clearUrls() {
        this.urlInput.value = '';
        this.autoResizeTextarea();
        this.addLog('Đã xóa tất cả URL', 'info');
    }

    async startScraping() {
        const urls = this.getUrlsFromInput();
        
        if (urls.length === 0) {
            this.addLog('Vui lòng nhập ít nhất một URL!', 'error');
            return;
        }

        const maxWorkers = parseInt(this.maxWorkers.value);
        
        try {
            const response = await fetch('/api/start_scraping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    urls: urls,
                    max_workers: maxWorkers
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.isRunning = true;
                this.updateUI('running');
                this.addLog(`Bắt đầu cào dữ liệu từ ${result.urls_count} danh mục`, 'success');
                this.startStatusPolling();
            } else {
                this.addLog(`Lỗi: ${result.message}`, 'error');
            }
        } catch (error) {
            this.addLog(`Lỗi kết nối: ${error.message}`, 'error');
        }
    }

    async stopScraping() {
        try {
            const response = await fetch('/api/stop_scraping', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.isRunning = false;
                this.updateUI('stopped');
                this.addLog('Đã dừng cào dữ liệu', 'warning');
                this.stopStatusPolling();
            } else {
                this.addLog(`Lỗi khi dừng: ${result.message}`, 'error');
            }
        } catch (error) {
            this.addLog(`Lỗi kết nối: ${error.message}`, 'error');
        }
    }

    async downloadResults() {
        try {
            const response = await fetch('/api/download_results');
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `fotek_products_${Date.now()}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.addLog('Tải xuống file thành công', 'success');
            } else {
                const error = await response.json();
                this.addLog(`Lỗi tải file: ${error.message}`, 'error');
            }
        } catch (error) {
            this.addLog(`Lỗi tải file: ${error.message}`, 'error');
        }
    }

    getUrlsFromInput() {
        return this.urlInput.value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0 && url.includes('fotek.com.tw'));
    }

    updateUI(state) {
        switch (state) {
            case 'running':
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.statusBadge.innerHTML = '<i class="bi bi-circle-fill spinning"></i> Đang chạy';
                this.statusBadge.className = 'badge bg-warning';
                this.resultsSection.classList.add('d-none');
                this.errorSection.classList.add('d-none');
                break;
                
            case 'completed':
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.statusBadge.innerHTML = '<i class="bi bi-check-circle-fill"></i> Hoàn thành';
                this.statusBadge.className = 'badge bg-success';
                this.resultsSection.classList.remove('d-none');
                break;
                
            case 'error':
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.statusBadge.innerHTML = '<i class="bi bi-x-circle-fill"></i> Lỗi';
                this.statusBadge.className = 'badge bg-danger';
                this.errorSection.classList.remove('d-none');
                break;
                
            case 'stopped':
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.statusBadge.innerHTML = '<i class="bi bi-stop-circle-fill"></i> Đã dừng';
                this.statusBadge.className = 'badge bg-secondary';
                break;
                
            default:
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.statusBadge.innerHTML = '<i class="bi bi-circle-fill"></i> Sẵn sàng';
                this.statusBadge.className = 'badge bg-secondary';
        }
    }

    startStatusPolling() {
        this.statusCheckInterval = setInterval(() => {
            this.checkStatus();
        }, 1000);
    }

    stopStatusPolling() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/scraping_status');
            const status = await response.json();
            
            this.updateProgress(status);
            
            if (!status.is_running && this.isRunning) {
                this.isRunning = false;
                this.stopStatusPolling();
                
                if (status.error) {
                    this.updateUI('error');
                    this.errorMessage.textContent = status.error;
                    this.addLog(`Lỗi: ${status.error}`, 'error');
                } else if (status.results && status.results.success_count > 0) {
                    this.updateUI('completed');
                    this.addLog('Cào dữ liệu hoàn thành!', 'success');
                } else {
                    this.updateUI('stopped');
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }

    updateProgress(status) {
        // Update progress bar
        this.progressBar.style.width = `${status.progress}%`;
        this.progressPercent.textContent = `${status.progress}%`;
        
        // Update current task
        this.currentTask.textContent = status.current_task || 'Chưa bắt đầu';
        
        // Update stats
        if (status.results) {
            this.seriesCount.textContent = status.results.series_count || 0;
            this.productsCount.textContent = status.results.products_count || 0;
            this.successCount.textContent = status.results.success_count || 0;
            this.errorCount.textContent = status.results.error_count || 0;
            
            if (status.results.duration) {
                this.duration.textContent = Math.round(status.results.duration);
            }
        }
    }

    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        let icon = 'bi-info-circle';
        if (type === 'success') icon = 'bi-check-circle';
        else if (type === 'warning') icon = 'bi-exclamation-triangle';
        else if (type === 'error') icon = 'bi-x-circle';
        
        logEntry.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <i class="bi ${icon}"></i>
            ${message}
        `;
        
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
        
        // Keep only last 100 log entries
        const logEntries = this.logContainer.querySelectorAll('.log-entry');
        if (logEntries.length > 100) {
            logEntries[0].remove();
        }
    }
}

// Global functions for modal
function toggleSampleUrl(index) {
    const checkbox = document.getElementById(`sample${index}`);
    const item = checkbox.closest('.sample-url-item');
    
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        item.classList.add('selected');
    } else {
        item.classList.remove('selected');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.fotekApp = new FotekScraperApp();
});

// Service Worker for offline capability (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}