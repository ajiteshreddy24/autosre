import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import time
import requests
import joblib
import pandas as pd
from datetime import datetime

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
    except Exception as e:
        return 0.0

def load_model_and_scaler():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "isolation_forest.joblib")
    scaler_path = os.path.join(script_dir, "scaler.joblib")

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print(f"✅ Loaded updated model and scaler from {script_dir}")
        return model, scaler
    except Exception as e:
        print(f"❌ Failed to load model artifacts: {e}")
        sys.exit(1)

def main():
    model, scaler = load_model_and_scaler()
    print("🚀 44-Feature Anomaly Detector Active! Polling Prometheus every 15s...\n")

    while True:
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

        df_live = pd.DataFrame([live_metrics])
        df_scaled = scaler.transform(df_live)

        prediction = model.predict(df_scaled)[0]
        score = model.decision_function(df_scaled)[0]

        timestamp = datetime.now().strftime("%H:%M:%S")

        if prediction == -1:
            scaled_series = pd.Series(df_scaled[0], index=df_live.columns)
            spiked_feature = scaled_series.abs().idxmax()
            target_service = spiked_feature.split("_")[0].upper()
            z_score = scaled_series[spiked_feature]
            raw_value = live_metrics[spiked_feature]
            
            print(f"[{timestamp}] 🚨 ANOMALY DETECTED | Score: {score:.4f} | Target Service: {target_service} | Spike: {spiked_feature} (Raw: {raw_value:.2f}, Z-Score: {z_score:.2f}σ)")
        else:
            print(f"[{timestamp}] 🟢 NORMAL | Score: {score:.4f}")

        time.sleep(15)

if __name__ == "__main__":
    main()
