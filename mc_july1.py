"""
🎲 7月1日 R32 淘汰赛 · 蒙特卡洛500次模拟
三场：科特迪瓦vs挪威 | 法国vs瑞典 | 墨西哥vs厄瓜多尔
整合：小组赛表现 + ELO + 攻防风格 + 淘汰赛战意
"""
import json, math, os, random
from datetime import datetime
from collections import defaultdict

DIR = os.path.dirname(__file__)
OUTPUT_JSON = os.path.join(DIR, "mc_results.json")
OUTPUT_HTML = os.path.join(DIR, "mc_report.html")

random.seed(42)

# ========================================
# 泊松
# ========================================
def poisson_sample(lmbda):
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

# ========================================
# ELO + 攻防数据
# ========================================
ELO = {
    '法国': 1930, '挪威': 1780, '瑞典': 1790,
    '墨西哥': 1770, '厄瓜多尔': 1740, '科特迪瓦': 1700,
}

STYLE = {
    '法国': (1.25, 1.0),   # 攻击强，防守正常
    '挪威': (1.25, 0.8),   # 攻击强（哈兰德），防守偏弱
    '瑞典': (1.0, 1.0),    # 均衡
    '墨西哥': (1.1, 0.9),  # 攻击略强
    '厄瓜多尔': (0.9, 0.85), # 偏防守
    '科特迪瓦': (1.0, 0.85), # 身体好，防守一般
}

# ========================================
# 比赛情报（小组赛表现 + 伤停 + 战术）
# ========================================
MATCH_INTEL = {
    '科特迪瓦 vs 挪威': {
        'venue': '波士顿',
        'home_form': '小组赛2胜1负：1-0厄瓜多尔，1-2德国，2-0库拉索。进4失2。身体对抗强，速度反击。',
        'away_form': '小组赛2胜1负：4-1伊拉克，3-2塞内加尔，1-4法国。进8失7。哈兰德3场4球，厄德高组织核心。防线漏洞大(场均失2.3球)。',
        'home_key': '速度反击 + 身体对抗',
        'away_key': '哈兰德(3场4球) + 厄德高(组织核心)',
        'home_vuln': '中场控制力弱，面对强压迫易丢球',
        'away_vuln': '防线转身慢，被反击时身后空档大。小组赛场均失2.3球。',
        'motivation_home': 1.12,  # 淘汰赛，拼了
        'motivation_away': 1.12,  # 哈兰德要证明自己
        'odds_est': '挪威让0.5球',
    },
    '法国 vs 瑞典': {
        'venue': '达拉斯',
        'home_form': '小组赛3战全胜：3-1塞内加尔，3-0伊拉克，4-1挪威。进10失2。姆巴佩5场6球，统治级表现。',
        'away_form': '小组赛1胜1平1负：5-1突尼斯，1-5荷兰，1-1日本。进7失7。状态起伏大，遇强队崩盘(1-5荷兰)。',
        'home_key': '姆巴佩(3场6球) + 登贝莱 + 奥利塞，攻击线世界顶级',
        'away_key': '无伊布时代团队足球，小组赛曾5-1屠杀突尼斯',
        'home_vuln': '偶尔防守松懈（小组赛只丢2球），高位防线有被打身后风险',
        'away_vuln': '遇强队心理脆弱（1-5荷兰惨败），中场创造力不足',
        'motivation_home': 1.08,  # 法国实力碾压，留力八强
        'motivation_away': 1.15,  # 瑞典拼了，爆冷才有机会
        'odds_est': '法国让1.5球',
    },
    '墨西哥 vs 厄瓜多尔': {
        'venue': '墨西哥城(阿兹台克高原2200m)',
        'home_form': '小组赛3战全胜零失球：2-0南非，1-0韩国，3-0捷克。进6失0。高原主场无敌。',
        'away_form': '小组赛1胜1平1负：0-1科特迪瓦，0-0库拉索，2-1德国。进2失2。防守稳固，爆冷击败德国。',
        'home_key': '高原主场（2200m）+ 防守体系完美（小组赛0失球）',
        'away_key': '高原适应强（本来就是高原国家），防守反击专家',
        'home_vuln': '进攻创造力有限（场均2球），破密集防守能力存疑',
        'away_vuln': '客场高原（虽然本国也高），进攻火力不足（小组赛仅2球）',
        'motivation_home': 1.15,  # 高原主场 + 全国期待
        'motivation_away': 1.10,  # 淘汰赛拼了
        'odds_est': '墨西哥让0.25球（平手盘偏主）',
    },
}

