"""
🎲 蒙特卡洛500次模拟 — 6月22日四场比赛深度分析
整合：ELO评分 + 攻防风格系数 + 球员阵容 + 出线压力/轻松状态 + 战术漏洞
用法：python monte_carlo_500.py
"""
import json, math, os, random
from datetime import datetime
from collections import defaultdict

DIR = os.path.dirname(__file__)
SCHEDULE_FILE = os.path.join(DIR, "schedule.json")
OUTPUT_JSON = os.path.join(DIR, "mc_results.json")
OUTPUT_HTML = os.path.join(DIR, "mc_report.html")

random.seed(42)  # 可复现

# ========================================
# 泊松分布
# ========================================
def poisson(lmbda, k):
    return math.exp(-lmbda) * lmbda**k / math.factorial(k)

def poisson_sample(lmbda):
    """从泊松分布采样（逆变换法）"""
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

# ========================================
# 核心：单场模拟引擎
# ========================================
def simulate_match(home_elo, away_elo, h_attack, h_defense, a_attack, a_defense,
                   motivation_h, motivation_a, h_style_desc="", a_style_desc="",
                   h_vuln="", a_vuln=""):
    """
    基于ELO + 攻防系数 + 战意 → 计算期望进球 → 泊松采样
    漏洞影响：防守方漏洞 → 对方攻击力上浮5-15%
    """
    elo_diff = home_elo - away_elo + 50  # 50分主场加成

    # 基础期望进球
    goal_diff_per_100 = elo_diff / 100 * 0.4
    base_h_xg = max(0.2, 1.6 + goal_diff_per_100 * 0.7)
    base_a_xg = max(0.2, 1.2 - goal_diff_per_100 * 0.4)

    # 攻防系数修正
    h_xg = base_h_xg * h_attack / max(a_defense, 0.4)
    a_xg = base_a_xg * a_attack / max(h_defense, 0.4)

    # 战意修正（出线压力/轻松状态）
    h_xg *= motivation_h
    a_xg *= motivation_a

    # 漏洞修正：对方有漏洞→攻击方加成
    if a_vuln and any(kw in a_vuln for kw in ['转身慢', '身后空档', '防线', '定位球']):
        h_xg *= random.uniform(1.05, 1.15)
    if h_vuln and any(kw in h_vuln for kw in ['转身慢', '身后空档', '防线', '定位球']):
        a_xg *= random.uniform(1.05, 1.15)

    # 随机扰动（模拟比赛不确定性）
    h_xg *= random.uniform(0.85, 1.15)
    a_xg *= random.uniform(0.85, 1.15)

    # 泊松采样
    h_goals = poisson_sample(max(0.1, h_xg))
    a_goals = poisson_sample(max(0.1, a_xg))

    # 红牌/点球随机事件（~3%概率）
    if random.random() < 0.03:
        if random.random() < 0.5:
            h_goals += 1  # 点球
        else:
            a_goals += 1

    return h_goals, a_goals, round(h_xg, 2), round(a_xg, 2)


# ========================================
# 加载数据
# ========================================
def load_june22_matches():
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        all_matches = json.load(f)

    june22 = [m for m in all_matches if m['date'] == '6/22']
    return june22


