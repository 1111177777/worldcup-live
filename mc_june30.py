"""
🎲 6月30日 R32淘汰赛 · 蒙特卡洛500次模拟
巴西vs日本 | 德国vs巴拉圭 | 荷兰vs摩洛哥
"""
import json, math, os, random
from datetime import datetime
from collections import defaultdict

DIR = os.path.dirname(__file__)
random.seed(42)

def poisson_sample(lmbda):
    L = math.exp(-lmbda); k = 0; p = 1.0
    while p > L: k += 1; p *= random.random()
    return k - 1

ELO = {'巴西':1920,'日本':1870,'德国':1860,'巴拉圭':1720,'荷兰':1820,'摩洛哥':1790}
STYLE = {
    '巴西':(1.3,1.0),'日本':(1.25,1.05),'德国':(1.3,1.0),
    '巴拉圭':(0.75,1.1),'荷兰':(1.0,0.85),'摩洛哥':(0.8,1.3),
}

INTEL = {
    '巴西 vs 日本': {
        'venue': '休斯顿',
        'home_form': '小组赛2胜1平：1-1摩洛哥，3-0海地，3-0苏格兰。进7失1。桑巴军团火力全开。',
        'away_form': '小组赛1胜2平：2-2荷兰，4-0突尼斯，1-1瑞典。进7失3。日本技术流传控，旅欧军团成熟。',
        'home_key': '维尼修斯+罗德里戈双翼，中场控制力世界顶级',
        'away_key': '三笘薰+久保建英+远藤航，技术流传控，曾2-2逼平荷兰',
        'home_vuln': '偶尔轻敌（1-1被摩洛哥逼平），防线高位有被打反击风险',
        'away_vuln': '身体对抗吃亏，面对巴西边路爆破压力巨大',
        'motivation_home': 1.05,  # 巴西实力碾压，但别轻敌
        'motivation_away': 1.18,  # 日本拼了，要创造历史
        'odds_est': '巴西让1球',
    },
    '德国 vs 巴拉圭': {
        'venue': '费城',
        'home_form': '小组赛2胜1负：7-1库拉索，2-1科特迪瓦，1-2厄瓜多尔。进10失4。最后一轮输球暴露问题。',
        'away_form': '小组赛1胜1平1负：1-4美国，1-0土耳其，0-0澳大利亚。进2失4。防守硬朗，进攻乏力。',
        'home_key': '穆西亚拉+维尔茨双核，中场创造力强',
        'away_key': '南美式铁血防守，定位球有威胁',
        'home_vuln': '防线不稳定（对厄瓜多尔丢2球），高位逼抢被反噬',
        'away_vuln': '进攻创造力严重不足（小组赛仅2球），被动挨打型',
        'motivation_home': 1.10,  # 最后一场输球需要证明自己
        'motivation_away': 1.12,  # 淘汰赛死守到底
        'odds_est': '德国让1.25球',
    },
    '荷兰 vs 摩洛哥': {
        'venue': '纽约',
        'home_form': '小组赛2胜1平：2-2日本，5-1瑞典，3-1突尼斯。进10失4。攻击力恐怖。',
        'away_form': '小组赛2胜1平：1-1巴西，1-0苏格兰，4-2海地。进6失3。上届四强，防反教科书。曾逼平巴西！',
        'home_key': '加克波+德佩+西蒙斯，攻击线丰富',
        'away_key': '上届四强班底，阿什拉夫+齐耶赫+马兹拉维，防守反击专杀强队',
        'home_vuln': '防线偶尔走神（被日本进2球），对阵防守型球队破局能力存疑',
        'away_vuln': '主动进攻能力有限，一旦先丢球很难翻盘',
        'motivation_home': 1.10,  # 荷兰要证明不是上届八强就完了
        'motivation_away': 1.15,  # 摩洛哥上届四强，要复制奇迹
        'odds_est': '荷兰让0.75球',
    },
}

def simulate(h_elo, a_elo, h_att, h_def, a_att, a_def, mot_h, mot_a, h_vuln, a_vuln):
    elo_diff = h_elo - a_elo + 50
    goal_diff = elo_diff / 100 * 0.4
    h_xg = max(0.2, 1.5 + goal_diff * 0.7)
    a_xg = max(0.2, 1.2 - goal_diff * 0.4)
    h_xg *= h_att / max(a_def, 0.4)
    a_xg *= a_att / max(h_def, 0.4)
    h_xg *= mot_h; a_xg *= mot_a
    if any(kw in a_vuln for kw in ['反击','身后','空档']): h_xg *= random.uniform(1.03, 1.10)
    if any(kw in h_vuln for kw in ['反击','身后','空档']): a_xg *= random.uniform(1.03, 1.10)
    h_xg *= random.uniform(0.85, 1.15); a_xg *= random.uniform(0.85, 1.15)
    hg = poisson_sample(max(0.1, h_xg)); ag = poisson_sample(max(0.1, a_xg))
    if random.random() < 0.03:
        if random.random() < 0.5: hg += 1
        else: ag += 1
    return hg, ag

