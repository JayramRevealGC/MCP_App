import json

def extract_content_from_result(result):
    """Extract and parse content from MCP result."""
    if result and 'content' in result and isinstance(result['content'], list):
        content_text = result['content'][0]['text']
        try:
            parsed_content = json.loads(content_text)
            return parsed_content.get('result')
        except json.JSONDecodeError:
            return "Error parsing response"
    return "No response received"
