"""
世界杯实时数据引擎 v2
读取 schedule.json → ELO预测 → 生成 live.html
每5分钟运行：python live_data.py
"""
import json, os, math
from datetime import datetime

import hashlib

DIR = os.path.dirname(__file__)
SCHEDULE_FILE = os.path.join(DIR, "schedule.json")
OUTPUT = os.path.join(DIR, "live.html")
PASSWORD = "wc2026"  # 访问密码，改这里即改密码
PASS_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()

ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1850,"意大利":1840,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1750,"韩国":1740,"伊朗":1730,"澳大利亚":1710,"埃及":1720,"尼日利亚":1710,"科特迪瓦":1700,"喀麦隆":1690,"加纳":1680,"突尼斯":1670,"阿尔及利亚":1660,"南非":1640,"加拿大":1730,"哥斯达黎加":1680,"巴拿马":1640,"牙买加":1630,"沙特阿拉伯":1670,"卡塔尔":1650,"伊拉克":1620,"阿联酋":1610,"新西兰":1600,"巴拉圭":1720,"厄瓜多尔":1740,"智利":1760,"秘鲁":1730,"委内瑞拉":1680,"玻利维亚":1620,"波黑":1690,"塞尔维亚":1750,"丹麦":1800,"瑞典":1790,"挪威":1780,"波兰":1760,"乌克兰":1740,"土耳其":1750,"比利时":1830,"威尔士":1700,"苏格兰":1690,"捷克":1720,"罗马尼亚":1680,"斯洛伐克":1670,"匈牙利":1700,"希腊":1680,"佛得角":1580,"库拉索":1560,"约旦":1590,"乌兹别克斯坦":1610,"海地":1550,"瑞士":1830,"摩洛哥":1790,"刚果民主共和国":1650,"奥地利":1760,"古巴":1540,"苏里南":1520}
FLAGS = dict(阿根廷="🇦🇷",法国="🇫🇷",巴西="🇧🇷",英格兰="🏴",西班牙="🇪🇸",葡萄牙="🇵🇹",德国="🇩🇪",荷兰="🇳🇱",意大利="🇮🇹",乌拉圭="🇺🇾",克罗地亚="🇭🇷",哥伦比亚="🇨🇴",摩洛哥="🇲🇦",美国="🇺🇸",墨西哥="🇲🇽",塞内加尔="🇸🇳",日本="🇯🇵",韩国="🇰🇷",伊朗="🇮🇷",澳大利亚="🇦🇺",埃及="🇪🇬",尼日利亚="🇳🇬",科特迪瓦="🇨🇮",喀麦隆="🇨🇲",加纳="🇬🇭",突尼斯="🇹🇳",南非="🇿🇦",加拿大="🇨🇦",巴拉圭="🇵🇾",厄瓜多尔="🇪🇨",智利="🇨🇱",秘鲁="🇵🇪",波黑="🇧🇦",塞尔维亚="🇷🇸",丹麦="🇩🇰",瑞典="🇸🇪",挪威="🇳🇴",波兰="🇵🇱",乌克兰="🇺🇦",土耳其="🇹🇷",比利时="🇧🇪",捷克="🇨🇿",卡塔尔="🇶🇦",新西兰="🇳🇿",海地="🇭🇹",苏格兰="🏴",瑞士="🇨🇭",奥地利="🇦🇹",约旦="🇯🇴",伊拉克="🇮🇶",库拉索="🇨🇼",巴拿马="🇵🇦",哥斯达黎加="🇨🇷",牙买加="🇯🇲",沙特阿拉伯="🇸🇦",阿联酋="🇦🇪",委内瑞拉="🇻🇪",玻利维亚="🇧🇴",威尔士="🏴",罗马尼亚="🇷🇴",斯洛伐克="🇸🇰",匈牙利="🇭🇺",希腊="🇬🇷",佛得角="🇨🇻",乌兹别克斯坦="🇺🇿",刚果民主共和国="🇨🇩",阿尔及利亚="🇩🇿")

def poisson(l,k): return math.exp(-l)*l**k/math.factorial(k)

