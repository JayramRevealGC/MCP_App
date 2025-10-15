import json
import requests
import streamlit as st
from typing import Dict, List, Optional

class MCPClient:
    """Client wrapper for MCP server communication."""
    
    def __init__(self, server_url: str = "http://54.164.108.181:8001/mcp"):
        self.server_url = server_url
        self.session_id = None
        
    def parse_sse_response(self, response_text: str) -> Optional[Dict]:
        """Parse Server-Sent Events response to extract JSON data."""
        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                json_str = line[6:]
                try:
                    return json.loads(json_str)
                except:
                    return None
        return None
    
    def initialize_session(self) -> bool:
        """Initialize a new MCP session."""
        try:
            init_response = requests.post(self.server_url, 
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {}
                        },
                        "clientInfo": {
                            "name": "streamlit-client",
                            "version": "1.0.0"
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if init_response.status_code != 200:
                return False
                
            # Extract session ID from response headers
            self.session_id = init_response.headers.get('mcp-session-id')
            
            # Send initialized notification
            requests.post(self.server_url, 
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id
                }
            )
            
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize MCP session: {str(e)}")
            return False
    
    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools from MCP server."""
        if not self.session_id:
            return []
            
        try:
            tools_response = requests.post(self.server_url, 
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id
                }
            )
            
            tools_data = self.parse_sse_response(tools_response.text)
            if tools_data and "result" in tools_data:
                return tools_data["result"].get("tools", [])
            return []
            
        except Exception as e:
            st.error(f"Failed to get tools: {str(e)}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """Call a specific tool with given arguments."""
        if not self.session_id:
            return None
            
        try:
            response = requests.post(self.server_url, 
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id
                }
            )
            
            tool_data = self.parse_sse_response(response.text)
            return tool_data
            
        except Exception as e:
            st.error(f"Failed to call tool: {str(e)}")
            return None
