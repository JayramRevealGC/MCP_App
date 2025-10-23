import json
import time
import requests
import streamlit as st
from typing import Dict, List, Optional

class MCPClient:
    """Client wrapper for MCP server communication."""
    
    def __init__(self, server_url: str = "http://54.164.108.181:8001/mcp", timeout: int = 30):
        self.server_url = server_url
        self.session_id = None
        self.timeout = timeout  # Request timeout in seconds
        
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
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """Call a specific tool with given arguments and timeout protection."""
        if not self.session_id:
            return None
            
        try:
            # Record start time for timeout tracking
            start_time = time.time()
            
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
                },
                timeout=self.timeout  # Add timeout to the request
            )
            
            # Check if request took too long
            elapsed_time = time.time() - start_time
            if elapsed_time > self.timeout:
                st.error(f"Request timed out after {elapsed_time:.2f} seconds")
                return {"error": f"Request timeout after {self.timeout} seconds"}
            
            tool_data = self.parse_sse_response(response.text)
            return tool_data
            
        except requests.exceptions.Timeout:
            st.error(f"Request timed out after {self.timeout} seconds")
            return {"error": f"Request timeout after {self.timeout} seconds"}
        except requests.exceptions.ConnectionError:
            st.error("Connection error: Unable to reach the MCP server")
            return {"error": "Connection error: Unable to reach the MCP server"}
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            st.error(f"Failed to call tool: {str(e)}")
            return {"error": f"Failed to call tool: {str(e)}"}
