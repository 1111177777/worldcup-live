"""
世界杯淘汰赛分析引擎
32强对阵 + 每场胜平负/总进球/比分 + 串关推荐
"""

import json, os, random, math
from collections import defaultdict

DIR = os.path.dirname(__file__)

ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"埃及":1720,"比利时":1830,"瑞典":1790,"挪威":1780,"瑞士":1830,"奥地利":1760,"科特迪瓦":1700,"南非":1640,"加拿大":1730,"波黑":1690,"阿尔及利亚":1660,"厄瓜多尔":1740,"加纳":1680,"澳大利亚":1710,"刚果民主共和国":1650}
FLAGS = {"阿根廷":"🇦🇷","法国":"🇫🇷","巴西":"🇧🇷","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","西班牙":"🇪🇸","葡萄牙":"🇵🇹","德国":"🇩🇪","荷兰":"🇳🇱","乌拉圭":"🇺🇾","克罗地亚":"🇭🇷","哥伦比亚":"🇨🇴","摩洛哥":"🇲🇦","美国":"🇺🇸","墨西哥":"🇲🇽","塞内加尔":"🇸🇳","日本":"🇯🇵","韩国":"🇰🇷","埃及":"🇪🇬","比利时":"🇧🇪","瑞典":"🇸🇪","挪威":"🇳🇴","瑞士":"🇨🇭","奥地利":"🇦🇹","科特迪瓦":"🇨🇮","南非":"🇿🇦","加拿大":"🇨🇦","波黑":"🇧🇦","阿尔及利亚":"🇩🇿","厄瓜多尔":"🇪🇨","加纳":"🇬🇭","澳大利亚":"🇦🇺","刚果民主共和国":"🇨🇩"}

# 32强对阵
def get_bracket():
    W = {'A':'墨西哥','B':'瑞士','C':'巴西','D':'美国','E':'德国','F':'荷兰','G':'埃及','H':'西班牙','I':'法国','J':'阿根廷','K':'哥伦比亚','L':'英格兰'}
    R = {'A':'南非','B':'加拿大','C':'摩洛哥','D':'澳大利亚','E':'科特迪瓦','F':'日本','G':'比利时','H':'乌拉圭','I':'挪威','J':'奥地利','K':'葡萄牙','L':'克罗地亚'}
    T = ['刚果民主共和国','瑞典','波黑','阿尔及利亚','塞内加尔','厄瓜多尔','加纳','韩国']
    return [
        (73, R['A'], R['B'], 'A2 vs B2'), (74, W['E'], T[0], 'E1 vs 3rd'),
        (75, W['F'], R['C'], 'F1 vs C2'), (76, W['C'], R['F'], 'C1 vs F2'),
        (77, W['I'], T[1], 'I1 vs 3rd'), (78, R['E'], R['I'], 'E2 vs I2'),
        (79, W['A'], T[2], 'A1 vs 3rd'), (80, W['L'], T[3], 'L1 vs 3rd'),
        (81, W['D'], T[4], 'D1 vs 3rd'), (82, W['G'], T[5], 'G1 vs 3rd'),
        (83, R['K'], R['L'], 'K2 vs L2'), (84, W['H'], R['J'], 'H1 vs J2'),
        (85, W['B'], T[6], 'B1 vs 3rd'), (86, W['J'], R['H'], 'J1 vs H2'),
        (87, W['K'], T[7], 'K1 vs 3rd'), (88, R['D'], R['G'], 'D2 vs G2'),
    ]

def win_prob(e1, e2):
    return 1/(1+10**(-(e1-e2)/400))

def poisson(l, k):
    return math.exp(-l)*l**k/math.factorial(k) if k>=0 else 0

def predict_match(t1, t2):
    """预测单场：胜平负 + 总进球 + 比分 Top3"""
    e1, e2 = ELO.get(t1, 1600), ELO.get(t2, 1600)
    h_adv = 30  # 中立场微调
    xh = max(0.5, 1.4 + (e1-e2+h_adv)/400*0.3)
    xa = max(0.5, 1.1 - (e1-e2+h_adv)/400*0.3)

    # 胜平负概率
    w = dr = lo = 0; sc = {}
    for i in range(8):
        for j in range(8):
            p = poisson(xh,i)*poisson(xa,j); sc[f"{i}:{j}"] = p
            if i>j: w+=p*0.85
            elif i==j: dr+=p*1.3
            else: lo+=p*0.85
    total = w+dr+lo; w,dr,lo = w/total*100, dr/total*100, lo/total*100

    # 比分Top3
    top = sorted(sc.items(), key=lambda x:-x[1])[:3]

    # 总进球分布
    gl = defaultdict(float)
    for i in range(8):
        for j in range(8):
            gl[i+j] += poisson(xh,i)*poisson(xa,j)
    goals_top = sorted(gl.items(), key=lambda x:-x[1])[:5]

    # 淘汰赛特殊：加时/点球概率
    et_prob = dr/100 * 0.35  # 平局中35%走加时

    return {
        'win': round(w,1), 'draw': round(dr,1), 'loss': round(lo,1),
        'xh': round(xh,2), 'xa': round(xa,2), 'total_goals': round(xh+xa,1),
        'top_scores': [(s, round(p*100,1)) for s,p in top],
        'goals_dist': [(k, round(v*100,1)) for k,v in goals_top],
        'et_prob': round(et_prob*100, 1),
    }

