import json
import openai

async def summarize_query_history(previous_queries: list) -> str:
    """
    Summarize previous queries to extract key context: table names, column names, and actions.
    
    Args:
        previous_queries: List of previous query strings
        
    Returns:
        A summarized context string highlighting table names, columns, and key information
    """
    if not previous_queries:
        return ""
    
    if len(previous_queries) == 1:
        # For single query, use it directly but extract key info
        summary_prompt = f"""Analyze the following database query and extract ONLY the key information:
        
Query: "{previous_queries[0]}"

Extract and format:
1. Table name(s) mentioned (if any)
2. Column name(s) mentioned (if any)
3. Action type (fetch records, join tables, etc.)
4. Any filters/conditions applied
5. Any join relationships (if applicable)

Format as: "Previously worked with table(s): [table names], column(s): [column names], action: [action type], filters: [filters if any]"
"""
    else:
        # For multiple queries, summarize them together
        queries_text = "\n".join([f"Query {i+1}: {q}" for i, q in enumerate(previous_queries)])
        summary_prompt = f"""Analyze the following database query history and extract key information:
        
{queries_text}

Extract and summarize:
1. ALL table names that were mentioned across all queries (consolidate and list uniquely)
2. ALL column names that were mentioned across all queries (consolidate and list uniquely)
3. Actions performed (join relationships, filters applied, etc.)
4. Context about what the user was exploring (summarize the query pattern)

Format as a structured summary that highlights:
- Tables used: [list all unique table names]
- Columns referenced: [list all unique column names]
- Recent query pattern: [brief summary of what user was doing]
- Join relationships: [if any joins were made, document the relationships]
"""
    
    client = openai.OpenAI()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a database query analyzer. Extract key information from queries focusing on table names, column names, and context."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback: return a simple summary
        return f"Previous queries: {len(previous_queries)} query/queries were made in this session."


