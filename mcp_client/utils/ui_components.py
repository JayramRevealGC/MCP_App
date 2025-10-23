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
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
            margin-left: -1rem;
            margin-right: -1rem;
            border: 1px solid rgba(37, 99, 235, 0.3);
        }}
        
        .main-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(255,255,255,0.2) 0%, transparent 50%, rgba(255,255,255,0.1) 100%);
            pointer-events: none;
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
            font-size: 32px;
            font-weight: 700;
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
        .stTextInput > div > div > input {{
            background: white;
            border: 2px solid var(--neutral-200);
            border-radius: 16px;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 400;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-sm);
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: var(--primary-blue-light);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), var(--shadow-md);
            outline: none;
        }}
        
        /* Button styling */
        .stButton > button {{
            background: linear-gradient(to right, #2563eb, #3b82f6, #10b981);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 14px 28px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            text-transform: none;
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
            border-radius: 0 24px 0 0;
            border-left: 1px solid rgba(37, 99, 235, 0.3);
        }}
        
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {{
            color: white !important;
            font-weight: 500;
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
            color: white !important;
            backdrop-filter: blur(10px);
        }}
        
        section[data-testid="stSidebar"] .stAlert > div {{
            color: white !important;
        }}
        
        section[data-testid="stSidebar"] .stAlert p {{
            color: white !important;
        }}
        
        /* Dataframe styling */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }}
        
        /* Expander styling */
        .streamlit-expanderHeader {{
            background: rgba(255, 255, 255, 0.8);
            border-radius: 12px;
            font-weight: 600;
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
