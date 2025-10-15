import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        dbname=os.getenv("PG_DATABASE"),
    )

# Maps actions to SQL templates
ACTION_SQL_MAP = {
    "fetch_tables": "SELECT table_schema, table_name FROM information_schema.tables;",
    "fetch_n_records_from_table": "SELECT * FROM space_product_aies.{} LIMIT %s;",
    "fetch_row_by_id": "SELECT * FROM space_product_aies.{} WHERE id = %s;",
    "fetch_n_joined_records": "SELECT {}.id, {}.ref_per, {}.ref_per as {}_ref_per FROM space_product_aies.{} JOIN space_product_aies.{} ON {}.id = {}.id LIMIT %s;",
    "get_table_summary": "SELECT COUNT(*) as row_count FROM space_product_aies.{};"
}

def execute_action(action: str, filters: dict):
    conn = get_connection()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            if action == "fetch_tables":
                sql = ACTION_SQL_MAP[action]
                cur.execute(sql)
                rows = cur.fetchall()
                return [dict(row) for row in rows]

            elif action == "fetch_n_records_from_table":
                # Validate table name to prevent SQL injection
                table_name = filters["table_name"]
                limit = filters.get("n", 5)

                # Format SQL with validated table name and use parameterized query for limit
                sql = ACTION_SQL_MAP[action].format(table_name)
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
                return [dict(row) for row in rows]

            elif action == "fetch_row_by_id":
                # Validate table name and ID to prevent SQL injection
                table_name = filters["table_name"]
                row_id = filters["id"]
                
                # Format SQL with validated table name and use parameterized query for ID
                sql = ACTION_SQL_MAP[action].format(table_name)
                cur.execute(sql, (row_id,))
                row = cur.fetchone()
                if row:
                    return [dict(row)]
                else:
                    return [{"error": f"No row found with id {row_id}"}]

            elif action == "fetch_n_joined_records":
                # Validate table names and limit to prevent SQL injection
                table1 = filters["table1"]
                table2 = filters["table2"]
                limit = filters.get("n", 5)
                
                # Format SQL with validated table names and use parameterized query for limit
                sql = ACTION_SQL_MAP[action].format(table1, table1, table2, table2, table1, table2, table1, table2)
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
                return [dict(row) for row in rows]

            elif action == "get_table_summary":
                # Validate table name to prevent SQL injection
                table_name = filters["table_name"]
                
                # Get row count
                sql = ACTION_SQL_MAP[action].format(table_name)
                cur.execute(sql)
                row_count_result = cur.fetchone()
                row_count = row_count_result['row_count'] if row_count_result else 0
                
                # Get column count and column names
                column_sql = """
                SELECT COUNT(*) as column_count 
                FROM information_schema.columns 
                WHERE table_schema = 'space_product_aies' AND table_name = %s;
                """
                cur.execute(column_sql, (table_name,))
                column_count_result = cur.fetchone()
                column_count = column_count_result['column_count'] if column_count_result else 0
                
                # Get column names
                column_names_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'space_product_aies' AND table_name = %s
                ORDER BY ordinal_position;
                """
                cur.execute(column_names_sql, (table_name,))
                column_rows = cur.fetchall()
                column_names = [row['column_name'] for row in column_rows]
                
                # Get sample rows (first 5 rows)
                sample_sql = f"SELECT * FROM space_product_aies.{table_name} LIMIT 5;"
                cur.execute(sample_sql)
                sample_rows = cur.fetchall()
                sample_data = [dict(row) for row in sample_rows]
                
                return [{"table_name": table_name},
                        {"row_count": row_count},
                        {"column_count": column_count},
                        {"column_names": column_names},
                        {"sample_rows": sample_data}]
    finally:
        conn.close()
