import subprocess

def inject_oom_limit():
    print("🔥 [CHAOS] Injecting severe memory limit on cartservice...")
    # Standard syntax: --requests=memory=10Mi
    cmd = 'kubectl set resources deployment/cartservice -c server --limits=memory=10Mi --requests=memory=10Mi'
    subprocess.run(cmd, shell=True, check=True)
    print("💥 Memory limit patched! cartservice will now OOMKill.")

if __name__ == "__main__":
    inject_oom_limit()