Write-Host "Starting AutoSRE Development Environment..." -ForegroundColor Green

# 1. Background Port Forwarding
Write-Host "Starting Kubernetes Port-Forwards..." -ForegroundColor Yellow
Start-Job -Name "prom_pf" -ScriptBlock { kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 }
Start-Job -Name "grafana_pf" -ScriptBlock { kubectl port-forward svc/prometheus-grafana 3000:80 }

# 2. Pause for port binding
Write-Host "Waiting for Prometheus and Grafana ports to open..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 3. Maintain load generator for active metric baseline
kubectl scale deployment/loadgenerator --replicas=1

# 4. Open Web Dashboards
Write-Host "Opening Dashboards..." -ForegroundColor Cyan
Start-Process "chrome.exe" "http://localhost:9090 http://localhost:3000"

# 5. Launch Detector
Write-Host "Starting Anomaly Detector..." -ForegroundColor Green
Set-Location D:\autosre
.\venv\Scripts\python.exe anomaly/detector.py
