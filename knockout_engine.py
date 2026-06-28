"""
世界杯淘汰赛完整分析引擎
R32→R16→QF→SF→Final 全赛程：每场胜平负+总进球+比分+串关
"""

import json, os, math, random
from collections import defaultdict

DIR = os.path.dirname(__file__)

ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"埃及":1720,"比利时":1830,"瑞典":1790,"挪威":1780,"瑞士":1830,"奥地利":1760,"科特迪瓦":1700,"南非":1640,"加拿大":1730,"波黑":1690,"阿尔及利亚":1660,"厄瓜多尔":1740,"加纳":1680,"澳大利亚":1710,"刚果民主共和国":1650}
FLAGS = {"阿根廷":"🇦🇷","法国":"🇫🇷","巴西":"🇧🇷","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","西班牙":"🇪🇸","葡萄牙":"🇵🇹","德国":"🇩🇪","荷兰":"🇳🇱","乌拉圭":"🇺🇾","克罗地亚":"🇭🇷","哥伦比亚":"🇨🇴","摩洛哥":"🇲🇦","美国":"🇺🇸","墨西哥":"🇲🇽","塞内加尔":"🇸🇳","日本":"🇯🇵","韩国":"🇰🇷","埃及":"🇪🇬","比利时":"🇧🇪","瑞典":"🇸🇪","挪威":"🇳🇴","瑞士":"🇨🇭","奥地利":"🇦🇹","科特迪瓦":"🇨🇮","南非":"🇿🇦","加拿大":"🇨🇦","波黑":"🇧🇦","阿尔及利亚":"🇩🇿","厄瓜多尔":"🇪🇨","加纳":"🇬🇭","澳大利亚":"🇦🇺","刚果民主共和国":"🇨🇩"}

def wp(e1,e2): return 1/(1+10**(-(e1-e2)/400))
def poisson(l,k): return math.exp(-l)*l**k/math.factorial(k) if k>=0 else 0

def predict(t1, t2):
    """Poisson模型预测：胜平负 + 比分Top3 + 总进球分布"""
    e1,e2 = ELO.get(t1,1600), ELO.get(t2,1600)
    adv = 20; xh = max(0.5, 1.4+(e1-e2+adv)/400*0.3)
    xa = max(0.5, 1.1-(e1-e2+adv)/400*0.3)
    w=dr=lo=0; sc={}
    for i in range(8):
        for j in range(8):
            p=poisson(xh,i)*poisson(xa,j); sc[f"{i}:{j}"]=p
            if i>j: w+=p*0.85
            elif i==j: dr+=p*1.3
            else: lo+=p*0.85
    total=w+dr+lo; w,dr,lo=w/total*100,dr/total*100,lo/total*100
    top=sorted(sc.items(),key=lambda x:-x[1])[:3]
    gl=defaultdict(float)
    for i in range(8):
        for j in range(8): gl[i+j]+=poisson(xh,i)*poisson(xa,j)
    gtop=sorted(gl.items(),key=lambda x:-x[1])[:5]
    return {'win':round(w,1),'draw':round(dr,1),'loss':round(lo,1),
        'xh':round(xh,2),'xa':round(xa,2),'tg':round(xh+xa,1),
        'top':[(s,round(p*100,1)) for s,p in top],
        'goals':[(k,round(v*100,1)) for k,v in gtop]}

def score_pick(t1,t2):
    d=ELO.get(t1,1600)-ELO.get(t2,1600)
    if d>=150: return "2:0/2:1/3:1",7.5,"强弱"
    elif d<=-150: return "0:2/1:2/1:3",7.5,"强弱"
    elif d>=50: return "2:1/1:1/1:0",7.0,"中距"
    elif d<=-50: return "1:2/1:1/0:1",7.0,"中距"
    else: return "1:1/0:0/1:0",6.0,"均势"