# ========================================
# 500次蒙特卡洛
# ========================================
def run_monte_carlo(matches, n=500):
    """对每场比赛跑n次蒙特卡洛模拟"""
    all_results = {}

    for m in matches:
        h, a = m['home'], m['away']
        mc = m.get('_mc_data', {})

        # 提取参数
        h_elo_key = [k for k in mc if k.endswith('_elo') and h in k.lower().replace(' ','')[:4]]
        a_elo_key = [k for k in mc if k.endswith('_elo') and a in k.lower().replace(' ','')[:4]]

        # 兼容不同命名
        h_elo = mc.get(f"{h}_elo") if f"{h}_elo" in mc else (
            mc.get('france_elo') if h == '法国' else
            mc.get('norway_elo') if h == '挪威' else
            mc.get('argentina_elo') if h == '阿根廷' else
            mc.get('jordan_elo') if h == '约旦' else 1700
        )
        a_elo = mc.get('iraq_elo') if a == '伊拉克' else (
            mc.get('senegal_elo') if a == '塞内加尔' else
            mc.get('austria_elo') if a == '奥地利' else
            mc.get('algeria_elo') if a == '阿尔及利亚' else 1700
        )

        # 攻防系数
        h_att = float(mc.get(f'{h}_attack', mc.get('france_attack' if h=='法国' else 'norway_attack' if h=='挪威' else 'argentina_attack' if h=='阿根廷' else 'jordan_attack', 1.0)))
        a_att = float(mc.get('iraq_attack' if a=='伊拉克' else 'senegal_attack' if a=='塞内加尔' else 'austria_attack' if a=='奥地利' else 'algeria_attack', 1.0))
        h_def = float(mc.get(f'{h}_defense', mc.get('france_defense' if h=='法国' else 'norway_defense' if h=='挪威' else 'argentina_defense' if h=='阿根廷' else 'jordan_defense', 1.0)))
        a_def = float(mc.get('iraq_defense' if a=='伊拉克' else 'senegal_defense' if a=='塞内加尔' else 'austria_defense' if a=='奥地利' else 'algeria_defense', 1.0))

        # 战意
        mot_h = float(mc.get('motivation_home', 1.0))
        mot_a = float(mc.get('motivation_away', 1.0))

        # 风格 + 漏洞
        h_style = mc.get(f'{h}_style', '')
        a_style = mc.get(f'{a}_style', '') if f'{a}_style' in mc else mc.get('iraq_style' if a=='伊拉克' else 'senegal_style' if a=='塞内加尔' else 'austria_style' if a=='奥地利' else 'algeria_style', '')
        h_vuln = mc.get(f'{h}_vulnerability', '')
        a_vuln = mc.get(f'{a}_vulnerability', '') if f'{a}_vulnerability' in mc else mc.get('iraq_vulnerability' if a=='伊拉克' else 'senegal_vulnerability' if a=='塞内加尔' else 'austria_vulnerability' if a=='奥地利' else 'algeria_vulnerability', '')

        # 跑模拟
        results = {
            'wins': 0, 'draws': 0, 'losses': 0,
            'scorelines': defaultdict(int),
            'total_goals': defaultdict(int),
            'h_goals_list': [],
            'a_goals_list': [],
            'xg_samples': [],
        }

        for _ in range(n):
            hg, ag, xh, xa = simulate_match(
                h_elo, a_elo, h_att, h_def, a_att, a_def,
                mot_h, mot_a, h_style, a_style, h_vuln, a_vuln
            )
            if hg > ag:
                results['wins'] += 1
            elif hg == ag:
                results['draws'] += 1
            else:
                results['losses'] += 1

            results['scorelines'][f"{hg}:{ag}"] += 1
            results['total_goals'][hg + ag] += 1
            results['h_goals_list'].append(hg)
            results['a_goals_list'].append(ag)
            results['xg_samples'].append((xh, xa))

        # 汇总
        avg_hg = sum(results['h_goals_list']) / n
        avg_ag = sum(results['a_goals_list']) / n
        avg_xh = sum(x[0] for x in results['xg_samples']) / n
        avg_xa = sum(x[1] for x in results['xg_samples']) / n

        top_scores = sorted(results['scorelines'].items(), key=lambda x: x[1], reverse=True)[:8]
        top_goals = sorted(results['total_goals'].items(), key=lambda x: x[0])

        # 进球分布统计
        h_goal_dist = defaultdict(int)
        a_goal_dist = defaultdict(int)
        for g in results['h_goals_list']:
            h_goal_dist[g] += 1
        for g in results['a_goals_list']:
            a_goal_dist[g] += 1

        summary = {
            'home': h, 'away': a,
            'elo_home': h_elo, 'elo_away': a_elo,
            'attack_home': h_att, 'defense_home': h_def,
            'attack_away': a_att, 'defense_away': a_def,
            'motivation_home': mot_h, 'motivation_away': mot_a,
            'qual_home': mc.get('qual_pressure_home', ''),
            'qual_away': mc.get('qual_pressure_away', ''),
            'style_home': h_style,
            'style_away': a_style,
            'vuln_home': h_vuln,
            'vuln_away': a_vuln,
            'key_players_home': mc.get(f'{h}_key_players', ''),
            'key_players_away': mc.get(f'{a}_key_players', '') if f'{a}_key_players' in mc else mc.get('iraq_key_players' if a=='伊拉克' else 'senegal_key_players' if a=='塞内加尔' else 'austria_key_players' if a=='奥地利' else 'algeria_key_players', ''),
            'simulations': n,
            'win_pct': round(results['wins'] / n * 100, 1),
            'draw_pct': round(results['draws'] / n * 100, 1),
            'loss_pct': round(results['losses'] / n * 100, 1),
            'avg_home_goals': round(avg_hg, 2),
            'avg_away_goals': round(avg_ag, 2),
            'avg_home_xg': round(avg_xh, 2),
            'avg_away_xg': round(avg_xa, 2),
            'top_scores': [(s, c, round(c/n*100, 1)) for s, c in top_scores],
            'goal_distribution': {str(k): round(v/n*100, 1) for k, v in top_goals},
            'h_goal_dist': {str(k): round(v/n*100, 1) for k, v in sorted(h_goal_dist.items())},
            'a_goal_dist': {str(k): round(v/n*100, 1) for k, v in sorted(a_goal_dist.items())},
            'over_25_pct': round(sum(1 for g in results['h_goals_list'] for ag in results['a_goals_list']
                                     if results['h_goals_list'].index(g) == results['a_goals_list'].index(ag)  # 这是个bug，修正如下
                                     ) / n * 100, 1),
        }

        # 修正 over_25 计算
        over_25 = sum(1 for i in range(n) if results['h_goals_list'][i] + results['a_goals_list'][i] > 2.5)
        summary['over_25_pct'] = round(over_25 / n * 100, 1)

        # BTTS (双方进球)
        btts = sum(1 for i in range(n) if results['h_goals_list'][i] > 0 and results['a_goals_list'][i] > 0)
        summary['btts_pct'] = round(btts / n * 100, 1)

        all_results[f"{h} vs {a}"] = summary

    return all_results