async def parse_nl_to_intent(user_input: str, previous_queries: list = None) -> dict:
    """
    Convert natural language into structured query intent.
    """
    system_prompt = """You are an intent parser for database queries.
    Convert the user's natural language into JSON with this format:
    {
        "action": "<one of: fetch_tables, fetch_n_records, fetch_n_joined_records, fetch_n_appended_records, get_table_summary, summarize_column, analyze_relationship>",
        "filters": {...} <optional, fill it with any parameter, if passed by user, similar to table_name, columns, n, id, table1, table2, limit, etc.>
    }
    
    ================================================================================
    CONVERSATION CONTEXT - CRITICAL INSTRUCTIONS:
    ================================================================================
    When conversation history is provided, you MUST treat the current query as a CONTINUATION.
    
    TABLE NAME RESOLUTION (HIGHEST PRIORITY):
    - If the current query mentions "that table", "the table", "same table", "previous table", etc.,
      you MUST map it to the EXACT table name(s) from the conversation summary
    - If the current query doesn't explicitly mention a table name, check if previous queries worked with tables
      and use the most recent/relevant table name from the summary
    - ALWAYS prioritize table names from the conversation summary over guessing
    - Pay special attention to tables that were joined together - use BOTH table names when relevant
    
    COLUMN NAME RESOLUTION:
    - When user says "that column", "the column", "same column", reference the exact column names from history
    - If columns were used in previous queries, maintain consistency in column names
    - For joins, remember which columns belong to which tables (use table prefixes: table.column when needed)
    
    CONTEXT AWARENESS:
    - Previous queries establish the database context - use table/column names from the summary
    - If user asks "show me more", "get 5 records", "filter by X", etc. without specifying table,
      assume they mean the table(s) from the most recent query context
    - Maintain conversation continuity - don't treat each query in isolation
    - If previous queries involved joins, current query might reference the joined result
    
    ================================================================================
    OPERATION CATEGORIES AND EXAMPLES
    ================================================================================
    
    1. FETCH_TABLES - Get list of all tables
    Examples:
    - "Show me all tables" -> {"action": "fetch_tables", "filters": {}}
    - "List all available tables" -> {"action": "fetch_tables", "filters": {}}
    - "What tables are available?" -> {"action": "fetch_tables", "filters": {}}
    
    2. FETCH_N_RECORDS - Get n records from a single table (with optional conditions and ordering)
    Supports operators: =, >, <, >=, <=, !=, LIKE, BETWEEN, IN, IS NULL, IS NOT NULL
    Supports ordering: ASC (ascending), DESC (descending)
    
    Basic Examples:
    - "Show me all products" -> {"action": "fetch_n_records", "filters": {"table_name": "products"}}
    - "Get 5 records from users table" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "n": 5}}
    - "Show me id and name from table users" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "columns": ["id", "name"]}}
    - "Get 5 records with columns id, title, price from products" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "n": 5, "columns": ["id", "title", "price"]}}
    
    Condition Examples:
    - "Get user with email john@example.com" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "email", "operator": "=", "value": "john@example.com"}, "n": 1}}
    - "Find product with name 'iPhone'" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "condition": {"column": "name", "operator": "=", "value": "iPhone"}, "n": 1}}
    - "Get 10 records where price is greater than 100" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "condition": {"column": "price", "operator": ">", "value": 100}, "n": 10}}
    - "Find records where date is before 2023-01-01" -> {"action": "fetch_n_records", "filters": {"table_name": "orders", "condition": {"column": "order_date", "operator": "<", "value": "2023-01-01"}}}
    - "Get records where score is between 80 and 95" -> {"action": "fetch_n_records", "filters": {"table_name": "students", "condition": {"column": "score", "operator": "BETWEEN", "values": [80, 95]}}}
    - "Find records where name contains 'test'" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "name", "operator": "LIKE", "value": "%test%"}}}
    - "Get records where status is not null" -> {"action": "fetch_n_records", "filters": {"table_name": "tasks", "condition": {"column": "status", "operator": "IS NOT NULL"}}}
    - "Find records where category is in ['electronics', 'books', 'clothing']" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "condition": {"column": "category", "operator": "IN", "values": ["electronics", "books", "clothing"]}}}
    - "Get 5 records where age is greater than or equal to 18" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "age", "operator": ">=", "value": 18}, "n": 5}}
    - "Find records where email is not equal to 'admin@example.com'" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "email", "operator": "!=", "value": "admin@example.com"}}}
    - "Get records where description is null" -> {"action": "fetch_n_records", "filters": {"table_name": "items", "condition": {"column": "description", "operator": "IS NULL"}}}
    - "Fetch row with id 123 showing only name and email" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "id", "operator": "=", "value": 123}, "n": 1, "columns": ["name", "email"]}}
    
    Ordering Examples:
    - "Show products ordered by price" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "order_by": {"column": "price", "direction": "ASC"}}}
    - "Get users sorted by name descending" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "order_by": {"column": "name", "direction": "DESC"}}}
    - "Show 10 products ordered by price descending" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "n": 10, "order_by": {"column": "price", "direction": "DESC"}}}
    - "Get users where age > 18 ordered by name" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "condition": {"column": "age", "operator": ">", "value": 18}, "order_by": {"column": "name", "direction": "ASC"}}}
    - "Show products ordered by creation date descending" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "order_by": {"column": "created_at", "direction": "DESC"}}}
    - "Get orders sorted by order date ascending" -> {"action": "fetch_n_records", "filters": {"table_name": "orders", "order_by": {"column": "order_date", "direction": "ASC"}}}
    - "Show products with price > 100 ordered by name" -> {"action": "fetch_n_records", "filters": {"table_name": "products", "condition": {"column": "price", "operator": ">", "value": 100}, "order_by": {"column": "name", "direction": "ASC"}}}
    - "Get users ordered by registration date descending" -> {"action": "fetch_n_records", "filters": {"table_name": "users", "order_by": {"column": "registration_date", "direction": "DESC"}}}
    
    3. FETCH_N_JOINED_RECORDS - Join two tables and get n records (with optional conditions and ordering)
    Supports operators: =, >, <, >=, <=, !=, LIKE, BETWEEN, IN, IS NULL, IS NOT NULL
    Supports ordering: ASC (ascending), DESC (descending)
    By default fetches ALL columns from both tables (with table prefixes)
    Supports flexible join columns and join types
    
    Basic Join Examples (default: INNER JOIN on id columns):
    - "Join users and orders tables" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders"}}
    - "Join products and categories tables showing 10 records" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "n": 10}}
    - "Join users and orders showing only id, name, and order_date columns" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "columns": ["id", "name", "order_date"]}}
    
    Flexible Join Column Examples:
    - "Join users and orders on user_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "join_columns": {"table1_column": "id", "table2_column": "user_id"}}}
    - "Join products and categories on product_id and category_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "join_columns": {"table1_column": "id", "table2_column": "product_id"}}}
    - "Join customers and orders on customer_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "customers", "table2": "orders", "join_columns": {"table1_column": "id", "table2_column": "customer_id"}}}
    - "Join users and profiles on user_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "profiles", "join_columns": {"table1_column": "id", "table2_column": "user_id"}}}
    
    Join Type Examples:
    - "Left join users and orders" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "join_type": "LEFT"}}
    - "Right join products and categories" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "join_type": "RIGHT"}}
    - "Full outer join customers and orders" -> {"action": "fetch_n_joined_records", "filters": {"table1": "customers", "table2": "orders", "join_type": "FULL OUTER"}}
    - "Inner join users and profiles" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "profiles", "join_type": "INNER"}}
    
    Combined Flexible Join Examples:
    - "Left join users and orders on user_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "join_type": "LEFT", "join_columns": {"table1_column": "id", "table2_column": "user_id"}}}
    - "Right join products and categories on product_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "join_type": "RIGHT", "join_columns": {"table1_column": "id", "table2_column": "product_id"}}}
    - "Full outer join customers and orders on customer_id" -> {"action": "fetch_n_joined_records", "filters": {"table1": "customers", "table2": "orders", "join_type": "FULL OUTER", "join_columns": {"table1_column": "id", "table2_column": "customer_id"}}}
    
    Join with Condition Examples:
    - "Join users and orders where user status is active" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "condition": {"column": "status", "operator": "=", "value": "active"}}}
    - "Join products and categories where price is greater than 100" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "condition": {"column": "price", "operator": ">", "value": 100}}}
    - "Join users and orders where user age is greater than 25" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "condition": {"column": "age", "operator": ">", "value": 25}}}
    - "Join products and categories where product price is between 50 and 200" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "condition": {"column": "price", "operator": "BETWEEN", "values": [50, 200]}}}
    - "Join customers and orders where customer status is active" -> {"action": "fetch_n_joined_records", "filters": {"table1": "customers", "table2": "orders", "condition": {"column": "status", "operator": "=", "value": "active"}}}
    - "Join users and profiles where user email contains 'gmail'" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "profiles", "condition": {"column": "email", "operator": "LIKE", "value": "%gmail%"}}}
    - "Join products and inventory where quantity is not null" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "inventory", "condition": {"column": "quantity", "operator": "IS NOT NULL"}}}
    
    Join with Table Prefix Examples:
    - "Join item_kaus and napcs and fetch rows with item_kaus.id field as 1" -> {"action": "fetch_n_joined_records", "filters": {"table1": "item_kaus", "table2": "napcs", "condition": {"column": "item_kaus.id", "operator": "=", "value": 1}}}
    - "Join table1 and table2 and fetch rows where table1.status equals active" -> {"action": "fetch_n_joined_records", "filters": {"table1": "table1", "table2": "table2", "condition": {"column": "table1.status", "operator": "=", "value": "active"}}}
    - "Join users and orders and fetch rows with users.age greater than 25" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "condition": {"column": "users.age", "operator": ">", "value": 25}}}
    - "Join products and inventory and fetch rows where products.price is 100" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "inventory", "condition": {"column": "products.price", "operator": "=", "value": 100}}}
    
    Join with Ordering Examples:
    - "Join users and orders ordered by order date" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "order_by": {"column": "orders.order_date", "direction": "ASC"}}}
    - "Join products and categories sorted by product name descending" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "categories", "order_by": {"column": "products.name", "direction": "DESC"}}}
    - "Join users and orders where user age > 25 ordered by order date" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "orders", "condition": {"column": "users.age", "operator": ">", "value": 25}, "order_by": {"column": "orders.order_date", "direction": "ASC"}}}
    - "Join customers and orders ordered by customer name" -> {"action": "fetch_n_joined_records", "filters": {"table1": "customers", "table2": "orders", "order_by": {"column": "customers.name", "direction": "ASC"}}}
    - "Join products and inventory sorted by quantity descending" -> {"action": "fetch_n_joined_records", "filters": {"table1": "products", "table2": "inventory", "order_by": {"column": "inventory.quantity", "direction": "DESC"}}}
    - "Join users and profiles ordered by user registration date" -> {"action": "fetch_n_joined_records", "filters": {"table1": "users", "table2": "profiles", "order_by": {"column": "users.registration_date", "direction": "ASC"}}}
    
    4. FETCH_N_APPENDED_RECORDS - Append/combine two tables vertically (UNION ALL) (with optional conditions and ordering)
    Supports operators: =, >, <, >=, <=, !=, LIKE, BETWEEN, IN, IS NULL, IS NOT NULL
    Supports ordering: ASC (ascending), DESC (descending)
    Only common columns between tables are returned
    
    Basic Append Examples:
    - "Append table1 and table2" -> {"action": "fetch_n_appended_records", "filters": {"table1": "table1", "table2": "table2"}}
    - "Combine users and customers tables" -> {"action": "fetch_n_appended_records", "filters": {"table1": "users", "table2": "customers"}}
    - "Append 10 records from table1 and table2" -> {"action": "fetch_n_appended_records", "filters": {"table1": "table1", "table2": "table2", "n": 10}}
    
    Append with Condition Examples:
    - "Append users and customers where status is active" -> {"action": "fetch_n_appended_records", "filters": {"table1": "users", "table2": "customers", "condition": {"column": "status", "operator": "=", "value": "active"}}}
    - "Combine products and inventory where quantity is greater than 0" -> {"action": "fetch_n_appended_records", "filters": {"table1": "products", "table2": "inventory", "condition": {"column": "quantity", "operator": ">", "value": 0}}}
    - "Append orders and shipments where date is after 2023-01-01" -> {"action": "fetch_n_appended_records", "filters": {"table1": "orders", "table2": "shipments", "condition": {"column": "date", "operator": ">", "value": "2023-01-01"}}}
    - "Combine users and employees where department is in ['IT', 'Sales', 'Marketing']" -> {"action": "fetch_n_appended_records", "filters": {"table1": "users", "table2": "employees", "condition": {"column": "department", "operator": "IN", "values": ["IT", "Sales", "Marketing"]}}}
    - "Append products and services where price is between 100 and 500" -> {"action": "fetch_n_appended_records", "filters": {"table1": "products", "table2": "services", "condition": {"column": "price", "operator": "BETWEEN", "values": [100, 500]}}}
    
    Append with Ordering Examples:
    - "Append users and customers ordered by name" -> {"action": "fetch_n_appended_records", "filters": {"table1": "users", "table2": "customers", "order_by": {"column": "name", "direction": "ASC"}}}
    - "Combine products and inventory sorted by price descending" -> {"action": "fetch_n_appended_records", "filters": {"table1": "products", "table2": "inventory", "order_by": {"column": "price", "direction": "DESC"}}}
    - "Append orders and shipments ordered by date" -> {"action": "fetch_n_appended_records", "filters": {"table1": "orders", "table2": "shipments", "order_by": {"column": "date", "direction": "ASC"}}}
    - "Combine users and employees where department is IT ordered by name" -> {"action": "fetch_n_appended_records", "filters": {"table1": "users", "table2": "employees", "condition": {"column": "department", "operator": "=", "value": "IT"}, "order_by": {"column": "name", "direction": "ASC"}}}
    - "Append products and services sorted by creation date descending" -> {"action": "fetch_n_appended_records", "filters": {"table1": "products", "table2": "services", "order_by": {"column": "created_at", "direction": "DESC"}}}
    
    5. GET_TABLE_SUMMARY - Get summary information about a table
    Examples:
    - "Get summary of users table" -> {"action": "get_table_summary", "filters": {"table_name": "users"}}
    - "Show me table info for products" -> {"action": "get_table_summary", "filters": {"table_name": "products"}}
    - "What's in the orders table?" -> {"action": "get_table_summary", "filters": {"table_name": "orders"}}
    
    6. SUMMARIZE_COLUMN - Get count of all values in a specific column (for pie chart visualization)
    Examples:
    - "Summarize the status column in users table" -> {"action": "summarize_column", "filters": {"table_name": "users", "column": "status"}}
    - "Show me count of all values in category column" -> {"action": "summarize_column", "filters": {"table_name": "products", "column": "category"}}
    - "Create a pie chart of department distribution" -> {"action": "summarize_column", "filters": {"table_name": "employees", "column": "department"}}
    - "Count all values in the region column" -> {"action": "summarize_column", "filters": {"table_name": "customers", "column": "region"}}
    - "Show distribution of product types" -> {"action": "summarize_column", "filters": {"table_name": "products", "column": "type"}}
    - "Summarize age groups in users table" -> {"action": "summarize_column", "filters": {"table_name": "users", "column": "age_group"}}
    
    7. ANALYZE_RELATIONSHIP - Analyze relationship between a categorical column and a quantitative column (for histogram visualization)
    Examples:
    - "Analyze ref_per column in item_kaus by revenue" -> {"action": "analyze_relationship", "filters": {"table_name": "item_kaus", "categorical_column": "ref_per", "quantitative_column": "revenue"}}
    - "Show revenue distribution by category" -> {"action": "analyze_relationship", "filters": {"table_name": "products", "categorical_column": "category", "quantitative_column": "revenue"}}
    - "Analyze sales by region" -> {"action": "analyze_relationship", "filters": {"table_name": "sales", "categorical_column": "region", "quantitative_column": "sales_amount"}}
    - "Show profit by department" -> {"action": "analyze_relationship", "filters": {"table_name": "employees", "categorical_column": "department", "quantitative_column": "profit"}}
    - "Analyze price by product type" -> {"action": "analyze_relationship", "filters": {"table_name": "products", "categorical_column": "type", "quantitative_column": "price"}}
    - "Show quantity by status" -> {"action": "analyze_relationship", "filters": {"table_name": "inventory", "categorical_column": "status", "quantitative_column": "quantity"}}
    - "Analyze score by grade level" -> {"action": "analyze_relationship", "filters": {"table_name": "students", "categorical_column": "grade_level", "quantitative_column": "score"}}
    - "Show revenue by customer segment" -> {"action": "analyze_relationship", "filters": {"table_name": "customers", "categorical_column": "segment", "quantitative_column": "revenue"}}
    
    ================================================================================
    IMPORTANT NOTES:
    ================================================================================
    - If no specific columns are mentioned, omit the "columns" field (will fetch all columns)
    - For joined records, you can specify columns from either table: ["table1.column1", "table2.column2"] or just ["column1", "column2"] if the column names are unique
    - For appended records, only common columns between both tables will be returned
    - Conditions support table prefixes for joins: "table1.column_name" or "table2.column_name"
    - ORDER BY supports both ASC (ascending) and DESC (descending) directions
    - For joined records ORDER BY, use table prefixes when column names exist in both tables: "table1.column_name" or "table2.column_name"
    - For appended records ORDER BY, only use column names that exist in both tables (no table prefixes needed)
    - Default limit is 5 records if not specified
    - For joins: Default join type is "INNER" and default join columns are "id" on both tables
    - Join types supported: "INNER", "LEFT", "RIGHT", "FULL", "FULL OUTER"
    - Join columns format: {"table1_column": "column_name", "table2_column": "column_name"}
    - ORDER BY format: {"column": "column_name", "direction": "ASC" or "DESC"}
    """

    client = openai.OpenAI()
    
    # Build messages list with conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add previous queries as conversation history - using summarized context
    if previous_queries:
        # Summarize previous queries to extract key context
        query_summary = await summarize_query_history(previous_queries)
        
        # Build detailed context prompt emphasizing table/column names
        history_context = "=" * 70 + "\n"
        history_context += "CONVERSATION CONTEXT - SUMMARY OF PREVIOUS QUERIES\n"
        history_context += "=" * 70 + "\n\n"
        history_context += query_summary + "\n\n"
        
        history_context += "-" * 70 + "\n"
        history_context += "CRITICAL TABLE/COLUMN NAME MAPPING INSTRUCTIONS:\n"
        history_context += "-" * 70 + "\n"
        history_context += "1. TABLE NAMES FROM HISTORY: Use the EXACT table name(s) listed in the summary above\n"
        history_context += "   - If current query says 'that table' or doesn't name a table, use table(s) from summary\n"
        history_context += "   - Multiple tables from joins? Use both table names when relevant\n"
        history_context += "   - Most recent table context takes priority if multiple tables were used\n\n"
        
        history_context += "2. COLUMN NAMES FROM HISTORY: Reference columns from the summary when mentioned\n"
        history_context += "   - Maintain exact column names as they appeared in previous queries\n"
        history_context += "   - For joins, remember table prefixes (table.column format)\n\n"
        
        history_context += "3. CONTEXT CONTINUITY: \n"
        history_context += "   - Current query builds on previous query context\n"
        history_context += "   - If query is vague (e.g., 'get 5 more', 'filter by status'), use context from summary\n"
        history_context += "   - Previous query actions inform what the current query is likely about\n\n"
        
        history_context += "4. EXAMPLES OF CONTEXT RESOLUTION:\n"
        history_context += "   - User previously queried 'item_kaus' table, now says 'get 10 from that table'\n"
        history_context += "     → Use table_name: 'item_kaus'\n"
        history_context += "   - User previously joined 'users' and 'orders', now says 'filter by customer_id'\n"
        history_context += "     → Consider both tables, use table prefix if needed\n"
        history_context += "   - User previously queried 'revenue' column, now says 'analyze that by category'\n"
        history_context += "     → Use the exact column names from history\n"
        history_context += "-" * 70 + "\n"
        
        messages.append({
            "role": "assistant",
            "content": history_context
        })
        
        # Add current query as continuation
        messages.append({
            "role": "user",
            "content": f"Current query (CONTINUING FROM ABOVE CONTEXT):\n{user_input}"
        })
    else:
        # No history, just add the current query normally
        messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )

    intent_text = response.choices[0].message.content
    # Parse JSON response safely
    try:
        return json.loads(intent_text)
    except Exception:
        return {"action": "unknown", "filters": {}}
