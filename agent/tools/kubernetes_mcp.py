import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def restart_pod(service_name: str) -> dict:
    """
    Restart a Kubernetes pod by deleting it.
    Kubernetes automatically recreates it.
    
    This is the agent's first response to most failures —
    if a pod is misbehaving, restart it and see if it recovers.
    """
    try:
        # Get the pod name first
        get_pod = subprocess.run(
            ["kubectl", "get", "pods", "-l", 
             f"app={service_name}",
             "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True
        )
        
        pod_name = get_pod.stdout.strip()
        
        if not pod_name:
            return {
                "success": False,
                "error": f"No pod found for service {service_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Delete the pod — K8s recreates it automatically
        result = subprocess.run(
            ["kubectl", "delete", "pod", pod_name],
            capture_output=True, text=True
        )
        
        return {
            "success": True,
            "service": service_name,
            "pod_deleted": pod_name,
            "action": "restart",
            "message": f"Pod {pod_name} deleted, Kubernetes will recreate it",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def scale_deployment(service_name: str, replicas: int) -> dict:
    """
    Scale a deployment up or down.
    
    Agent uses this when:
    - DB connection exhaustion → scale down to reduce connections
    - High traffic causing failures → scale up to handle load
    """
    try:
        result = subprocess.run(
            ["kubectl", "scale", "deployment", service_name,
             f"--replicas={replicas}"],
            capture_output=True, text=True
        )
        
        return {
            "success": True,
            "service": service_name,
            "action": "scale",
            "replicas": replicas,
            "message": f"Scaled {service_name} to {replicas} replicas",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def rollback_deployment(service_name: str) -> dict:
    """
    Rollback a deployment to its previous version.
    
    Agent uses this when:
    - Error rate spiked right after a deployment
    - GitHub shows recent deploy matches anomaly timestamp
    - Root cause = bad deployment
    
    This is a HIGH RISK action — requires human approval first.
    """
    try:
        result = subprocess.run(
            ["kubectl", "rollout", "undo", 
             f"deployment/{service_name}"],
            capture_output=True, text=True
        )
        
        return {
            "success": True,
            "service": service_name,
            "action": "rollback",
            "message": f"Rolled back {service_name} to previous version",
            "output": result.stdout,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Test it directly
if __name__ == "__main__":
    print("Testing Kubernetes MCP...")
    
    # Test scale (safe to test)
    result = scale_deployment("frontend", 2)
    print("Scale result:", result)
    
    # Scale back to 1
    result = scale_deployment("frontend", 1)
    print("Scale back result:", result)