def gen_all():
    # R32 bracket
    W={'A':'墨西哥','B':'瑞士','C':'巴西','D':'美国','E':'德国','F':'荷兰','G':'埃及','H':'西班牙','I':'法国','J':'阿根廷','K':'哥伦比亚','L':'英格兰'}
    R={'A':'南非','B':'加拿大','C':'摩洛哥','D':'澳大利亚','E':'科特迪瓦','F':'日本','G':'比利时','H':'乌拉圭','I':'挪威','J':'奥地利','K':'葡萄牙','L':'克罗地亚'}
    T=['刚果民主共和国','瑞典','波黑','阿尔及利亚','塞内加尔','厄瓜多尔','加纳','韩国']
    R32=[(73,R['A'],R['B']),(74,W['E'],T[0]),(75,W['F'],R['C']),(76,W['C'],R['F']),
         (77,W['I'],T[1]),(78,R['E'],R['I']),(79,W['A'],T[2]),(80,W['L'],T[3]),
         (81,W['D'],T[4]),(82,W['G'],T[5]),(83,R['K'],R['L']),(84,W['H'],R['J']),
         (85,W['B'],T[6]),(86,W['J'],R['H']),(87,W['K'],T[7]),(88,R['D'],R['G'])]

    # 推演R16→Final
    def winner(t1,t2):
        e1,e2=ELO.get(t1,1600),ELO.get(t2,1600)
        return t1 if wp(e1,e2)>0.5 else t2
    r32_winners=[winner(t1,t2) for _,t1,t2 in R32]
    R16=[(89,r32_winners[0],r32_winners[1]),(90,r32_winners[2],r32_winners[3]),
         (91,r32_winners[4],r32_winners[5]),(92,r32_winners[6],r32_winners[7]),
         (93,r32_winners[8],r32_winners[9]),(94,r32_winners[10],r32_winners[11]),
         (95,r32_winners[12],r32_winners[13]),(96,r32_winners[14],r32_winners[15])]
    r16_winners=[winner(t1,t2) for _,t1,t2 in R16]
    QF=[(97,r16_winners[0],r16_winners[1]),(98,r16_winners[2],r16_winners[3]),
        (99,r16_winners[4],r16_winners[5]),(100,r16_winners[6],r16_winners[7])]
    qf_winners=[winner(t1,t2) for _,t1,t2 in QF]
    SF=[(101,qf_winners[0],qf_winners[1]),(102,qf_winners[2],qf_winners[3])]
    sf_winners=[winner(t1,t2) for _,t1,t2 in SF]
    FINAL=[(103,sf_winners[0],sf_winners[1])]
    # 半决赛败者 = 四个半决赛队中没进决赛的两个
    sf_teams = [QF[0][1], QF[0][2], QF[1][1], QF[1][2], QF[2][1], QF[2][2], QF[3][1], QF[3][2]]
    sf_all = []
    for i in range(0,8,2):
        w = r16_winners[i] if wp(ELO.get(R16[i][1],1600),ELO.get(R16[i][2],1600))>0.5 else R16[i][2] if wp(ELO.get(R16[i][1],1600),ELO.get(R16[i][2],1600))>0.5 else R16[i][1]
        sf_all.append(w)
    third_t1 = sf_all[0] if sf_all[0]!=sf_winners[0] else sf_all[1]
    third_t2 = sf_all[2] if sf_all[2]!=sf_winners[1] else sf_all[3]
    THIRD=[(104, third_t1, third_t2)]

    # 串关
    combos=[]
    sorted_m=sorted(R32,key=lambda m:-abs(ELO.get(m[1],1600)-ELO.get(m[2],1600)))
    for i in range(min(4,len(sorted_m)-1)):
        a,b=sorted_m[i],sorted_m[i+1]
        e1a,e2a=ELO.get(a[1],1600),ELO.get(a[2],1600)
        e1b,e2b=ELO.get(b[1],1600),ELO.get(b[2],1600)
        combos.append({'id':f'K2_{i}','name':f'2串1·#{a[0]}×#{b[0]}','level':'稳健',
            'legs':[{'match':f'{a[1]} vs {a[2]}','pick':'胜方向','odds':1.4},
                {'match':f'{b[1]} vs {b[2]}','pick':'胜方向','odds':1.5}],
            'rate':'42-55%','odds':2.1,'note':'淘汰赛深盘组合'})
    if len(sorted_m)>=3:
        a,b,c=sorted_m[0],sorted_m[1],sorted_m[2]
        combos.append({'id':'K3','name':'3串1','level':'稳健','legs':[{'match':f'{x[1]} vs {x[2]}','pick':'胜方向','odds':1.35} for x in [a,b,c]],'rate':'25-38%','odds':2.5,'note':'三场淘汰赛'})
    for ci in range(2):
        p=random.sample(sorted_m[:6],3)
        combos.append({'id':f'K32_{ci}','name':f'3串2容错·方案{ci+1}','level':'稳健','legs':[{'match':f'{x[1]} vs {x[2]}','pick':'胜方向','odds':1.4} for x in p],'rate':'40-52%(中2场)','odds':2.0,'note':'3场拆3注2串1'})
    for ci in range(2):
        p=random.sample(sorted_m[:6],3);od=1.0;legs=[]
        for m in p:
            sc,sco,_=score_pick(m[1],m[2]);legs.append({'match':f'{m[1]} vs {m[2]}','pick':f'比分{sc}','odds':sco});od*=sco
        combos.append({'id':f'KCS_{ci}','name':f'比分3串2·方案{ci+1}','level':'推演','legs':legs,'rate':'极低(<5%)','odds':round(od,1),'note':'淘汰赛比分博冷'})

    return {'R32':R32,'R16':R16,'QF':QF,'SF':SF,'FINAL':FINAL,'THIRD':THIRD,'combos':combos}

