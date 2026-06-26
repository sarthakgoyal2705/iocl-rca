document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages-container');

    // Create unique IDs for typing indicators
    let typingIndicatorId = 0;

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        // Disable input while processing
        queryInput.value = '';
        queryInput.disabled = true;
        sendButton.disabled = true;

        // Add user message to UI
        appendUserMessage(query);

        // Add typing indicator
        const currentTypingId = `typing-${++typingIndicatorId}`;
        appendTypingIndicator(currentTypingId);

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator(currentTypingId);

            if (response.ok) {
                appendBotMessage(data.answer, data.sources);
            } else {
                appendBotMessage(`Error: ${data.error || 'Something went wrong.'}`);
            }

        } catch (error) {
            removeTypingIndicator(currentTypingId);
            appendBotMessage(`Connection Error: ${error.message}`);
        } finally {
            // Re-enable input
            queryInput.disabled = false;
            sendButton.disabled = false;
            queryInput.focus();
        }
    });

    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-message';
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-user"></i></div>
            <div class="message-content">
                <p>${escapeHTML(text)}</p>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendBotMessage(text, sources = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message';
        
        let sourcesHTML = '';
        if (sources && sources.length > 0) {
            // Deduplicate sources by file and page
            const uniqueSources = [];
            const seen = new Set();
            sources.forEach(s => {
                const key = `${s.file}-${s.page}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    uniqueSources.push(s);
                }
            });

            let listItems = uniqueSources.map(s => `<li><i class="fa-solid fa-link"></i> ${escapeHTML(s.file)} (Page ${s.page})</li>`).join('');
            
            sourcesHTML = `
                <div class="sources-box">
                    <strong>Sources Used:</strong>
                    <ul>${listItems}</ul>
                </div>
            `;
        }

        // Extremely simple markdown-like parsing for bold text and newlines
        let formattedText = escapeHTML(text)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <p>${formattedText}</p>
                ${sourcesHTML}
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendTypingIndicator(id) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message typing';
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // Modal Logic
    const navDocs = document.getElementById('nav-docs');
    const navSettings = document.getElementById('nav-settings');
    const docsModal = document.getElementById('docs-modal');
    const settingsModal = document.getElementById('settings-modal');
    const closeButtons = document.querySelectorAll('.close-modal');

    navDocs.addEventListener('click', (e) => {
        e.preventDefault();
        docsModal.classList.remove('hidden');
    });

    navSettings.addEventListener('click', (e) => {
        e.preventDefault();
        settingsModal.classList.remove('hidden');
    });

    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            docsModal.classList.add('hidden');
            settingsModal.classList.add('hidden');
        });
    });

    // Close on clicking outside modal content
    window.addEventListener('click', (e) => {
        if (e.target === docsModal) {
            docsModal.classList.add('hidden');
        }
        if (e.target === settingsModal) {
            settingsModal.classList.add('hidden');
        }
    });

});
