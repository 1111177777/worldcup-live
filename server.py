
from flask import Flask, send_from_directory
import subprocess, os, threading, time

app = Flask(__name__)

# 每10分钟自动刷新数据
def auto_refresh():
    while True:
        time.sleep(600)
        subprocess.run(["python", "live_data.py"], capture_output=True)

t = threading.Thread(target=auto_refresh, daemon=True)
t.start()

@app.route("/")
@app.route("/live.html")
def index():
    return send_from_directory(".", "live.html")

@app.route("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}

if __name__ == "__main__":
    subprocess.run(["python", "live_data.py"], capture_output=True)
    print("🚀 服务器启动: http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080)
