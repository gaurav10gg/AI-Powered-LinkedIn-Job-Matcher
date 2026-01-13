const API_BASE = window.location.origin;

let currentJobId = null;
let pollingInterval = null;
let currentResults = [];

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const resumeInput = document.getElementById('resumeInput');
const browseBtn = document.getElementById('browseBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeFileBtn = document.getElementById('removeFile');
const uploadBtn = document.getElementById('uploadBtn');

const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const processingStatus = document.getElementById('processingStatus');
const skillsSection = document.getElementById('skillsSection');
const waitingSection = document.getElementById('waitingSection');
const resultsSection = document.getElementById('resultsSection');

const jobIdDisplay = document.getElementById('jobId');
const copyJobIdBtn = document.getElementById('copyJobId');
const skillsList = document.getElementById('skillsList');
const queriesList = document.getElementById('queriesList');
const startPollingBtn = document.getElementById('startPollingBtn');

const waitingStatus = document.getElementById('waitingStatus');
const totalPosts = document.getElementById('totalPosts');
const totalQueries = document.getElementById('totalQueries');
const resultsContainer = document.getElementById('resultsContainer');

const exportBtn = document.getElementById('exportBtn');
const resetBtn = document.getElementById('resetBtn');

// =========================
// FILE UPLOAD HANDLERS
// =========================

// Upload Area - Click to browse
browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resumeInput.click();
});

uploadArea.addEventListener('click', (e) => {
    if (e.target !== browseBtn && !e.target.closest('.btn')) {
        resumeInput.click();
    }
});

// Drag & Drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

// File Input Change
resumeInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Handle File Selection
function handleFileSelect(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showNotification('Please select a PDF file', 'error');
        return;
    }
    
    fileName.textContent = file.name;
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    uploadBtn.style.display = 'block';
}

// Remove File
removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resumeInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    uploadBtn.style.display = 'none';
});

// =========================
// UPLOAD RESUME
// =========================
uploadBtn.addEventListener('click', async () => {
    const file = resumeInput.files[0];
    if (!file) {
        showNotification('Please select a file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show processing
    showSection(processingSection);
    processingStatus.textContent = 'Uploading and analyzing resume...';
    
    try {
        const response = await fetch(`${API_BASE}/process-resume`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.error || 'Failed to process resume');
        }
        
        if (data.success) {
            currentJobId = data.job_id;
            displaySkillsAndQueries(data);
            showSection(skillsSection);
            showNotification('Resume processed successfully!', 'success');
        } else {
            throw new Error(data.error || 'Processing failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
        showSection(uploadSection);
    }
});

// =========================
// DISPLAY SKILLS & QUERIES
// =========================
function displaySkillsAndQueries(data) {
    jobIdDisplay.textContent = data.job_id;
    
    // Display skills
    skillsList.innerHTML = '';
    if (data.skills && data.skills.length > 0) {
        data.skills.forEach(skill => {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = skill;
            skillsList.appendChild(tag);
        });
    } else {
        skillsList.innerHTML = '<p>No skills detected</p>';
    }
    
    // Display queries
    queriesList.innerHTML = '';
    if (data.queries && data.queries.length > 0) {
        data.queries.forEach(query => {
            const tag = document.createElement('span');
            tag.className = 'tag query-tag';
            tag.textContent = query;
            queriesList.appendChild(tag);
        });
    } else {
        queriesList.innerHTML = '<p>No queries generated</p>';
    }
}

// =========================
// COPY JOB ID
// =========================
copyJobIdBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(currentJobId).then(() => {
        showNotification('Job ID copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy Job ID', 'error');
    });
});

// =========================
// START POLLING
// =========================
startPollingBtn.addEventListener('click', () => {
    showSection(waitingSection);
    startPolling();
});

function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    waitingStatus.textContent = 'Checking for results...';
    
    // Check immediately
    checkResults();
    
    // Then check every 3 seconds
    pollingInterval = setInterval(checkResults, 3000);
}

