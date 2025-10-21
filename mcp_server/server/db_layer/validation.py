"""
Database validation functions for columns, joins, and conditions.
"""

from .connection import get_connection

def validate_columns(table_name: str, columns: list) -> list:
    """
    Validate that the specified columns exist in the table.
    Returns the validated column list or all columns if validation fails.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get all column names for the table
            column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'space_product_aies' AND table_name = %s
            ORDER BY ordinal_position;
            """
            cur.execute(column_sql, (table_name,))
            available_columns = [row[0] for row in cur.fetchall()]
            
            if not columns:
                return available_columns
            
            # Validate each requested column
            valid_columns = []
            for col in columns:
                if col in available_columns:
                    valid_columns.append(col)
                else:
                    print(f"Warning: Column '{col}' not found in table '{table_name}'. Available columns: {available_columns}")
            
            # If no valid columns found, return all columns
            return valid_columns if valid_columns else available_columns
            
    except Exception as e:
        print(f"Error validating columns: {e}")
        return ["*"]  # Fallback to all columns
    finally:
        conn.close()

def validate_join_columns(table1: str, table2: str, join_columns: dict) -> tuple:
    """
    Validate join columns exist in their respective tables.
    
    Args:
        table1: First table name
        table2: Second table name  
        join_columns: Dict with 'table1_column' and 'table2_column' keys
        
    Returns:
        Tuple of (table1_column, table2_column) if valid
        
    Raises:
        ValueError: If columns don't exist in their respective tables
    """
    table1_col = join_columns.get("table1_column", "id")
    table2_col = join_columns.get("table2_column", "id")
    
    # Validate table1 column exists
    table1_columns = validate_columns(table1, [])
    if table1_col not in table1_columns:
        raise ValueError(f"Column '{table1_col}' not found in table '{table1}'. Available columns: {table1_columns}")
    
    # Validate table2 column exists
    table2_columns = validate_columns(table2, [])
    if table2_col not in table2_columns:
        raise ValueError(f"Column '{table2_col}' not found in table '{table2}'. Available columns: {table2_columns}")
    
    return table1_col, table2_col

def validate_join_type(join_type: str) -> str:
    """
    Validate and normalize join type.
    
    Args:
        join_type: Join type string
        
    Returns:
        Normalized join type (uppercase)
        
    Raises:
        ValueError: If join type is invalid
    """
    valid_join_types = ["INNER", "LEFT", "RIGHT", "FULL", "FULL OUTER"]
    normalized_type = join_type.upper().strip()
    
    if normalized_type not in valid_join_types:
        raise ValueError(f"Invalid join type '{join_type}'. Valid types: {valid_join_types}")
    
    return normalized_type

def validate_order_by(table_name: str, order_by: dict) -> str:
    """
    Validate and format ORDER BY clause.
    
    Args:
        table_name: Table name for validation
        order_by: Dict with 'column' and 'direction' keys
        
    Returns:
        Formatted ORDER BY clause string
        
    Raises:
        ValueError: If column doesn't exist or direction is invalid
    """
    column = order_by.get("column")
    direction = order_by.get("direction", "ASC").upper()
    
    # Handle table-prefixed column names (e.g., "napcs.id" -> "id")
    column_name_for_validation = column
    if "." in column:
        column_name_for_validation = column.split(".")[-1]
    
    # Validate that the column exists in the table
    available_columns = validate_columns(table_name, [])
    if column_name_for_validation not in available_columns:
        raise ValueError(f"Column '{column}' not found in table '{table_name}'. Available columns: {available_columns}")
    
    # Validate direction
    valid_directions = ["ASC", "DESC"]
    if direction not in valid_directions:
        raise ValueError(f"Invalid order direction '{direction}'. Valid directions: {valid_directions}")
    
    return f"ORDER BY {column} {direction}"

