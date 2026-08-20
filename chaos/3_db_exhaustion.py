import subprocess

def inject_db_failure():
    print("🔥 [CHAOS] Bringing down Redis database (redis-cart)...")
    # Scale database replicas to 0
    cmd = "kubectl scale deployment/redis-cart --replicas=0"
    subprocess.run(cmd, shell=True, check=True)
    print("🔌 Redis is offline! cartservice cannot store user items.")

if __name__ == "__main__":
    inject_db_failure()