"""
Sidebar components utility for chat management and settings.
Contains functions for rendering sidebar elements, chat management, and user settings.
"""

import streamlit as st
from typing import Dict, Any
from datetime import datetime

# Local Imports
from .chat_utils import create_new_chat, get_current_chat

def render_sidebar():
    """Render the complete sidebar with chat management and settings."""
    with st.sidebar:
        render_chat_settings()
        render_chat_management()
        render_chat_history()
        render_export_options()

def render_chat_settings():
    """Render chat settings section in sidebar."""
    st.markdown("### Chat Settings")
    
    # AI Model selection
    model = st.selectbox(
        "AI Model",
        ["GPT-4"],
        index=0
    )
    
    # Store model in session state
    st.session_state.selected_model = model

def render_chat_management():
    """Render chat management section in sidebar."""
    st.markdown("### Chat Management")
    
    # New chat button
    if st.button("New Chat", width='stretch'):
        new_chat_id = create_new_chat()
        st.success(f"Created new chat: {new_chat_id[:8]}...")
        st.rerun()

def render_chat_history():
    """Render chat history section in sidebar."""
    st.subheader("Chat History")
    
    if st.session_state.chats:
        for chat_id, chat_data in st.session_state.chats.items():
            chat_name = f"Chat {chat_id[:8]}"
            is_active = chat_id == st.session_state.current_chat_id
            
            # Style the button differently if it's the active chat
            button_type = "primary" if is_active else "secondary"
            
            if st.button(chat_name, key=f"chat_{chat_id}", type=button_type, width='stretch'):
                st.session_state.current_chat_id = chat_id
                st.rerun()
    else:
        st.info("No chat history yet. Start a new conversation!")

def render_export_options():
    """Render export options section in sidebar."""
    st.markdown("### Export Options")
    
    current_chat = get_current_chat()
    
    if current_chat and current_chat.get('messages'):
        # Download chat history
        if st.button("⬇️ Download Chat"):
            download_chat_history(current_chat)
        
        # Clear chat button
        if st.button("❌ Clear Chat"):
            clear_current_chat()

def download_chat_history(chat_data: Dict[str, Any]):
    """Create and download chat history as text file."""
    try:
        # Create chat history text
        chat_text = f"Chat ID: {chat_data['id']}\n"
        chat_text += f"Created: {chat_data.get('created_at', 'Unknown')}\n"
        chat_text += f"Messages: {len(chat_data.get('messages', []))}\n"
        chat_text += "=" * 50 + "\n\n"
        
        for message in chat_data.get('messages', []):
            role = "User" if message['role'] == 'user' else "Assistant"
            chat_text += f"{role}: {message['content']}\n\n"
        
        # Create download button
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reveal_labs_chat_{timestamp}.txt"
        
        st.download_button(
            label="Download as TXT",
            data=chat_text,
            file_name=filename,
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Error creating download: {str(e)}")

def clear_current_chat():
    """Clear the current chat messages."""
    current_chat = get_current_chat()
    if current_chat:
        current_chat['messages'] = [
            {"role": "assistant", "content": "Chat cleared. How can I help you today?"}
        ]
        st.success("Chat cleared successfully!")
        st.rerun()
