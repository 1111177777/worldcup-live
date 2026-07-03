"""
添加R16对阵到schedule.json + MC模拟
"""
import json, math, os, random
from collections import defaultdict

DIR = os.path.dirname(__file__)
random.seed(42)

def ps(l):
    L=math.exp(-l);k=0;p=1.0
    while p>L:k+=1;p*=random.random()
    return k-1

ELO={'法国':1930,'巴西':1920,'阿根廷':1950,'英格兰':1900,'西班牙':1890,'葡萄牙':1870,'比利时':1830,'瑞士':1830,'美国':1780,'墨西哥':1770,'挪威':1780,'摩洛哥':1790,'加拿大':1730,'巴拉圭':1720,'澳大利亚':1710,'埃及':1720,'哥伦比亚':1800,'加纳':1680,'佛得角':1580}
STYLE={'法国':(1.25,1.0),'巴西':(1.3,1.0),'阿根廷':(1.2,1.0),'英格兰':(1.15,1.0),'西班牙':(1.1,1.0),'葡萄牙':(1.2,0.95),'比利时':(1.1,0.9),'瑞士':(0.85,1.1),'美国':(1.1,0.9),'墨西哥':(1.1,0.9),'挪威':(1.25,0.8),'摩洛哥':(0.8,1.3),'加拿大':(1.0,0.85),'巴拉圭':(0.75,1.1),'澳大利亚':(1.1,0.95),'埃及':(0.95,1.1),'哥伦比亚':(1.1,0.85),'加纳':(0.9,0.85),'佛得角':(0.5,0.4)}

# R16 对阵
R16 = [
    (89,'加拿大','摩洛哥','7/4','休斯顿','R16'),
    (90,'巴拉圭','法国','7/5','费城','R16'),
    (91,'巴西','挪威','7/5','纽约','R16'),
    (92,'墨西哥','英格兰','7/5','墨西哥城','R16'),
    (93,'西班牙','葡萄牙','7/6','洛杉矶','R16'),
    (94,'比利时','美国','7/6','西雅图','R16'),
    (95,'阿根廷','澳大利亚','7/7','休斯顿','R16'),  # assuming Argentina & Australia advance
    (96,'瑞士','哥伦比亚','7/7','多伦多','R16'),   # assuming Switzerland & Colombia advance
]

def sim(h,a):
    he=ELO.get(h,1700);ae=ELO.get(a,1700)
    ha,hd=STYLE.get(h,(1.0,1.0));aa,ad=STYLE.get(a,(1.0,1.0))
    g=abs(he-ae)
    mh,ma=(1.05,1.18) if g>200 else ((1.08,1.15) if g>100 else (1.10,1.12))
    ed=he-ae+50;gd=ed/100*0.4
    hx=max(0.2,1.5+gd*0.7)*ha/max(ad,0.4)*mh*random.uniform(0.85,1.15)
    ax=max(0.2,1.2-gd*0.4)*aa/max(hd,0.4)*ma*random.uniform(0.85,1.15)
    hg=ps(max(0.1,hx));ag=ps(max(0.1,ax))
    if random.random()<0.03:
        if random.random()<0.5:hg+=1
        else:ag+=1
    return hg,ag

print('🎲 R16 全部8场 · MC 500次模拟')
print('='*55)

# 跑MC并生成schedule条目
r16_matches = []
for num,h,a,date,venue,group in R16:
    print(f'⚽ {h} vs {a} @ {venue} ({date})...',end=' ',flush=True)
    w=d=l=0;scores=defaultdict(int);hgs=[];ags=[]
    for _ in range(500):
        hg,ag=sim(h,a)
        if hg>ag:w+=1
        elif hg==ag:d+=1
        else:l+=1
        scores[f'{hg}:{ag}']+=1;hgs.append(hg);ags.append(ag)
    top=sorted(scores.items(),key=lambda x:x[1],reverse=True)[:3]
    o25=sum(1 for i in range(500) if hgs[i]+ags[i]>2.5)
    mc_text=f'16强。{h}胜{round(w/500*100,1)}%/平{round(d/500*100,1)}%/{a}胜{round(l/500*100,1)}%。MC最可能{top[0][0]}({round(top[0][1]/500*100,1)}%)。大2.5球{round(o25/500*100,1)}%。'
    r16_matches.append({'home':h,'away':a,'date':date,'group':group,'venue':venue,'time':'','intel':mc_text,'odds_home':'','odds_draw':'','odds_away':'','result':'','status':'','injury':'','risk':[],'value':''})
    print(f'{h}胜{round(w/500*100,1)}% 平{round(d/500*100,1)}% {a}胜{round(l/500*100,1)}% | {top[0][0]}')

# 合并到schedule.json
with open(os.path.join(DIR,'schedule.json'),'r',encoding='utf-8') as f:
    schedule=json.load(f)

# 删除旧R16
schedule=[m for m in schedule if m['group']!='R16']
schedule.extend(r16_matches)
schedule.sort(key=lambda m:(m['date'].split('/')[0].zfill(2),m['date'].split('/')[1].zfill(2)))

with open(os.path.join(DIR,'schedule.json'),'w',encoding='utf-8') as f:
    json.dump(schedule,f,ensure_ascii=False,indent=2)

print(f'\n✅ R16 8场已添加，总{len(schedule)}场')
for m in r16_matches:
    d = m['date']; h = m['home']; a = m['away']; v = m['venue']
    print(f'  {d} {h} vs {a} @ {v}')