def gen_score_pick(t1, t2):
    """为一场比赛推3个最可能比分"""
    e1, e2 = ELO.get(t1,1600), ELO.get(t2,1600)
    diff = e1-e2
    if diff >= 150: return "2:0 / 2:1 / 3:1", 7.5, "强弱"
    elif diff <= -150: return "0:2 / 1:2 / 1:3", 7.5, "强弱"
    elif diff >= 50: return "2:1 / 1:1 / 1:0", 7.0, "中距"
    elif diff <= -50: return "1:2 / 1:1 / 0:1", 7.0, "中距"
    else: return "1:1 / 0:0 / 1:0", 6.0, "均势"

def gen_combos(matches):
    """生成淘汰赛串关推荐"""
    combos = []
    # 取Top matches by Elo clarity
    sorted_m = sorted(matches, key=lambda m: -abs(ELO.get(m[1],1600)-ELO.get(m[2],1600)))

    # 2串1：用Elo最清晰的2场
    for i in range(min(4, len(sorted_m)-1)):
        a, b = sorted_m[i], sorted_m[i+1]
        e1a, e2a = ELO.get(a[1],1600), ELO.get(a[2],1600)
        e1b, e2b = ELO.get(b[1],1600), ELO.get(b[2],1600)
        fav_a = a[1] if e1a>e2a else a[2]
        fav_b = b[1] if e1b>e2b else b[2]
        od = round(1.4*1.5, 2)
        combos.append({'id':f'K2_{i}','name':f'2串1·#{a[0]}×#{b[0]}','level':'稳健','stars':3,
            'legs':[{'match':f'{a[1]} vs {a[2]}','pick':f'「胜」{fav_a}','odds':1.4},
                {'match':f'{b[1]} vs {b[2]}','pick':f'「胜」{fav_b}','odds':1.5}],
            'rate':'42-55%','odds':od,'cat':'2串1','note':'淘汰赛深盘场次组合'})

    # 3串1
    if len(sorted_m) >= 3:
        a,b,c = sorted_m[0], sorted_m[1], sorted_m[2]
        favs = []
        od = 1.0
        for m in [a,b,c]:
            e1,e2=ELO.get(m[1],1600),ELO.get(m[2],1600)
            favs.append(m[1] if e1>e2 else m[2]); od*=1.35
        od=round(od,2)
        combos.append({'id':'K3','name':'3串1·淘汰赛锚定','level':'稳健','stars':3,
            'legs':[{'match':f'{x[1]} vs {x[2]}','pick':'「胜」方向','odds':1.35} for x in [a,b,c]],
            'rate':'25-38%','odds':od,'cat':'3串1','note':'三场淘汰赛深盘组合'})

    # 3串2 容错
    for ci in range(2):
        picks = random.sample(sorted_m[:6], 3)
        legs = []
        for m in picks:
            e1,e2=ELO.get(m[1],1600),ELO.get(m[2],1600)
            legs.append({'match':f'{m[1]} vs {m[2]}','pick':'「胜」方向','odds':1.4})
        combos.append({'id':f'K32_{ci}','name':f'3串2容错·方案{ci+1}','level':'稳健','stars':3,
            'legs':legs,'rate':'40-52%(中2场)','odds':round(1.4**2,2),'cat':'3串2',
            'note':'3场拆3注2串1 容错1场'})

    # 4串2 容错
    for ci in range(2):
        picks = random.sample(sorted_m[:8], 4)
        legs = [{'match':f'{m[1]} vs {m[2]}','pick':'「胜」方向','odds':1.4} for m in picks]
        combos.append({'id':f'K42_{ci}','name':f'4串2容错·方案{ci+1}','level':'探索','stars':2,
            'legs':legs,'rate':'35-48%(中2场)','odds':round(1.4**2,2),'cat':'4串2',
            'note':'4场拆6注2串1 容错2场'})

    # 比分串关
    for ci in range(2):
        picks = random.sample(sorted_m[:6], 3)
        legs = []; od = 1.0
        for m in picks:
            sc, sco, _ = gen_score_pick(m[1], m[2])
            legs.append({'match':f'{m[1]} vs {m[2]}','pick':f'比分 {sc}','odds':sco})
            od *= sco
        combos.append({'id':f'KCS_{ci}','name':f'比分3串2·方案{ci+1}','level':'推演','stars':1,
            'legs':legs,'rate':'极低(<5%)','odds':round(od,1),'cat':'比分串',
            'note':'淘汰赛比分博冷 3场双选'})

    return combos


