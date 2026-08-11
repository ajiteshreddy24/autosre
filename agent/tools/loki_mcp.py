import os
import time
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import warnings

warnings.filterwarnings("ignore", module="pydantic_settings")

# Load environment variables from .env
load_dotenv()

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

# Initialize the MCP Server instance
mcp = FastMCP("Loki-MCP-Server")

@mcp.tool()
def get_logs(service_name: str, time_range_minutes: int = 15, level: str = "ERROR") -> dict:
    """
    Fetch recent log lines for a specific microservice from Loki filtered by severity level.
    
    Args:
        service_name: Name of the microservice (e.g., 'frontend', 'cartservice', 'paymentservice')
        time_range_minutes: How many minutes back to query (default: 15)
        level: Severity level filter string (e.g., 'ERROR', 'WARN', 'INFO')
        
    Returns:
        dict containing query status, total log count, and formatted log lines.
    """
    try:
        # 1. Convert minutes back into nanosecond epoch timestamps (Loki requirement)
        now_sec = time.time()
        end_time_ns = int(now_sec * 1e9)
        start_time_ns = int((now_sec - (time_range_minutes * 60)) * 1e9)
        
        # 2. Build LogQL query: selects log stream by app label and filters for text string match
        # Example LogQL generated: {app="cartservice"} |= "ERROR"
        logql_query = f'{{app="{service_name}"}} |= "{level}"'
        
        endpoint = f"{LOKI_URL.rstrip('/')}/loki/api/v1/query_range"
        params = {
            "query": logql_query,
            "start": start_time_ns,
            "end": end_time_ns,
            "limit": 100,
            "direction": "BACKWARD"  # Fetch newest logs first
        }
        
        # 3. Query Loki REST API
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        log_lines = []
        
        # 4. Extract log lines from streams response structure
        results = data.get("data", {}).get("result", [])
        for stream in results:
            # stream['values'] is a list of [timestamp_str_ns, log_message_str]
            for ts, line in stream.get("values", []):
                log_lines.append({
                    "timestamp_ns": ts,
                    "message": line.strip()
                })
                
        return {
            "status": "success",
            "service": service_name,
            "query": logql_query,
            "count": len(log_lines),
            "logs": log_lines
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "service": service_name,
            "error": f"Failed to connect to Loki at {LOKI_URL}: {str(e)}",
            "logs": []
        }
    except Exception as e:
        return {
            "status": "error",
            "service": service_name,
            "error": f"Unexpected error querying Loki: {str(e)}",
            "logs": []
        }

if __name__ == "__main__":
    print("Testing Loki MCP tool locally...")
    test_result = get_logs(service_name="cartservice", time_range_minutes=30, level="ERROR")
    print(f"Status: {test_result['status']}")
    print(f"Logs fetched: {test_result['count']}")
    if test_result['logs']:
        print(f"Sample log: {test_result['logs'][0]['message']}")