"""
Database query execution and action handling.
"""
import psycopg
from .validation import (
    validate_columns, validate_join_columns, validate_join_type,
    validate_order_by, validate_order_by_for_join, parse_condition
)
from .connection import get_connection, execute_with_timeout, QueryTimeoutError
from .query_builder import format_columns_for_sql, format_join_condition, ACTION_SQL_MAP

def execute_action(action: str, filters: dict):
    """Execute database action with timeout protection."""
    def _execute_query():
        conn = get_connection()
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                if action == "fetch_tables":
                    sql = ACTION_SQL_MAP[action]
                    cur.execute(sql)
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]

                elif action == "fetch_n_records":
                    # Unified action for fetching records with optional conditions and ordering
                    table_name = filters["table_name"]
                    limit = filters.get("n", 5)
                    columns = filters.get("columns", [])
                    
                    # Determine if we have conditions
                    condition = None
                    where_clause = ""
                    condition_params = []
                    
                    if "condition" in filters:
                        condition = filters["condition"]
                    elif "column" in filters and "value" in filters:
                        condition = {
                            "column": filters["column"],
                            "operator": "=",
                            "value": filters["value"]
                        }
                        if "n" not in filters:
                            limit = 1
                    
                    # Parse condition if it exists
                    if condition:
                        try:
                            where_clause, condition_params = parse_condition(condition, table_name)
                            where_clause = f" WHERE {where_clause}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing condition: {str(e)}"}]
                    
                    # Handle ORDER BY clause
                    order_by_clause = ""
                    if "order_by" in filters:
                        try:
                            order_by_clause = f" {validate_order_by(table_name, filters['order_by'])}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing order by: {str(e)}"}]
                    
                    try:
                        # Validate and format columns
                        validated_columns = validate_columns(table_name, columns)
                        columns_str = format_columns_for_sql(validated_columns)
                        
                        # Format SQL with validated table name, columns, optional WHERE clause, and optional ORDER BY clause
                        sql = ACTION_SQL_MAP[action].format(columns_str, table_name, where_clause, order_by_clause)
                        
                        # Execute with condition parameters (if any) and limit
                        cur.execute(sql, condition_params + [limit])
                        rows = cur.fetchall()
                        return [dict(row) for row in rows]
                        
                    except Exception as e:
                        return [{"error": f"Error executing query: {str(e)}"}]

                elif action == "fetch_n_joined_records":
                    # Validate table names and limit to prevent SQL injection
                    table1 = filters["table1"]
                    table2 = filters["table2"]
                    limit = filters.get("n", 5)
                    columns = filters.get("columns", [])
                    
                    join_columns = filters.get("join_columns", {"table1_column": "id", "table2_column": "id"})
                    try:
                        table1_col, table2_col = validate_join_columns(table1, table2, join_columns)
                    except ValueError as e:
                        return [{"error": str(e)}]
                    
                    join_type = filters.get("join_type", "INNER")
                    try:
                        normalized_join_type = validate_join_type(join_type)
                    except ValueError as e:
                        return [{"error": str(e)}]
                    
                    # Handle conditions for joined records
                    condition = filters.get("condition")
                    where_clause = ""
                    condition_params = []
                    
                    # Parse condition if it exists
                    if condition:
                        try:
                            # For joined tables, we need to determine which table the condition applies to
                            # If column has table prefix, use it as is; otherwise, try to find which table has the column
                            column_name = condition.get("column")
                            if "." in column_name:
                                # Column already has table prefix
                                condition["column"] = column_name
                            else:
                                # Try to find which table has this column
                                table1_cols = validate_columns(table1, [])
                                table2_cols = validate_columns(table2, [])
                                
                                if column_name in table1_cols:
                                    condition["column"] = f"{table1}.{column_name}"
                                elif column_name in table2_cols:
                                    condition["column"] = f"{table2}.{column_name}"
                                else:
                                    return [{"error": f"Column '{column_name}' not found in either table '{table1}' or '{table2}'"}]
                            
                            where_clause, condition_params = parse_condition(condition, table1)  # Use table1 for validation, but column already has prefix
                            where_clause = f" WHERE {where_clause}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing condition: {str(e)}"}]
                    
                    # Handle ORDER BY clause for joined records
                    order_by_clause = ""
                    if "order_by" in filters:
                        try:
                            order_by_clause = f" {validate_order_by_for_join(table1, table2, filters['order_by'])}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing order by: {str(e)}"}]
                    
                    # For joined records, if no columns specified, fetch all columns from both tables
                    if not columns:
                        # Get all columns from both tables
                        table1_cols = validate_columns(table1, [])
                        table2_cols = validate_columns(table2, [])
                        
                        # Create column list with table prefixes to avoid ambiguity
                        all_columns = []
                        for col in table1_cols:
                            all_columns.append(f"{table1}.{col}")
                        for col in table2_cols:
                            all_columns.append(f"{table2}.{col}")
                        columns_str = ", ".join(all_columns)
                    else:
                        # Validate and format specified columns
                        validated_columns = validate_columns(table1, columns)  # Use table1 for validation
                        columns_str = format_columns_for_sql(validated_columns)
                    
                    try:
                        # Format join condition
                        join_condition = format_join_condition(table1, table2, table1_col, table2_col)
                        
                        # Format SQL for joined records with dynamic join type, condition, and optional ORDER BY clause
                        sql = ACTION_SQL_MAP[action].format(columns_str, table1, normalized_join_type, table2, join_condition, where_clause, order_by_clause)
                        
                        # Execute with condition parameters (if any) and limit
                        cur.execute(sql, condition_params + [limit])
                        rows = cur.fetchall()
                        return [dict(row) for row in rows]
                        
                    except Exception as e:
                        return [{"error": f"Error executing joined query: {str(e)}"}]

                elif action == "fetch_n_appended_records":
                    # Validate table names and limit to prevent SQL injection
                    table1 = filters["table1"]
                    table2 = filters["table2"]
                    limit = filters.get("n", 5)
                    
                    # Handle conditions for appended records
                    condition = filters.get("condition")
                    where_clause = ""
                    condition_params = []
                    
                    # Parse condition if it exists
                    if condition:
                        try:
                            where_clause, condition_params = parse_condition(condition, table1)
                            where_clause = f" WHERE {where_clause}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing condition: {str(e)}"}]
                    
                    # Handle ORDER BY clause for appended records
                    order_by_clause = ""
                    if "order_by" in filters:
                        try:
                            # For appended records, we need to validate the column exists in both tables
                            order_by = filters["order_by"]
                            column = order_by.get("column")
                            direction = order_by.get("direction", "ASC").upper()
                            
                            # Get common columns between tables
                            table1_cols = validate_columns(table1, [])
                            table2_cols = validate_columns(table2, [])
                            common_cols = list(set(table1_cols) & set(table2_cols))
                            
                            if column not in common_cols:
                                raise ValueError(f"Column '{column}' not found in common columns between tables '{table1}' and '{table2}'. Common columns: {common_cols}")
                            
                            # Validate direction
                            valid_directions = ["ASC", "DESC"]
                            if direction not in valid_directions:
                                raise ValueError(f"Invalid order direction '{direction}'. Valid directions: {valid_directions}")
                            
                            order_by_clause = f" ORDER BY {column} {direction}"
                        except ValueError as e:
                            return [{"error": str(e)}]
                        except Exception as e:
                            return [{"error": f"Error parsing order by: {str(e)}"}]
                    
                    try:
                        # Get common columns between tables
                        table1_cols = validate_columns(table1, [])
                        table2_cols = validate_columns(table2, [])
                        common_cols = list(set(table1_cols) & set(table2_cols))
                        
                        if not common_cols:
                            return [{"error": f"No common columns found between tables '{table1}' and '{table2}'"}]
                        
                        columns_str = ", ".join(common_cols)
                        
                        # Format SQL for appended records with optional ORDER BY clause
                        sql = ACTION_SQL_MAP[action].format(columns_str, table1, where_clause, columns_str, table2, where_clause, order_by_clause)
                        
                        # Execute with condition parameters (if any) and limit
                        cur.execute(sql, condition_params + condition_params + [limit])
                        rows = cur.fetchall()
                        return [dict(row) for row in rows]
                        
                    except Exception as e:
                        return [{"error": f"Error executing appended query: {str(e)}"}]

                elif action == "summarize_column":
                    table_name = filters["table_name"]
                    column = filters["column"]
                    
                    try:
                        # Validate that the column exists in the table
                        validated_columns = validate_columns(table_name, [column])
                        if column not in validated_columns:
                            return [{"error": f"Column '{column}' not found in table '{table_name}'. Available columns: {validated_columns}"}]
                        
                        # Execute column summary query
                        sql = ACTION_SQL_MAP[action].format(column, table_name, column)
                        cur.execute(sql)
                        rows = cur.fetchall()
                        
                        # Format the results for visualization
                        summary_data = [dict(row) for row in rows]
                        
                        # Create visualization configuration
                        visualization = {
                            "type": "bar_chart",
                            "config": {
                                "title": f"Distribution of {column} in {table_name}",
                                "value_field": column,
                                "count_field": "count"
                            },
                            "data": summary_data
                        }
                        
                        return {
                            "data": summary_data,
                            "visualization": visualization,
                            "table_name": table_name,
                            "column": column
                        }
                        
                    except Exception as e:
                        return [{"error": f"Error summarizing column: {str(e)}"}]

                elif action == "analyze_relationship":
                    table_name = filters["table_name"]
                    categorical_column = filters["categorical_column"]
                    quantitative_column = filters["quantitative_column"]
                    
                    try:
                        # Validate that both columns exist in the table
                        validated_columns = validate_columns(table_name, [categorical_column, quantitative_column])
                        if categorical_column not in validated_columns:
                            return [{"error": f"Categorical column '{categorical_column}' not found in table '{table_name}'. Available columns: {validated_columns}"}]
                        if quantitative_column not in validated_columns:
                            return [{"error": f"Quantitative column '{quantitative_column}' not found in table '{table_name}'. Available columns: {validated_columns}"}]
                        
                        # Execute relationship analysis query
                        sql = ACTION_SQL_MAP[action].format(categorical_column, categorical_column, quantitative_column, quantitative_column, table_name, categorical_column, quantitative_column)
                        cur.execute(sql)
                        rows = cur.fetchall()
                        
                        # Format the results for visualization
                        relationship_data = [dict(row) for row in rows]
                        
                        # Create visualization configuration for histogram
                        visualization = {
                            "type": "histogram",
                            "config": {
                                "title": f"Sum of {quantitative_column} by {categorical_column} in {table_name}",
                                "category_field": categorical_column,
                                "value_field": quantitative_column
                            },
                            "data": relationship_data
                        }
                        
                        return {
                            "data": relationship_data,
                            "visualization": visualization,
                            "table_name": table_name,
                            "categorical_column": categorical_column,
                            "quantitative_column": quantitative_column
                        }
                        
                    except Exception as e:
                        return [{"error": f"Error analyzing relationship: {str(e)}"}]

                elif action == "get_table_summary":
                    table_name = filters["table_name"]
                    
                    try:
                        # Get row count
                        count_sql = ACTION_SQL_MAP[action].format(table_name)
                        cur.execute(count_sql)
                        row_count = cur.fetchone()["row_count"]
                        
                        # Get column information
                        column_sql = """
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'space_product_aies' AND table_name = %s
                        ORDER BY ordinal_position;
                        """
                        cur.execute(column_sql, (table_name,))
                        column_info = cur.fetchall()
                        column_count = len(column_info)
                        column_names = [col["column_name"] for col in column_info]
                        
                        # Get sample data (first 3 rows)
                        sample_sql = f"SELECT * FROM space_product_aies.{table_name} LIMIT 3;"
                        cur.execute(sample_sql)
                        sample_rows = cur.fetchall()
                        sample_data = [dict(row) for row in sample_rows]
                        
                        return [{"table_name": table_name},
                                {"row_count": row_count},
                                {"column_count": column_count},
                                {"column_names": column_names},
                                {"sample_rows": sample_data}]
                        
                    except Exception as e:
                        return [{"error": f"Error getting table summary: {str(e)}"}]
                        
        finally:
            conn.close()
    
    # Execute the query with timeout protection
    try:
        return execute_with_timeout(_execute_query)
    except QueryTimeoutError as e:
        return [{"error": f"Query timeout: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}"}]
