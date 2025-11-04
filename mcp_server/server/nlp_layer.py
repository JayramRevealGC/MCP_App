import json
import openai
from server.logger_config import logger

async def parse_nl_to_intent(user_input: str, default_parameters: dict = None) -> dict:
    """
    Convert natural language into structured query intent for database queries.
    Supports 6 specific query patterns:
    1. Fetch data for enterprise/company (with optional specific fields)
    2. Compare two variables with percentage difference threshold
    3. Filter by submit date
    4. Count units and KAUs for a company
    5. Count unique enterprises
    6. Get company name from enterprise ID
    """
    
    system_prompt = """You are an intent parser for database queries.
    Convert the user's natural language into JSON with this format:
    {
        "action": "<one of: fetch_data, compare_variables, filter_by_date, count_units_kaus, count_enterprises, get_company_name, unknown>",
        "filters": {...} <fill with relevant parameters>
    }
    
    IMPORTANT: If the user's query does NOT match any of the 6 specific query types described below, 
    you MUST return action: "unknown" with filters: {}.
    
    Use "unknown" when:
    - The query is not related to enterprise/company data retrieval
    - The query asks for operations not supported by the 6 query types
    - The query is unclear or incomplete
    - The query requests unsupported database operations (INSERT, UPDATE, DELETE, etc.)
    
    ================================================================================
    QUERY TYPES AND EXAMPLES
    ================================================================================
    
    1. FETCH_DATA - Fetch data for enterprise/company (all fields or specific fields)
    Action: "fetch_data"
    Filters: {
        "variables": ["x", "y", "z"],  // OPTIONAL: List of column/variable names to fetch. If not provided or empty, fetch all fields.
        "ent_id": "000" OR "company_name": "XXX"  // REQUIRED: Either enterprise ID OR company name. Prioritize ent_id if both are mentioned.
    }
    Logic:
    - If specific variables/fields are mentioned, include them in the "variables" array
    - If no specific fields mentioned, omit "variables" or set to empty array []
    - If enterprise ID is mentioned, use "ent_id"
    - If only company name is mentioned (no enterprise ID), use "company_name"
    - If both enterprise ID and company name are mentioned, prefer "ent_id"
    
    Examples:
    - "Fetch all records for enterprise ID 000"  // All fields, by ent_id
    - "Show me all data for enterprise 000"  // All fields, by ent_id
    - "I want to see all the data from company XXX"  // All fields, by company_name
    - "Show me all records for company ABC Corp"  // All fields, by company_name
    - "Give me x, y, z variable values for enterprise 000"  // Specific fields, by ent_id
    - "Show me revenue and profit for company ABC"  // Specific fields, by company_name
    - "Get variables x, y, z for company XXX"  // Specific fields, by company_name
    - "What are the values of revenue, cost, profit for enterprise 123"  // Specific fields, by ent_id
    - "Get all records where ent_id is 000"  // All fields, by ent_id
    - "Fetch all data where company is XYZ"  // All fields, by company_name
    
    2. COMPARE_VARIABLES - Compare two variables with percentage difference threshold
    Action: "compare_variables"
    Filters: {
        "variable_x": "x",  // First variable name
        "variable_y": "y",  // Second variable name (to compare against)
        "percentage_threshold": 0.2,  // Threshold as decimal (0.2 = 20%)
        "company_name": "XXX" OR "ent_id": "000"  // Filter by company or enterprise ID
    }
    Examples:
    - "I want to see all values of variable x that are more than 20% different than variable y for company XXX"
    - "Show me x values where x is 25% different from y for enterprise 000"
    - "Find establishments where revenue differs from profit by more than 15% for company ABC"
    - "Get all x values that differ from y by over 30% for company XYZ"
    
    3. FILTER_BY_DATE - Get companies that submitted on a specific date
    Action: "filter_by_date"
    Filters: {
        "submit_date": "2023-09-20"  // Date in YYYY-MM-DD format
    }
    Examples:
    - "What companies submitted on 2023-09-20"
    - "Show me enterprises that submitted on September 20, 2023"
    - "Which companies submitted on date 2023-09-20"
    - "Find all companies with submit date 2023-09-20"
    
    4. COUNT_UNITS_KAUS - Count units and KAUs for a company/enterprise
    Action: "count_units_kaus"
    Filters: {
        "ent_id": "000" OR "company_name": "XXX"  // Either enterprise ID OR company name. Prioritize ent_id if both are mentioned.
    }
    Logic:
    - If enterprise ID is mentioned, use "ent_id"
    - If only company name is mentioned (no enterprise ID), use "company_name"
    - If both enterprise ID and company name are mentioned, prefer "ent_id"
    
    Examples:
    - "How many units and KAUs are present under company XXX"  // By company_name
    - "Count units and KAUs for company ABC"  // By company_name
    - "What's the count of units and KAUs for enterprise 000"  // By ent_id
    - "How many reporting IDs and KAUs for company 123"  // By company_name
    - "Count units and KAUs for enterprise ID 000"  // By ent_id
    - "How many units and KAUs are present under enterprise XYZ"  // By ent_id
    
    5. COUNT_ENTERPRISES - Count unique enterprises in the database
    Action: "count_enterprises"
    Filters: {}  // No filters needed
    Examples:
    - "How many unique enterprise/companies are there in the database"
    - "Count all unique enterprises"
    - "How many distinct companies are there"
    - "What's the total number of enterprises"
    
    6. GET_COMPANY_NAME - Get company name for a specific enterprise ID
    Action: "get_company_name"
    Filters: {
        "ent_id": "000"  // The enterprise ID
    }
    Examples:
    - "Fetch company name with enterprise ID 000"
    - "What is the company name for enterprise 000"
    - "Get company name where ent_id is 000"
    - "Show me the company name for enterprise ID 123"
    
    7. UNKNOWN - For queries that don't match any of the above 6 types
    Filters: {}  // Always empty
    Use this action when the query doesn't fit any of the 6 supported query types.
    
    ================================================================================
    IMPORTANT NOTES:
    ================================================================================
    - Always extract the exact values mentioned (enterprise IDs, company names, dates, variable names)
    - For dates, convert to YYYY-MM-DD format
    - For percentage thresholds, convert to decimal (20% = 0.2, 25% = 0.25, etc.)
    - Variable names should be extracted exactly as mentioned (case-sensitive)
    - Company names should preserve quotes if present in the query
    - If user mentions "enterprise" or "ent_id", use ent_id filter
    - If user mentions "company" or "company name", use company_name filter
    """
    
    client = openai.OpenAI()
    
    # Build user message with context about default parameters
    user_message = user_input
    if default_parameters:
        context_parts = []
        if default_parameters.get("ent_id"):
            context_parts.append(f"Enterprise ID: {default_parameters['ent_id']}")
        if default_parameters.get("company_name"):
            context_parts.append(f"Company Name: {default_parameters['company_name']}")
        
        if context_parts:
            context = "\nNote: If the query doesn't specify an enterprise ID or company name, use the following default: " + ", ".join(context_parts) + "."
            user_message = user_input + "\n\n" + context
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        logger.debug(f"Calling OpenAI API for intent parsing")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        intent_data = json.loads(response.choices[0].message.content)
        logger.debug(f"Successfully parsed intent from OpenAI response")
        
        # Apply default parameters if ent_id or company_name is missing
        if default_parameters:
            filters = intent_data.get("filters", {})
            
            # Only use default parameters if they're not already present in the parsed intent
            # Prioritize ent_id over company_name if both are available in defaults
            if not filters.get("ent_id") and not filters.get("company_name"):
                if default_parameters.get("ent_id"):
                    filters["ent_id"] = default_parameters["ent_id"]
                    logger.debug(f"Using default ent_id: {default_parameters['ent_id']}")
                elif default_parameters.get("company_name"):
                    filters["company_name"] = default_parameters["company_name"]
                    logger.debug(f"Using default company_name: {default_parameters['company_name']}")
            
            intent_data["filters"] = filters
        
        return intent_data
    except Exception as e:
        # Fallback parsing attempt
        logger.error(f"Error parsing intent: {e}", exc_info=True)
        return {"action": "unknown", "filters": {}}
        