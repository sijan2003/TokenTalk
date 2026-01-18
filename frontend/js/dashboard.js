// --- Security Guard ---
// Prevents unauthenticated users from seeing the dashboard contents.
if (!localStorage.getItem('token')) {
    window.location.href = 'index.html';
}

document.addEventListener('DOMContentLoaded', async () => {
    // Clean session and return to login
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        window.location.href = 'index.html';
    });

    // Populate data grids on page load
    await loadDocuments();
    await loadVideos();
    await loadWebpages();

    // --- UI Component Logic: PDF Upload Area ---
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Click anywhere on the box to trigger the hidden file browser
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and Drop Visual Feedback
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary)';
        uploadArea.style.background = 'rgba(99, 102, 241, 0.1)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--glass-border)';
        uploadArea.style.background = 'transparent';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileInput.files = e.dataTransfer.files;
        handleFileUpload(fileInput.files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    // --- UI Component Logic: YouTube Integration ---
    document.getElementById('addYoutubeBtn').addEventListener('click', async () => {
        const urlInput = document.getElementById('youtubeUrl');
        const url = urlInput.value.trim();
        if (!url) return;

        try {
            const btn = document.getElementById('addYoutubeBtn');
            btn.innerHTML = '<div class="loader" style="width:16px;height:16px;"></div>';
            btn.disabled = true;

            // Trigger backend processing (Transcript fetching + FAISS indexing)
            await API.processYouTube(url);
            urlInput.value = '';
            await loadVideos(); // Refresh list to show new item
        } catch (error) {
            alert('Failed to process video: ' + error.message);
        } finally {
            const btn = document.getElementById('addYoutubeBtn');
            btn.innerHTML = '<i class="fas fa-plus"></i> Add';
            btn.disabled = false;
        }
    });

    // --- UI Component Logic: Webpage Integration ---
    document.getElementById('addWebpageBtn').addEventListener('click', async () => {
        const urlInput = document.getElementById('webpageUrl');
        const url = urlInput.value.trim();
        if (!url) return;

        try {
            const btn = document.getElementById('addWebpageBtn');
            btn.innerHTML = '<div class="loader" style="width:16px;height:16px;"></div>';
            btn.disabled = true;

            // Trigger backend scraping and vectorization
            await API.processWebpage(url);
            urlInput.value = '';
            await loadWebpages();
        } catch (error) {
            alert('Failed to process webpage: ' + error.message);
        } finally {
            const btn = document.getElementById('addWebpageBtn');
            btn.innerHTML = '<i class="fas fa-plus"></i> Add';
            btn.disabled = false;
        }
    });
});

/**
 * Validates and uploads a PDF file to the server.
 */
async function handleFileUpload(file) {
    if (file.type !== 'application/pdf') {
        alert('Only PDF files are allowed');
        return;
    }

    const statusEl = document.getElementById('uploadStatus');
    statusEl.classList.remove('hidden');
    statusEl.innerHTML = `<div class="loader" style="display:inline-block; vertical-align:middle; width:16px; height:16px; margin-right:10px;"></div> Uploading ${file.name}...`;

    try {
        await API.uploadDocument(file);
        statusEl.innerHTML = `<i class="fas fa-check" style="color:var(--success)"></i> Upload complete! Processing in background...`;
        await loadDocuments();

        // Hide success message after 3 seconds
        setTimeout(() => statusEl.classList.add('hidden'), 3000);

        // Start polling for this document (optional, loadDocuments handles it broadly)
        startStatusPolling();
    } catch (error) {
        statusEl.innerHTML = `<i class="fas fa-times" style="color:var(--error)"></i> Error: ${error.message}`;
    }
}

let pollingInterval = null;

function startStatusPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(async () => {
        const docs = await loadDocuments(true); // silent load
        const stillProcessing = docs.some(d => d.status === 'processing');
        if (!stillProcessing) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }, 3000);
}

/**
 * Dynamically generates a card element to show in our grids.
 */
