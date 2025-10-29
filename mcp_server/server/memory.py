"""
Memory storage module for session-based query retention.
Stores user queries per session to enable conversation context.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta

# In-memory storage: {session_id: [query_history]}
_session_memory: Dict[str, List[Dict[str, Any]]] = {}

# Optional: session expiration time (24 hours)
_SESSION_EXPIRY = timedelta(hours=24)
_session_timestamps: Dict[str, datetime] = {}

def store_query(session_id: str, query: str) -> None:
    """
    Store a user query for a given session.
    
    Args:
        session_id: The session identifier
        query: The user query to store
    """
    if not session_id:
        return
    
    # Initialize session if it doesn't exist
    if session_id not in _session_memory:
        _session_memory[session_id] = []
    
    # Store the query with timestamp
    _session_memory[session_id].append({
        "query": query,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update session timestamp
    _session_timestamps[session_id] = datetime.now()

def get_query_history(session_id: str, max_queries: int = None) -> List[str]:
    """
    Retrieve previous queries for a session.
    
    Args:
        session_id: The session identifier
        max_queries: Optional limit on number of queries to return (most recent)
        
    Returns:
        List of previous queries (most recent last)
    """
    if not session_id or session_id not in _session_memory:
        return []
    
    # Clean up expired sessions
    _cleanup_expired_sessions()
    
    queries = _session_memory.get(session_id, [])
    
    # Extract just the query strings
    query_strings = [q["query"] for q in queries]
    
    # Return most recent queries if limit specified
    if max_queries:
        return query_strings[-max_queries:]
    
    return query_strings


def get_full_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Get full query history with metadata for a session.
    
    Args:
        session_id: The session identifier
        
    Returns:
        List of query dictionaries with metadata
    """
    if not session_id or session_id not in _session_memory:
        return []
    
    _cleanup_expired_sessions()
    return _session_memory.get(session_id, [])


def clear_session(session_id: str) -> None:
    """
    Clear all queries for a session.
    
    Args:
        session_id: The session identifier to clear
    """
    if session_id in _session_memory:
        del _session_memory[session_id]
    if session_id in _session_timestamps:
        del _session_timestamps[session_id]


def _cleanup_expired_sessions() -> None:
    """Remove expired sessions to prevent memory leaks."""
    now = datetime.now()
    expired_sessions = [
        session_id 
        for session_id, timestamp in _session_timestamps.items()
        if now - timestamp > _SESSION_EXPIRY
    ]
    
    for session_id in expired_sessions:
        if session_id in _session_memory:
            del _session_memory[session_id]
        if session_id in _session_timestamps:
            del _session_timestamps[session_id]
