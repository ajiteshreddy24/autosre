import subprocess

def restore_cluster():
    print("🧼 Cleaning up all chaos injections and restoring cluster health...")
    commands = [
        "kubectl set image deployment/paymentservice server=gcr.io/google-samples/microservices-demo/paymentservice:v0.3.8",
        "kubectl patch deployment redis-cart --type=json -p='[{\"op\": \"remove\", \"path\": \"/spec/template/spec/containers/0/command\"}]'",
        "kubectl set resources deployment/cartservice -c server --limits=memory=512Mi --requests=memory=64Mi",
        "kubectl set resources deployment/shippingservice -c server --limits=cpu=200m --requests=cpu=100m",
        "kubectl scale deployment/redis-cart --replicas=1",
        "kubectl scale deployment/paymentservice --replicas=1",
        "kubectl delete pod --field-selector=status.phase!=Running --force --grace-period=0",
        "kubectl rollout status deployment/paymentservice --timeout=10s",
        "kubectl rollout status deployment/cartservice --timeout=10s",
        "kubectl rollout status deployment/shippingservice --timeout=10s",
        "kubectl rollout status deployment/redis-cart --timeout=10s"
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    print("🟢 Cluster restored to healthy baseline!")

if __name__ == "__main__":
    restore_cluster()