# 球队风格系数（攻击力/防守力加成，基准1.0）
STYLE = {
    "德国":(1.3,1.0),"巴西":(1.3,1.0),"法国":(1.25,1.0),"阿根廷":(1.2,1.0),
    "英格兰":(1.15,1.0),"西班牙":(1.1,1.0),"荷兰":(1.15,0.95),"葡萄牙":(1.2,0.95),
    "比利时":(1.1,0.9),"挪威":(1.25,0.8),"库拉索":(0.5,0.3),"海地":(0.6,0.4),
    "卡塔尔":(0.6,0.5),"佛得角":(0.5,0.4),"新西兰":(0.7,0.6),
    "巴拿马":(0.7,0.5),"约旦":(0.65,0.6),"伊拉克":(0.7,0.6),
    "乌兹别克斯坦":(0.65,0.55),"刚果民主共和国":(0.8,0.6),
    "伊朗":(0.7,1.15),"巴拉圭":(0.75,1.1),"瑞士":(0.85,1.1),
    "乌拉圭":(1.0,1.15),"克罗地亚":(0.9,1.1),"摩洛哥":(0.8,1.15),
    # 均衡型
    "墨西哥":(1.1,0.9),"美国":(1.1,0.9),"韩国":(1.05,0.85),
    "日本":(1.05,0.8),"加拿大":(1.0,0.85),"澳大利亚":(0.9,0.95),
    "塞内加尔":(1.05,0.9),"埃及":(0.95,0.9),"科特迪瓦":(1.0,0.85),
    "加纳":(0.9,0.85),"喀麦隆":(0.85,0.85),"尼日利亚":(0.95,0.85),
    "突尼斯":(0.75,0.9),"阿尔及利亚":(0.85,0.85),"南非":(0.8,0.8),
    "丹麦":(1.05,1.0),"瑞典":(1.0,1.0),"波兰":(1.0,0.9),
    "乌克兰":(0.9,0.85),"土耳其":(1.05,0.85),"奥地利":(1.0,0.9),
    "塞尔维亚":(1.0,0.85),"威尔士":(0.85,0.9),"苏格兰":(0.9,0.85),
    "捷克":(0.95,0.9),"罗马尼亚":(0.8,0.85),"斯洛伐克":(0.75,0.85),
    "匈牙利":(0.9,0.8),"希腊":(0.7,0.95),"哥伦比亚":(1.1,0.85),
    "智利":(0.95,0.9),"秘鲁":(0.85,0.85),"厄瓜多尔":(0.9,0.85),
    "委内瑞拉":(0.75,0.8),"玻利维亚":(0.7,0.7),
    "哥斯达黎加":(0.75,0.8),"牙买加":(0.8,0.7),
    "沙特阿拉伯":(0.75,0.7),"阿联酋":(0.7,0.7),
    "意大利":(1.05,1.05),
}

def predict(h,a):
    he,ae=ELO.get(h,1700),ELO.get(a,1700)
    hs=STYLE.get(h,(1.0,1.0)); as_=STYLE.get(a,(1.0,1.0))
    d=he-ae+50; gd=d/100*0.4  # 加大ELO影响
    xh=max(0.3, (1.6+gd*0.7)*hs[0]/max(as_[1],0.5))
    xa=max(0.3, (1.2-gd*0.4)*as_[0]/max(hs[1],0.5))
    w=dr=lo=0; sc={}
    for i in range(9):
        for j in range(9):
            p=poisson(xh,i)*poisson(xa,j); sc[f"{i}:{j}"]=p
            if i>j:w+=p
            elif i==j:dr+=p
            else:lo+=p
    top=sorted(sc.items(),key=lambda x:x[1],reverse=True)[:5]
    gl={}
    for i in range(10):
        for j in range(10):
            p=poisson(xh,i)*poisson(xa,j); t=i+j; gl[t]=gl.get(t,0)+p
    return {"win":round(w*100,1),"draw":round(dr*100,1),"loss":round(lo*100,1),"xh":round(xh,2),"xa":round(xa,2),"top":[(s,round(p*100,1))for s,p in top],"gl":{str(k):round(v*100,1)for k,v in sorted(gl.items())[:8]},"he":he,"ae":ae}

