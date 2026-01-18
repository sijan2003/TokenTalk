// --- Session Check ---
if (!localStorage.getItem('token')) {
    window.location.href = 'index.html';
}

// --- Parameter Extraction ---
const urlParams = new URLSearchParams(window.location.search);
const sourceId = urlParams.get('id');
const sourceType = urlParams.get('type');

// Fail-safe: If no source is specified, return to dashboard.
if (!sourceId || !sourceType) {
    window.location.href = 'dashboard.html';
}

const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const typingIndicator = document.getElementById('typingIndicator');

document.addEventListener('DOMContentLoaded', async () => {
    // Dynamic Header Title
    const typeLabel = sourceType === 'pdf' ? 'Document' : sourceType === 'youtube' ? 'Video' : 'Webpage';
    document.getElementById('chatHeaderTitle').textContent = `Chat with ${typeLabel}`;

    // Load persistent history
    await loadHistory();
});

// --- Chat Form Handler ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;

    // 1. Add User's message
    appendMessage(message, false);
    messageInput.value = '';

    // 2. Show typing indicator
    typingIndicator.classList.remove('hidden');
    scrollToBottom();

    try {
        // 3. Trigger Backend
        const response = await API.chat(sourceId, sourceType, message);
        typingIndicator.classList.add('hidden');

        // 4. Add AI's answer with animation
        appendMessage(response.answer, true, true);
    } catch (error) {
        typingIndicator.classList.add('hidden');
        appendMessage('Error: ' + error.message, true);
    }
});

/**
 * Appends a message to the chat interface.
 */
function appendMessage(text, isAI, animate = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message-bubble ${isAI ? 'message-ai' : 'message-user'} fade-in`;

    if (isAI && animate) {
        msgDiv.innerHTML = '';
        chatMessages.appendChild(msgDiv);
        typeText(msgDiv, text);
    } else {
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');

        // Add timestamp
        const time = document.createElement('div');
        time.style.fontSize = '0.65rem';
        time.style.marginTop = '0.4rem';
        time.style.opacity = '0.6';
        time.style.textAlign = isAI ? 'left' : 'right';
        time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        msgDiv.appendChild(time);

        chatMessages.appendChild(msgDiv);
    }

    scrollToBottom();
}

/**
 * Simulates a typing effect for AI responses.
 */
function typeText(element, text) {
    let i = 0;
    const speed = 10;

    function type() {
        if (i < text.length) {
            if (text.substr(i, 2) === '\n\n') {
                element.innerHTML += '<br><br>';
                i += 2;
            } else if (text[i] === '\n') {
                element.innerHTML += '<br>';
                i++;
            } else {
                element.innerHTML += text[i];
                i++;
            }
            scrollToBottom();
            setTimeout(type, speed);
        } else {
            // Add timestamp after typing completes
            const time = document.createElement('div');
            time.style.fontSize = '0.65rem';
            time.style.marginTop = '0.4rem';
            time.style.opacity = '0.6';
            time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            element.appendChild(time);
            scrollToBottom();
        }
    }
    type();
}

/**
 * Loads history.
 */
async function loadHistory() {
    try {
        const history = await API.getHistory(sourceId, sourceType);
        chatMessages.innerHTML = '';

        // Initial greeting
        appendMessage(`System connected. Analyzing ${sourceType} context... How can I assist you today?`, true);

        history.forEach(item => {
            appendMessage(item.question, false);
            appendMessage(item.answer, true);
        });
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
