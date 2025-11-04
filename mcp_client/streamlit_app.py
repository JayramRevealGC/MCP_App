"""
Main Streamlit application for Reveal Labs AI Chat.
Organized and modular frontend using utility components.
"""

import streamlit as st

# Local Imports
from utils.ui_components import (
    render_header, 
    render_footer,
    render_custom_css,
    render_instructions,
    render_chat_interface
)

from utils.config import get_config
from utils.sidebar_components import render_sidebar
from utils.speech_utils import render_audio_transcription
from utils.chat_utils import initialize_session_state, get_current_chat, create_new_chat

# --- PAGE SETUP ---
app_config = get_config("app")
st.set_page_config(
    page_title=app_config["page_title"],
    page_icon=app_config["page_icon"],
    layout=app_config["layout"],
    initial_sidebar_state=app_config["initial_sidebar_state"]
)

# --- CUSTOM CSS ---
render_custom_css()

# --- SIDEBAR ---
# Initialize session state before rendering sidebar
initialize_session_state()

# Initialize chat if needed (before rendering sidebar)
current_chat = get_current_chat()
if not current_chat:
    create_new_chat()

# Render sidebar
speech_model = render_sidebar()

# --- HEADER ---
render_header()

# --- INSTRUCTIONS ---
render_instructions()

# --- MAIN CONTENT (Chat Interface) ---
render_chat_interface()

# --- AUDIO TRANSCRIPTION ---
render_audio_transcription(speech_model)

# --- FOOTER ---
render_footer()