def main():
    print('=' * 60)
    print('   🎲 6月30日 R32淘汰赛 · MC 500次')
    print('=' * 60)
    N = 500
    all_results = {}
    for name, intel in INTEL.items():
        h, _, a = name.split()
        h_att, h_def = STYLE[h]; a_att, a_def = STYLE[a]
        print(f'\n⚽ {name} @ {intel["venue"]}')
        print(f'   ELO: {h} {ELO[h]} vs {a} {ELO[a]}')
        print(f'   跑 {N} 次...', end=' ', flush=True)
        wins = draws = losses = 0
        scores = defaultdict(int); goals = defaultdict(int)
        hg_list = []; ag_list = []
        for _ in range(N):
            hg, ag = simulate(ELO[h], ELO[a], h_att, h_def, a_att, a_def,
                              intel['motivation_home'], intel['motivation_away'],
                              intel['home_vuln'], intel['away_vuln'])
            if hg > ag: wins += 1
            elif hg == ag: draws += 1
            else: losses += 1
            scores[f"{hg}:{ag}"] += 1; goals[hg+ag] += 1
            hg_list.append(hg); ag_list.append(ag)
        avg_h = sum(hg_list)/N; avg_a = sum(ag_list)/N
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        o25 = sum(1 for i in range(N) if hg_list[i]+ag_list[i] > 2.5)
        btts = sum(1 for i in range(N) if hg_list[i]>0 and ag_list[i]>0)
        print('✅')
        r = {
            'home':h,'away':a,'venue':intel['venue'],
            'elo_home':ELO[h],'elo_away':ELO[a],
            'win_pct':round(wins/N*100,1),'draw_pct':round(draws/N*100,1),'loss_pct':round(losses/N*100,1),
            'avg_home_goals':round(avg_h,2),'avg_away_goals':round(avg_a,2),
            'top_scores':[(s,c,round(c/N*100,1)) for s,c in top],
            'over_25_pct':round(o25/N*100,1),'btts_pct':round(btts/N*100,1),
        }
        all_results[name] = r
        print(f'   📊 {h}胜 {r["win_pct"]}% | 平 {r["draw_pct"]}% | {a}胜 {r["loss_pct"]}%')
        print(f'   ⚽ 平均进球: {avg_h:.2f} - {avg_a:.2f}')
        print(f'   🎯 最可能: {", ".join(f"{s}({c/N*100:.1f}%)" for s,c in top[:3])}')
        print(f'   📈 大2.5球: {r["over_25_pct"]}% | 双方进球: {r["btts_pct"]}%')

    # 保存
    with open(os.path.join(DIR,'mc_results.json'),'w',encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f'\n📁 mc_results.json 已保存')

    # 更新 schedule.json
    with open(os.path.join(DIR,'schedule.json'),'r',encoding='utf-8') as f:
        schedule = json.load(f)
    for m in schedule:
        if m['date'] == '6/30':
            key = f'{m["home"]} vs {m["away"]}'
            if key in all_results:
                r = all_results[key]
                t = r['top_scores'][0]
                m['intel'] = f'淘汰赛R32。{r["home"]}胜{r["win_pct"]}%/平{r["draw_pct"]}%/{r["away"]}胜{r["loss_pct"]}%。MC最可能{t[0]}({t[2]}%)。大2.5球{r["over_25_pct"]}%。'
                print(f'{key}: schedule已更新')
    with open(os.path.join(DIR,'schedule.json'),'w',encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    # 对比
    print()
    print('=' * 60)
    print('   📋 与原有预测对比')
    print('=' * 60)
    for name, r in all_results.items():
        t = r['top_scores'][0]
        print(f'\n{name}:')
        print(f'   胜平负: {r["home"]}胜{r["win_pct"]}% / 平{r["draw_pct"]}% / {r["away"]}胜{r["loss_pct"]}%')
        print(f'   最可能比分: {t[0]} ({t[2]}%)')
        print(f'   大2.5球: {r["over_25_pct"]}% | BTTS: {r["btts_pct"]}%')

    print(f'\n{"="*60}')
    print('✅ 全部完成')
    print('='*60)

if __name__ == '__main__':
    main()
