import subprocess
import json

def inject_db_crash():
    print("🔥 [CHAOS] Patching redis-cart with failing command...")
    
    # Safely format JSON patch array
    patch_payload = json.dumps([
        {
            "op": "add",
            "path": "/spec/template/spec/containers/0/command",
            "value": ["sh", "-c", "exit 1"]
        }
    ])
    
    # Pass as a clean list without shell=True to prevent PowerShell quote stripping
    cmd = [
        "kubectl", "patch", "deployment", "redis-cart",
        "--type=json",
        "-p", patch_payload
    ]
    
    subprocess.run(cmd, check=True)
    print("🔌 redis-cart is now crashing repeatedly in a restart loop!")

if __name__ == "__main__":
    inject_db_crash()