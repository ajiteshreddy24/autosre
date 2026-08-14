import os
import sys
import time
import requests
import joblib
import pandas as pd
from dotenv import load_dotenv

# Ensure agent module is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
MODEL_PATH = "anomaly/isolation_forest.joblib"
SCALER_PATH = "anomaly/scaler.joblib"
COOLDOWN_SECONDS = 180  # 3-minute cooldown between triggers

PROM_QUERIES = {
    "cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{namespace="default", container!=""}[2m])) or vector(0)',
    "memory_usage": 'sum(container_memory_working_set_bytes{namespace="default", container!=""}) or vector(0)',
    "pod_restarts": 'sum(changes(kube_pod_container_status_restarts_total{namespace="default"}[5m])) or vector(0)',
    "network_rx": 'sum(rate(container_network_receive_bytes_total{namespace="default"}[2m])) or vector(0)'
}

def fetch_current_metric(query: str) -> float:
    """Fetch current metric instant vector from Prometheus."""
    url = f"{PROMETHEUS_URL.rstrip('/')}/api/v1/query"
    try:
        res = requests.get(url, params={"query": query}, timeout=5)
        res.raise_for_status()
        data = res.json().get("data", {}).get("result", [])
        if data:
            return float(data[0]["value"][1])
        return 0.0
    except Exception as e:
        print(f"⚠️ Prometheus instant query error: {e}")
        return 0.0

def run_detector():
    """Runs polling loop and triggers LangGraph agent on anomaly."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        print(f"❌ Model missing! Please run 'python anomaly/train.py' first.")
        return

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("🚀 Anomaly Detector active! Polling Prometheus every 15s...\n")
    last_trigger_time = 0

    while True:
        try:
            # 1. Fetch current live feature vector
            live_metrics = {name: fetch_current_metric(q) for name, q in PROM_QUERIES.items()}

            # 2. Scale & Predict
            df_live = pd.DataFrame([live_metrics])
            scaled_vector = scaler.transform(df_live)
            
            prediction = model.predict(scaled_vector)[0]      # 1 = Normal, -1 = Anomaly
            anomaly_score = model.score_samples(scaled_vector)[0]

            timestamp_str = time.strftime('%H:%M:%S')
            status_str = "🚨 ANOMALY DETECTED" if prediction == -1 else "🟢 NORMAL"
            print(f"[{timestamp_str}] Status: {status_str} | Anomaly Score: {anomaly_score:.4f}")

            # 3. Trigger LangGraph Agent Workflow
            if prediction == -1:
                now = time.time()
                if (now - last_trigger_time) < COOLDOWN_SECONDS:
                    remaining = int(COOLDOWN_SECONDS - (now - last_trigger_time))
                    print(f"⏱️ Anomaly active, but agent is in cooldown ({remaining}s remaining).")
                else:
                    print("\n🔥 TRIGGERING AUTOSRE LANGGRAPH AGENT...")
                    last_trigger_time = now

                    # Construct initial state matching AgentState in agent/state.py
                    initial_state = {
                        "anomaly_detected": True,
                        "anomaly_score": float(anomaly_score),
                        "metrics": live_metrics,
                        "timestamp": time.time(),
                        "status": "triggered"
                    }

                    # Dynamically import and invoke LangGraph graph
                    try:
                        from agent.graph import app as agent_app
                        print("🤖 Executing LangGraph state machine starting at 'detect' node...")
                        final_state = agent_app.invoke(initial_state)
                        print(f"✅ Workflow execution complete! Final Status: {final_state.get('status')}\n")
                    except ImportError:
                        print("⚠️ 'agent.graph' not found yet. Logging anomaly payload:")
                        print(initial_state)

        except Exception as e:
            print(f"⚠️ Error in detector loop: {e}")

        time.sleep(15)

if __name__ == "__main__":
    run_detector()