def auto_tags(m, p):
    """自动生成伤停/风险/价值标签，无需手动填"""
    h,a = m['home'], m['away']
    he,ae = p['he'], p['ae']
    diff = he-ae
    injury = m.get('injury','')  # 手动填的优先
    risk = list(m.get('risk',[]))
    value = m.get('value','')

    # 自动风险标签
    v = m.get('venue','')
    if '高原' in v or '墨西哥城' in v or '阿兹台克' in v:
        if '高原' not in ' '.join(risk): risk.append('高原2200m')
    if abs(diff)>200:
        if '实力悬殊' not in ' '.join(risk): risk.append('实力悬殊')
    elif abs(diff)<30:
        if '实力接近' not in ' '.join(risk): risk.append('实力接近')
    if m.get('date','') in ['6/24','6/25','6/26','6/27']:
        if '小组末轮' not in ' '.join(risk): risk.append('小组末轮')

    # 自动价值标签
    if not value and m.get('odds_home'):
        oh = float(m.get('odds_home',0) or 0)
        if oh>0:
            fair = round(1/max(p['win']/100,0.01),1)
            gap = oh-fair
            if gap>0.5: value = f'主胜市场赔率偏高，模型认为被低估'
            elif gap<-0.3: value = f'主胜市场赔率偏低，热度可能过高'

    # 爆冷概率
    upset_prob = 0
    upset_why = ''
    if p['win'] > 50:  # 主队热门
        upset_prob = p['loss']
        fav, udog = h, a
    elif p['loss'] > 50:  # 客队热门
        upset_prob = p['win']
        fav, udog = a, h
    else:
        upset_prob = 0
        fav, udog = '', ''

    if upset_prob > 25:
        upset_why = f'{udog}有{upset_prob:.0f}%概率爆冷——不低。'
        if upset_prob > 35:
            upset_why += '双方实力差距不大，任何结果都可能。'
        if '高原' in ' '.join(risk):
            upset_why += '高原因素可能放大不确定性。'
        if abs(diff) < 60:
            upset_why += 'ELO差距小，冷门土壤肥沃。'
    elif upset_prob > 18:
        upset_why = f'{udog}爆冷概率{upset_prob:.0f}%，偏低但非零。{fav}发挥失常或{udog}超常可能翻盘。'
    elif upset_prob > 0:
        upset_why = f'{fav}优势明显，{udog}爆冷概率仅{upset_prob:.0f}%。除非重大意外（红牌/伤病），冷门难现。'
    else:
        upset_why = '双方均势，没有明确的冷门概念。'

    return injury, risk, value, round(upset_prob, 1), upset_why

def explain(p, m, h, a, d):
    ad=abs(d)
    if d>100:ew=f"{h} ELO领先{ad}分，明显优势。"
    elif d>40:ew=f"{h} ELO略高{ad}分，主场加权后有优势。"
    else:ew=f"两队仅差{ad}分，实力非常接近。"
    if p['win']>50:sw=f"倾向{h}获胜——主场+ELO优势转化为{p['win']}%胜率。"
    elif p['loss']>50:sw=f"倾向{a}——ELO差距在下半场可能体现。"
    else:sw="三者接近——平局往往被市场低估。"
    # 多样化总进球分析
    p01=p['gl'].get('0',0)+p['gl'].get('1',0)
    p23=p['gl'].get('2',0)+p['gl'].get('3',0)
    p45=p['gl'].get('4',0)+p['gl'].get('5',0)
    p6p=sum(p['gl'].get(str(g),0) for g in range(6,13))
    if p['xh']>2.0: gw=f"进攻火力强劲，期望进球{p['xh']:.1f}球，大比分概率高——4球及以上占{p45+p6p:.0f}%。"
    elif p['xh']>1.5: gw=f"进球集中在2-3球（{p23:.0f}%），典型世界杯节奏。但也有{p45:.0f}%概率打出4球以上。"
    elif p['xh']<1.0: gw=f"进攻乏力，{p01:.0f}%概率低于2球，小球倾向明显。"
    else: gw=f"进球分布分散——2-3球占{p23:.0f}%，但{p45:.0f}%概率4球以上，{p01:.0f}%概率低于2球。"
    if p['win']>50:rec=f"倾向：{h}获胜"
    elif p['loss']>50:rec=f"倾向：{a}获胜"
    else:rec="建议观望，平局概率偏高"

    # 伤停+风险+价值标签
    tags_html = ''
    if m.get('injury'):
        tags_html += '<div class="tag-row"><span class="tag tag-injury">🚑 ' + m['injury'] + '</span></div>'
    if m.get('risk') and len(m['risk'])>0:
        rt = ''.join('<span class="tag tag-risk">⚠️ ' + r + '</span>' for r in m['risk'])
        tags_html += '<div class="tag-row">' + rt + '</div>'
    if m.get('value'):
        tags_html += '<div class="tag-row"><span class="tag tag-value">💰 ' + m['value'] + '</span></div>'

    # 爆冷 - 从 auto_tags 获取
    up = m.get('_upset_prob', 0)
    uw = m.get('_upset_why', '')
    upset_html = ''
    if up > 0 and uw:
        upset_color = '#e44' if up > 25 else ('#f80' if up > 15 else '#999')
        upset_html = f'<div class="tag-row"><span class="tag" style="background:#fff5f5;color:{upset_color};border:1px solid #fcc;font-size:11px;padding:3px 8px;">🎲 爆冷概率 {up}% · {uw}</span></div>'

    return ew, sw, gw, rec, tags_html + upset_html

