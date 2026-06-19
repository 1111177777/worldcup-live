"""
世界杯聊天室组件
原生 WebSocket 版本——不依赖任何第三方 BaaS
"""

# ========== 配置（部署聊天服务器后填写）==========
WS_URL = "ws://localhost:8890"       # WebSocket 地址
HTTP_URL = "http://localhost:8891"   # 图片上传地址
# =================================================

def get_chat_html():
    """返回聊天室的完整 HTML/CSS/JS"""

    css = """
    .chat-wrap { margin: 14px 0; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden; background: #fff; }
    .chat-head { background: #111; color: #fff; padding: 10px 14px; font-size: 14px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
    .chat-head .live-dot { display: inline-block; width: 7px; height: 7px; background: #4f4; border-radius: 50%; margin-right: 5px; animation: chat-pulse 2s infinite; }
    .chat-head .live-dot.dead { background: #e44; }
    .chat-head .count { font-size: 12px; color: #4f4; font-weight: 400; }
    @keyframes chat-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .chat-list { height: 300px; overflow-y: auto; padding: 10px 12px; background: #f8f9fa; -webkit-overflow-scrolling: touch; }
    .chat-msg { margin-bottom: 10px; display: flex; gap: 8px; align-items: flex-start; }
    .chat-msg.me { flex-direction: row-reverse; }
    .chat-msg .av { width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: #fff; }
    .chat-msg .bubble { max-width: 72%; }
    .chat-msg .nick { font-size: 10px; color: #999; margin-bottom: 3px; padding: 0 4px; }
    .chat-msg.me .nick { text-align: right; }
    .chat-msg .txt { font-size: 13px; color: #333; background: #fff; padding: 8px 12px; border-radius: 14px; line-height: 1.5; word-break: break-word; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
    .chat-msg.me .txt { background: #111; color: #fff; }
    .chat-msg .img-in-chat { max-width: 180px; max-height: 180px; border-radius: 10px; cursor: pointer; display: block; }
    .chat-msg .time { font-size: 9px; color: #bbb; margin-top: 3px; padding: 0 4px; }
    .chat-msg.me .time { text-align: right; }
    .chat-sys { text-align: center; font-size: 10px; color: #bbb; margin: 8px 0; }
    .chat-bar { display: flex; gap: 6px; padding: 8px 10px; border-top: 1px solid #eee; background: #fff; align-items: center; }
    .chat-bar input[type="text"] { flex: 1; padding: 9px 14px; border: 1px solid #ddd; border-radius: 22px; font-size: 13px; outline: none; background: #f5f5f5; }
    .chat-bar input[type="text"]:focus { border-color: #111; background: #fff; }
    .chat-bar .btn { padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; white-space: nowrap; }
    .chat-bar .btn-send { background: #111; color: #fff; }
    .chat-bar .btn-img { background: #fff; color: #666; border: 1px solid #ddd; padding: 8px 10px; font-size: 16px; }
    .chat-bar .btn-img:active { background: #f0f0f0; }
    .chat-toast { position: fixed; top: 60px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,.75); color: #fff; padding: 8px 20px; border-radius: 20px; font-size: 12px; z-index: 9999; pointer-events: none; opacity: 0; transition: opacity .3s; }
    .chat-toast.show { opacity: 1; }
    .chat-disabled { text-align: center; padding: 40px 20px; color: #bbb; font-size: 12px; }
    """

    js = f"""
(function() {{
    var WS_URL = '{WS_URL}';
    var HTTP_URL = '{HTTP_URL}';
    var MAX_IMG = 5*1024*1024;
    var RECONNECT_DELAY = 3000;

    // Skip if not configured
    if (WS_URL.indexOf('localhost') >= 0) {{
        document.getElementById('chat-wrap').innerHTML = '<div class="chat-head">💬 球友聊天室 <span class="count">等待部署</span></div><div class="chat-disabled">聊天服务器未部署<br><small>部署 chat_server.py 后自动开启</small></div>';
        return;
    }}

    // ====== DOM ======
    var listEl = document.getElementById('chat-list');
    var inputEl = document.getElementById('chat-input');
    var sendBtn = document.getElementById('chat-send');
    var imgBtn = document.getElementById('chat-img-btn');
    var imgFile = document.getElementById('chat-img-file');
    var onlineEl = document.getElementById('chat-online');
    var toastEl = document.getElementById('chat-toast');
    var headDot = document.querySelector('.chat-head .live-dot');

    // ====== 昵称 + 颜色 ======
    var COLORS = ['#e74c3c','#3498db','#2ecc71','#e67e22','#9b59b6','#1abc9c','#f39c12','#e91e63','#00bcd4','#ff5722'];
    function getNick() {{
        var n = localStorage.getItem('wc_nick');
        if (!n) {{
            var emoji = ['⚽','🏆','🎯','🔥','💪','🌟','🎉','🏅','⭐','👑','🎲','🍺'];
            var name = ['球迷','球探','老球迷','队长','射手','门将','中场','后卫','解说','教练','小球迷','看球群众'];
            n = emoji[Math.floor(Math.random()*emoji.length)] + ' ' + name[Math.floor(Math.random()*name.length)] + Math.floor(Math.random()*900+100);
            localStorage.setItem('wc_nick', n);
        }}
        return n;
    }}
    function getColor(s) {{
        var h = 0;
        for (var i=0;i<s.length;i++) h = s.charCodeAt(i) + ((h<<5)-h);
        return COLORS[Math.abs(h) % COLORS.length];
    }}
    var NICKNAME = getNick();
    var MY_COLOR = getColor(NICKNAME);

    // ====== WebSocket ======
    var ws = null;
    var reconnectTimer = null;

    function connect() {{
        if (ws && ws.readyState === WebSocket.OPEN) return;
        try {{
            ws = new WebSocket(WS_URL);
        }} catch(e) {{
            scheduleReconnect();
            return;
        }}

        ws.onopen = function() {{
            // 发送握手
            ws.send(JSON.stringify({{nickname: NICKNAME, color: MY_COLOR}}));
            if (headDot) headDot.classList.remove('dead');
            onlineEl.innerHTML = '<span class="live-dot"></span>连接中...';
        }};

        ws.onmessage = function(e) {{
            try {{
                var msg = JSON.parse(e.data);
            }} catch(err) {{ return; }}

            if (msg.type === 'init') {{
                // 加载历史
                listEl.innerHTML = '';
                if (msg.history && msg.history.length > 0) {{
                    for (var i=0;i<msg.history.length;i++) {{
                        addMsgEl(msg.history[i]);
                    }}
                }} else {{
                    var emp = document.createElement('div');
                    emp.style.cssText = 'text-align:center;padding:50px 20px;color:#ccc;font-size:13px';
                    emp.innerHTML = '<div style="font-size:32px;margin-bottom:8px">💬</div>聊聊今天的比赛吧！';
                    listEl.appendChild(emp);
                }}
                scrollBot();
                onlineEl.innerHTML = '<span class="live-dot"></span>' + (msg.online||0) + '人在线';
            }} else if (msg.type === 'text' || msg.type === 'image') {{
                if (listEl.querySelector('.chat-empty')) listEl.innerHTML = '';
                addMsgEl(msg);
                scrollBot();
                if (document.hidden && msg.nick !== NICKNAME) {{
                    toast('📩 ' + msg.nick + '：' + (msg.text||'[图片]').substr(0,20));
                }}
            }} else if (msg.type === 'join' || msg.type === 'leave') {{
                addSys(msg.nick + (msg.type==='join'?' 加入了聊天室':' 离开了聊天室'));
                onlineEl.innerHTML = '<span class="live-dot"></span>' + (msg.online||'?') + '人在线';
            }}
        }};

        ws.onclose = function() {{
            if (headDot) headDot.classList.add('dead');
            onlineEl.innerHTML = '<span class="live-dot dead"></span>已断开';
            scheduleReconnect();
        }};

        ws.onerror = function() {{
            ws.close();
        }};
    }}

    function scheduleReconnect() {{
        if (reconnectTimer) clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(function() {{
            connect();
        }}, RECONNECT_DELAY);
    }}

    // ====== 消息渲染 ======
    function addMsgEl(msg) {{
        var isMe = msg.nick === NICKNAME;
        var div = document.createElement('div');
        div.className = 'chat-msg' + (isMe ? ' me' : '');

        var av = document.createElement('div');
        av.className = 'av';
        av.style.background = msg.color || '#999';
        av.textContent = (msg.nick||'?')[0];

        var bubble = document.createElement('div');
        bubble.className = 'bubble';

        var nk = document.createElement('div');
        nk.className = 'nick';
        nk.textContent = msg.nick || '?';
        bubble.appendChild(nk);

        if (msg.type === 'image') {{
            var img = document.createElement('img');
            img.className = 'img-in-chat';
            img.src = msg.url;
            img.onclick = function() {{ window.open(msg.url); }};
            bubble.appendChild(img);
        }} else {{
            var t = document.createElement('div');
            t.className = 'txt';
            t.textContent = msg.text || '';
            bubble.appendChild(t);
        }}

        var tm = document.createElement('div');
        tm.className = 'time';
        var d = msg.time ? new Date(msg.time) : new Date();
        tm.textContent = ('0'+d.getHours()).slice(-2) + ':' + ('0'+d.getMinutes()).slice(-2);
        bubble.appendChild(tm);

        div.appendChild(av);
        div.appendChild(bubble);
        listEl.appendChild(div);
    }}

    function addSys(text) {{
        var d = document.createElement('div');
        d.className = 'chat-sys';
        d.textContent = text;
        listEl.appendChild(d);
    }}

    function scrollBot() {{
        listEl.scrollTop = listEl.scrollHeight;
    }}

    function toast(msg) {{
        toastEl.textContent = msg;
        toastEl.classList.add('show');
        setTimeout(function(){{ toastEl.classList.remove('show'); }}, 2000);
    }}

    // ====== 发送 ======
    function sendText() {{
        var text = inputEl.value.trim();
        if (!text) return;
        if (text.length > 500) {{ toast('最多500字'); return; }}
        if (!ws || ws.readyState !== WebSocket.OPEN) {{ toast('连接已断开，正在重连...'); return; }}
        inputEl.value = '';
        ws.send(JSON.stringify({{type:'text', text:text}}));
    }}

    function sendImage(file) {{
        if (!file) return;
        if (file.size > MAX_IMG) {{ toast('图片不能超过5MB'); return; }}
        var allow = ['image/jpeg','image/png','image/gif','image/webp'];
        if (allow.indexOf(file.type) === -1) {{ toast('仅支持 JPG/PNG/GIF/WebP'); return; }}
        if (!ws || ws.readyState !== WebSocket.OPEN) {{ toast('连接已断开，正在重连...'); return; }}

        addSys('📤 正在上传图片...');
        var fd = new FormData();
        fd.append('file', file);

        fetch(HTTP_URL + '/upload', {{ method:'POST', body:fd }})
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            var imgUrl = HTTP_URL + data.url;
            ws.send(JSON.stringify({{type:'image', url:imgUrl}}));
        }})
        .catch(function(e) {{
            toast('上传失败：' + e.message);
        }});
    }}

    // ====== 事件绑定 ======
    sendBtn.addEventListener('click', sendText);
    inputEl.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter' || e.keyCode === 13) {{ e.preventDefault(); sendText(); }}
    }});
    imgBtn.addEventListener('click', function() {{ imgFile.click(); }});
    imgFile.addEventListener('change', function() {{
        if (this.files && this.files[0]) {{ sendImage(this.files[0]); this.value = ''; }}
    }});

    // ====== 清理 ======
    window.addEventListener('beforeunload', function() {{
        if (reconnectTimer) clearTimeout(reconnectTimer);
        if (ws) {{ ws.onclose = null; ws.close(); }}
    }});

    // ====== 启动 ======
    connect();
}})();
"""

    html = f"""
    <style>{css}</style>

    <div class="chat-wrap" id="chat-wrap">
        <div class="chat-head">
            💬 球友聊天室
            <span class="count" id="chat-online"><span class="live-dot"></span>连接中...</span>
        </div>
        <div class="chat-list" id="chat-list">
            <div style="text-align:center;padding:50px;color:#ccc;font-size:13px">连接聊天室中...</div>
        </div>
        <div class="chat-bar">
            <input type="text" id="chat-input" placeholder="聊聊比赛..." maxlength="500" autocomplete="off">
            <button class="btn btn-img" id="chat-img-btn" title="发送图片">📎</button>
            <input type="file" id="chat-img-file" accept="image/jpeg,image/png,image/gif,image/webp" style="display:none">
            <button class="btn btn-send" id="chat-send-btn">发送</button>
        </div>
    </div>
    <div class="chat-toast" id="chat-toast"></div>

    <script>{js}</script>
    """

    return html