def gen_html():
    bracket = get_bracket()
    matches_data = []
    for num, t1, t2, label in bracket:
        p = predict_match(t1, t2)
        sc, sco, stag = gen_score_pick(t1, t2)
        matches_data.append({'num':num,'t1':t1,'t2':t2,'label':label,'p':p,'sc':sc,'sco':sco,'stag':stag})

    combos = gen_combos(bracket)

    # HTML
    CSS = '''*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#fff;padding:20px;max-width:1100px;margin:0 auto;color:#333;font-size:16px}
h1{font-size:24px;text-align:center;margin:12px 0}
.sub{text-align:center;font-size:14px;color:#999;margin-bottom:18px}
.section{margin-bottom:18px;border:1px solid #ccc;border-radius:5px;overflow:hidden}
.sec-title{background:#111;color:#fff;padding:9px 16px;font-size:15px;font-weight:600;display:flex;justify-content:space-between;align-items:center}
.sec-title .badge{font-size:12px;color:#8f8}
.sec-body{padding:14px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.two-col{grid-template-columns:1fr}}
.match-card{border:1px solid #ddd;padding:14px;background:#fafafa;margin-bottom:8px;border-radius:4px}
.mh{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.mnum{font-size:10px;background:#111;color:#fff;padding:2px 7px;border-radius:3px}
.mlabel{font-size:12px;color:#999}
.tier{font-size:10px;padding:2px 8px;border-radius:3px;font-weight:600}
.tier.t0{background:#e8f5e9;color:#2e7d32}.tier.t1{background:#fff8e1;color:#f57f17}
.tier.t2{background:#fff3e0;color:#e65100}.tier.t3{background:#f5f5f5;color:#999}
.teams{font-weight:700;font-size:16px;margin:6px 0}
.teams .vs{color:#bbb;font-size:12px;margin:0 8px}
.bar-row{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:12px}
.bar-row .lbl{width:40px;text-align:right;color:#888}
.bar-row .track{flex:1;height:5px;background:#eee;border-radius:2px}
.bar-row .fill{height:5px;border-radius:2px}
.bar-row .pct{width:42px;text-align:right;font-weight:600;font-size:12px}
.info{font-size:12px;color:#666;margin-top:6px;line-height:1.6}
.info b{color:#111}
.combo-item{border-bottom:1px solid #eee;padding:8px 0}
.combo-item:last-child{border-bottom:none}
.combo-head{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.clvl{font-size:9px;padding:2px 6px;border-radius:3px;font-weight:600}
.clvl.h{background:#e8f5e9;color:#2e7d32}.clvl.m{background:#fff8e1;color:#f57f17}
.clvl.s{background:#fff3e0;color:#e65100}.clvl.x{background:#ffebee;color:#c62828}
.cname{font-size:12px;font-weight:600;color:#111;flex:1}
.cleg{display:flex;align-items:center;gap:5px;padding:2px 0;font-size:11px}
.cleg .lm{font-weight:600;color:#111;font-size:11px;min-width:100px}
.cleg .lp{font-size:10px;color:#888;margin-left:auto}
.cleg .lo{font-size:11px;font-weight:700;color:#1976d2;min-width:36px;text-align:right}
.cnote{font-size:10px;color:#999;margin:2px 0}
.cstats{display:flex;gap:12px;font-size:10px;color:#666}
.score-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px}
.sc-card{text-align:center;padding:8px;border:1px solid #ddd;background:#fafafa;border-radius:4px;font-size:11px}
.sc-card .sct{font-size:9px;padding:2px 6px;border-radius:3px;display:inline-block;margin-bottom:3px}
.sct.hi{background:#e8f5e9;color:#2e7d32}.sct.md{background:#fff8e1;color:#f57f17}.sct.lo{background:#ffebee;color:#c62828}
.sc-card .scm{font-weight:600;color:#111;font-size:11px}
.sc-card .scs{font-weight:700;font-size:14px;color:#111;margin:3px 0}
.sc-card .sco{font-size:11px;color:#1976d2;font-weight:600}
.disclaimer{margin-top:20px;padding:16px;border:2px solid #ddd;border-radius:6px;text-align:center;font-size:13px;color:#888;line-height:1.8}
.disclaimer .dw{color:#e65100;font-weight:700}'''

    # 比赛卡片
    cards = ''
    for md in matches_data:
        num, t1, t2, label = md['num'], md['t1'], md['t2'], md['label']
        p = md['p']; sc, sco, stag = md['sc'], md['sco'], md['stag']
        e1, e2 = ELO.get(t1,1600), ELO.get(t2,1600); diff = e1-e2
        tier_cls = 't0' if abs(diff)>=200 else ('t1' if abs(diff)>=100 else ('t2' if abs(diff)>=30 else 't3'))
        tier_txt = '碾压' if abs(diff)>=200 else ('优势' if abs(diff)>=100 else ('接近' if abs(diff)>=30 else '均势'))
        f1, f2 = FLAGS.get(t1,''), FLAGS.get(t2,'')
        glist = ' | '.join([f'{k}球:{v}%' for k,v in p['goals_dist']])

        cards += f'''<div class="match-card"><div class="mh"><span class="mnum">#{num}</span><span class="mlabel">{label}</span><span class="tier {tier_cls}">{tier_txt}</span></div>
<div class="teams">{f1} {t1}<span class="vs">vs</span>{f2} {t2}</div>
<div class="bar-row"><span class="lbl">{t1}</span><div class="track"><div class="fill" style="width:{p['win']:.0f}%;background:#4caf50"></div></div><span class="pct">{p['win']:.0f}%</span></div>
<div class="bar-row"><span class="lbl">平局</span><div class="track"><div class="fill" style="width:{min(p['draw'],30):.0f}%;background:#ffc107"></div></div><span class="pct">{p['draw']:.0f}%</span></div>
<div class="bar-row"><span class="lbl">{t2}</span><div class="track"><div class="fill" style="width:{p['loss']:.0f}%;background:#f44336"></div></div><span class="pct">{p['loss']:.0f}%</span></div>
<div class="info"><b>预期进球</b> {p['total_goals']}球 | <b>加时概率</b> {p['et_prob']}% | <b>Elo差</b> {diff:+d}<br><b>总进球分布</b> {glist}<br><b>比分推荐</b> {sc} (赔率{sco}) · {stag}</div></div>'''

    # 组合
    ch = ''
    for c in combos[:15]:
        cls = 'h' if c['level']=='稳健' else ('m' if c['level']=='探索' else 'x')
        legs = ''
        for l in c['legs']:
            legs += f'<div class="cleg"><span class="lm">{l["match"]}</span><span class="lp">{l["pick"]}</span><span class="lo">{l["odds"]}</span></div>'
        ch += f'''<div class="combo-item"><div class="combo-head"><span class="clvl {cls}">{c['level']}</span><span class="cname">{c['name']}</span></div>{legs}<div class="cnote">{c['note']}</div><div class="cstats"><span>赔率 <b>{c['odds']}</b></span><span>匹配度 <b>{c['rate']}</b></span></div></div>'''

    # 比分推演卡片
    sc_cards = ''
    for md in matches_data[:8]:
        num, t1, t2 = md['num'], md['t1'], md['t2']
        sc, sco, stag = md['sc'], md['sco'], md['stag']
        stc = 'hi' if stag=='强弱' else ('md' if stag=='中距' else 'lo')
        sc_cards += f'<div class="sc-card"><div class="sct {stc}">{stag}</div><div class="scm">{t1[:3]} vs {t2[:3]}</div><div class="scs">{sc}</div><div class="sco">{sco}</div></div>'

    html = f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>世界杯32强淘汰赛</title><style>{CSS}</style></head><body>
