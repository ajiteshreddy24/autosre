# start_dev.ps1
Write-Host "🚀 Starting AutoSRE Port Forwards..." -ForegroundColor Green

# 1. Prometheus
Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/prometheus-server 9090:80"

# 2. Loki
Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/loki 3100:3100"

# 3. Frontend Demo
Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/frontend 8080:80"

Write-Host "✅ All port-forwards started in background windows!" -ForegroundColor Cyan