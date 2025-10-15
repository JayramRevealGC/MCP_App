import pandas as pd
import streamlit as st

#MCP Client Imports
from utils.display_utils import extract_content_from_result, is_summary_data, display_summary_data
from utils.chat_utils import initialize_session_state, create_new_chat, get_current_chat, add_message_to_chat

def main():
    st.set_page_config(
        page_title="MCP Chat App",
        layout="wide"
    )
     
    st.title("MCP Chat Application")
    st.markdown("Start a new chat to interact with the MCP server!")
    
    # User instructions section
    with st.expander("What can you do?", expanded=True):
        st.markdown("""
        **You can perform the following database actions:**
        
        1. **Fetch Tables**: See all available tables in the database
        
        2. **Fetch Records**: Get **n** records from any table
        
        3. **Find Specific Record**: Search for a record from item_kaus table through **id** field
        
        4. **Join Tables**: Join two tables and return **n** rows
        
        5. **Table Summary**: Get comprehensive summary information about any table including row count, column count, column names, and sample data
        """)
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for chat management
    with st.sidebar:
        st.header("Chat Management")
        
        # New chat button
        if st.button("New Chat", width='stretch'):
            new_chat_id = create_new_chat()
            st.success(f"Created new chat: {new_chat_id[:8]}...")
            st.rerun()
        
        # Chat list
        st.subheader("Chat History")
        if st.session_state.chats:
            for chat_id, chat_data in st.session_state.chats.items():
                chat_name = f"Chat {chat_id[:8]}"
                is_active = chat_id == st.session_state.current_chat_id
                
                # Style the button differently if it's the active chat
                button_type = "primary" if is_active else "secondary"
                
                if st.button(f"{chat_name}", 
                           key=f"chat_{chat_id}",
                           width='stretch',
                           type=button_type):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        else:
            st.info("No chats yet. Create a new chat to get started!")
    
    # Main chat interface
    current_chat = get_current_chat()
    
    if current_chat is None:
        st.info("Click **New Chat** in the sidebar to start a conversation!")
        return
    
    # Chat messages container
    messages_container = st.container()
    
    with messages_container:
        for message in current_chat['messages']:
            with st.chat_message(message['role']):
                if isinstance(message['content'], pd.DataFrame):
                    message['content'] = message['content'].astype(str)
                    st.dataframe(message['content'], width='stretch', hide_index=True)
                elif isinstance(message['content'], dict) and message['content'].get('type') == 'summary':
                    # Display summary data from chat history
                    summary_data = message['content']
                    st.subheader(f"Table Summary: {summary_data.get('table_name', 'Unknown')}")
                    
                    # Create columns for metrics
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Rows", summary_data.get('row_count', 0))
                    
                    with col2:
                        st.metric("Total Columns", summary_data.get('column_count', 0))
                    
                    # Display column names in a table format
                    column_names = summary_data.get('column_names', [])
                    if column_names:
                        st.subheader("Column Names")
                        # Create a DataFrame with column names and their index
                        column_df = pd.DataFrame({
                            'Column Name': column_names
                        })
                        column_df = column_df.astype(str)
                        st.dataframe(column_df, width='stretch', hide_index=True)
                    
                    # Display sample data
                    sample_rows = summary_data.get('sample_rows', [])
                    if sample_rows:
                        st.subheader("Sample Data (First 5 rows)")
                        sample_df = pd.DataFrame(sample_rows)
                        sample_df = sample_df.astype(str)
                        st.dataframe(sample_df, width='stretch', hide_index=True)
                else:
                    st.write(message['content'])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about the database..."):
        # Add user message
        add_message_to_chat(current_chat['id'], "user", prompt)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Initialize MCP client for this chat if not done
        mcp_client = current_chat['mcp_client']
        if not mcp_client.session_id:
            with st.spinner("Initializing MCP session..."):
                if not mcp_client.initialize_session():
                    st.error("Failed to initialize MCP session. Please try again.")
                    return
        
        tool_name = "query_users"
        
        # Call the tool
        with st.spinner("Processing your request..."):
            result = mcp_client.call_tool(tool_name, {"user_query": prompt})
        
        # Display assistant response
        content = None
        with st.chat_message("assistant"):
            if result:
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                    content = f"Error: {result['error']}"
                elif "result" in result:
                    st.success("Query executed successfully!")
                    content = extract_content_from_result(result)
                    
                    # Check if this is summary data
                    if is_summary_data(content):
                        # Create a summary display object to save in chat history
                        summary_display = {
                            "type": "summary",
                            "table_name": content[0].get('table_name', 'Unknown'),
                            "row_count": content[1].get('row_count', 0),
                            "column_count": content[2].get('column_count', 0),
                            "column_names": content[3].get('column_names', []),
                            "sample_rows": content[4].get('sample_rows', [])
                        }
                        display_summary_data(content)
                        add_message_to_chat(current_chat['id'], "assistant", summary_display)
                    elif isinstance(content, list) and len(content) > 0:
                        df = pd.DataFrame(content)
                        df = df.astype(str)
                        # Configure DataFrame display with consistent styling
                        st.dataframe(df, width='stretch', hide_index=True)
                        add_message_to_chat(current_chat['id'], "assistant", df)
                    else:
                        st.write("No data to display")
                        add_message_to_chat(current_chat['id'], "assistant", "No data to display")
                else:
                    st.warning("Unexpected response format")
                    content = "Unexpected response format"
            else:
                st.error("Failed to get response from MCP server")
                content = "Failed to get response from MCP server"
            
            if content and not isinstance(content, list) and not is_summary_data(content):
                add_message_to_chat(current_chat['id'], "assistant", str(content))


if __name__ == "__main__":
    main()