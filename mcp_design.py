import streamlit as st
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Reveal Labs AI Chat",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with Reveal Labs vibrant theme
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background: linear-gradient(to bottom right, #eff6ff, #d1fae5);
    }
    
    /* Header gradient */
    .main-header {
        background: linear-gradient(to right, #2563eb, #3b82f6, #10b981);
        padding: 1.5rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
    }
    
    .logo-text {
        font-size: 28px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    /* Chat containers */
    .chat-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(to right, #1f2937, #374151);
        color: white;
        padding: 12px 20px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0;
        margin-left: 20%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    }
    
    .bot-message {
        background: linear-gradient(to right, #3b82f6, #2563eb);
        color: white;
        padding: 12px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px 0;
        margin-right: 20%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
    }
    
    /* Quick action buttons */
    .quick-action {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: #2563eb;
        padding: 8px 16px;
        border-radius: 8px;
        margin: 4px;
        display: inline-block;
        transition: all 0.2s ease;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
    }
    
    .quick-action:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: #3b82f6;
        transform: translateY(-1px);
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 12px 20px;
        background: linear-gradient(to right, #3b82f6, #2563eb);
        color: white;
        border-radius: 18px 18px 18px 4px;
        margin-right: 60%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .typing-dot {
        height: 8px;
        width: 8px;
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 50%;
        display: inline-block;
        margin: 0 3px;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(1);
            opacity: 0.7;
        }
        40% {
            transform: scale(1.3);
            opacity: 1;
        }
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #2563eb, #1e40af);
        color: white;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "content": "Welcome to Reveal Labs AI Assistant! I can help you with data analysis, database queries, and AI-powered insights. What can I do for you today?"}
    ]

if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

# Header with logo
st.markdown("""
<div class="main-header">
    <div class="logo-container">
        <span class="logo-text">RL 🌐 Reveal Labs</span>
    </div>
    <p style="color: rgba(255,255,255,0.9); margin-top: 8px; font-size: 16px;">
        AI-Powered Data Intelligence Platform
    </p>
</div>
""", unsafe_allow_html=True)

# Quick actions
st.markdown("""
<div style="margin-bottom: 20px;">
    <span class="quick-action">📊 Database Query</span>
    <span class="quick-action">📈 Table Analysis</span>
    <span class="quick-action">🔍 Smart Search</span>
    <span class="quick-action">📄 Generate Report</span>
</div>
""", unsafe_allow_html=True)

# Chat interface
chat_container = st.container()

with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Typing indicator
    if st.session_state.is_typing:
        st.markdown("""
        <div class="typing-indicator">
            <span>Analyzing data</span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Input area
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "Message",
        placeholder="Ask about data, run queries, or request analysis...",
        key="user_input",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send", use_container_width=True)

# Handle message sending
if send_button and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Set typing indicator
    st.session_state.is_typing = True
    st.rerun()

# Simulate bot response
if st.session_state.is_typing:
    time.sleep(1.5)  # Simulate processing time
    
    # Add bot response
    bot_responses = [
        "I've analyzed your request. Based on the data patterns, here are my insights...",
        "Processing your query through our advanced AI models. The results show interesting patterns in the dataset.",
        "I understand your query. Let me process that information using our data analytics capabilities.",
        "Great question! I've examined the relevant data and here's what I found...",
    ]
    
    import random
    response = random.choice(bot_responses)
    
    st.session_state.messages.append({"role": "bot", "content": response})
    st.session_state.is_typing = False
    st.rerun()

# Sidebar with additional options
with st.sidebar:
    st.markdown("### Chat Settings")
    
    model = st.selectbox(
        "AI Model",
        ["GPT-4", "Claude Opus", "Llama 3.1"],
        index=0
    )
    
    st.markdown("### Export Options")
    if st.button("📥 Download Chat"):
        # Create chat history text
        chat_text = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'RL Bot'}: {msg['content']}" 
            for msg in st.session_state.messages
        ])
        st.download_button(
            label="Download as TXT",
            data=chat_text,
            file_name=f"reveal_labs_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    st.markdown("### Quick Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Current Model", model)
    
    if st.button("Clear Chat"):
        st.session_state.messages = [
            {"role": "bot", "content": "Chat cleared. How can I help you today?"}
        ]
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 12px; margin-top: 40px;">
    Powered by advanced AI models • Enterprise-grade security • © 2024 Reveal Labs
</div>
""", unsafe_allow_html=True)