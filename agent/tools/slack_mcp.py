import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import warnings

warnings.filterwarnings("ignore", module="pydantic_settings")


load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

mcp = FastMCP("Slack-MCP-Server")

@mcp.tool()
def send_alert(channel: str = "#alerts", message: str = "", severity: str = "HIGH") -> dict:
    """
    Send an automated incident alert notification to Slack via Webhook.
    
    Args:
        channel: Slack channel name (e.g., '#alerts')
        message: Notification message containing anomaly details or RCA summary
        severity: Incident severity level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        
    Returns:
        dict indicating notification delivery status.
    """
    try:
        if not SLACK_WEBHOOK_URL:
            return {
                "status": "warning",
                "message": "SLACK_WEBHOOK_URL not configured in .env. Alert logged locally.",
                "details": f"[{severity}] {message}"
            }
            
        color_map = {
            "CRITICAL": "#FF0000", # Red
            "HIGH": "#FFA500",     # Orange
            "MEDIUM": "#FFFF00",   # Yellow
            "LOW": "#00FF00"       # Green
        }
        
        # Slack Block Kit payload structure
        payload = {
            "text": f"🚨 *AutoSRE Incident Alert* [{severity}]",
            "attachments": [
                {
                    "color": color_map.get(severity, "#FFA500"),
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Severity:* `{severity}` | *Channel:* `{channel}`\n\n*Incident Summary:*\n{message}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "success",
            "channel": channel,
            "severity": severity,
            "message_sent": True
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to deliver Slack webhook: {str(e)}",
            "message_sent": False
        }

@mcp.tool()
def request_approval(action: str, service: str, risk_level: str = "HIGH") -> dict:
    """
    Request Human-in-the-Loop (HITL) approval before executing a high-risk action.
    Pauses the LangGraph state machine execution pending engineer verification.
    
    Args:
        action: Proposed remediation action (e.g., 'rollback_deployment', 'restart_pod')
        service: Target microservice name (e.g., 'paymentservice')
        risk_level: Action risk classification ('MEDIUM', 'HIGH', 'CRITICAL')
        
    Returns:
        dict containing approval status and human gate flag.
    """
    try:
        approval_prompt = (
            f"⚠️ *HUMAN APPROVAL REQUIRED*\n"
            f"The AutoSRE Agent has proposed a high-risk remediation:\n"
            f"• *Target Service:* `{service}`\n"
            f"• *Proposed Action:* `{action}`\n"
            f"• *Risk Classification:* `{risk_level}`\n\n"
            f"Please approve or reject this action in the React Dashboard or Slack."
        )
        
        # Deliver notification to Slack
        slack_result = send_alert(channel="#sre-approvals", message=approval_prompt, severity=risk_level)
        
        # Return state metadata to pause LangGraph execution
        return {
            "status": "pending_approval",
            "action": action,
            "service": service,
            "risk_level": risk_level,
            "slack_notified": slack_result.get("status") == "success",
            "requires_human_gate": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to request HITL approval: {str(e)}",
            "requires_human_gate": True
        }

if __name__ == "__main__":
    print("Testing Slack MCP tools locally...")
    alert_res = send_alert(channel="#alerts", message="Test alert from AutoSRE agent local execution.", severity="HIGH")
    print(f"Send Alert Status: {alert_res['status']}")
    if alert_res.get("error"):
        print(f"Alert Error: {alert_res['error']}")
    elif alert_res.get("message"):
        print(f"Alert Info: {alert_res['message']}")
        
    approval_res = request_approval(action="rollback_deployment", service="paymentservice", risk_level="HIGH")
    print(f"Approval Request Status: {approval_res['status']}")
    if approval_res.get("error"):
        print(f"Approval Error: {approval_res['error']}")