def validate_order_by_for_join(table1: str, table2: str, order_by: dict) -> str:
    """
    Validate and format ORDER BY clause for joined tables.
    
    Args:
        table1: First table name
        table2: Second table name
        order_by: Dict with 'column' and 'direction' keys
        
    Returns:
        Formatted ORDER BY clause string
        
    Raises:
        ValueError: If column doesn't exist in either table or direction is invalid
    """
    column = order_by.get("column")
    direction = order_by.get("direction", "ASC").upper()
    
    # Handle table-prefixed column names
    if "." in column:
        # Column already has table prefix, validate it exists
        table_prefix = column.split(".")[0]
        column_name = column.split(".")[1]
        
        if table_prefix == table1:
            table1_cols = validate_columns(table1, [])
            if column_name not in table1_cols:
                raise ValueError(f"Column '{column}' not found in table '{table1}'. Available columns: {table1_cols}")
        elif table_prefix == table2:
            table2_cols = validate_columns(table2, [])
            if column_name not in table2_cols:
                raise ValueError(f"Column '{column}' not found in table '{table2}'. Available columns: {table2_cols}")
        else:
            raise ValueError(f"Table prefix '{table_prefix}' not found. Available tables: {table1}, {table2}")
    else:
        # Try to find which table has this column
        table1_cols = validate_columns(table1, [])
        table2_cols = validate_columns(table2, [])
        
        if column in table1_cols and column in table2_cols:
            # Column exists in both tables, require table prefix
            raise ValueError(f"Column '{column}' exists in both tables '{table1}' and '{table2}'. Please specify table prefix (e.g., '{table1}.{column}' or '{table2}.{column}')")
        elif column in table1_cols:
            column = f"{table1}.{column}"
        elif column in table2_cols:
            column = f"{table2}.{column}"
        else:
            raise ValueError(f"Column '{column}' not found in either table '{table1}' or '{table2}'")
    
    # Validate direction
    valid_directions = ["ASC", "DESC"]
    if direction not in valid_directions:
        raise ValueError(f"Invalid order direction '{direction}'. Valid directions: {valid_directions}")
    
    return f"ORDER BY {column} {direction}"

def parse_condition(condition: dict, table_name: str) -> tuple:
    """
    Parse a flexible condition dictionary into SQL WHERE clause and parameters.
    
    Expected condition format:
    {
        "column": "column_name",
        "operator": ">",  # >, <, >=, <=, =, !=, LIKE, BETWEEN, IN, IS NULL, IS NOT NULL
        "value": value,   # single value for most operators
        "values": [val1, val2]  # for BETWEEN and IN operators
    }
    
    Returns: (where_clause, parameters)
    """
    column = condition.get("column")
    operator = condition.get("operator", "=")
    value = condition.get("value")
    values = condition.get("values", [])
    
    # Handle table-prefixed column names (e.g., "napcs.id" -> "id")
    column_name_for_validation = column
    if "." in column:
        column_name_for_validation = column.split(".")[-1]
    
    # Validate that the column exists in the table
    available_columns = validate_columns(table_name, [])
    if column_name_for_validation not in available_columns:
        raise ValueError(f"Column '{column}' not found in table '{table_name}'. Available columns: {available_columns}")
    
    # Validate operator
    valid_operators = [">", "<", ">=", "<=", "=", "!=", "LIKE", "ILIKE", "BETWEEN", "IN", "IS NULL", "IS NOT NULL"]
    if operator not in valid_operators:
        raise ValueError(f"Invalid operator '{operator}'. Valid operators: {valid_operators}")
    
    parameters = []
    
    if operator in ["IS NULL", "IS NOT NULL"]:
        # These operators don't need values
        where_clause = f"{column} {operator}"
    elif operator == "BETWEEN":
        if len(values) != 2:
            raise ValueError("BETWEEN operator requires exactly 2 values")
        where_clause = f"{column} BETWEEN %s AND %s"
        parameters.extend(values)
    elif operator == "IN":
        if not values:
            raise ValueError("IN operator requires at least one value")
        placeholders = ", ".join(["%s"] * len(values))
        where_clause = f"{column} IN ({placeholders})"
        parameters.extend(values)
    elif operator in ["LIKE", "ILIKE"]:
        if value is None:
            raise ValueError(f"{operator} operator requires a value")
        where_clause = f"{column} {operator} %s"
        parameters.append(value)
    else:
        # Standard operators: >, <, >=, <=, =, !=
        if value is None:
            raise ValueError(f"Operator '{operator}' requires a value")
        where_clause = f"{column} {operator} %s"
        parameters.append(value)
    
    return where_clause, parameters