# ========================================
# 单场模拟
# ========================================
def simulate(h_elo, a_elo, h_att, h_def, a_att, a_def, mot_h, mot_a, h_vuln, a_vuln):
    """核心模拟引擎"""
    elo_diff = h_elo - a_elo + 50  # 主场加成

    # 基础期望进球 (ELO差)
    goal_diff = elo_diff / 100 * 0.4
    h_xg = max(0.2, 1.5 + goal_diff * 0.7)
    a_xg = max(0.2, 1.2 - goal_diff * 0.4)

    # 攻防修正
    h_xg *= h_att / max(a_def, 0.4)
    a_xg *= a_att / max(h_def, 0.4)

    # 战意
    h_xg *= mot_h
    a_xg *= mot_a

    # 漏洞修正
    if '转身慢' in a_vuln or '身后空档' in a_vuln:
        h_xg *= random.uniform(1.05, 1.15)
    if '转身慢' in h_vuln or '身后空档' in h_vuln:
        a_xg *= random.uniform(1.05, 1.15)
    if '防线' in a_vuln and ('漏洞' in a_vuln or '弱' in a_vuln):
        h_xg *= random.uniform(1.03, 1.10)

    # 随机扰动
    h_xg *= random.uniform(0.85, 1.15)
    a_xg *= random.uniform(0.85, 1.15)

    hg = poisson_sample(max(0.1, h_xg))
    ag = poisson_sample(max(0.1, a_xg))

    # 红牌/点球 (~3%)
    if random.random() < 0.03:
        if random.random() < 0.5:
            hg += 1
        else:
            ag += 1

    return hg, ag, round(h_xg, 2), round(a_xg, 2)