async function checkResults() {
    try {
        const response = await fetch(`${API_BASE}/results/${currentJobId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.error || 'Failed to fetch results');
        }
        
        const resultCount = data.result_count || 0;
        
        if (data.status === 'completed' && resultCount > 0) {
            // Stop polling
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            
            // Display results
            displayResults(data);
            showSection(resultsSection);
            showNotification(`Found ${resultCount} job posts!`, 'success');
            
        } else if (data.status === 'waiting_for_linkedin') {
            waitingStatus.textContent = `Waiting for scraper... (${resultCount} posts so far)`;
        } else {
            waitingStatus.textContent = `Polling... (${resultCount} posts collected)`;
        }
        
    } catch (error) {
        console.error('Polling error:', error);
        waitingStatus.textContent = `Error: ${error.message}`;
    }
}

// =========================
// DISPLAY RESULTS
// =========================
function displayResults(data) {
    currentResults = data.results || [];
    
    // Update stats
    totalPosts.textContent = currentResults.length;
    totalQueries.textContent = data.queries?.length || 0;
    
    // Render posts
    renderPosts(currentResults);
}

function renderPosts(posts) {
    resultsContainer.innerHTML = '';
    
    if (posts.length === 0) {
        resultsContainer.innerHTML = '<p class="text-center">No posts found</p>';
        return;
    }
    
    posts.forEach((post, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const linksHtml = post.links && post.links.length > 0
            ? `
                <div class="result-links">
                    <strong>🔗 Links:</strong>
                    ${post.links.slice(0, 3).map(link => 
                        `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">${truncate(link, 60)}</a>`
                    ).join('')}
                </div>
            `
            : '';
        
        card.innerHTML = `
            <div class="result-header">
                <div>
                    <div class="result-author">
                        <i class="fas fa-user-circle"></i>
                        ${escapeHtml(post.author || 'Unknown')}
                    </div>
                    <span class="result-query">${escapeHtml(post.query || 'N/A')}</span>
                </div>
            </div>
            <div class="result-content">
                ${escapeHtml(post.content || 'No content')}
            </div>
            ${linksHtml}
        `;
        
        resultsContainer.appendChild(card);
    });
}

// =========================
// EXPORT RESULTS
// =========================
exportBtn.addEventListener('click', () => {
    if (currentResults.length === 0) {
        showNotification('No results to export', 'error');
        return;
    }
    
    const dataStr = JSON.stringify(currentResults, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `linkedin_jobs_${currentJobId.substring(0, 8)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Results exported successfully!', 'success');
});

// =========================
// RESET / START OVER
// =========================
resetBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to start over? This will clear all current data.')) {
        // Stop polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        
        // Reset state
        currentJobId = null;
        currentResults = [];
        resumeInput.value = '';
        
        // Reset UI
        uploadArea.style.display = 'block';
        fileInfo.style.display = 'none';
        uploadBtn.style.display = 'none';
        
        // Show upload section
        showSection(uploadSection);
        
        showNotification('Reset complete. Upload a new resume to start.', 'success');
    }
});

// =========================
// UTILITY FUNCTIONS
// =========================

function showSection(section) {
    // Hide all sections
    [uploadSection, processingSection, skillsSection, waitingSection, resultsSection].forEach(s => {
        s.style.display = 'none';
    });
    
    // Show target section
    section.style.display = 'block';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'info': 'info-circle'
    };
    
    notification.innerHTML = `
        <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 4 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, length) {
    if (!text) return '';
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

// =========================
// ADD NOTIFICATION STYLES
// =========================
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1000;
        transform: translateX(400px);
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        max-width: 400px;
        border: 1px solid rgba(0,0,0,0.08);
    }
    
    .notification.show {
        transform: translateX(0);
    }
    
    .notification i {
        font-size: 20px;
    }
    
    .notification-success {
        border-left: 4px solid var(--success);
    }
    
    .notification-success i {
        color: var(--success);
    }
    
    .notification-error {
        border-left: 4px solid var(--danger);
    }
    
    .notification-error i {
        color: var(--danger);
    }
    
    .notification-info {
        border-left: 4px solid var(--info);
    }
    
    .notification-info i {
        color: var(--info);
    }
    
    .notification span {
        flex: 1;
        color: var(--text-primary);
        font-weight: 600;
    }
`;
document.head.appendChild(style);

// =========================
// INITIALIZE
// =========================
console.log('LinkedIn Job Finder initialized');
console.log('API Base:', API_BASE);