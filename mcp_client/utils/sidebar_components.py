"""
Sidebar components utility for chat management and settings.
Contains functions for rendering sidebar elements, chat management, and user settings.
"""

import os
import base64
import streamlit as st
from typing import Dict, Any
from datetime import datetime

# Local Imports
from .config import get_logo_path
from .speech_utils import render_speech_settings
from .chat_utils import create_new_chat, get_current_chat

def render_sidebar():
    """Render the complete sidebar with chat management and settings."""
    with st.sidebar:
        render_sidebar_logo()
        st.markdown("---")

        # Chat Management Section - Collapsible
        with st.expander("Chat Management", expanded=True):
            render_chat_management()
            render_chat_history()
        
        st.markdown("---")

        # Settings Section - Collapsible
        with st.expander("Settings", expanded=False):
            render_chat_settings()
            st.markdown("---")
            speech_model = render_speech_settings()
        
        st.markdown("---")
        
        # Export Options Section - Collapsible
        render_export_options()

    return speech_model

def render_sidebar_logo():
    """Render the logo and tagline at the top of the sidebar."""
    try:
        logo_path = get_logo_path()
        
        # Try multiple possible paths for logo file
        possible_paths = [
            logo_path,  # Original path from config
            f"/app/{logo_path}",  # Docker container path
            f"./{logo_path}",  # Current directory
            f"../{logo_path}",  # Parent directory
        ]
        
        logo_found = False
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode()
                logo_found = True
                break
        
        if not logo_found:
            raise FileNotFoundError(f"Logo file not found in any of the expected locations: {possible_paths}")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <img src="data:image/png;base64,{logo_data}" alt="Reveal Labs Logo" style="height: 100px; width: auto; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">
        </div>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Logo file not found. Please check the logo path in configuration.")
    except Exception as e:
        st.error(f"Error loading logo: {str(e)}")

def render_chat_settings():
    """Render chat settings section in sidebar."""
    st.markdown("#### AI Model")
    
    # AI Model selection
    model = st.selectbox(
        "Model",
        ["GPT-4"],
        index=0,
        label_visibility="collapsed"
    )
    
    # Store model in session state
    st.session_state.selected_model = model

def render_chat_management():
    """Render chat management section in sidebar."""
    # New chat button
    if st.button("New Chat", use_container_width=True):
        new_chat_id = create_new_chat()
        st.success(f"Created new chat: {new_chat_id[:8]}...")
        st.rerun()

def render_chat_history():
    """Render chat history section in sidebar."""
    st.markdown("#### Chat History")
    
    if st.session_state.chats:
        for chat_id, chat_data in st.session_state.chats.items():
            is_active = chat_id == st.session_state.current_chat_id
            
            # Add visual indicator for current chat
            if is_active:
                chat_name = f"Chat {chat_id[:8]}"
            else:
                chat_name = f"Chat {chat_id[:8]}"
            
            # Style the button differently if it's the active chat
            button_type = "primary" if is_active else "secondary"
            
            if st.button(chat_name, key=f"chat_{chat_id}", type=button_type, use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
    else:
        st.info("No chat history yet. Start a new conversation!")

def render_export_options():
    """Render export options section in sidebar."""
    
    current_chat = get_current_chat()
    
    if current_chat and current_chat.get('messages'):
        # Export Options Section - Collapsible
        with st.expander("Export Options", expanded=False):
            # Download chat history - direct download
            download_chat_history(current_chat)

            # Clear chat button
            if st.button("Clear Chat", use_container_width=True):
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
        
        # Create download button with direct download
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reveal_labs_chat_{timestamp}.txt"
        
        st.download_button(
            label="Download Chat",
            data=chat_text,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
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