# ========================================
# 主程序
# ========================================
def main():
    print('=' * 65)
    print('   🎲 7月1日 R32淘汰赛 · 蒙特卡洛 500次模拟')
    print('=' * 65)

    all_results = {}
    N = 500

    for match_name, intel in MATCH_INTEL.items():
        h, _, a = match_name.split()
        h_att, h_def = STYLE[h]
        a_att, a_def = STYLE[a]

        print(f'\n⚽ {match_name} @ {intel["venue"]}')
        print(f'   ELO: {h} {ELO[h]} vs {a} {ELO[a]}')
        print(f'   {h}: {intel["home_form"][:60]}...')
        print(f'   {a}: {intel["away_form"][:60]}...')
        print(f'   跑 {N} 次模拟...', end=' ', flush=True)

        # 累积统计
        wins = draws = losses = 0
        scorelines = defaultdict(int)
        goal_dist = defaultdict(int)
        h_goals_list = []
        a_goals_list = []

        for _ in range(N):
            hg, ag, xh, xa = simulate(
                ELO[h], ELO[a],
                h_att, h_def, a_att, a_def,
                intel['motivation_home'], intel['motivation_away'],
                intel['home_vuln'], intel['away_vuln']
            )
            if hg > ag:
                wins += 1
            elif hg == ag:
                draws += 1
            else:
                losses += 1
            scorelines[f"{hg}:{ag}"] += 1
            goal_dist[hg + ag] += 1
            h_goals_list.append(hg)
            a_goals_list.append(ag)

        avg_hg = sum(h_goals_list) / N
        avg_ag = sum(a_goals_list) / N
        top_scores = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)[:6]
        over_25 = sum(1 for i in range(N) if h_goals_list[i] + a_goals_list[i] > 2.5)
        btts = sum(1 for i in range(N) if h_goals_list[i] > 0 and a_goals_list[i] > 0)

        print('✅')

        result = {
            'home': h, 'away': a,
            'venue': intel['venue'],
            'elo_home': ELO[h], 'elo_away': ELO[a],
            'attack_home': h_att, 'defense_home': h_def,
            'attack_away': a_att, 'defense_away': a_def,
            'motivation_home': intel['motivation_home'],
            'motivation_away': intel['motivation_away'],
            'home_form': intel['home_form'],
            'away_form': intel['away_form'],
            'key_home': intel['home_key'],
            'key_away': intel['away_key'],
            'vuln_home': intel['home_vuln'],
            'vuln_away': intel['away_vuln'],
            'odds_est': intel['odds_est'],
            'simulations': N,
            'win_pct': round(wins / N * 100, 1),
            'draw_pct': round(draws / N * 100, 1),
            'loss_pct': round(losses / N * 100, 1),
            'avg_home_goals': round(avg_hg, 2),
            'avg_away_goals': round(avg_ag, 2),
            'top_scores': [(s, c, round(c/N*100, 1)) for s, c in top_scores],
            'goal_distribution': {str(k): round(v/N*100, 1) for k, v in sorted(goal_dist.items())},
            'over_25_pct': round(over_25 / N * 100, 1),
            'btts_pct': round(btts / N * 100, 1),
        }
        all_results[match_name] = result

        # 打印摘要
        print(f'   📊 {h}胜 {result["win_pct"]}% | 平 {result["draw_pct"]}% | {a}胜 {result["loss_pct"]}%')
        print(f'   ⚽ 平均进球: {avg_hg:.2f} - {avg_ag:.2f}')
        print(f'   🎯 最可能比分: {", ".join(f"{s}({c/N*100:.1f}%)" for s, c in top_scores[:3])}')
        print(f'   📈 大2.5球: {result["over_25_pct"]}% | 双方进球: {result["btts_pct"]}%')

    # 保存JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f'\n📁 JSON: {OUTPUT_JSON}')

    # 生成HTML报告
    generate_html(all_results)

    # 对比schedule现有预测
    print()
    print('=' * 65)
    print('   📋 与现有预测对比')
    print('=' * 65)
    schedule_path = os.path.join(DIR, 'schedule.json')
    with open(schedule_path, 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    for m in schedule:
        if m.get('date') == '7/1':
            match_name = f"{m['home']} vs {m['away']}"
            if match_name in all_results:
                r = all_results[match_name]
                # 看现有预测比分
                old_pred = m.get('intel', '')[:60]
                print(f'\n{match_name}:')
                print(f'   原预测: {old_pred}')
                print(f'   新模拟: {r["home"]}胜{r["win_pct"]}% | 平{r["draw_pct"]}% | {r["away"]}胜{r["loss_pct"]}%')
                top_score = r['top_scores'][0] if r['top_scores'] else ('?', 0, 0)
                print(f'   最可能比分: {top_score[0]} ({top_score[2]}%)')
                print(f'   大2.5球: {r["over_25_pct"]}%')

    print()
    print('=' * 65)
    print('   ✅ 全部完成')
    print('=' * 65)


def generate_html(results):
    """生成HTML报告"""
    cards = ""
    for name, r in results.items():
        h, a = r['home'], r['away']
        w = r['win_pct']; d = r['draw_pct']; l = r['loss_pct']

        # 信心评级
        if w > 75: conf = "🟢 高置信"
        elif w > 60: conf = "🟡 中等"
        elif w > 45: conf = "🟠 均势"
        else: conf = "🔴 不确定"

        # 比分条
        score_rows = ""
        for s, cnt, pct in r['top_scores'][:5]:
            bar_w = pct * 3
            score_rows += f'<tr><td style="font-weight:bold;font-family:monospace;color:#fbbf24;">{s}</td><td>{cnt}/500</td><td>{pct}%</td><td><div style="width:{bar_w}px;height:16px;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:8px;"></div></td></tr>'

        cards += f"""
    <div style="background:#1e293b;border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #334155;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
        <span style="font-size:1.4em;font-weight:bold;color:#e2e8f0;">{h} vs {a}</span>
        <span style="font-size:0.85em;padding:4px 10px;border-radius:12px;background:#334155;">{conf}</span>
        <span style="font-size:0.8em;color:#94a3b8;">@ {r['venue']}</span>
      </div>
      <div style="font-size:11px;color:#94a3b8;margin-bottom:8px;line-height:1.5;">
        ⭐ {h}: {r['key_home']}<br>
        ⭐ {a}: {r['key_away']}
      </div>
      <div style="font-size:10px;color:#64748b;margin-bottom:12px;">
        🔻 {h}: {r['vuln_home']}<br>
        🔻 {a}: {r['vuln_away']}
      </div>
      <div style="margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">{h}胜</span>
          <div style="flex:1;height:24px;background:#1e293b;border-radius:12px;overflow:hidden;">
            <div style="height:100%;width:{w}%;background:{'#22c55e' if w>50 else '#f59e0b'};border-radius:12px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;"><span style="font-size:11px;font-weight:bold;color:#0f172a;">{w}%</span></div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">平局</span>
          <div style="flex:1;height:24px;background:#1e293b;border-radius:12px;overflow:hidden;">
            <div style="height:100%;width:{d}%;background:#888;border-radius:12px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;"><span style="font-size:11px;font-weight:bold;color:#fff;">{d}%</span></div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">{a}胜</span>
          <div style="flex:1;height:24px;background:#1e293b;border-radius:12px;overflow:hidden;">
            <div style="height:100%;width:{l}%;background:{'#22c55e' if l>50 else '#ef4444'};border-radius:12px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;"><span style="font-size:11px;font-weight:bold;color:#fff;">{l}%</span></div>
          </div>
        </div>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;">
        <div style="background:#0f172a;padding:8px 14px;border-radius:8px;text-align:center;">
          <div style="font-size:10px;color:#64748b;">平均进球</div>
          <div style="font-size:1.1em;font-weight:bold;color:#e2e8f0;">{r['avg_home_goals']} - {r['avg_away_goals']}</div>
        </div>
        <div style="background:#0f172a;padding:8px 14px;border-radius:8px;text-align:center;">
          <div style="font-size:10px;color:#64748b;">大2.5球</div>
          <div style="font-size:1.1em;font-weight:bold;color:#34d399;">{r['over_25_pct']}%</div>
        </div>
        <div style="background:#0f172a;padding:8px 14px;border-radius:8px;text-align:center;">
          <div style="font-size:10px;color:#64748b;">双方进球</div>
          <div style="font-size:1.1em;font-weight:bold;color:#fbbf24;">{r['btts_pct']}%</div>
        </div>
      </div>
      <div style="font-size:12px;font-weight:600;color:#94a3b8;margin-bottom:6px;">🎯 模拟500次 比分TOP5</div>
      <table style="width:100%;border-collapse:collapse;">{score_rows}</table>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>7/1 R32淘汰赛 · 蒙特卡洛500次模拟</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;max-width:800px;margin:0 auto}}
h1{{font-size:1.5em;text-align:center;margin:16px 0;background:linear-gradient(135deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.sub{{text-align:center;font-size:11px;color:#64748b;margin-bottom:20px}}
.note{{text-align:center;color:#475569;font-size:11px;padding:20px;line-height:1.6}}
</style></head>
<body>
<h1>🎲 蒙特卡洛 500次模拟</h1>
<div class="sub">2026世界杯 · 7月1日 R32淘汰赛 3场<br>整合: ELO+攻防风格+小组赛表现+淘汰赛战意+情报分析<br>生成: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
<div style="background:#1e3a5f;border:1px solid #2563eb;border-radius:12px;padding:16px;margin-bottom:20px;font-size:12px;color:#93c5fd;line-height:1.8;">
<b>🔬 模拟方法：</b>ELO基础实力 → 攻防系数修正 → 淘汰赛战意 → 战术漏洞 → ±15%随机波动 → 泊松采样进球 → 3%概率点球/红牌事件
</div>
{cards}
<div class="note">⚠️ 统计模型模拟，仅供参考。⚽ 理性观赛。</div>
</body></html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'📁 HTML: {OUTPUT_HTML}')


if __name__ == '__main__':
    main()
