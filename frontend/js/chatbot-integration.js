/**
 * Healthcare Chatbot Frontend Integration Example
 * 
 * This file demonstrates how to integrate the chatbot API
 * into your frontend application.
 */

// ============================================================
// Configuration
// ============================================================

const CHATBOT_API = 'http://127.0.0.1:5000/chatbot';

// SECURITY: Store conversations in browser only (not in database)
const CHAT_STORAGE_KEY = 'healthnova_chat_history';
const MAX_STORED_MESSAGES = 50; // Limit history size

// ============================================================
// Main Chat Function
// ============================================================

/**
 * Send message to chatbot and handle response
 * @param {string} message - User's message
 * @returns {Promise<Object>} - Chatbot response with metadata
 */
async function sendChatMessage(message) {
    try {
        const response = await fetch(`${CHATBOT_API}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_id: getCurrentUserId(), // Optional: track user
                session_id: getSessionId()   // Optional: track conversation
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // SECURITY: Store conversation in browser sessionStorage only
        // This keeps chat history private and not in database
        saveChatMessage('user', message);
        saveChatMessage('bot', data.response, data.metadata);
        
        return data;

    } catch (error) {
        console.error('Chatbot error:', error);
        return {
            success: false,
            response: "I'm having trouble connecting. Please try again later.",
            metadata: {
                response_type: 'error',
                error: error.message
            }
        };
    }
}

// ============================================================
// UI Integration Example
// ============================================================

/**
 * Handle chat submission from UI
 */
async function handleChatSubmit(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('chatMessage');
    const userMessage = messageInput.value.trim();
    
    if (!userMessage) return;
    
    // Clear input
    messageInput.value = '';
    
    // Show user message in UI
    displayMessage(userMessage, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to chatbot
    const result = await sendChatMessage(userMessage);
    
    // Hide typing indicator
    hideTypingIndicator();
    
    // Display chatbot response
    displayMessage(result.response, 'bot');
    
    // Handle metadata for special cases
    handleResponseMetadata(result.metadata);
}

/**
 * Display message in chat UI
 */
function displayMessage(text, sender) {
    const chatContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${sender}`;
    
    // Add icon
    const icon = document.createElement('span');
    icon.className = 'message-icon';
    icon.innerHTML = sender === 'user' 
        ? '<i class="bi bi-person-circle"></i>' 
        : '<i class="bi bi-robot"></i>';
    
    // Add text (support markdown/formatting)
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessageText(text);
    
    messageDiv.appendChild(icon);
    messageDiv.appendChild(textDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Format message text (convert markdown, links, etc.)
 */
function formatMessageText(text) {
    // Convert markdown bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert markdown lists
    text = text.replace(/^\s*[-•]\s/gm, '&bull; ');
    
    // Convert numbered lists
    text = text.replace(/^\s*(\d+)\.\s/gm, '$1. ');
    
    // Convert line breaks
    text = text.replace(/\n/g, '<br>');
    
    // Make phone numbers clickable
    text = text.replace(/(\d{3,4}[-\s]?\d{3,4}[-\s]?\d{4})/g, '<a href="tel:$1">$1</a>');
    
    return text;
}

/**
 * Handle response metadata for special UI behavior
 */
function handleResponseMetadata(metadata) {
    if (!metadata) return;
    
    // Handle emergency responses
    if (metadata.safety_check === 'emergency') {
        highlightAsEmergency();
        playAlertSound();
    }
    
    // Track response types for analytics
    trackAnalytics('chatbot_response', {
        type: metadata.response_type,
        safety_check: metadata.safety_check,
        context_used: metadata.context_retrieved
    });
    
    // Show badge for different response types
    updateResponseTypeBadge(metadata.response_type);
}

/**
 * Highlight chat as emergency
 */
function highlightAsEmergency() {
    const chatContainer = document.getElementById('chatMessages');
    const lastMessage = chatContainer.lastElementChild;
    
    if (lastMessage) {
        lastMessage.classList.add('emergency-message');
        
        // Add emergency banner
        const banner = document.createElement('div');
        banner.className = 'emergency-banner';
        banner.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill"></i>
            <strong>EMERGENCY DETECTED</strong> - Follow instructions immediately
        `;
        chatContainer.appendChild(banner);
    }
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const chatContainer = document.getElementById('chatMessages');
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
    `;
    chatContainer.appendChild(indicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Update response type badge (for debugging/monitoring)
 */
function updateResponseTypeBadge(type) {
    const badge = document.getElementById('responseTypeBadge');
    if (badge) {
        badge.textContent = type;
        badge.className = `badge badge-${type}`;
    }
}

// ============================================================
// Quick Action Buttons
// ============================================================

/**
 * Send predefined quick action message
 */
function sendQuickAction(action) {
    const messages = {
        'book_appointment': 'How do I book an appointment?',
        'lab_results': 'How do I check my lab test results?',
        'video_call': 'How do I start a video consultation?',
        'medical_history': 'Where can I see my medical history?',
        'emergency': 'What should I do in a medical emergency?'
    };
    
    const message = messages[action];
    if (message) {
   Chat History Management (Client-Side Only - SECURE)
// ============================================================

/**
 * Save chat message to browser sessionStorage (not database)
 * @param {string} sender - 'user' or 'bot'
 * @param {string} message - Message text
 * @param {Object} metadata - Optional metadata
 */
function saveChatMessage(sender, message, metadata = null) {
    try {
        const history = getChatHistory();
        
        history.push({
            sender: sender,
            message: message,
            metadata: metadata,
            timestamp: new Date().toISOString()
        });
        
        // Limit history size to prevent storage overflow
        if (history.length > MAX_STORED_MESSAGES) {
            history.shift(); // Remove oldest message
        }
        
        sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
        console.warn('Could not save chat history:', error);
    }
}

/**
 * Get chat history from browser sessionStorage
 * @returns {Array} - Array of chat messages
 */
function getChatHistory() {
    try {
        const history = sessionStorage.getItem(CHAT_STORAGE_KEY);
        return history ? JSON.parse(history) : [];
    } catch (error) {
        console.warn('Could not load chat history:', error);
        return [];
    }
}

/**
 * Clear chat history from browser
 */
function clearChatHistory() {
    try {
        sessionStorage.removeItem(CHAT_STORAGE_KEY);
        console.log('Chat history cleared from browser');
    } catch (error) {
        console.warn('Could not clear chat history:', error);
    }
}

/**
 * Load previous chat history into UI
 */
function loadChatHistory() {
    const history = getChatHistory();
    const chatContainer = document.getElementById('chatMessages');
    
    if (chatContainer && history.length > 0) {
        // Clear welcome message if exists
        chatContainer.innerHTML = '';
       Load previous chat history from sessionStorage
    const history = getChatHistory();
    if (history.length > 0) {
        loadChatHistory();
    } else {
        // Show welcome message only if no history
        displayMessage(
            "Hello! 👋 I'm your Health Nova assistant. I can help you with appointments, lab tests, and general health guidance. How can I assist you today?",
            'bot'
        );
    }
    
    // Add clear history button if needed
    addClearHistoryButton();
});

/**
 * Add clear history button to chat interface
 */    <!-- Clear history button added automatically -->
    </div>
    
    <!-- Chat Messages -->
    <div id="chatMessages" class="chat-messages">
        <!-- Messages loaded from sessionStorage or welcome message -->
    </div>
    
    <!-- Security Notice -->
    <div class="chat-security-notice">
        <small><i class="bi bi-shield-check"></i> Chats stored locally only, not in database</small');
        clearBtn.id = 'clearHistoryBtn';
        clearBtn.className = 'btn btn-sm btn-outline-secondary ms-auto';
        clearBtn.innerHTML = '<i class="bi bi-trash"></i>';
        clearBtn.title = 'Clear chat history';
        clearBtn.onclick = function() {
            if (confirm('Clear chat history? This cannot be undone.')) {
                clearChatHistory();
                document.getElementById('chatMessages').innerHTML = '';
                displayMessage(
                    "Chat history cleared. How can I help you?",
                    'bot'
                );
            }
        };
        chatHeader.appendChild(clearBtn);
    }
} }
}

// ============================================================
//      document.getElementById('chatMessage').value = message;
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
    }
}

// ============================================================
// Helper Functions
// ============================================================

/**
 * Get current user ID (from session storage or authentication)
 */
function getCurrentUserId() {
    const user = JSON.parse(sessionStorage.getItem('user') || '{}');
    return user.id || null;
}

/**
 * Get or create session ID for conversation tracking
 */
function getSessionId() {
    let sessionId = sessionStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('chatSessionId', sessionId);
    }
    return sessionId;
}

/**
 * Track analytics (replace with your analytics service)
 */
function trackAnalytics(event, data) {
    // Example: Google Analytics
    // gtag('event', event, data);
    
    // Example: Custom analytics
    console.log('Analytics:', event, data);
}

/**
 * Play alert sound for emergencies
 */
function playAlertSound() {
    // Add audio element for emergency alert
    const audio = new Audio('/assets/sounds/alert.mp3');
    audio.play().catch(e => console.log('Audio play failed:', e));
}

// ============================================================
// Initialize on Page Load
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Attach event listener to chat form
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }
    
    // Attach event listeners to quick action buttons
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            sendQuickAction(this.dataset.action);
        });
    });
    
    // Show welcome message
    displayMessage(
        "Hello! 👋 I'm your Health Nova assistant. I can help you with appointments, lab tests, and general health guidance. How can I assist you today?",
        'bot'
    );
});

