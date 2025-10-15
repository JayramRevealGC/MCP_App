import json
import openai

async def parse_nl_to_intent(user_input: str) -> dict:
    """
    Convert natural language into structured query intent.
    """
    system_prompt = """You are an intent parser for database queries.
    Convert the user's natural language into JSON with this format:
    {
        "action": "<one of: fetch_tables, fetch_n_records_from_table, fetch_row_by_id, fetch_n_joined_records, get_table_summary>",
        "filters": {...} <optional, fill it with any parameter, if passed by user, similar to table_name, column_name, n, id, table1, table2, limit, etc.>
    }
    
    Available actions:
    - fetch_tables: Get list of all tables
    - fetch_n_records_from_table: Get n records from a specific table
    - fetch_row_by_id: Get a specific row by ID from a table
    - fetch_n_joined_records: Join two tables and get n records
    - get_table_summary: Get summary information about a table (row count, column count, column names, sample rows)
    
    For get_table_summary action, use filters like: {"table_name": "table_name"}
    """

    client = openai.OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.2
    )

    intent_text = response.choices[0].message.content
    # Parse JSON response safely
    try:
        return json.loads(intent_text)
    except Exception:
        return {"action": "unknown", "filters": {}}
