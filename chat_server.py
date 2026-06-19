"""
世界杯聊天服务器 —— 自建 WebSocket + HTTP
启动: python chat_server.py
端口: 8890 (WebSocket) + 8891 (HTTP图片)
"""
import asyncio, json, os, time, threading, hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import websockets

# ====== 配置 ======
WS_HOST = "0.0.0.0"
WS_PORT = 8890
HTTP_PORT = 8891
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_uploads")
MAX_IMG = 5 * 1024 * 1024
MAX_TEXT = 500
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")
# ==================

os.makedirs(UPLOAD_DIR, exist_ok=True)

# 在线客户端
clients = {}       # {websocket: {"nick": str, "color": str}}
history = []       # [{type, nick, text/url, time, color}]

def load_history():
    global history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)[-100:]
    except: pass

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[-200:], f, ensure_ascii=False)
    except: pass

def online_count():
    return len(clients)

def clean_clients():
    dead = []
    for ws in list(clients):
        try:
            # websockets 16.x 没有 .closed 属性，用 state 判断
            from websockets.protocol import State
            if ws.state == State.CLOSED:
                dead.append(ws)
        except:
            dead.append(ws)
    for ws in dead:
        if ws in clients: del clients[ws]

async def broadcast(data):
    clean_clients()
    msg = json.dumps(data, ensure_ascii=False)
    dead = []
    for ws in list(clients):
        try:
            await ws.send(msg)
        except:
            dead.append(ws)
    for ws in dead:
        if ws in clients: del clients[ws]

async def handle_ws(websocket):
    # 等待客户端握手（含昵称）
    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=10)
        hello = json.loads(raw)
        nick = str(hello.get('nickname', '球迷'))[:16]
        color = str(hello.get('color', '#111'))[:7]
    except:
        nick, color = '球迷', '#111'

    clients[websocket] = {"nick": nick, "color": color}
    clean_clients()

    # 发历史 + 在线人数
    await websocket.send(json.dumps({
        "type": "init", "history": history[-50:], "online": online_count()
    }, ensure_ascii=False))

    # 广播加入
    await broadcast({"type": "join", "nick": nick, "online": online_count(), "time": time.time()*1000})

    try:
        async for raw in websocket:
            try: msg = json.loads(raw)
            except: continue
            t = msg.get("type", "text")
            now = time.time() * 1000
            if t == "text":
                txt = str(msg.get("text", ""))[:MAX_TEXT].strip()
                if not txt: continue
                entry = {"type": "text", "nick": nick, "text": txt, "color": color, "time": now}
                history.append(entry)
                if len(history) > 200: history.pop(0)
                save_history()
                await broadcast(entry)
            elif t == "image":
                url = str(msg.get("url", ""))[:500]
                if not url: continue
                entry = {"type": "image", "nick": nick, "url": url, "color": color, "time": now}
                history.append(entry)
                if len(history) > 200: history.pop(0)
                save_history()
                await broadcast(entry)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket in clients: del clients[websocket]
        clean_clients()
        await broadcast({"type": "leave", "nick": nick, "online": online_count(), "time": time.time()*1000})

# ====== HTTP 图片上传服务 ======
class ImgHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/upload":
            try:
                length = int(self.headers.get("content-length", 0))
                if length > MAX_IMG:
                    self.send_error(413, "图片过大")
                    return
                data = self.rfile.read(length)
                # 简单 multipart 解析
                content_type = self.headers.get("content-type", "")
                if "multipart" in content_type:
                    boundary = content_type.split("boundary=")[1].encode()
                    parts = data.split(b"--" + boundary)
                    for part in parts:
                        if b"filename=" in part:
                            # 找到文件内容
                            header_end = part.find(b"\r\n\r\n")
                            file_data = part[header_end+4:]
                            file_data = file_data.rsplit(b"\r\n--", 1)[0] if b"\r\n--" in file_data else file_data.rstrip(b"\r\n")
                            ext = ".jpg"
                            for ext_try in [b".png", b".gif", b".webp", b".jpg", b".jpeg"]:
                                if ext_try in part[:header_end].lower(): ext = ext_try.decode(); break
                            fname = hashlib.md5(file_data[:100] + str(time.time()).encode()).hexdigest()[:12] + ext
                            fpath = os.path.join(UPLOAD_DIR, fname)
                            with open(fpath, "wb") as f: f.write(file_data)
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.send_header("Access-Control-Allow-Origin", "*")
                            self.end_headers()
                            self.wfile.write(json.dumps({"url": "/img/" + fname}).encode())
                            return
                # 非 multipart 直接存
                fname = hashlib.md5(data[:100]+str(time.time()).encode()).hexdigest()[:12] + ".jpg"
                with open(os.path.join(UPLOAD_DIR, fname), "wb") as f: f.write(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"url": "/img/" + fname}).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path.startswith("/img/"):
            fname = os.path.basename(self.path)
            fpath = os.path.join(UPLOAD_DIR, fname)
            if os.path.exists(fpath):
                ext = os.path.splitext(fname)[1].lower()
                ct = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","gif":"image/gif","webp":"image/webp"}.get(ext, "image/jpeg")
                with open(fpath, "rb") as f: data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Content-Length", len(data))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

def run_http():
    srv = HTTPServer((WS_HOST, HTTP_PORT), ImgHandler)
    print(f"📁 图片服务: http://{WS_HOST}:{HTTP_PORT}")
    srv.serve_forever()

async def main():
    load_history()
    print(f"💬 聊天 WebSocket: ws://{WS_HOST}:{WS_PORT}")
    threading.Thread(target=run_http, daemon=True).start()
    async with websockets.serve(handle_ws, WS_HOST, WS_PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
