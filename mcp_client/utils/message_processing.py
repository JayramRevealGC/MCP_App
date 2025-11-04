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
from .display_utils import extract_content_from_result
from .chat_utils import get_current_chat, add_message_to_chat

def queue_user_message(user_input: str) -> bool:
    """Queue the user's message and mark it for processing, then return immediately.
    This enables the UI to rerun and show the user's message before the response arrives.
    """
    if not user_input.strip():
        st.warning("Please enter a message.")
        return False

    current_chat = get_current_chat()
    if not current_chat:
        st.error("No active chat session. Please create a new chat.")
        return False

    audio_bytes = st.session_state.get('current_audio_bytes')
    if audio_bytes:
        add_message_to_chat(current_chat['id'], "user", user_input, audio_bytes)
    else:
        add_message_to_chat(current_chat['id'], "user", user_input)

    # Mark message as pending to process on next render cycle
    st.session_state.pending_user_input = user_input
    return True

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
    
    # Call the MCP tool with session_id
    with st.spinner("Processing your request..."):
        try:
            arguments = {
                "user_query": user_input,
                "session_id": mcp_client.session_id
            }
            response = mcp_client.call_tool(tool_name, arguments)
            return handle_mcp_response(response, current_chat)
            
        except Exception as e:
            _handle_error(f"Error processing request: {str(e)}", current_chat)
            return True  # Continue processing to clear input

def process_pending_message_if_any() -> None:
    """If a user message was queued, process it now and rerun after completion."""
    pending = st.session_state.get('pending_user_input')
    if not pending:
        return

    current_chat = get_current_chat()
    if not current_chat:
        # Clear pending to avoid loops if chat disappeared
        st.session_state.pending_user_input = None
        return

    mcp_client: MCPClient = current_chat['mcp_client']
    if not mcp_client.session_id:
        with st.spinner("Initializing MCP session..."):
            if not mcp_client.initialize_session():
                render_error_message("Failed to initialize MCP session. Please try again.")
                add_message_to_chat(current_chat['id'], "assistant", "Failed to initialize MCP session. Please try again.")
                st.session_state.pending_user_input = None
                st.rerun()
                return

    # Process and then clear pending
    _ = process_mcp_request(mcp_client, pending, current_chat)
    st.session_state.pending_user_input = None
    st.rerun()

def _handle_error(error_msg: str, current_chat: Dict[str, Any], is_timeout: bool = False) -> None:
    """Centralized error handling to reduce code duplication."""
    if is_timeout:
        render_error_message(
            "Query timed out after 30 seconds. Please try a more specific query or reduce the data size.",
            is_timeout=True
        )
        add_message_to_chat(current_chat['id'], "assistant", f"Query timeout: {error_msg}")
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
    
    # Check for unknown action response
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
        first_item = content[0]
        if first_item.get('action') == 'unknown':
            # Handle unknown action - show message with supported queries
            unknown_content = {
                'unknown_action': True,
                'message': first_item.get('message', 'Your query doesn\'t match any supported query types.')
            }
            add_message_to_chat(current_chat['id'], "assistant", unknown_content)
            return True
    
    # Check for error responses
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict) and 'error' in content[0]:
        # Check if error response includes SQL query
        error_item = content[0]
        error_msg = error_item['error']
        sql_query = error_item.get('sql_query')
        sql_params = error_item.get('sql_params', [])
        
        # Store error message with SQL query if available
        if sql_query:
            error_content = {
                'error': error_msg,
                'sql_query': sql_query,
                'sql_params': sql_params
            }
            add_message_to_chat(current_chat['id'], "assistant", error_content)
        else:
            _handle_error(error_msg, current_chat)
        return True
    
    # Handle different types of content
    return handle_content_response(content, current_chat)

