import subprocess

def restore_cluster():
    print("🧼 Cleaning up all chaos injections and restoring cluster health...")
    commands = [
        "kubectl rollout undo deployment/paymentservice",
        "kubectl set resources deployment/cartservice -c server --limits=memory=256Mi --requests=memory=64Mi",
        "kubectl set resources deployment/shippingservice -c server --limits=cpu=200m --requests=cpu=100m",
        "kubectl scale deployment/redis-cart --replicas=1",
        "kubectl rollout status deployment/paymentservice",
        "kubectl rollout status deployment/cartservice",
        "kubectl rollout status deployment/shippingservice"
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    print("🟢 Cluster restored to healthy baseline!")

if __name__ == "__main__":
    restore_cluster()