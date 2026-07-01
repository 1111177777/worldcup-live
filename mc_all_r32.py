"""
🎲 R32全部16场 · 蒙特卡洛500次模拟 + 更新schedule.json
"""
import json, math, os, random
from collections import defaultdict

DIR = os.path.dirname(__file__)
random.seed(42)

def ps(lmbda):
    L = math.exp(-lmbda); k = 0; p = 1.0
    while p > L: k += 1; p *= random.random()
    return k - 1

ELO = {'法国':1930,'巴西':1920,'阿根廷':1950,'英格兰':1900,'西班牙':1890,'葡萄牙':1870,'德国':1860,'荷兰':1820,'比利时':1830,'哥伦比亚':1800,'瑞士':1830,'美国':1780,'墨西哥':1770,'克罗地亚':1810,'摩洛哥':1790,'日本':1870,'挪威':1780,'埃及':1720,'科特迪瓦':1700,'奥地利':1760,'瑞典':1790,'厄瓜多尔':1740,'加纳':1680,'波黑':1690,'阿尔及利亚':1660,'巴拉圭':1720,'塞内加尔':1760,'南非':1640,'加拿大':1730,'澳大利亚':1710,'刚果民主共和国':1650,'佛得角':1580}

STYLE = {'法国':(1.25,1.0),'巴西':(1.3,1.0),'阿根廷':(1.2,1.0),'英格兰':(1.15,1.0),'西班牙':(1.1,1.0),'葡萄牙':(1.2,0.95),'德国':(1.3,1.0),'荷兰':(1.0,0.85),'比利时':(1.1,0.9),'哥伦比亚':(1.1,0.85),'瑞士':(0.85,1.1),'美国':(1.1,0.9),'墨西哥':(1.1,0.9),'克罗地亚':(0.9,1.1),'摩洛哥':(0.8,1.3),'日本':(1.25,1.05),'挪威':(1.25,0.8),'埃及':(0.95,1.1),'科特迪瓦':(1.0,0.85),'奥地利':(1.0,0.9),'瑞典':(1.0,1.0),'厄瓜多尔':(0.9,0.85),'加纳':(0.9,0.85),'波黑':(0.9,0.85),'阿尔及利亚':(0.85,0.85),'巴拉圭':(0.75,1.1),'塞内加尔':(1.05,0.9),'南非':(0.8,0.8),'加拿大':(1.0,0.85),'澳大利亚':(1.1,0.95),'刚果民主共和国':(0.8,0.6),'佛得角':(0.5,0.4)}

def sim(h_elo, a_elo, h_att, h_def, a_att, a_def, mot_h=1.10, mot_a=1.10):
    ed = h_elo - a_elo + 50
    gd = ed / 100 * 0.4
    hx = max(0.2, 1.5 + gd * 0.7) * h_att / max(a_def, 0.4) * mot_h * random.uniform(0.85, 1.15)
    ax = max(0.2, 1.2 - gd * 0.4) * a_att / max(h_def, 0.4) * mot_a * random.uniform(0.85, 1.15)
    hg = ps(max(0.1, hx)); ag = ps(max(0.1, ax))
    if random.random() < 0.03:
        if random.random() < 0.5: hg += 1
        else: ag += 1
    return hg, ag

def mc_match(h, a, n=500):
    he = ELO.get(h, 1700); ae = ELO.get(a, 1700)
    ha, hd = STYLE.get(h, (1.0,1.0)); aa, ad = STYLE.get(a, (1.0,1.0))
    # 淘汰赛战意
    elo_gap = abs(he - ae)
    if elo_gap > 200: mot_h, mot_a = 1.05, 1.18  # 强队留力，弱队拼命
    elif elo_gap > 100: mot_h, mot_a = 1.08, 1.15
    else: mot_h, mot_a = 1.10, 1.12  # 势均力敌都拼

    w = d = l = 0; scores = defaultdict(int); goals = defaultdict(int)
    hgs = []; ags = []
    for _ in range(n):
        hg, ag = sim(he, ae, ha, hd, aa, ad, mot_h, mot_a)
        if hg > ag: w += 1
        elif hg == ag: d += 1
        else: l += 1
        scores[f"{hg}:{ag}"] += 1; goals[hg+ag] += 1
        hgs.append(hg); ags.append(ag)
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    o25 = sum(1 for i in range(n) if hgs[i]+ags[i] > 2.5)
    return {
        'win': round(w/n*100,1), 'draw': round(d/n*100,1), 'loss': round(l/n*100,1),
        'avg_h': round(sum(hgs)/n,2), 'avg_a': round(sum(ags)/n,2),
        'top': [(s, round(c/n*100,1)) for s,c in top],
        'o25': round(o25/n*100,1),
    }

def main():
    with open(os.path.join(DIR, 'schedule.json'), 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    r32 = [m for m in schedule if m['group'] == 'R32']
    print(f'🎲 R32 全部 {len(r32)} 场 · 500次模拟')
    print('=' * 55)

    for m in r32:
        h, a = m['home'], m['away']
        print(f'⚽ {h} vs {a} @ {m["venue"]} ({m["date"]})...', end=' ', flush=True)
        r = mc_match(h, a)
        t = r['top'][0]
        m['intel'] = f'淘汰赛R32。{h}胜{r["win"]}%/平{r["draw"]}%/{a}胜{r["loss"]}%。MC最可能{t[0]}({t[1]}%)。大2.5球{r["o25"]}%。'
        print(f'{h}胜{r["win"]}% 平{r["draw"]}% {a}胜{r["loss"]}% | {t[0]}({t[1]}%)')

    with open(os.path.join(DIR, 'schedule.json'), 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    print()
    print('=' * 55)
    print('📊 R32 胜平负汇总')
    print('=' * 55)
    for m in r32:
        h, a = m['home'], m['away']
        print(f'{m["date"]} {h:6s} vs {a:6s} @ {m["venue"]}')
        print(f'       {m["intel"]}')
    print()
    print('✅ schedule.json 已更新，重新生成 live.html...')

if __name__ == '__main__':
    main()
