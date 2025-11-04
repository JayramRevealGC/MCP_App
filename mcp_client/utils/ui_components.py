"""
UI Components utility for reusable Streamlit components.
Contains functions for rendering headers, sidebars, forms, and other UI elements.
"""

import streamlit as st

# Local Imports
from .config import get_config, get_app_tagline

def render_custom_css():
    """Render the custom CSS styles for the application."""
    css_config = get_config("theme")
    
    st.markdown(f"""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        /* Root variables for consistent theming */
        :root {{
            --primary-blue-light: {css_config['primary_blue_light']};
            --neutral-200: {css_config['neutral_200']};
            --neutral-300: {css_config['neutral_300']};
            --neutral-400: {css_config['neutral_400']};
            --neutral-100: {css_config['neutral_100']};
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }}
        
        /* Global font settings */
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        .stElementContainer > *, 
        .stMetric > div > * {{
            color: #374151;
        }}

        /* Main app background */
        .stApp {{
            background: #f8fafc;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Header gradient */
        .main-header {{
            background: linear-gradient(to right, #2563eb, #3b82f6, #10b981);
            padding: 2rem;
            border-radius: 0 0 0 24px;
            margin: 0 0 2rem 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            position: relative;
            overflow: hidden;
            margin-left: -1rem;
            margin-right: -1rem;
            border: 1px solid rgba(37, 99, 235, 0.3);
        }}

        .stExpander > details > summary, .stExpander > details > summary:hover, details[open] > summary:hover {{
            color: #374151;
        }}

        .stExpander > details[open] > summary {{
            color: #374151;
        }}

        details[open] > div {{
            color: #374151;
        }}

        /* Spinner styling */
        .stSpinner, .stCacheSpinner {{
            background: transparent !important;
        }}
        
        .stSpinner > div, .stSpinner > div > i {{
            color: #374151 !important;
            stroke: #374151 !important;
            fill: #374151 !important;
            background: transparent !important;
            border-color: rgb(250, 250, 250, 0.2) rgba(0, 0, 0) rgba(0, 0, 0);
        }}

        /* Logo styling */
        .logo-container {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            position: relative;
            z-index: 1;
        }}
        
        .logo-image {{
            height: 80px;
            width: auto;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }}
        
        .tagline-text {{
            color: rgba(255,255,255,0.95);
            font-size: 2.5em;
            font-weight: 800;
            margin: 0;
            line-height: 1.2;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        
        /* Minimal chat container */
        .chat-container-minimal {{
            padding: 0.5rem 0;
            margin-bottom: 1rem;
        }}
        
        /* Message bubbles */
        .user-message {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            color: #0c4a6e;
            padding: 16px 24px;
            border-radius: 20px 20px 6px 20px;
            margin: 12px 0;
            margin-left: 25%;
            box-shadow: var(--shadow-md);
            animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            line-height: 1.5;
            border: 1px solid rgba(14, 165, 233, 0.2);
        }}
        
        .bot-message {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: #495057;
            padding: 16px 24px;
            border-radius: 20px 20px 20px 6px;
            margin: 12px 0;
            margin-right: 25%;
            box-shadow: var(--shadow-md);
            animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            line-height: 1.5;
            border: 1px solid rgba(108, 117, 125, 0.2);
        }}
        
        /* Input styling */
        .stTextInput > div {{
            border-radius: 4rem;
            border: transparent;
        }}

        .stTextInput > div > div > input {{
            background: white;
            border: 2px solid var(--neutral-200);
            border-radius: 4rem;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 400;
            color: #495057;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-sm);
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: var(--primary-blue-light);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), var(--shadow-md);
            outline: none;
            caret-color: var(--primary-blue-light);
        }}

        .stTextInput > div > div > input::placeholder {{
            color: var(--neutral-400);
        }}

        /* Form container styling - hide border */
        form[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
        }}
        
        form[data-testid="stForm"] > div {{
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
        }}
        
        div[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
        }}

        /* Audio input button styling */
        .stAudioInput > label {{
            color: #495057;
        }}

        .stAudioInput > div > div > span > button > svg, 
        .stAudioInput > div > span,
        .stElementToolbar > div {{
            background: transparent;
            color: #495057;
        }}

        .stAudioInput > div > div > span:hover > button > svg {{
            color: #3b82f6;
        }}

        .stAudioInput > div {{
            background: white;
            border: 2px solid var(--neutral-200);
            border-radius: 4rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .stAudioInput > div:hover {{
            border-color: #3b82f6;
        }}
        
        /* Button styling */
        .stButton > button {{
            width: 100%;
            background: linear-gradient(to right, #2563eb, #3b82f6, #10b981);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 14px 20px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            text-transform: none;
            min-height: 56px;
        }}
        
        .stButton > button:hover {{
            background: linear-gradient(to right, #1d4ed8, #2563eb, #059669);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Enhanced animations */
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(20px) scale(0.95);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}
        
        /* Sidebar styling - gradient theme */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(to right, #2563eb, #3b82f6, #10b981);
            color: white;
            box-shadow: var(--shadow-xl);
            border-left: 1px solid rgba(37, 99, 235, 0.3);
            width: 300px !important;
        }}
        
        /* Sidebar width fix for Streamlit */
        section[data-testid="stSidebar"] > div {{
            width: 300px !important;
        }}
        
        /* Make all text white in sidebar */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {{
            color: white !important;
            font-weight: 500;
        }}
        
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}
        
        /* Sidebar button styling for blue gradient background */
        section[data-testid="stSidebar"] .stButton > button {{
            background: rgba(255, 255, 255, 0.2);
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            width: 100%;
            min-width: 200px;
        }}
        
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            border-color: rgba(255, 255, 255, 0.5);
        }}
        
        /* Enhanced styling for active/current chat button */
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: rgba(255, 255, 255, 0.4) !important;
            border: 2px solid rgba(255, 255, 255, 0.8) !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.02) !important;
        }}
        
        section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
            background: rgba(255, 255, 255, 0.5) !important;
            border-color: rgba(255, 255, 255, 1) !important;
            transform: scale(1.02) translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(255, 255, 255, 0.4) !important;
        }}
        
        /* Download button styling in sidebar */
        section[data-testid="stSidebar"] .stDownloadButton > button {{
            background: rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
            backdrop-filter: blur(10px) !important;
            width: 100% !important;
            min-width: 200px !important;
        }}
        
        section[data-testid="stSidebar"] .stDownloadButton > button:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
        }}
        
        /* Sidebar info box styling */
        section[data-testid="stSidebar"] .stAlert {{
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }}
        
        /* Dataframe styling */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }}
        
        /* Expander styling in main content */
        .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.8);
            border-radius: 12px;
            font-weight: 600;
            box-shadow: var(--shadow-sm);
        }}
        
        /* Sidebar expander styling - matches gradient theme */
        section[data-testid="stSidebar"] .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.15) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
            backdrop-filter: blur(10px) !important;
            color: white !important;
            padding: 12px 16px !important;
            margin-bottom: 8px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        
        section[data-testid="stSidebar"] .streamlit-expanderHeader:hover {{
            background: rgba(255, 255, 255, 0.25) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        }}
        
        /* Keep expander header background consistent when open */
        section[data-testid="stSidebar"] details[open] > summary,
        section[data-testid="stSidebar"] details[open] .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }}
        
        section[data-testid="stSidebar"] .streamlit-expanderHeader > summary,
        section[data-testid="stSidebar"] details > summary {{
            color: white !important;
        }}
        
        /* Override any Streamlit default backgrounds for expander content */
        section[data-testid="stSidebar"] details[open] > div,
        section[data-testid="stSidebar"] .streamlit-expanderContent > div,
        section[data-testid="stSidebar"] .streamlit-expanderContent .stMarkdown,
        section[data-testid="stSidebar"] .streamlit-expanderContent .stMarkdown > div,
        section[data-testid="stSidebar"] .streamlit-expanderContent .element-container {{
            background: transparent !important;
            color: white !important;
        }}
        
        /* Selectbox styling in sidebar */
        section[data-testid="stSidebar"] .stSelectbox > label {{
            color: white !important;
        }}
        
        section[data-testid="stSidebar"] .stSelectbox > div > div {{
            background: rgba(255, 255, 255, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 8px !important;
        }}
        
        section[data-testid="stSidebar"] .stSelectbox > div > div:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            border-color: rgba(255, 255, 255, 0.5) !important;
        }}
        
        /* Success/Info messages text color */
        section[data-testid="stSidebar"] .stSuccess,
        section[data-testid="stSidebar"] .stSuccess *,
        section[data-testid="stSidebar"] .stInfo,
        section[data-testid="stSidebar"] .stInfo * {{
            color: white !important;
        }}
        
        /* Main content area styling */
        .main .block-container {{
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--neutral-100);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--neutral-300);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--neutral-400);
        }}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header."""
    st.markdown(f"""
    <div class="main-header">
        <div style="text-align: center; color: white;">
            <div class="tagline-text">
                {get_app_tagline()}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_instructions():
    """Render the database instructions expander."""
    instructions_config = get_config("instructions")
    
    with st.expander(instructions_config["title"], expanded=instructions_config["expanded"]):
        st.markdown("**You can perform the following database actions:**")
        
        for instruction in instructions_config["instructions"]:
            st.markdown(instruction)

def render_footer():
    """Render the application footer."""
    app_config = get_config("app")
    
    st.markdown(f"""
    <div style="text-align: center; color: #71717a; font-size: 13px; margin-top: 40px;">
        Powered by advanced AI models • Enterprise-grade security • © {app_config['copyright_year']} {app_config['app_name']}
    </div>
    """, unsafe_allow_html=True)

def render_error_message(message: str, is_timeout: bool = False):
    """Render an error message with appropriate styling."""
    if is_timeout:
        st.error(f"⏰ {message}")
    else:
        st.error(f"❌ {message}")

def render_chat_interface():
    """Render the main chat interface."""
    from .chat_utils import get_current_chat
    from .message_processing import render_chat_messages, process_pending_message_if_any
    
    current_chat = get_current_chat()
    
    # Only render chat container if we have messages
    if current_chat and current_chat.get('messages'):
        st.markdown('<div class="chat-container-minimal">', unsafe_allow_html=True)
        
        # Display chat messages
        render_chat_messages(current_chat)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # After showing messages, process any pending message so the user's text appears immediately before the response is fetched
        process_pending_message_if_any()
    
    # Input area (always render if we have a current chat)
    if current_chat:
        render_input_area()

def render_input_area():
    """Render the input area for user messages."""
    from .message_processing import queue_user_message, clear_input_and_rerun
    
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        transcribed_text = st.session_state.get("transcribed_text", "")
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask about data, run queries, or request analysis...",
                key=f"user_input_{st.session_state.get('input_counter', 0)}",
                value=transcribed_text,
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send", use_container_width=True)
        
        # Handle message sending: queue and rerun to show immediately
        if send_button and user_input:
            if queue_user_message(user_input):
                clear_input_and_rerun()
