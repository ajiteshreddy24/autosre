import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

def query_prometheus(promql: str) -> float:
    """
    Send a PromQL query to Prometheus and return the value.
    PromQL is the query language Prometheus uses.
    Example: 'rate(http_requests_total[5m])' means
    'give me the per-second rate of HTTP requests over 5 minutes'
    """
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=10
        )
        data = response.json()
        
        # Prometheus returns results in this format:
        # {"data": {"result": [{"value": [timestamp, "value"]}]}}
        results = data.get("data", {}).get("result", [])
        if results:
            return float(results[0]["value"][1])
        return 0.0
    except Exception as e:
        print(f"Prometheus query failed: {e}")
        return 0.0


def get_metrics(service_name: str, time_range_minutes: int = 5) -> dict:
    """
    Get health metrics for a specific service.
    
    This is the tool the agent calls when it detects an anomaly.
    It queries Prometheus for 4 key metrics that tell us
    how healthy a service is right now.
    
    Args:
        service_name: Name of the Kubernetes service (e.g. "paymentservice")
        time_range_minutes: How far back to look (default: 5 minutes)
    
    Returns:
        dict with error_rate, latency, cpu, memory metrics
    """
    time_range = f"{time_range_minutes}m"
    
    # Error rate: what % of requests are failing?
    # If this spikes → something is broken
    error_rate = query_prometheus(
        f'rate(http_requests_total{{job="{service_name}",status=~"5.."}}[{time_range}])'
    )
    
    # Total request rate: how many requests per second?
    total_rate = query_prometheus(
        f'rate(http_requests_total{{job="{service_name}"}}[{time_range}])'
    )
    
    # Error percentage: error_rate / total_rate * 100
    error_percentage = (error_rate / total_rate * 100) if total_rate > 0 else 0.0
    
    # CPU usage: how much CPU is the service using?
    cpu_usage = query_prometheus(
        f'rate(container_cpu_usage_seconds_total{{pod=~"{service_name}.*"}}[{time_range}])'
    )
    
    # Memory usage in MB
    memory_usage = query_prometheus(
        f'container_memory_usage_bytes{{pod=~"{service_name}.*"}}'
    ) / (1024 * 1024)  # Convert bytes to MB
    
    return {
        "service": service_name,
        "time_range_minutes": time_range_minutes,
        "error_rate_percent": round(error_percentage, 2),
        "total_requests_per_sec": round(total_rate, 2),
        "cpu_usage_cores": round(cpu_usage, 4),
        "memory_usage_mb": round(memory_usage, 2),
        "timestamp": datetime.now().isoformat()
    }


# Test it directly
if __name__ == "__main__":
    print("Testing Prometheus MCP...")
    result = get_metrics("frontend", 5)
    print(result)