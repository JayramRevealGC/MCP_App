"""
Database query execution for AIES database queries.
"""
import psycopg
from .query_builder import (
    build_fetch_data_query,
    build_filter_by_date_query,
    build_count_units_kaus_query,
    build_get_company_name_query,
    build_count_enterprises_query,
    build_compare_variables_query
)
from .connection import get_connection, execute_with_timeout, QueryTimeoutError

def _format_sql_with_params(sql: str, params: list) -> str:
    """Format SQL query with parameters for display."""
    if not params:
        return sql
    # Replace %s placeholders with parameter values (for display only)
    formatted_sql = sql
    for param in params:
        if isinstance(param, str):
            formatted_sql = formatted_sql.replace('%s', f"'{param}'", 1)
        else:
            formatted_sql = formatted_sql.replace('%s', str(param), 1)
    return formatted_sql

def _add_sql_to_result(result: list, sql: str, params: list) -> list:
    """Add SQL query information to the result."""
    formatted_sql = _format_sql_with_params(sql, params)
    sql_info = {
        "sql_query": formatted_sql,
        "sql_params": params if params else []
    }
    
    # If result is a list of dicts, add SQL info to each dict
    if isinstance(result, list) and len(result) > 0:
        for item in result:
            if isinstance(item, dict):
                item.update(sql_info)
        return result
    else:
        # If result is empty or not a list, wrap it
        if not result:
            return [sql_info]
        return result

def execute_action(action: str, filters: dict):
    """Execute database action with timeout protection."""
    # Handle unknown action without database connection
    if action == "unknown":
        return [{
            "message": "I'm sorry, but your query doesn't match any of the supported query types.",
            "action": "unknown",
            "sql_query": None,
            "sql_params": []
        }]
    
    # Build SQL query first (before execution) so we can return it even on errors
    sql = None
    params = []
    build_error = None
    
    try:
        if action == "fetch_data":
            # Unified fetch data action
            # Variables are optional - if not provided or empty, fetch all fields
            variables = filters.get("variables")
            if variables is not None and not isinstance(variables, list):
                return [{
                    "error": "variables must be a list",
                    "sql_query": None,
                    "sql_params": []
                }]
            if variables and len(variables) == 0:
                variables = None
            
            # Either ent_id or company_name must be provided
            ent_id = filters.get("ent_id")
            company_name = filters.get("company_name")
            
            if not ent_id and not company_name:
                return [{
                    "error": "Either enterprise ID or company name is required",
                    "sql_query": None,
                    "sql_params": []
                }]
            
            sql, params = build_fetch_data_query(
                variables=variables,
                company_name=company_name,
                ent_id=ent_id
            )
            
        elif action == "compare_variables":
            variable_x = filters.get("variable_x")
            variable_y = filters.get("variable_y")
            percentage_threshold = filters.get("percentage_threshold")
            if not variable_x or not variable_y or percentage_threshold is None:
                return [{
                    "error": "variable_x, variable_y, and percentage_threshold are required",
                    "sql_query": None,
                    "sql_params": []
                }]
            company_name = filters.get("company_name")
            ent_id = filters.get("ent_id")
            sql, params = build_compare_variables_query(
                variable_x, variable_y, percentage_threshold, company_name, ent_id
            )
            
        elif action == "filter_by_date":
            submit_date = filters.get("submit_date")
            if not submit_date:
                return [{
                    "error": "Submit date is required (format: YYYY-MM-DD)",
                    "sql_query": None,
                    "sql_params": []
                }]
            sql, params = build_filter_by_date_query(submit_date)
            
        elif action == "count_units_kaus":
            # Either ent_id or company_name must be provided
            ent_id = filters.get("ent_id")
            company_name = filters.get("company_name")
            
            if not ent_id and not company_name:
                return [{
                    "error": "Either enterprise ID or company name is required",
                    "sql_query": None,
                    "sql_params": []
                }]
            
            sql, params = build_count_units_kaus_query(
                company_name=company_name,
                ent_id=ent_id
            )
            
        elif action == "count_enterprises":
            sql, params = build_count_enterprises_query()
            
        elif action == "get_company_name":
            ent_id = filters.get("ent_id")
            if not ent_id:
                return [{
                    "error": "Enterprise ID is required",
                    "sql_query": None,
                    "sql_params": []
                }]
            sql, params = build_get_company_name_query(ent_id)
            
        else:
            return [{
                "error": f"Unknown action: {action}",
                "sql_query": None,
                "sql_params": []
            }]
            
    except Exception as e:
        build_error = str(e)
        # Continue to return error with SQL info if available
    
    # If there was an error building the query, return error with SQL if available
    if build_error:
        error_result = [{
            "error": f"Error building query: {build_error}",
            "sql_query": _format_sql_with_params(sql, params) if sql else None,
            "sql_params": params if params else []
        }]
        return error_result
    
    # Now execute the query with the SQL already built
    def _execute_query():
        conn = get_connection()
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                
                if action in ["count_units_kaus", "count_enterprises"]:
                    row = cur.fetchone()
                    return [dict(row)] if row else []
                else:
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
                        
        except Exception as e:
            # Return error but include SQL query info
            return [{
                "error": f"Error executing query: {str(e)}",
                "sql_query": _format_sql_with_params(sql, params),
                "sql_params": params if params else []
            }]
        finally:
            conn.close()
    
    # Execute the query with timeout protection
    try:
        result = execute_with_timeout(_execute_query)
        # Add SQL to successful results
        return _add_sql_to_result(result, sql, params)
    except QueryTimeoutError as e:
        return [{
            "error": f"Query timeout: {str(e)}",
            "sql_query": _format_sql_with_params(sql, params),
            "sql_params": params if params else []
        }]
    except Exception as e:
        return [{
            "error": f"Unexpected error: {str(e)}",
            "sql_query": _format_sql_with_params(sql, params),
            "sql_params": params if params else []
        }]