<h1>🏆 2026世界杯 · 32强淘汰赛分析</h1>
<div class="sub">小组赛72场全结束 · 16场对阵 · 胜平负+总进球+比分 · 纯数据工具</div>

<div class="section"><div class="sec-title">⚽ 16场对阵预测 <span class="badge">胜平负·总进球·比分</span></div>
<div class="sec-body"><div class="two-col">{cards}</div></div></div>

<div class="section"><div class="sec-title" style="background:#555">🎯 比分推演 <span class="badge">每场最可能3比分</span></div>
<div class="sec-body"><div class="score-grid">{sc_cards}</div></div></div>

<div class="section"><div class="sec-title">🔗 淘汰赛串关推荐 <span class="badge">{len(combos)}组</span></div>
<div class="sec-body">{ch}</div></div>

<div class="disclaimer">
⚠️ 本页面为<b>纯数据分析工具</b>，所有内容仅供赛事逻辑研究。<br>
<span class="dw">🚫 不提供购彩渠道链接，不参与任何资金往来。</span><br>
淘汰赛含加时/点球，以上分析仅限90分钟常规时间。
</div>
</body></html>'''
    return html


if __name__ == '__main__':
    html = gen_html()
    out = os.path.join(DIR, 'knockout.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ {out}')
    print(f'   16场对阵 + 比分推演 + 串关推荐')
