"""
Configuration utilities for the MCP Client application.
Contains app settings, constants, and configuration management.
"""

from typing import Dict, Any

# App Configuration
APP_CONFIG = {
    "page_title": "Reveal Labs AI Chat",
    "page_icon": "🌐",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
    "app_name": "Reveal Labs",
    "app_tagline": "AI-Powered Data Intelligence Platform",
    "copyright_year": "2025"
}

# MCP Server Configuration
MCP_CONFIG = {
    "server_url": "http://54.164.108.181:8001/mcp",
    "timeout": 30,  # seconds
    "tool_name": "query_users"
}

# UI Configuration
UI_CONFIG = {
    "logo_path": "RevealLabs_Logo.png"  # Relative path for Docker compatibility
}

# Color Theme Configuration
THEME_CONFIG = {
    "primary_blue_light": "#6366f1", 
    "neutral_200": "#e4e4e7",
    "neutral_300": "#d4d4d8",
    "neutral_400": "#a1a1aa",
    "neutral_100": "#f4f4f5"
}

# Database Instructions Configuration
DB_INSTRUCTIONS = {
    "title": "What can you do?",
    "expanded": True,
    "instructions": [
        "**🗂️ Fetch Tables**: List all available tables in the database",
        "**📄 Fetch Records**: Get n records from any table with advanced filtering and sorting", 
        "**🔗 Join Tables**: Join two tables with flexible join types",
        "**➕ Append Tables**: Combine two tables vertically using UNION ALL",
        "**📊 Table Summary**: Get comprehensive table information and statistics",
        "**📈 Column Summary**: Create pie charts by counting values in categorical columns",
        "**🔍 Relationship Analysis**: Analyze relationships between categorical and quantitative columns"
    ]
}

def get_config(section: str = None) -> Dict[str, Any]:
    """
    Get configuration values.
    
    Args:
        section: Specific config section to return. If None, returns all configs.
        
    Returns:
        Dictionary containing configuration values
    """
    configs = {
        "app": APP_CONFIG,
        "mcp": MCP_CONFIG,
        "ui": UI_CONFIG,
        "theme": THEME_CONFIG,
        "instructions": DB_INSTRUCTIONS
    }
    
    if section:
        return configs.get(section, {})
    
    return configs

def get_logo_path() -> str:
    """Get the path to the logo file."""
    return UI_CONFIG["logo_path"]


def get_app_tagline() -> str:
    """Get the application tagline."""
    return APP_CONFIG["app_tagline"]
