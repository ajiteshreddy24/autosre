#!/bin/bash

echo "🚀 Starting AutoSRE development environment..."

# Step 1: Deploy Online Boutique
echo "📦 Deploying Online Boutique..."
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml

# Step 2: Fix cartservice memory
echo "🔧 Fixing cartservice memory..."
sleep 10
kubectl set resources deployment cartservice --limits=memory=256Mi --requests=memory=128Mi

# Step 3: Install Prometheus
echo "📊 Installing Prometheus + Grafana..."
helm install prometheus prometheus-community/kube-prometheus-stack --set grafana.adminPassword=admin123 2>/dev/null || echo "Prometheus already installed"

# Step 4: Install Loki
echo "📝 Installing Loki..."
helm install loki grafana/loki-stack 2>/dev/null || echo "Loki already installed"

echo "⏳ Waiting for pods to start (60 seconds)..."
sleep 60

# Step 5: Start port-forwards
echo "🔌 Starting port-forwards..."
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &
kubectl port-forward svc/loki 3100:3100 &
kubectl port-forward svc/frontend 8080:80 &

echo "✅ Environment ready!"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo "Online Boutique: http://localhost:8080"