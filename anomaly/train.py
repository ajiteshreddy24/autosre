import os
import time
import pandas as pd
import requests
import joblib
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

load_dotenv()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
MODEL_PATH = "anomaly/isolation_forest.joblib"
SCALER_PATH = "anomaly/scaler.joblib"

# Prometheus container metrics available out-of-the-box
PROM_QUERIES = {
    "cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{namespace="default", container!=""}[2m])) or vector(0)',
    "memory_usage": 'sum(container_memory_working_set_bytes{namespace="default", container!=""}) or vector(0)',
    "pod_restarts": 'sum(changes(kube_pod_container_status_restarts_total{namespace="default"}[5m])) or vector(0)',
    "network_rx": 'sum(rate(container_network_receive_bytes_total{namespace="default"}[2m])) or vector(0)'
}

def fetch_prometheus_range(query: str, start_time: int, end_time: int, step: str = "15s") -> list:
    """Fetch time-series range vector from Prometheus API."""
    url = f"{PROMETHEUS_URL.rstrip('/')}/api/v1/query_range"
    params = {"query": query, "start": start_time, "end": end_time, "step": step}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", {}).get("result", [])
        if data:
            return data[0].get("values", [])
        return []
    except Exception as e:
        print(f"⚠️ Error fetching range query '{query}': {e}")
        return []

def train_isolation_forest():
    """Fetches 1 hour of baseline telemetry and trains Isolation Forest."""
    print("📥 Gathering baseline Prometheus container metrics for training...")
    
    end_time = int(time.time())
    start_time = end_time - 3600  # 1 hour lookback
    
    dataset = {}
    for feature_name, query in PROM_QUERIES.items():
        raw_values = fetch_prometheus_range(query, start_time, end_time)
        dataset[feature_name] = [float(v[1]) for v in raw_values]
        
    # Align metric list lengths
    lengths = [len(v) for v in dataset.values() if len(v) > 0]
    if not lengths:
        print("❌ Error: Could not retrieve Prometheus metrics. Is port-forward active on http://localhost:9090?")
        return
        
    min_length = min(lengths)
    data_matrix = {k: v[:min_length] for k, v in dataset.items()}
    df = pd.DataFrame(data_matrix)
    print(f"✅ Baseline dataset created with {len(df)} samples across 4 features.")

    # 1. Scale metrics
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)

    # 2. Train Isolation Forest
    model = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
    model.fit(scaled_data)

    # 3. Save model & scaler
    os.makedirs("anomaly", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"🎉 Model saved to '{MODEL_PATH}' and '{SCALER_PATH}'!")

if __name__ == "__main__":
    train_isolation_forest()