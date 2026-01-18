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

document.addEventListener('DOMContentLoaded', async () => {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const typingIndicator = document.getElementById('typingIndicator');

    // Dynamic Header Title
    const typeLabel = sourceType === 'pdf' ? 'Document' : sourceType === 'youtube' ? 'Video' : 'Webpage';
    document.getElementById('chatHeaderTitle').textContent = `Chat with ${typeLabel}`;

    // Load persistent history
    await loadHistory(chatMessages);

    // --- Chat Form Handler ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        // 1. Add User's message
        appendMessage(chatMessages, message, false);
        messageInput.value = '';

        // 2. Show typing indicator
        typingIndicator.classList.remove('hidden');
        scrollToBottom(chatMessages);

        try {
            // 3. Trigger Backend
            const response = await API.chat(sourceId, sourceType, message);
            typingIndicator.classList.add('hidden');

            // 4. Add AI's answer with animation
            appendMessage(chatMessages, response.answer, true, true);
        } catch (error) {
            typingIndicator.classList.add('hidden');
            appendMessage(chatMessages, 'Error: ' + error.message, true);
        }
    });
});

/**
 * Appends a message to the chat interface.
 */
function appendMessage(container, text, isAI, animate = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message-bubble ${isAI ? 'message-ai' : 'message-user'}`;

    // Formatting helper (bold, code, etc)
    const format = (t) => {
        return t.replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    if (isAI && animate) {
        msgDiv.innerHTML = '';
        container.appendChild(msgDiv);
        typeText(container, msgDiv, text, format);
    } else {
        msgDiv.innerHTML = format(text);

        // Add timestamp
        const time = document.createElement('div');
        time.style.fontSize = '0.65rem';
        time.style.marginTop = '0.6rem';
        time.style.opacity = '0.5';
        time.style.textAlign = isAI ? 'left' : 'right';
        time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        msgDiv.appendChild(time);

        container.appendChild(msgDiv);
    }

    // Use requestAnimationFrame for smoother scrolling
    requestAnimationFrame(() => scrollToBottom(container));
}

/**
 * Simulates a typing effect.
 */
function typeText(container, element, text, formatter) {
    let currentText = "";
    let i = 0;
    const speed = 5; // Even faster for responsiveness

    function type() {
        if (i < text.length) {
            currentText += text[i];
            element.innerHTML = formatter(currentText);
            i++;
            if (i % 3 === 0) scrollToBottom(container); // Scroll every few chars to reduce jank
            setTimeout(type, speed);
        } else {
            const time = document.createElement('div');
            time.style.fontSize = '0.65rem';
            time.style.marginTop = '0.6rem';
            time.style.opacity = '0.5';
            time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            element.appendChild(time);
            scrollToBottom(container);
        }
    }
    type();
}

/**
 * Loads history.
 */
async function loadHistory(container) {
    try {
        const history = await API.getHistory(sourceId, sourceType);
        container.innerHTML = '';

        // Initial greeting
        appendMessage(container, `System connected. Analyzing ${sourceType} context... How can I assist you today?`, true);

        history.forEach(item => {
            appendMessage(container, item.question, false);
            appendMessage(container, item.answer, true);
        });
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

function scrollToBottom(container) {
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}
