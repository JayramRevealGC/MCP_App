import json
import pandas as pd
import altair as alt
import streamlit as st

def extract_content_from_result(result):
    """Extract and parse content from MCP result."""
    if result and 'content' in result and isinstance(result['content'], list):
        content_text = result['content'][0]['text']
        
        if result['isError']:
            return content_text, True
        # Add error handling for JSON parsing
        try:
            parsed_content = json.loads(content_text)
            return parsed_content.get('result'), False
        except json.JSONDecodeError as e:
            print(f"Raw content: {content_text}")
            return "Error parsing response", True
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

def is_visualization_data(data):
    """Check if the data contains visualization information."""
    return isinstance(data, dict) and "visualization" in data and "data" in data

def render_bar_chart(visualization_data):
    """Render a bar chart based on visualization configuration."""
    if not visualization_data or not visualization_data.get("data"):
        st.error("No data available for bar chart")
        return
    
    config = visualization_data.get("config", {})
    data = visualization_data.get("data", [])
    
    if not data:
        st.error("No data points available for bar chart")
        return
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Get field names from config, but use actual data columns if config fields don't exist
    value_field = config.get("value_field", "value")
    count_field = config.get("count_field", "count")
    title = config.get("title", "Bar Chart")
    
    # If config fields don't exist, use the actual column names from the data
    if value_field not in df.columns or count_field not in df.columns:
        if len(df.columns) >= 2:
            # Use the actual column names from the data
            value_field = df.columns[0]  # First column (e.g., actual column name)
            count_field = df.columns[1]  # Second column (e.g., "count")
        else:
            st.error(f"Required fields '{value_field}' or '{count_field}' not found in data")
            return
    
    # Create bar chart using Altair
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(field=value_field, type="nominal", sort="-y", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(field=count_field, type="quantitative"),
        color=alt.Color(field=value_field, type="nominal", scale=alt.Scale(scheme="category20")),
        tooltip=[value_field, count_field]
    ).properties(
        title=title,
        width=600,
        height=400
    ).resolve_scale(
        color="independent"
    )
    
    # Display the chart
    st.altair_chart(chart, use_container_width=True)
    
    # Also display the data as a table
    st.subheader("Data Summary")
    display_df = df.copy()
    display_df = display_df.astype(str)
    st.dataframe(display_df, width='stretch', hide_index=True)

def render_histogram(visualization_data):
    """Render a histogram based on visualization configuration."""
    if not visualization_data or not visualization_data.get("data"):
        st.error("No data available for histogram")
        return
    
    config = visualization_data.get("config", {})
    data = visualization_data.get("data", [])
    
    if not data:
        st.error("No data points available for histogram")
        return
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Get field names from config, but use actual data columns if config fields don't exist
    category_field = config.get("category_field", "category")
    value_field = config.get("value_field", "total_value")
    title = config.get("title", "Histogram")
    
    # If config fields don't exist, use the actual column names from the data
    if category_field not in df.columns or value_field not in df.columns:
        if len(df.columns) >= 2:
            # Use the actual column names from the data
            category_field = df.columns[0]  # First column (e.g., "updated_by")
            value_field = df.columns[1]     # Second column (e.g., "capex_build_used_val")
        else:
            st.error(f"Required fields '{category_field}' or '{value_field}' not found in data")
            return
    
    # Create histogram using Altair
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(field=category_field, type="nominal", sort="-y", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(field=value_field, type="quantitative"),
        color=alt.Color(field=category_field, type="nominal", scale=alt.Scale(scheme="category20")),
        tooltip=[category_field, value_field]
    ).properties(
        title=title,
        width=600,
        height=400
    ).resolve_scale(
        color="independent"
    )
    
    # Display the chart
    st.altair_chart(chart, use_container_width=True)
    
    # Also display the data as a table
    st.subheader("Data Summary")
    display_df = df.copy()
    display_df = display_df.astype(str)
    st.dataframe(display_df, width='stretch', hide_index=True)

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
        st.subheader("Sample Data (First 3 rows)")
        sample_df = pd.DataFrame(sample_rows)
        sample_df = sample_df.astype(str)
        st.dataframe(sample_df, width='stretch', hide_index=True)
