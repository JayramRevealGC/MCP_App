import uuid
import streamlit as st

#MCP Client Imports
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
        'messages': [],
        'mcp_client': MCPClient()
    }
    st.session_state.current_chat_id = chat_id
    return chat_id

def get_current_chat():
    """Get the current active chat."""
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
        return st.session_state.chats[st.session_state.current_chat_id]
    return None

def add_message_to_chat(chat_id: str, role: str, content):
    """Add a message to a specific chat."""
    if chat_id in st.session_state.chats:
        st.session_state.chats[chat_id]['messages'].append({
            'role': role,
            'content': content
        })