def gen_html():
    d = gen_all()
    CSS = '''*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#fff;padding:16px;max-width:600px;margin:0 auto;color:#333;font-size:15px}
h1{font-size:20px;text-align:center;margin:10px 0}
.sub{text-align:center;font-size:12px;color:#999;margin-bottom:14px}
.round-title{font-weight:700;font-size:14px;margin:16px 0 6px;padding:6px 10px;background:#111;color:#fff;border-radius:4px}
.match{border-bottom:1px solid #eee;padding:14px 0}
.match:last-child{border-bottom:none}
.mh{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.mnum{font-size:9px;background:#111;color:#fff;padding:2px 6px;border-radius:3px}
.mdate{font-size:11px;color:#999}
.teams{font-weight:700;font-size:15px;margin:4px 0}
.bar{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:12px}
.bar .lbl{width:36px;text-align:right;color:#888;font-size:11px}
.bar .track{flex:1;height:5px;background:#eee;border-radius:2px}
.bar .fill{height:5px;border-radius:2px}
.bar .pct{width:40px;text-align:right;font-weight:600;font-size:11px}
.info{font-size:11px;color:#666;margin-top:4px;line-height:1.5}
.info b{color:#111}
.combo{border:1px solid #eee;padding:8px;margin:4px 0;background:#fafafa;border-radius:4px;font-size:11px}
.combo .cl{font-weight:600;color:#111}
.combo .clg{font-size:10px;color:#666;margin:2px 0}
.sc-grid{display:flex;gap:4px;margin:6px 0}
.sc-c{flex:1;text-align:center;padding:6px;border:1px solid #ddd;background:#fafafa;font-size:10px}
.sc-c .sct{font-size:8px;padding:1px 5px;border-radius:3px;display:inline-block;margin-bottom:2px}
.sct.hi{background:#e8f5e9;color:#2e7d32}.sct.md{background:#fff8e1;color:#f57f17}.sct.lo{background:#ffebee;color:#c62828}
.sc-c .sctm{font-weight:600;color:#111;font-size:10px}
.sc-c .scts{font-weight:700;font-size:13px;color:#111;margin:2px 0}
.disclaimer{margin-top:20px;padding:14px;border:2px solid #ddd;border-radius:6px;text-align:center;font-size:12px;color:#999;line-height:1.8}
.disclaimer .dw{color:#e65100;font-weight:700}'''

    def match_card(num,t1,t2,date=""):
        p=predict(t1,t2);sc,sco,stag=score_pick(t1,t2)
        e1,e2=ELO.get(t1,1600),ELO.get(t2,1600);diff=e1-e2
        dstr=f'Elo差{diff:+d} · ' if t1 and t2 else ''
        glist=' | '.join([f'{k}球:{v}%' for k,v in p['goals']])
        return f'''<div class="match"><div class="mh"><span class="mnum">#{num}</span><span class="mdate">{date}</span></div>
<div class="teams">{FLAGS.get(t1,'')} {t1} vs {FLAGS.get(t2,'')} {t2}</div>
<div class="bar"><span class="lbl">{t1[:3]}</span><div class="track"><div class="fill" style="width:{p['win']:.0f}%;background:#4caf50"></div></div><span class="pct">{p['win']:.0f}%</span></div>
<div class="bar"><span class="lbl">平局</span><div class="track"><div class="fill" style="width:{min(p['draw'],30):.0f}%;background:#ffc107"></div></div><span class="pct">{p['draw']:.0f}%</span></div>
<div class="bar"><span class="lbl">{t2[:3]}</span><div class="track"><div class="fill" style="width:{p['loss']:.0f}%;background:#f44336"></div></div><span class="pct">{p['loss']:.0f}%</span></div>
<div class="info"><b>预期进球</b> {p['tg']}球 · <b>总进球</b> {glist}<br><b>比分</b> {sc} (x{sco}) · {stag} · {dstr}90分钟常规时间</div></div>'''

    html=f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>世界杯淘汰赛完整分析</title><style>{CSS}</style></head><body>
