import subprocess
import time

def inject_bad_release():
    print("🔥 [CHAOS] Injecting Bad Release into paymentservice...")
    # Point deployment to a bad docker image tag
    cmd = "kubectl set image deployment/paymentservice server=gcr.io/google-samples/microservices-demo/paymentservice:v999.0.0"
    subprocess.run(cmd, shell=True, check=True)
    print("❌ Bad image applied! paymentservice will now fail deployments.")

if __name__ == "__main__":
    inject_bad_release()