def _extract_sql_query(content: list) -> tuple:
    """Extract SQL query from content list and return (content_without_sql, sql_query)."""
    if not content or not isinstance(content, list) or len(content) == 0:
        return content, None
    
    # Check if first item has sql_query field
    first_item = content[0]
    if isinstance(first_item, dict) and 'sql_query' in first_item:
        sql_query = first_item.get('sql_query')
        sql_params = first_item.get('sql_params', [])
        
        # Remove sql_query and sql_params from all items to keep DataFrame clean
        cleaned_content = []
        for item in content:
            if isinstance(item, dict):
                cleaned_item = {k: v for k, v in item.items() if k not in ['sql_query', 'sql_params']}
                # Only add non-empty dicts to avoid creating empty rows
                if cleaned_item:
                    cleaned_content.append(cleaned_item)
            else:
                cleaned_content.append(item)
        
        # Format SQL query info
        sql_info = {
            'query': sql_query,
            'params': sql_params
        }
        
        return cleaned_content if cleaned_content else [], sql_info
    
    return content, None

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
        
        # Handle list content (typically DataFrame data)
        if isinstance(content, list) and content:
            # Extract SQL query before creating DataFrame
            cleaned_content, sql_info = _extract_sql_query(content)
            
            # Check if this is an empty query result (only SQL metadata, no data rows)
            is_empty_query = len(cleaned_content) == 0 and sql_info is not None
            
            if is_empty_query:
                # Handle empty query result - show friendly message with SQL
                message_content = {
                    'empty_result': True,
                    'message': "No results found for your query.",
                    'sql_query': sql_info.get('query'),
                    'sql_params': sql_info.get('params', [])
                }
                add_message_to_chat(chat_id, "assistant", message_content)
                return True
            
            # Create DataFrame from non-empty content
            df = _create_dataframe_safely(cleaned_content)
            
            # Add message with SQL query metadata
            if sql_info:
                # Store message with SQL query in a custom structure
                message_content = {
                    'dataframe': df,
                    'sql_query': sql_info.get('query'),
                    'sql_params': sql_info.get('params', [])
                }
                add_message_to_chat(chat_id, "assistant", message_content)
            else:
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
        if isinstance(content, dict) and 'error' in content:
            # Handle error message with optional SQL query
            error_msg = content['error']
            sql_query = content.get('sql_query')
            sql_params = content.get('sql_params', [])
            
            # Display error message
            st.error(f"❌ {error_msg}")
            
            # Display SQL query in an expander if available
            if sql_query:
                with st.expander("View SQL query", expanded=False):
                    st.code(sql_query, language='sql')
                    if sql_params:
                        st.caption(f"Parameters: {sql_params}")
        elif isinstance(content, dict) and 'unknown_action' in content:
            # Handle unknown action response
            
            # Display unknown action message
            st.warning(f"⚠️ Your query doesn\'t match any supported query types.")

        elif isinstance(content, dict) and 'empty_result' in content:
            # Handle empty query result with SQL query
            empty_msg = content.get('message', 'No results found for your query.')
            sql_query = content.get('sql_query')
            sql_params = content.get('sql_params', [])
            
            # Display friendly empty result message
            st.info(f"ℹ️ {empty_msg}")
            
            # Display SQL query in an expander if available
            if sql_query:
                with st.expander("View SQL query", expanded=False):
                    st.code(sql_query, language='sql')
                    if sql_params:
                        st.caption(f"Parameters: {sql_params}")
        elif isinstance(content, dict) and 'dataframe' in content:
            # Handle message with DataFrame and SQL query
            df = content['dataframe']
            sql_query = content.get('sql_query')
            sql_params = content.get('sql_params', [])
            
            # Display dataframe
            st.dataframe(df, width='stretch', hide_index=True)
            
            # Display SQL query in an expander if available
            if sql_query:
                with st.expander("View SQL query", expanded=False):
                    st.code(sql_query, language='sql')
                    if sql_params:
                        st.caption(f"Parameters: {sql_params}")
        elif isinstance(content, pd.DataFrame):
            # Display dataframe (legacy format without SQL)
            st.dataframe(content, width='stretch', hide_index=True)
        else:
            # Display regular text message
            st.markdown(f'<div class="bot-message">{content}</div>', unsafe_allow_html=True)

def clear_input_and_rerun():
    """Clear the input field and rerun the app to display new messages."""
    st.session_state.input_counter = st.session_state.get('input_counter', 0) + 1
    st.session_state.transcribed_text = ""
    st.session_state.current_audio_bytes = None
    st.rerun()