# ========================================
# HTML报告生成
# ========================================
def generate_html_report(all_results):
    cards_html = ""
    for match_name, r in all_results.items():
        h, a = r['home'], r['away']

        # 胜平负颜色
        w_color = "#22c55e" if r['win_pct'] > 50 else ("#f59e0b" if r['win_pct'] > 35 else "#ef4444")
        d_color = "#888"
        l_color = "#22c55e" if r['loss_pct'] > 50 else ("#f59e0b" if r['loss_pct'] > 35 else "#ef4444")

        # 信心评级
        if r['win_pct'] > 75:
            confidence = "🟢 高置信"
        elif r['win_pct'] > 60:
            confidence = "🟡 中等置信"
        elif r['win_pct'] > 45:
            confidence = "🟠 势均力敌"
        else:
            confidence = "🔴 不确定性高"

        # 比分TOP5
        score_rows = ""
        for s, cnt, pct in r['top_scores'][:5]:
            bar_w = pct * 3
            score_rows += f"<tr><td style='font-weight:bold;font-family:monospace;font-size:1.1em;color:#fbbf24;'>{s}</td><td>{cnt}/500</td><td>{pct}%</td><td><div style='width:{bar_w}px;height:16px;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:8px;'></div></td></tr>"

        # 总进球分布
        goal_rows = ""
        for g, pct in sorted(r['goal_distribution'].items(), key=lambda x: int(x[0])):
            bar_w = pct * 3
            goal_rows += f"<tr><td>{g}球</td><td>{pct}%</td><td><div style='width:{bar_w}px;height:12px;background:linear-gradient(90deg,#10b981,#34d399);border-radius:6px;'></div></td></tr>"

        cards_html += f"""
    <div style="background:#1e293b;border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #334155;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <span style="font-size:1.4em;font-weight:bold;color:#e2e8f0;">{h} vs {a}</span>
        <span style="font-size:0.85em;padding:4px 10px;border-radius:12px;background:#334155;color:#94a3b8;">{confidence}</span>
      </div>

      <!-- 出线状态 -->
      <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
        <span style="font-size:11px;padding:3px 8px;background:#064e3b;color:#34d399;border-radius:4px;">🏠 {r['qual_home']}</span>
        <span style="font-size:11px;padding:3px 8px;background:#7f1d1d;color:#fca5a5;border-radius:4px;">🚶 {r['qual_away']}</span>
      </div>

      <!-- 关键球员 -->
      <div style="font-size:11px;color:#94a3b8;margin-bottom:8px;line-height:1.6;">
        <div>⭐ {h}: {r['key_players_home']}</div>
        <div>⭐ {a}: {r['key_players_away']}</div>
      </div>

      <!-- 漏洞 -->
      <div style="font-size:10px;color:#94a3b8;margin-bottom:12px;line-height:1.5;">
        <div>🔻 {h}漏洞: {r['vuln_home']}</div>
        <div>🔻 {a}漏洞: {r['vuln_away']}</div>
      </div>

      <!-- 胜平负概率条 -->
      <div style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">{h}胜</span>
          <div style="flex:1;height:22px;background:#1e293b;border-radius:11px;overflow:hidden;border:1px solid #334155;">
            <div style="height:100%;width:{r['win_pct']}%;background:{w_color};border-radius:11px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
              <span style="font-size:11px;font-weight:bold;color:#0f172a;">{r['win_pct']}%</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">平局</span>
          <div style="flex:1;height:22px;background:#1e293b;border-radius:11px;overflow:hidden;border:1px solid #334155;">
            <div style="height:100%;width:{r['draw_pct']}%;background:#888;border-radius:11px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
              <span style="font-size:11px;font-weight:bold;color:#fff;">{r['draw_pct']}%</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:40px;font-size:12px;color:#94a3b8;">{a}胜</span>
          <div style="flex:1;height:22px;background:#1e293b;border-radius:11px;overflow:hidden;border:1px solid #334155;">
            <div style="height:100%;width:{r['loss_pct']}%;background:{l_color};border-radius:11px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
              <span style="font-size:11px;font-weight:bold;color:#fff;">{r['loss_pct']}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 关键指标 -->
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;">
        <div style="background:#0f172a;padding:8px 14px;border-radius:8px;text-align:center;">
          <div style="font-size:10px;color:#64748b;">平均进球</div>
          <div style="font-size:1.1em;font-weight:bold;color:#e2e8f0;">{r['avg_home_goals']} - {r['avg_away_goals']}</div>
        </div>
        <div style="background:#0f172a;padding:8px 14px;border-radius:8px;text-align:center;">
          <div style="font-size:10px;color:#64748b;">期望进球(xG)</div>
          <div style="font-size:1.1em;font-weight:bold;color:#e2e8f0;">{r['avg_home_xg']} - {r['avg_away_xg']}</div>
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

      <!-- 比分分布 -->
      <div style="margin-bottom:12px;">
        <div style="font-size:12px;font-weight:600;color:#94a3b8;margin-bottom:6px;">🎯 模拟500次比分TOP5</div>
        <table style="width:100%;border-collapse:collapse;">{score_rows}</table>
      </div>

      <!-- 总进球分布 -->
      <div>
        <div style="font-size:12px;font-weight:600;color:#94a3b8;margin-bottom:6px;">📊 总进球分布</div>
        <table style="width:100%;border-collapse:collapse;">{goal_rows}</table>
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>6/22 蒙特卡洛500次模拟 · 世界杯深度分析</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;max-width:800px;margin:0 auto}}
h1{{font-size:1.6em;font-weight:600;text-align:center;margin:16px 0;background:linear-gradient(135deg,#fbbf24,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.subtitle{{text-align:center;font-size:12px;color:#64748b;margin-bottom:20px}}
.disclaimer{{text-align:center;color:#475569;font-size:11px;padding:20px;line-height:1.6}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:12px 0}}
.stat-card{{background:#0f172a;padding:10px;border-radius:8px;text-align:center}}
.stat-label{{font-size:10px;color:#64748b}}
.stat-value{{font-size:1.1em;font-weight:bold;color:#e2e8f0;margin-top:2px}}
@media(max-width:500px){{body{{padding:10px}}h1{{font-size:1.3em}}}}
</style>
</head>
<body>
<h1>🎲 蒙特卡洛 500次模拟</h1>
<div class="subtitle">2026世界杯 · 6月22日四场比赛 · 整合ELO+风格+阵容+出线压力+漏洞分析<br>
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} · 每场独立模拟500次 · 泊松分布采样</div>

<div style="background:#1e3a5f;border:1px solid #2563eb;border-radius:12px;padding:16px;margin-bottom:20px;font-size:12px;color:#93c5fd;line-height:1.8;">
<b>🔬 模拟方法说明：</b><br>
① <b>ELO基础</b>：每队ELO评分决定基础实力差 → 转期望进球<br>
② <b>攻防系数</b>：攻击力/防守力系数修正（如法国攻击1.25×伊拉克防守0.6）<br>
③ <b>出线压力</b>：🔴生死战队×1.15战意加成，🟢出线在望队×0.95留力折扣<br>
④ <b>战术漏洞</b>：防守方特定漏洞（如转身慢、身后空档）→ 攻击方额外5-15%加成<br>
⑤ <b>随机扰动</b>：每场±15%随机波动 + 3%概率红牌/点球事件<br>
⑥ <b>泊松采样</b>：从期望进球通过泊松分布随机抽取实际进球数
</div>

{cards_html}

<div class="disclaimer">
⚠️ 所有数据为统计模型计算结果，仅供赛事数据研究参考，不构成任何建议。<br>
蒙特卡洛模拟基于概率模型，无法预测真实比赛中的突发因素（红牌、伤病、天气等）。<br>
理性观赛 ⚽
</div>
</body>
</html>"""
    return html


