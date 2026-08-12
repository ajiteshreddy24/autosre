import subprocess

def inject_cascading_delay():
    print("🔥 [CHAOS] Injecting CPU starvation/delay into shippingservice...")
    # Standard syntax: --requests=cpu=1m
    cmd = 'kubectl set resources deployment/shippingservice -c server --limits=cpu=1m --requests=cpu=1m'
    subprocess.run(cmd, shell=True, check=True)
    print("🐢 shippingservice is CPU starved! Inbound requests will now experience severe delays.")

if __name__ == "__main__":
    inject_cascading_delay()