"""
Database connection management and timeout handling.
"""
import os
import psycopg
import threading
from dotenv import load_dotenv

load_dotenv()

# Query timeout configuration (60 seconds)
QUERY_TIMEOUT = 60

class QueryTimeoutError(Exception):
    """Raised when a database query exceeds the timeout limit."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for query timeout."""
    raise QueryTimeoutError("Query execution timed out after 60 seconds")

def execute_with_timeout(func, *args, **kwargs):
    """Execute a function with a timeout limit."""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=QUERY_TIMEOUT)
    
    if thread.is_alive():
        # Thread is still running, query timed out
        raise QueryTimeoutError(f"Query execution timed out after {QUERY_TIMEOUT} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def get_connection():
    """Get a database connection using environment variables."""
    return psycopg.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        dbname=os.getenv("PG_DATABASE"),
    )