<h1>🏆 2026世界杯淘汰赛完整分析</h1>
<div class="sub">R32→R16→QF→SF→Final · Poisson模型 · 纯数据工具</div>'''

    # R32
    html+='<div class="round-title">═══ 32强 · 6/28-7/3 ═══</div>'
    for num,t1,t2 in d['R32']: html+=match_card(num,t1,t2,"6/28-7/3")

    # 比分推演
    html+='<div class="round-title">🎯 32强比分推演</div><div class="sc-grid">'
    for num,t1,t2 in d['R32'][:8]:
        sc,sco,stag=score_pick(t1,t2);tc='hi' if stag=='强弱' else ('md' if stag=='中距' else 'lo')
        html+=f'<div class="sc-c"><div class="sct {tc}">{stag}</div><div class="sctm">{t1[:3]}vs{t2[:3]}</div><div class="scts">{sc}</div><div style="font-size:9px;color:#1976d2">x{sco}</div></div>'
    html+='</div>'

    # R16 预测
    html+='<div class="round-title">═══ 16强预测 · 7/4-7 ═══</div>'
    for num,t1,t2 in d['R16']: html+=match_card(num,t1,t2,"7/4-7")

    # QF
    html+='<div class="round-title">═══ 8强预测 · 7/9-11 ═══</div>'
    for num,t1,t2 in d['QF']: html+=match_card(num,t1,t2,"7/9-11")

    # SF
    html+='<div class="round-title">═══ 半决赛预测 · 7/14-15 ═══</div>'
    for num,t1,t2 in d['SF']: html+=match_card(num,t1,t2,"7/14-15")

    # Final
    html+='<div class="round-title" style="background:#c62828">🏆 决赛预测 · 7/19 · 纽约</div>'
    for num,t1,t2 in d['FINAL']: html+=match_card(num,t1,t2,"7/19 纽约")
    html+='<div class="round-title" style="background:#555">🥉 三四名决赛 · 7/18</div>'
    for num,t1,t2 in d['THIRD']: html+=match_card(num,t1,t2,"7/18")

    # 串关
    n_combos = len(d['combos'])
    html+=f'<div class="round-title">🔗 淘汰赛串关推荐 · {n_combos}组</div>'
    for c in d['combos'][:12]:
        leg_parts = []
        for l in c['legs']:
            leg_parts.append(l['match'] + ' ' + l['pick'])
        legs=' · '.join(leg_parts)
        html+=f'<div class="combo"><span class="cl">{c['name']}</span> · {c['level']}<br><span class="clg">{legs}</span><br><span style="font-size:10px;color:#999">赔率{c['odds']} · 匹配度{c['rate']} · {c['note']}</span></div>'

    html+='<div class="disclaimer">⚠️ 纯数据分析工具 · 不构成预测结论 · <span class="dw">🚫 不涉及资金往来</span><br>淘汰赛含加时/点球，以上分析仅限90分钟常规时间</div></body></html>'
    return html

if __name__=='__main__':
    html=gen_html()
    out=os.path.join(DIR,'knockout.html')
    with open(out,'w',encoding='utf-8') as f: f.write(html)
    print(f'✅ {out}')
    print('   R32 16场 + 比分推演 + R16→Final 全赛程 + 串关')