def gen():
    with open(SCHEDULE_FILE,encoding='utf-8') as f: matches=json.load(f)
    now=datetime.now().strftime("%m/%d %H:%M:%S")
    cards,results="",""
    for m in matches:
        p=predict(m['home'],m['away'])
        # 自动补全伤停/风险/价值/爆冷
        ai,ar,av,up,uw=auto_tags(m,p)
        if not m.get('injury'): m['injury']=ai
        if not m.get('risk') or len(m.get('risk',[]))==0: m['risk']=ar
        if not m.get('value'): m['value']=av
        m['_upset_prob']=up
        m['_upset_why']=uw
        fh,fa=FLAGS.get(m['home'],''),FLAGS.get(m['away'],'')
        ew,sw,gw,rec,tags=explain(p,m,m['home'],m['away'],p['he']-p['ae']+50)
        d=f"{m['date']} {m['time']}".strip()

        # 实时结果
        live=""
        if m.get('result'):
            live=f'<div class="live">⚡ {m["result"]}</div>'
            results+=f'<div class="res"><span>{fh} {m["home"]} {m["result"]} {m["away"]} {fa}</span><span class="d">{d}</span></div>'

        # 赔率
        on=""
        if m.get('odds_home'):
            o=float(m['odds_home']);fair=round(1/max(p['win']/100,0.01),1)
            on=f"市场赔率{o} · 模型公允{fair}"

        cards+=f"""
    <div class="match">
      <div class="mh"><span class="g">G{m['group']}</span><span class="t">{fh} {m['home']} vs {m['away']} {fa}</span><span class="d">{d}</span></div>
      <div class="v">{m['venue']}</div>{live}
      <div class="int">📰 {m['intel']}</div>
      {tags}
      <div class="s"><div class="st">胜负 · {ew}</div>
        <div class="b"><span>主</span><div class="t"><i style="width:{p['win']}%"></i></div><span class="n">{p['win']}%</span></div>
        <div class="b"><span>平</span><div class="t"><i style="width:{p['draw']}%;background:#888"></i></div><span class="n">{p['draw']}%</span></div>
        <div class="b"><span>客</span><div class="t"><i style="width:{p['loss']}%;background:#ccc"></i></div><span class="n">{p['loss']}%</span></div>
        <div class="why">{sw} · {on}</div>
      </div>
      <div class="s"><div class="st">比分 TOP5</div><div class="cs">{' '.join(f'<span class="c"><b>{s}</b> {pr}%</span>'for s,pr in p['top'])}</div></div>
      <div class="s"><div class="st">总进球 · {gw}</div><div class="cs">{' '.join(f'<span class="c">{g}球 {pr}%</span>'for g,pr in list(p['gl'].items())[:6])}</div></div>
      <div class="s" style="border-left:3px solid #111;padding-left:12px;background:#fafafa"><div class="st">建议</div><div style="font-weight:600;font-size:15px">{rec}</div></div>
    </div>"""

    html=f"""<!DOCTYPE html><html lang="zh-CN"><head>
<script>
// 访问验证
const HASH='{PASS_HASH}';
async function sha256(m){{ const e=new TextEncoder();const d=await crypto.subtle.digest('SHA-256',e.encode(m));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join(''); }}
async function check(){{ const p=document.getElementById('pw').value; const h=await sha256(p); if(h===HASH){{ localStorage.setItem('wc_auth','1'); document.getElementById('gate').style.display='none'; document.getElementById('main').style.display='block'; }}else{{ document.getElementById('err').style.display='block'; }} }}
function init(){{ if(localStorage.getItem('wc_auth')==='1'){{ document.getElementById('gate').style.display='none';document.getElementById('main').style.display='block'; }} }}
</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>世界杯实时分析</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#fff;padding:12px;max-width:500px;margin:0 auto;color:#333}}
h1{{font-size:18px;font-weight:600;text-align:center;margin:8px 0}}
.sub{{text-align:center;font-size:11px;color:#999}}
.upd{{text-align:center;font-size:10px;color:#ccc;margin:4px 0 12px}}
.results{{background:#fafafa;padding:10px;margin-bottom:12px}}
.results .rt{{font-size:11px;color:#999;margin-bottom:6px;font-weight:600}}
.res{{font-size:12px;padding:3px 0;display:flex;justify-content:space-between}}
.res .d{{color:#999}}
.match{{border-bottom:1px solid #eee;padding:12px 0}}
.match:last-child{{border-bottom:none}}
.mh{{display:flex;align-items:center;gap:6px}}
.g{{font-size:10px;background:#111;color:#fff;padding:1px 6px;font-weight:600}}
.t{{font-weight:600;font-size:14px;flex:1}}
.d{{font-size:11px;color:#999}}
.v{{font-size:11px;color:#ccc;margin:2px 0 6px}}
.live{{background:#e44;color:#fff;padding:4px 10px;font-size:13px;font-weight:600;display:inline-block;margin:6px 0}}
.int{{font-size:12px;color:#666;line-height:1.5;margin:6px 0;padding:8px;background:#fafafa}}
.s{{margin:10px 0}}
.st{{font-size:11px;color:#999;font-weight:600;margin-bottom:4px}}
.why{{font-size:11px;color:#999;margin-top:4px;line-height:1.5}}
.b{{display:flex;align-items:center;gap:6px;margin:2px 0}}
.b span:first-child{{width:20px;font-size:11px;color:#666}}
.b .t{{flex:1;height:5px;background:#eee}}
.b .t i{{display:block;height:5px;background:#111}}
.b .n{{width:40px;font-size:12px;text-align:right;font-weight:600}}
.cs{{display:flex;flex-wrap:wrap;gap:3px}}
.c{{padding:2px 7px;border:1px solid #e0e0e0;font-size:11px}}
.c b{{color:#111}}
.tag-row{{margin:4px 0;display:flex;flex-wrap:wrap;gap:4px}}
.tag{{font-size:11px;padding:3px 8px;border-radius:2px;line-height:1.4}}
.tag-injury{{background:#fff0f0;color:#c44;border:1px solid #fcc}}
.tag-risk{{background:#fff8e0;color:#b80;border:1px solid #fe8}}
.tag-value{{background:#f0f8ff;color:#36c;border:1px solid #bdf}}
.rf{{text-align:center;font-size:11px;color:#999;margin:10px 0}}
.ft{{text-align:center;color:#ccc;font-size:10px;margin:20px 0;line-height:1.6}}
.nav{{display:flex;gap:4px;flex-wrap:wrap;margin:0 0 12px;justify-content:center}}
.nav a{{font-size:11px;padding:3px 8px;border:1px solid #ddd;text-decoration:none;color:#666}}
.nav a.on{{background:#111;color:#fff;border-color:#111}}
.gate{{position:fixed;top:0;left:0;width:100%;height:100%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}}
.gate input{{width:200px;padding:12px;border:1px solid #ccc;font-size:16px;text-align:center;margin:12px 0}}
.gate button{{padding:12px 40px;background:#111;color:#fff;border:none;font-size:15px;font-weight:600}}
.err{{color:#e44;font-size:13px;display:none}}
</style></head><body onload="init()">
<div id="gate" class="gate">
  <div style="font-size:16px;font-weight:600;margin-bottom:4px">🔒 世界杯实时分析</div>
  <div style="font-size:12px;color:#999;margin-bottom:8px">请输入访问密码</div>
  <input id="pw" type="password" placeholder="密码" onkeydown="if(event.key==='Enter')check()">
  <button onclick="check()">验证</button>
  <div id="err" class="err">密码错误</div>
  <div style="font-size:10px;color:#ccc;margin-top:16px">购买后获取密码 · 一机一码永久有效</div>
</div>
<div id="main" style="display:none">
<h1>世界杯 · 实时分析</h1>
<div style="padding:0 0 10px"><input id="search" type="text" placeholder="🔍 搜索球队..." oninput="filter()" style="width:100%;padding:10px;border:1px solid #ddd;font-size:14px"></div>
<div class="sub">ELO模型 + 泊松分布 · 赔率对比</div>
<div class="upd">更新 {now} · 每5分钟自动刷新</div>
<div class="rf">⏳ <span id="cd">60</span>秒后刷新</div>
{"<div class=\"results\"><div class=\"rt\">⚡ 最新赛果</div>"+results+"</div>" if results else ""}
{cards}
<div class="ft">ELO评分基于FIFA排名和历史战绩<br>泊松分布推演比分概率 · 赔率来源于公开市场<br>所有数据仅供赛事分析参考</div>
<script>
let t=60;setInterval(()=>{{t--;document.getElementById('cd').textContent=t;if(t<=0)location.reload()}},1000);
function filter(){{var q=document.getElementById('search').value.toLowerCase();var ms=document.querySelectorAll('.match');ms.forEach(function(m){{var t=m.querySelector('.t').textContent.toLowerCase();m.style.display=t.indexOf(q)>=0?'':'none'}});}}
</script>
</div>
</body></html>"""

    with open(OUTPUT,'w',encoding='utf-8') as f:f.write(html)
    print(f"✅ {len(matches)}场比赛已生成")
    print(f"   手机: http://172.20.10.2:8899/live.html")

if __name__=="__main__":gen()
