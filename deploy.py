"""
世界杯分析工具 — 云端部署脚本
用法: python deploy.py
"""
import os, json, sys

REQUIREMENTS = """
flask>=3.0.0
akshare>=1.14.0
matplotlib>=3.8.0
"""

DEPLOY_FILES = [
    "live_data.py",
    "schedule.json",
    "dashboard.py",
    "live.html",
]

def check_files():
    """检查必需文件是否齐全"""
    missing = [f for f in DEPLOY_FILES if not os.path.exists(f)]
    if missing:
        print(f"❌ 缺少文件: {missing}")
        sys.exit(1)
    print("✅ 所有必要文件就绪")

def create_requirements():
    with open("requirements.txt", "w") as f:
        f.write(REQUIREMENTS)
    print("✅ requirements.txt 已生成")

def create_web_server():
    """生成简单的 Flask Web 服务器"""
    server_code = '''
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
'''
    with open("server.py", "w") as f:
        f.write(server_code)
    print("✅ server.py 已生成")

if __name__ == "__main__":
    check_files()
    create_requirements()
    create_web_server()
    print()
    print("="*50)
    print("部署包准备完成！")
    print("="*50)
    print()
    print("📦 上传到服务器后执行:")
    print("  pip install -r requirements.txt")
    print("  python live_data.py")
    print("  python server.py")
    print()
    print("📱 手机访问: http://服务器IP:8080")
