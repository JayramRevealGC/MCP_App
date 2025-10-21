"""
SQL query construction and formatting utilities.
"""

def format_columns_for_sql(columns: list) -> str:
    """
    Format column list for SQL SELECT statement.
    """
    if not columns:
        return "*"

    return ", ".join(columns)

def format_join_condition(table1: str, table2: str, table1_col: str, table2_col: str) -> str:
    """
    Format join condition for SQL.
    
    Args:
        table1: First table name
        table2: Second table name
        table1_col: Column name in first table
        table2_col: Column name in second table
        
    Returns:
        Formatted join condition string
    """
    return f"{table1}.{table1_col} = {table2}.{table2_col}"

# Maps actions to SQL templates
ACTION_SQL_MAP = {
    "fetch_tables": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'space_product_aies';",
    "fetch_n_records": "SELECT {} FROM space_product_aies.{}{}{} LIMIT %s;",
    "fetch_n_joined_records": "SELECT {} FROM space_product_aies.{} {} JOIN space_product_aies.{} ON {}{}{} LIMIT %s;",
    "fetch_n_appended_records": "SELECT {} FROM space_product_aies.{}{} UNION ALL SELECT {} FROM space_product_aies.{}{}{} LIMIT %s;",
    "get_table_summary": "SELECT COUNT(*) as row_count FROM space_product_aies.{};",
    "summarize_column": "SELECT {}, COUNT(*) as count FROM space_product_aies.{} GROUP BY {} ORDER BY count DESC;",
    "analyze_relationship": "SELECT {} as {}, SUM({}) as {} FROM space_product_aies.{} GROUP BY {} ORDER BY {} DESC;"
}
