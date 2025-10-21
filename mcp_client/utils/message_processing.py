"""
Message processing utility for handling user input and MCP responses.
Contains functions for processing messages, handling errors, and managing chat flow.
"""

import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional

# Local Imports
from .config import get_config
from .mcp_client import MCPClient
from .ui_components import render_error_message
from .chat_utils import get_current_chat, add_message_to_chat
from .display_utils import extract_content_from_result, is_summary_data, display_summary_data, is_visualization_data, render_bar_chart, render_histogram


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
                return False
    
    # Process the message
    return process_mcp_request(mcp_client, user_input, current_chat)

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
    mcp_config = get_config("mcp")
    tool_name = mcp_config["tool_name"]
    
    # Call the MCP tool
    with st.spinner("Processing your request..."):
        try:
            response = mcp_client.call_tool(tool_name, {"user_query": user_input})
            # Handle response
            return handle_mcp_response(response, current_chat)
            
        except Exception as e:
            render_error_message(f"Error processing request: {str(e)}")
            add_message_to_chat(current_chat['id'], "assistant", f"Error: {str(e)}")
            return False

def handle_mcp_response(response: Optional[Dict[str, Any]], current_chat: Dict[str, Any]) -> bool:
    """
    Handle the MCP response and update the chat.
    
    Args:
        response: The MCP response
        current_chat: The current chat data
        
    Returns:
        bool: True if handling was successful, False otherwise
    """
    if not response:
        render_error_message("No response received from MCP server")
        add_message_to_chat(current_chat['id'], "assistant", "No response received from MCP server")
        return False
    
    # Check for errors in response
    if "error" in response:
        error_msg = response["error"]
        is_timeout = "timeout" in error_msg.lower()
        
        if is_timeout:
            render_error_message(
                "Query timed out after 30 seconds. Please try a more specific query or reduce the data size.",
                is_timeout=True
            )
            add_message_to_chat(current_chat['id'], "assistant", f"⏰ Query timeout: {error_msg}")
        else:
            render_error_message(error_msg)
            add_message_to_chat(current_chat['id'], "assistant", f"Error: {error_msg}")
        return False
    
    # Process successful response
    result = response.get('result')
    if not result:
        render_error_message("Failed to get response from MCP server")
        add_message_to_chat(current_chat['id'], "assistant", "Failed to get response from MCP server")
        return False
    
    # Extract and process content
    content, is_error = extract_content_from_result(result)
    
    if is_error:
        render_error_message(str(content))
        add_message_to_chat(current_chat['id'], "assistant", f"Error: {content}")
        return False
    
    # Handle different types of content
    return handle_content_response(content, current_chat)

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
        # Check if this is visualization data
        if is_visualization_data(content):
            # Store the visualization data in chat history for proper display
            add_message_to_chat(current_chat['id'], "assistant", content)
            
        # Check if this is summary data
        elif is_summary_data(content):
            # Store the raw summary data in chat history for proper display
            add_message_to_chat(current_chat['id'], "assistant", content)
            
        elif isinstance(content, list) and len(content) > 0:
            # Handle data table
            df = pd.DataFrame(content)
            df = df.astype(str)
            add_message_to_chat(current_chat['id'], "assistant", df)
            
        else:
            # Handle other content types
            add_message_to_chat(current_chat['id'], "assistant", "No data to display")
        
        return True
        
    except Exception as e:
        render_error_message(f"Error processing content: {str(e)}")
        add_message_to_chat(current_chat['id'], "assistant", f"Error processing content: {str(e)}")
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
    else:
        # Handle different content types for assistant messages
        if is_visualization_data(content):
            # Display visualization data
            visualization = content.get("visualization", {})
            if visualization.get("type") == "bar_chart":
                render_bar_chart(content)
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