// ============================================================
// Example HTML Structure
// ============================================================

/*
<div class="chatbot-container">
    <!-- Chat Header -->
    <div class="chat-header">
        <i class="bi bi-robot"></i>
        <span>Health Nova Assistant</span>
        <span id="responseTypeBadge" class="badge"></span>
    </div>
    
    <!-- Chat Messages -->
    <div id="chatMessages" class="chat-messages">
        <!-- Messages will be added here dynamically -->
    </div>
    
    <!-- Quick Actions -->
    <div class="quick-actions">
        <button class="quick-action-btn" data-action="book_appointment">
            <i class="bi bi-calendar"></i> Book Appointment
        </button>
        <button class="quick-action-btn" data-action="lab_results">
            <i class="bi bi-file-medical"></i> Lab Results
        </button>
        <button class="quick-action-btn" data-action="video_call">
            <i class="bi bi-camera-video"></i> Video Call
        </button>
    </div>
    
    <!-- Chat Input -->
    <form id="chatForm" class="chat-form">
        <input 
            type="text" 
            id="chatMessage" 
            placeholder="Type your message..." 
            autocomplete="off"
            required
        />
        <button type="submit">
            <i class="bi bi-send"></i>
        </button>
    </form>
</div>
*/

// ============================================================
// Example CSS (Add to your stylesheet)
// ============================================================

/*
.message {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
    padding: 10px;
    border-radius: 8px;
}

.message-user {
    background-color: #e3f2fd;
    flex-direction: row-reverse;
}

.message-bot {
    background-color: #f5f5f5;
}

.emergency-message {
    background-color: #ffebee !important;
    border: 2px solid #f44336;
}

.chat-security-notice {
    background-color: #e8f5e9;
    padding: 5px 10px;
    text-align: center;
    font-size: 11px;
    color: #2e7d32;
    border-top: 1px solid #c8e6c9;
}

.chat-security-notice i {
    margin-right: 5px;
}

.emergency-banner {
    background-color: #f44336;
    color: white;
    padding: 10px;
    text-align: center;
    border-radius: 5px;
    margin-top: 10px;
}

.typing-indicator {
    display: flex;
    gap: 5px;
    padding: 10px;
}

.typing-indicator .dot {
    width: 8px;
    height: 8px;
    background-color: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite;
}

.typing-indicator .dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-10px);
    }
}
*/