function createSourceCard(id, title, subtitle, type, icon, status = 'completed') {
    const card = document.createElement('div');
    card.className = 'source-card glass';

    const isProcessing = status === 'processing';
    const isFailed = status === 'failed';

    card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <div class="card-icon">
                ${isProcessing ? '<div class="loader" style="width:20px;height:20px;"></div>' : icon}
            </div>
            <div style="display:flex; flex-direction:column; align-items:end; gap:0.4rem;">
                <span class="badge badge-${type}">${type}</span>
                <span class="badge badge-status ${status}">${status}</span>
            </div>
        </div>
        
        <div style="margin-top:0.5rem;">
            <h3 style="font-size:1.1rem; margin-bottom:0.3rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${title}</h3>
            <p style="font-size:0.85rem; color:var(--text-muted);">${subtitle}</p>
        </div>

        <div style="display:flex; gap:0.8rem; margin-top:auto; padding-top:1rem; border-top:1px solid var(--glass-border);">
            <button onclick="goToChat(${id}, '${type}')" 
                    class="btn btn-primary" 
                    style="flex:1; padding:0.6rem;"
                    ${isProcessing || isFailed ? 'disabled' : ''}>
                <i class="fas fa-comment-alt"></i> Chat
            </button>
            <button onclick="deleteSource(${id}, '${type}')" 
                    class="btn btn-secondary" 
                    style="padding:0.6rem 1rem; color:var(--error);">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    `;
    return card;
}

// Fetch and render the PDF list
async function loadDocuments(silent = false) {
    const list = document.getElementById('documentList');
    try {
        const docs = await API.getDocuments();
        if (silent) return docs;

        list.innerHTML = '';
        if (docs.length === 0) list.innerHTML = '<p class="text-muted">No documents uploaded.</p>';

        docs.forEach(doc => {
            const date = new Date(doc.upload_date).toLocaleDateString();
            list.appendChild(createSourceCard(doc.id, doc.filename, date, 'pdf', '📄', doc.status));
        });

        document.getElementById('docCount').textContent = docs.length;

        if (docs.some(d => d.status === 'processing')) {
            startStatusPolling();
        }

        return docs;
    } catch (e) {
        if (!silent) console.error(e);
        return [];
    }
}

// Fetch and render the YouTube list
async function loadVideos() {
    const list = document.getElementById('youtubeList');
    try {
        const videos = await API.getVideos();
        list.innerHTML = '';
        if (videos.length === 0) list.innerHTML = '<p class="text-muted">No videos added.</p>';
        videos.forEach(vid => {
            const date = new Date(vid.processed_date).toLocaleDateString();
            list.appendChild(createSourceCard(vid.id, vid.title || vid.url, date, 'youtube', '🎥'));
        });
        document.getElementById('vidCount').textContent = videos.length;
    } catch (e) {
        console.error(e);
    }
}

// Fetch and render the Webpage list
async function loadWebpages() {
    const list = document.getElementById('webpageList');
    try {
        const pages = await API.getWebpages();
        list.innerHTML = '';
        if (pages.length === 0) list.innerHTML = '<p class="text-muted">No webpages added.</p>';
        pages.forEach(page => {
            const date = new Date(page.processed_date).toLocaleDateString();
            list.appendChild(createSourceCard(page.id, page.title || page.url, date, 'web', '🌐'));
        });
        document.getElementById('webCount').textContent = pages.length;
    } catch (e) {
        console.error(e);
    }
}

// Navigation to the Chat screen
window.goToChat = (id, type) => {
    // Passes the Source ID and Type in the URL so chat.js knows what to load
    window.location.href = `chat.html?id=${id}&type=${type}`;
};

// Deletion logic
window.deleteSource = async (id, type) => {
    if (!confirm('Are you sure you want to delete this source?')) return;
    try {
        // We only implemented the PDF deletion route in the current iteration.
        if (type === 'pdf') {
            await API.deleteDocument(id);
            loadDocuments();
        } else {
            alert('To keep your data safe, delete functionality for YouTube/Web is currently restricted.');
        }
    } catch (e) {
        alert('Error deleting: ' + e.message);
    }
};
