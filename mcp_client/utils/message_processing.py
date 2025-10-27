"""
Message processing utility for handling user input and MCP responses.
Contains functions for processing messages, handling errors, and managing chat flow.
"""

import pandas as pd
import streamlit as st
from functools import lru_cache
from typing import Dict, Any, Optional

# Local Imports
from .config import get_config
from .mcp_client import MCPClient
from .ui_components import render_error_message
from .chat_utils import get_current_chat, add_message_to_chat
from .display_utils import extract_content_from_result, is_summary_data, display_summary_data, is_visualization_data, render_histogram

def process_user_message(user_input: str) -> bool:
    """
    Process a user message and handle the MCP response.
    
    Args:
        user_input: The user's input message
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    if not user_input.strip():
        st.warning("Please enter a message.")
        return False
    
    # Get current chat
    current_chat = get_current_chat()
    if not current_chat:
        st.error("No active chat session. Please create a new chat.")
        return False
    
    # Add user message to chat
    add_message_to_chat(current_chat['id'], "user", user_input)
    
    # Initialize MCP client if needed
    mcp_client = current_chat['mcp_client']
    if not mcp_client.session_id:
        with st.spinner("Initializing MCP session..."):
            if not mcp_client.initialize_session():
                render_error_message("Failed to initialize MCP session. Please try again.")
                add_message_to_chat(current_chat['id'], "assistant", "Failed to initialize MCP session. Please try again.")
                return True  # Continue processing to clear input
    
    # Process the message
    return process_mcp_request(mcp_client, user_input, current_chat)

@lru_cache(maxsize=1)
def _get_mcp_tool_name() -> str:
    """Cache the MCP tool name to avoid repeated config lookups."""
    return get_config("mcp")["tool_name"]

def process_mcp_request(mcp_client: MCPClient, user_input: str, current_chat: Dict[str, Any]) -> bool:
    """
    Process the MCP request and handle the response.
    
    Args:
        mcp_client: The MCP client instance
        user_input: The user's input message
        current_chat: The current chat data
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    tool_name = _get_mcp_tool_name()
    
    # Call the MCP tool
    with st.spinner("Processing your request..."):
        try:
            response = mcp_client.call_tool(tool_name, {"user_query": user_input})
            return handle_mcp_response(response, current_chat)
            
        except Exception as e:
            _handle_error(f"Error processing request: {str(e)}", current_chat)
            return True  # Continue processing to clear input

def _handle_error(error_msg: str, current_chat: Dict[str, Any], is_timeout: bool = False) -> None:
    """Centralized error handling to reduce code duplication."""
    if is_timeout:
        render_error_message(
            "Query timed out after 30 seconds. Please try a more specific query or reduce the data size.",
            is_timeout=True
        )
        add_message_to_chat(current_chat['id'], "assistant", f"⏰ Query timeout: {error_msg}")
    else:
        render_error_message(error_msg)
        add_message_to_chat(current_chat['id'], "assistant", f"Error: {error_msg}")

def handle_mcp_response(response: Optional[Dict[str, Any]], current_chat: Dict[str, Any]) -> bool:
    """
    Handle the MCP response and update the chat.
    
    Args:
        response: The MCP response
        current_chat: The current chat data
        
    Returns:
        bool: True if handling was successful, False otherwise
    """
    # Early return for no response
    if not response:
        _handle_error("No response received from MCP server", current_chat)
        return True
    
    # Early return for response errors
    if "error" in response:
        error_msg = response["error"]
        is_timeout = "timeout" in error_msg.lower()
        _handle_error(error_msg, current_chat, is_timeout)
        return True
    
    # Process successful response
    result = response.get('result')
    if not result:
        _handle_error("Failed to get response from MCP server", current_chat)
        return True
    
    # Check if result contains an error
    if isinstance(result, dict) and result.get('isError'):
        error_msg = result.get('content', 'Unknown error occurred')
        _handle_error(error_msg, current_chat)
        return True
    
    # Extract and process content
    content = extract_content_from_result(result)
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict) and 'error' in content[0]:
        _handle_error(content[0]['error'], current_chat)
        return True
    
    # Handle different types of content
    return handle_content_response(content, current_chat)

def _create_dataframe_safely(content: list) -> pd.DataFrame:
    """Safely create DataFrame with optimized type conversion."""
    if not content:
        return pd.DataFrame()
    
    df = pd.DataFrame(content)
    # Only convert to string if there are actual columns
    if not df.empty:
        df = df.astype(str)
    return df

def handle_content_response(content: Any, current_chat: Dict[str, Any]) -> bool:
    """
    Handle different types of content responses.
    
    Args:
        content: The extracted content from MCP response
        current_chat: The current chat data
        
    Returns:
        bool: True if handling was successful, False otherwise
    """
    try:
        chat_id = current_chat['id']
        
        # Use early returns for better flow control
        if is_visualization_data(content):
            add_message_to_chat(chat_id, "assistant", content)
            return True
            
        if is_summary_data(content):
            add_message_to_chat(chat_id, "assistant", content)
            return True
            
        if isinstance(content, list) and content:
            df = _create_dataframe_safely(content)
            add_message_to_chat(chat_id, "assistant", df)
            return True
            
        # Default case
        add_message_to_chat(chat_id, "assistant", "No data to display")
        return True
        
    except Exception as e:
        _handle_error(f"Error processing content: {str(e)}", current_chat)
        return False

def render_chat_messages(current_chat=None):
    """Render all chat messages in the current chat."""
    if current_chat is None:
        current_chat = get_current_chat()
    
    if not current_chat or not current_chat.get('messages'):
        st.info("No messages yet. Start a conversation!")
        return
    
    # Render each message
    for message in current_chat['messages']:
        render_single_message(message)

def render_single_message(message: Dict[str, Any]):
    """
    Render a single chat message.
    
    Args:
        message: The message data containing role and content
    """
    role = message['role']
    content = message['content']

    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
        
        # Display audio if present
        if message.get("audio"):
            with st.expander("🎧 Audio clip"):
                st.audio(message["audio"])
    else:
        # Handle different content types for assistant messages
        if is_visualization_data(content):
            # Display visualization data
            visualization = content.get("visualization", {})
            if visualization.get("type") == "bar_chart":
                render_histogram(content, chart_type="bar")
            elif visualization.get("type") == "histogram":
                render_histogram(content)
            else:
                st.error(f"Unsupported visualization type: {visualization.get('type')}")
        elif is_summary_data(content):
            # Display summary data
            display_summary_data(content)
        elif isinstance(content, pd.DataFrame):
            # Display dataframe
            st.dataframe(content, width='stretch', hide_index=True)
        else:
            # Display regular text message
            st.markdown(f'<div class="bot-message">{content}</div>', unsafe_allow_html=True)

def clear_input_and_rerun():
    """Clear the input field and rerun the app to display new messages."""
    st.session_state.input_counter = st.session_state.get('input_counter', 0) + 1
    st.rerun()