# ========================================
# 主流程
# ========================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎲 蒙特卡洛 500次模拟 · 6月22日四场比赛")
    print("=" * 60)

    matches = load_june22_matches()
    print(f"\n📋 已加载 {len(matches)} 场比赛：")
    for m in matches:
        mc = m.get('_mc_data', {})
        h, a = m['home'], m['away']
        qh = mc.get('qual_pressure_home', '?')
        qa = mc.get('qual_pressure_away', '?')
        print(f"   {m['date']} {h} vs {a} | 主场: {qh} | 客场: {qa}")

    print(f"\n⏳ 正在运行500次模拟...")
    results = run_monte_carlo(matches, n=500)
    print("✅ 模拟完成！\n")

    # 输出结果摘要
    for match_name, r in results.items():
        print(f"\n{'─'*50}")
        print(f"⚽ {match_name}")
        print(f"{'─'*50}")
        print(f"ELO: {r['elo_home']} vs {r['elo_away']} | 攻: {r['attack_home']}/{r['defense_home']} vs {r['attack_away']}/{r['defense_away']}")
        print(f"出线状态: {r['qual_home']} | {r['qual_away']}")
        print(f"战意系数: {r['motivation_home']} vs {r['motivation_away']}")
        print(f"\n📊 500次模拟结果：")
        print(f"   {r['home']}胜: {r['win_pct']}% | 平局: {r['draw_pct']}% | {r['away']}胜: {r['loss_pct']}%")
        print(f"   平均进球: {r['avg_home_goals']} - {r['avg_away_goals']} (xG: {r['avg_home_xg']} - {r['avg_away_xg']})")
        print(f"   大2.5球: {r['over_25_pct']}% | 双方进球: {r['btts_pct']}%")
        print(f"   最可能比分: {', '.join(f'{s}({pct}%)' for s, _, pct in r['top_scores'][:3])}")

    # 保存JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📁 JSON结果已保存: {OUTPUT_JSON}")

    # 生成HTML
    html = generate_html_report(results)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"📁 HTML报告已保存: {OUTPUT_HTML}")

    print(f"\n{'='*60}")
    print("✅ 全部完成！可以打开 mc_report.html 查看报告")
    print(f"{'='*60}")
