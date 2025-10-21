"""
Main Streamlit application for Reveal Labs AI Chat.
Organized and modular frontend using utility components.
"""

import streamlit as st

# Local Imports
from utils.ui_components import (
    render_custom_css, 
    render_header, 
    render_instructions, 
    render_footer
)

from utils.message_processing import (
    process_user_message, 
    render_chat_messages, 
    clear_input_and_rerun
)

from utils.config import get_config
from utils.sidebar_components import render_sidebar
from utils.chat_utils import initialize_session_state, get_current_chat

def main():
    """Main application function."""
    # Configure page
    app_config = get_config("app")
    st.set_page_config(
        page_title=app_config["page_title"],
        page_icon=app_config["page_icon"],
        layout=app_config["layout"],
        initial_sidebar_state=app_config["initial_sidebar_state"]
    )
    
    # Render UI components
    render_custom_css()
    render_header()
    render_instructions()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat interface
    render_chat_interface()
    
    # Footer
    render_footer()

def render_chat_interface():
    """Render the main chat interface."""
    current_chat = get_current_chat()
    
    # Automatically create a new chat if none exists
    if not current_chat:
        from utils.chat_utils import create_new_chat
        create_new_chat()
        current_chat = get_current_chat()
    
    # Only render chat container if we have messages
    if current_chat and current_chat.get('messages'):
        st.markdown('<div class="chat-container-minimal">', unsafe_allow_html=True)
        
        # Display chat messages
        render_chat_messages(current_chat)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area (always render if we have a current chat)
    if current_chat:
        render_input_area()

def render_input_area():
    """Render the input area for user messages."""
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Ask about data, run queries, or request analysis...",
            key=f"user_input_{st.session_state.get('input_counter', 0)}",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    # Handle message sending
    if send_button and user_input:
        success = process_user_message(user_input)
        if success:
            clear_input_and_rerun()

if __name__ == "__main__":
    main()
