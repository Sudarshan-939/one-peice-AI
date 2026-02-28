document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    // UI Elements
    const modelIdInput = document.getElementById('model-id');
    const systemPromptInput = document.getElementById('system-prompt');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const currentModelDisplay = document.getElementById('current-model-display');

    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const clearChatBtn = document.getElementById('clear-chat');

    // State
    let conversationHistory = [];

    // Auto-resize textarea
    messageInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') {
            this.style.height = 'auto';
        }
    });

    // Enter to submit (Shift+Enter for newline)
    messageInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });



    // Update model display when input changes
    modelIdInput.addEventListener('input', () => {
        const selectedOption = modelIdInput.options[modelIdInput.selectedIndex];
        currentModelDisplay.textContent = selectedOption ? selectedOption.text : (modelIdInput.value || 'No model specified');
    });

    // Clear chat
    clearChatBtn.addEventListener('click', () => {
        chatMessages.innerHTML = `
            <div class="message system greeting">
                <div class="avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content">
                    Chat cleared. Ready for a new conversation.
                </div>
            </div>`;
        conversationHistory = [];
        updateStatus('Ready', 'active');
    });

    // Create message element
    function createMessageElement(role, content, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} ${isError ? 'error' : ''}`;

        let iconClass = 'fa-user';
        if (role === 'bot') iconClass = 'fa-robot';
        if (role === 'system') iconClass = 'fa-info-circle';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar';
        avatarDiv.innerHTML = `<i class="fas ${iconClass}"></i>`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Parse markdown if it's the bot or if marked.js is available
        if (typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.textContent = content; // Fallback
        }

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        return messageDiv;
    }

    // Add loading indicator
    function addLoadingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot loading-msg';
        messageDiv.id = 'loading-indicator';

        messageDiv.innerHTML = `
            <div class="avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Remove loading indicator
    function removeLoadingIndicator() {
        const loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.remove();
        }
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Update status
    function updateStatus(text, stateClass = '') {
        statusText.textContent = text;
        statusDot.className = 'status-dot';
        if (stateClass) {
            statusDot.classList.add(stateClass);
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const modelId = modelIdInput.value.trim();
        const systemPrompt = systemPromptInput.value.trim();
        const userMessage = messageInput.value.trim();

        if (!userMessage) return;

        // Reset input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add user message to UI
        chatMessages.appendChild(createMessageElement('user', userMessage));
        scrollToBottom();

        // Update history if empty (add system prompt)
        if (conversationHistory.length === 0 && systemPrompt) {
            conversationHistory.push({
                role: 'system',
                content: systemPrompt
            });
        }

        // Add user message to history
        conversationHistory.push({
            role: 'user',
            content: userMessage
        });

        // Add loading state
        addLoadingIndicator();
        updateStatus('Generating response...', 'active');
        sendButton.disabled = true;

        try {
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: modelId,
                    messages: conversationHistory
                })
            });

            removeLoadingIndicator();

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMsg = errorData.error?.message || `HTTP Error ${response.status}`;
                throw new Error(errorMsg);
            }

            const data = await response.json();
            const botMessage = data.choices[0].message.content;

            // Add bot message to UI
            chatMessages.appendChild(createMessageElement('bot', botMessage));

            // Add bot message to history
            conversationHistory.push({
                role: 'assistant',
                content: botMessage
            });

            updateStatus('Connected', 'active');
        } catch (error) {
            removeLoadingIndicator();
            console.error('API Error:', error);

            // Add error message to UI
            const errorText = `**Error:** ${error.message}\n\nPlease check your API key, connection, or model availability.`;
            chatMessages.appendChild(createMessageElement('bot', errorText, true));
            updateStatus('API Error', 'error');

            // Remove the failed user message from history to allow retry
            conversationHistory.pop();
        } finally {
            sendButton.disabled = false;
            scrollToBottom();
            messageInput.focus();
        }
    });

    // Initialize with default state
    updateStatus('Waiting for input');
});
