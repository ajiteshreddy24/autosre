import os
import sys
import time
import requests
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

SERVICES = [
    "frontend",
    "cartservice",
    "paymentservice",
    "checkoutservice",
    "shippingservice",
    "emailservice",
    "productcatalogservice",
    "recommendationservice",
    "adservice",
    "currencyservice",
    "redis-cart"
]

def fetch_current_metric(query):
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': query}, timeout=5)
        data = response.json()
        results = data.get('data', {}).get('result', [])
        if results:
            return float(results[0]['value'][1])
        return 0.0
    except Exception:
        return 0.0

def collect_training_data():
    print("📥 Gathering live Prometheus metrics to establish healthy 44-feature baseline...")
    records = []
    
    # Collect 30 live samples with 2-second delays
    for i in range(30):
        live_metrics = {}
        for svc in SERVICES:
            live_metrics[f"{svc}_cpu"] = fetch_current_metric(
                f'sum(rate(container_cpu_usage_seconds_total{{namespace="default", pod=~"{svc}.*", container!=""}}[2m])) or vector(0)'
            )
            live_metrics[f"{svc}_memory"] = fetch_current_metric(
                f'sum(container_memory_working_set_bytes{{namespace="default", pod=~"{svc}.*", container!=""}}) or vector(0)'
            )
            live_metrics[f"{svc}_restarts"] = fetch_current_metric(
                f'sum(changes(kube_pod_container_status_restarts_total{{namespace="default", pod=~"{svc}.*"}}[5m])) or vector(0)'
            )
            live_metrics[f"{svc}_replicas"] = fetch_current_metric(
                f'sum(kube_deployment_status_replicas_available{{namespace="default", deployment="{svc}"}}) or vector(0)'
            )
        records.append(live_metrics)
        time.sleep(2)

    df = pd.DataFrame(records)
    print(f"✅ Training dataset built: {len(df)} samples across {len(df.columns)} features.")
    return df

def main():
    df = collect_training_data()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_scaled)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    joblib.dump(model, os.path.join(script_dir, "isolation_forest.joblib"))
    joblib.dump(scaler, os.path.join(script_dir, "scaler.joblib"))
    
    print("🎉 Saved updated 44-feature model and scaler to anomaly directory!")

if __name__ == "__main__":
    main()
