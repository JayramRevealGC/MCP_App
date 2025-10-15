import json
import pandas as pd
import streamlit as st

def extract_content_from_result(result):
    """Extract and parse content from MCP result."""
    if result and 'result' in result and 'content' in result['result'] and isinstance(result['result']['content'], list):
        content_text = result['result']['content'][0]['text']
        
        # Add error handling for JSON parsing
        try:
            parsed_content = json.loads(content_text)
            return parsed_content.get('result')
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON response: {e}")
            print(f"Raw content: {content_text}")
            return "Error parsing response"
    return "No response received"

def is_summary_data(data):
    """Check if the data represents a table summary."""
    if isinstance(data, list) and len(data) == 5:
        # Check if it has the exact structure of summary data (5 items: table_name, row_count, column_count, column_names, sample_rows)
        try:
            # Check each item has the expected structure
            has_table_name = isinstance(data[0], dict) and 'table_name' in data[0]
            has_row_count = isinstance(data[1], dict) and 'row_count' in data[1]
            has_column_count = isinstance(data[2], dict) and 'column_count' in data[2]
            has_column_names = isinstance(data[3], dict) and 'column_names' in data[3]
            has_sample_rows = isinstance(data[4], dict) and 'sample_rows' in data[4]
            
            return has_table_name and has_row_count and has_column_count and has_column_names and has_sample_rows
        except (IndexError, TypeError):
            return False
    return False

def display_summary_data(summary_data):
    """Display table summary data in a formatted way."""
    if not isinstance(summary_data, list) or len(summary_data) < 5:
        st.error("Invalid summary data format")
        return
    
    # Extract summary components directly
    table_info = summary_data[0]  # {"table_name": "item_kaus"}
    row_count_info = summary_data[1]  # {"row_count": 123}
    column_count_info = summary_data[2]  # {"column_count": 5}
    column_names_info = summary_data[3]  # {"column_names": ["id", "name", ...]}
    sample_data_info = summary_data[4]  # {"sample_rows": [...]}
    
    # Display table information
    st.subheader(f"Table Summary: {table_info.get('table_name', 'Unknown')}")
    
    # Create columns for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Rows", row_count_info.get('row_count', 0))
    
    with col2:
        st.metric("Total Columns", column_count_info.get('column_count', 0))
    
    # Display column names in a table format
    column_names = column_names_info.get('column_names', [])
    if column_names:
        st.subheader("Column Names")
        # Create a DataFrame with column names and their index
        column_df = pd.DataFrame({
            'Column Name': column_names
        })
        column_df = column_df.astype(str)
        st.dataframe(column_df, width='stretch', hide_index=True)
    
    # Display sample data
    sample_rows = sample_data_info.get('sample_rows', [])
    if sample_rows:
        st.subheader("Sample Data (First 5 rows)")
        sample_df = pd.DataFrame(sample_rows)
        sample_df = sample_df.astype(str)
        st.dataframe(sample_df, width='stretch', hide_index=True)
