"""
Tools for the MCP server.
"""

import json
from server.core import mcp
from server.logger_config import logger
from server.db_layer import execute_action
from server.nlp_layer import parse_nl_to_intent
from server.memory import get_default_parameters, update_default_parameters

@mcp.tool()
async def query_users(user_query: str, session_id: str = None) -> dict:

    # Log input
    logger.info("=" * 80)
    logger.info(f"NEW QUERY - Session ID: {session_id}")
    logger.info(f"INPUT: {user_query}")
    
    # Get default parameters for this session
    default_params = get_default_parameters(session_id) if session_id else {}
    
    try:
        # Parse intent with default parameters
        intent = await parse_nl_to_intent(user_query, default_params)
        
        # Update default parameters with any new ent_id or company_name found
        if session_id:
            filters = intent.get("filters", {})
            params_to_update = {}
            
            # Update if new ent_id or company_name is found
            if "ent_id" in filters and filters["ent_id"]:
                params_to_update["ent_id"] = filters["ent_id"]
            if "company_name" in filters and filters["company_name"]:
                params_to_update["company_name"] = filters["company_name"]
            
            if params_to_update:
                update_default_parameters(session_id, params_to_update)
                logger.debug(f"Updated default parameters: {params_to_update}")
        
        # Log intent
        intent_json = json.dumps(intent, indent=2)
        logger.info(f"INTENT:\n{intent_json}")
        
        # Execute action
        result = execute_action(intent["action"], intent.get("filters", {}))
        
        return {"result": result}
        
    except Exception as e:
        # Log errors
        logger.error(f"ERROR processing query: {str(e)}", exc_info=True)
        logger.info("=" * 80)
        raise
