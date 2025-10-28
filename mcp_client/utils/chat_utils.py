import uuid
import streamlit as st

#Local Imports
from utils.mcp_client import MCPClient

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'chats' not in st.session_state:
        st.session_state.chats = {}
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None

def create_new_chat():
    """Create a new chat session."""
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        'id': chat_id,
        'messages': [
            {"role": "assistant", "content": "Welcome to Reveal Labs AI Assistant! I can help you with data analysis, database queries, and AI-powered insights. What can I do for you today?"}
        ],
        'mcp_client': MCPClient()
    }
    st.session_state.current_chat_id = chat_id
    return chat_id

def get_current_chat():
    """Get the current active chat."""
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
        return st.session_state.chats[st.session_state.current_chat_id]
    return None

def add_message_to_chat(chat_id: str, role: str, content, audio_bytes: bytes | None = None):
    """Add a message to a specific chat."""
    if chat_id in st.session_state.chats:
        if audio_bytes is None:
            st.session_state.chats[chat_id]['messages'].append({
                'role': role,
                'content': content
            })
        else:
            st.session_state.chats[chat_id]['messages'].append({
                'role': role,
                'content': content,
                'audio': audio_bytes
            })
