"""
Logging configuration for MCP server.
Outputs logs to console/stdout for container logs.
"""

import os
import logging

def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the MCP server.
    Logs are output to console/stdout only (for container logs).
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger with only console handler
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler only - for container logs
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("mcp_server")

# Get log level from environment variable or default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Initialize logger
logger = setup_logging(log_level=LOG_LEVEL)
