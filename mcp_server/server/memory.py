"""
Memory storage module for session-based default parameters.
Stores default ent_id and company_name per session.
"""

from typing import Dict, Any
from datetime import datetime, timedelta

# Default parameters per session: {session_id: {"ent_id": "...", "company_name": "..."}}
_default_parameters: Dict[str, Dict[str, Any]] = {}

# Optional: session expiration time (24 hours)
_SESSION_EXPIRY = timedelta(hours=24)
_session_timestamps: Dict[str, datetime] = {}

def get_default_parameters(session_id: str) -> Dict[str, Any]:
    """
    Get default parameters (ent_id, company_name) for a session.
    
    Args:
        session_id: The session identifier
        
    Returns:
        Dictionary with default parameters (may contain "ent_id" and/or "company_name")
    """
    if not session_id or session_id not in _default_parameters:
        return {}
    
    _cleanup_expired_sessions()
    return _default_parameters.get(session_id, {}).copy()


def update_default_parameters(session_id: str, parameters: Dict[str, Any]) -> None:
    """
    Update default parameters for a session with new values.
    Only updates ent_id and company_name if they are present in parameters.
    
    Args:
        session_id: The session identifier
        parameters: Dictionary containing "ent_id" and/or "company_name" to update
    """
    if not session_id:
        return
    
    # Initialize session if it doesn't exist
    if session_id not in _default_parameters:
        _default_parameters[session_id] = {}
    
    # Update only if the parameter is provided
    if "ent_id" in parameters and parameters["ent_id"]:
        _default_parameters[session_id]["ent_id"] = parameters["ent_id"]
    
    if "company_name" in parameters and parameters["company_name"]:
        _default_parameters[session_id]["company_name"] = parameters["company_name"]
    
    # Update session timestamp
    _session_timestamps[session_id] = datetime.now()


def clear_session(session_id: str) -> None:
    """
    Clear default parameters for a session.
    
    Args:
        session_id: The session identifier to clear
    """
    if session_id in _default_parameters:
        del _default_parameters[session_id]
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
        if session_id in _default_parameters:
            del _default_parameters[session_id]
        if session_id in _session_timestamps:
            del _session_timestamps[session_id]
