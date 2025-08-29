/**
 * AI Research Assistant Frontend JavaScript
 * Version: 3.1 (Recent Queries Removed)
 */

class ResearchAssistant {
    constructor() {
        this.socket = null;
        this.currentQuery = '';
        this.isResearching = false;
        // this.recentQueries = this.loadRecentQueries(); // REMOVED
        this.currentResults = null;
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        // this.updateRecentQueries(); // REMOVED
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = window.location.port || '8000';
        const wsUrl = `${protocol}//${host}:${port}`;

        try {
            this.socket = io(wsUrl, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5
            });

            this.socket.on('connect', () => {
                console.log("Socket connected successfully!");
                this.updateConnectionStatus(true);
                this.checkAgentStatus();
                this.checkSystemHealth();
            });

            this.socket.on('disconnect', () => {
                console.log("Socket disconnected.");
                this.updateConnectionStatus(false);
            });

            this.socket.on('research_response', (data) => this.handleResearchResponse(data));
            this.socket.on('research_progress', (data) => this.updateProgress(data));
            this.socket.on('agents_response', (data) => this.updateAgentStatus(data));
            this.socket.on('health_response', (data) => this.updateSystemHealth(data));

        } catch (error) {
            console.error('WebSocket connection failed to initialize:', error);
            this.updateConnectionStatus(false);
        }
    }

    setupEventListeners() {
        document.getElementById('searchBtn').addEventListener('click', () => this.startResearch());
        document.getElementById('queryInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isResearching) this.startResearch();
        });
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        document.getElementById('copyBtn').addEventListener('click', () => this.copyResults());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadResults());
        document.getElementById('shareBtn').addEventListener('click', () => this.shareResults());
        document.getElementById('cancelBtn').addEventListener('click', () => this.cancelResearch());
    }

    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');
        if (connected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Disconnected';
        }
    }

    async startResearch() {
        const query = document.getElementById('queryInput').value.trim();
        console.log("Starting research for query:", query);
        if (!query) {
            this.showError('Please enter a research query');
            return;
        }
        if (this.isResearching) return;
        if (!this.socket || !this.socket.connected) {
            this.showError('Not connected. Please wait or refresh.');
            return;
        }

        this.currentQuery = query;
        this.isResearching = true;
        this.clearResultPanes();
        this.showProgressSection();
        // this.addToRecentQueries(query); // REMOVED
        document.getElementById('searchBtn').disabled = true;
        document.getElementById('searchBtn').innerHTML = '<span class="btn-text">Researching...</span><span class="btn-icon">⏳</span>';
        this.socket.emit('research_request', { query });
    }

    cancelResearch() {
        if (this.isResearching) {
            this.isResearching = false;
            this.hideProgressSection();
            this.resetSearchButton();
            this.showError('Research cancelled');
        }
    }

    handleResearchResponse(data) {
        this.isResearching = false;
        this.hideProgressSection();
        this.resetSearchButton();

        if (data.success && data.data && data.data.results) {
            this.currentResults = data.data.results;
            this.displayResults(data.data.results);
            this.showSuccess('Research completed successfully!');
        } else {
            this.showError(data.error || 'Research failed to return valid results.');
            this.clearResultPanes(true);
        }
    }

    displayResults(results) {
        console.log("Displaying results:", results);
        try {
            this.displaySummary(results.summary);
            this.displayReport(results.report);
            this.displaySources(results.search_results);
            this.displayInsights(results);
        } catch (error) {
            console.error('Error rendering results:', error);
            this.showError('A client-side error occurred while displaying results.');
        }
    }

    displaySummary(summary) {
        const el = document.getElementById('summaryContent');
        el.innerHTML = (summary && summary.trim()) ? this.formatContent(summary) : '<p class="placeholder">No summary could be generated.</p>';
    }

    displayReport(report) {
        const el = document.getElementById('reportContent');
        el.innerHTML = (report && report.trim()) ? this.formatContent(report) : '<p class="placeholder">A full report could not be generated.</p>';
    }

    displaySources(sources) {
        const contentEl = document.getElementById('sourcesContent');
        const statsEl = document.getElementById('sourceStats');
        if (sources && sources.length > 0) {
            statsEl.innerHTML = `<span class="stat">Sources: ${sources.length}</span>`;
            contentEl.innerHTML = sources.map((source, index) => `
                <div class="source-item">
                    <h5>${index + 1}. ${source.title || 'Untitled'}</h5>
                    <p>${source.content || 'No snippet.'}</p>
                    ${source.url ? `<a href="${source.url}" target="_blank" rel="noopener noreferrer">🔗 View Source</a>` : ''}
                </div>
            `).join('');
        } else {
            statsEl.innerHTML = `<span class="stat">Sources: 0</span>`;
            contentEl.innerHTML = '<p class="placeholder">No sources were found for this query.</p>';
        }
    }
    
    displayInsights(results) {
        const el = document.getElementById('insightsContent');
        const insights = this.generateInsights(results);
        if (insights.length > 0) {
            el.innerHTML = insights.map(insight => `
                <div class="insight-item ${insight.type}">
                    <div class="insight-icon">${this.getInsightIcon(insight.type)}</div>
                    <div class="insight-content"><h5>${insight.title}</h5><p>${insight.description}</p></div>
                </div>
            `).join('');
        } else {
            el.innerHTML = '<p class="placeholder">No key insights generated.</p>';
        }
    }

    generateInsights(results) {
        const insights = [];
        if (!results) return insights;
        insights.push({ type: 'success', title: 'Research Completed', description: 'The agent workflow has finished.' });
        const sourceCount = results.search_results ? results.search_results.length : 0;
        insights.push({
            type: sourceCount > 0 ? 'trends' : 'challenges',
            title: `Information Sources`,
            description: `Found ${sourceCount} relevant source(s) to generate the report.`
        });
        if (this.currentQuery.toLowerCase().includes('latest')) {
            insights.push({ type: 'opportunities', title: 'Timely Analysis', description: 'Query focused on the most recent data available.' });
        }
        return insights;
    }

    getInsightIcon(type) {
        return { trends: '📈', opportunities: '💡', challenges: '⚠️', success: '✅' }[type] || '📊';
    }
    
    formatContent(content) {
        if (typeof marked !== 'undefined') return marked.parse(content);
        return `<p>${content.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
    }

    updateProgress(data) {
        document.getElementById('progressMessage').textContent = data.message || 'Processing...';
    }

    showProgressSection() {
        document.getElementById('progressSection').style.display = 'block';
    }

    hideProgressSection() {
        document.getElementById('progressSection').style.display = 'none';
    }

    resetSearchButton() {
        const btn = document.getElementById('searchBtn');
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">Research</span><span class="btn-icon">🔍</span>';
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.dataset.pane === tabName));
    }

    checkAgentStatus() {
        if (this.socket && this.socket.connected) this.socket.emit('get_agents');
    }

    updateAgentStatus(data) {
        if (!data.success) return;
        const agents = data.data.agents || {};
        document.querySelectorAll('.agent-item').forEach(item => {
            const agentName = item.querySelector('.agent-name').textContent;
            const statusEl = item.querySelector('.agent-status');
            const agentData = Object.values(agents).find(a => agentName.toLowerCase().includes(a.type.replace(/_/g, ' ')));
            statusEl.className = `agent-status ${agentData ? 'online' : 'unknown'}`;
        });
    }

    checkSystemHealth() {
        if (this.socket && this.socket.connected) this.socket.emit('health_check');
    }
    
    updateSystemHealth(data) {
        const el = document.getElementById('backendStatus');
        if (data.success) {
            el.textContent = 'Healthy';
            el.style.color = 'var(--success-color)';
        } else {
            el.textContent = 'Unavailable';
            el.style.color = 'var(--error-color)';
        }
    }

    // --- ALL METHODS FOR RECENT QUERIES HAVE BEEN REMOVED FROM HERE ---

    copyResults() {
        const content = document.querySelector('.tab-pane.active .content-body')?.innerText;
        if (content) {
            navigator.clipboard.writeText(content).then(() => this.showSuccess('Copied to clipboard!'));
        }
    }

    downloadResults() {
            const activeTab = document.querySelector('.tab.active').dataset.tab;
            if (!this.currentResults) {
                this.showError('No results to download.');
                return;
            }

            // The logic for downloading the summary is now different
            if (activeTab === 'summary') {
                try {
                    // Ensure jsPDF is loaded
                    if (typeof window.jspdf === 'undefined') {
                        this.showError('PDF library not loaded. Please refresh.');
                        return;
                    }
                    const { jsPDF } = window.jspdf;
                    const doc = new jsPDF(); // Create a new PDF document

                    const summaryText = this.currentResults.summary || 'No summary available.';
                    
                    // Set text properties
                    doc.setFontSize(12);
                    doc.setTextColor(40, 40, 40);

                    // Add the text to the PDF, with automatic line wrapping.
                    // The '180' is the max width of the text block in mm.
                    const lines = doc.splitTextToSize(summaryText, 180);
                    doc.text(lines, 15, 20); // Add text at 15mm from left, 20mm from top

                    doc.save('summary.pdf'); // Trigger the download
                    this.showSuccess('Summary PDF downloaded!');
                } catch (error) {
                    console.error("Failed to generate PDF:", error);
                    this.showError("Could not generate the PDF file.");
                }
                return; // Important: exit the function after handling PDF
            }

            // --- Fallback for other download types (report, sources, etc.) ---
            let content = '', filename = 'research.txt';
            switch(activeTab) {
                case 'report': 
                    content = this.currentResults.report; 
                    filename = 'report.txt'; 
                    break;
                case 'sources': 
                    content = (this.currentResults.search_results || []).map(s => `${s.title}\n${s.url}`).join('\n\n'); 
                    filename = 'sources.txt'; 
                    break;
                default: 
                    content = JSON.stringify(this.currentResults, null, 2); 
                    filename = 'results.json';
            }
            this.downloadFile(content, filename);
        }

    downloadFile(content, filename) {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([content], {type: 'text/plain'}));
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
    }

    shareResults() {
        this.showError('Share functionality is not yet implemented.');
    }

    // Helper methods for showing success/error messages
    showSuccess(message) {
        this.showToast('successToast', message);
    }

    showError(message) {
        this.showToast('errorToast', message);
    }
    
    showToast(toastId, message) {
        const toast = document.getElementById(toastId);
        toast.querySelector('.toast-message').textContent = message;
        toast.style.display = 'flex';
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => this.hideToast(toastId), 4000);
    }
    
    hideToast(toastId) {
        const toast = document.getElementById(toastId);
        toast.classList.remove('show');
        setTimeout(() => toast.style.display = 'none', 300);
    }
    
    clearResultPanes(isError = false) {
        const welcomeMessage = `<div class="welcome-message"><div class="welcome-icon">🎯</div><h3>Welcome to AI Research Assistant</h3><p>Enter a research query above to get started.</p></div>`;
        const errorMessage = `<p class="placeholder">An error occurred. Please try a different query.</p>`;
        document.getElementById('summaryContent').innerHTML = isError ? errorMessage : welcomeMessage;
        document.getElementById('reportContent').innerHTML = '<p class="placeholder">The full report will appear here.</p>';
        document.getElementById('sourcesContent').innerHTML = '<p class="placeholder">Research sources will be listed here.</p>';
        document.getElementById('insightsContent').innerHTML = '<p class="placeholder">Key insights will be displayed here.</p>';
    }
}

function hideToast(toastId) {
    window.research?.hideToast(toastId);
}

document.addEventListener('DOMContentLoaded', () => {
    window.research = new ResearchAssistant();
});