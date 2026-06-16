"""
世界杯仪表盘：小组积分 + 模型准确率 + 蒙特卡洛出线概率
用法：python dashboard.py → 生成 dashboard.html 片段
"""
import json, math, random, os
from live_data import predict

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, "schedule.json")
OUTPUT = os.path.join(DIR, "dashboard.html")

def gen_dashboard():
    with open(SCHEDULE, 'r', encoding='utf-8') as f:
        matches = json.load(f)

    # ===== 小组积分 =====
    groups = {}
    for m in matches:
        g = m['group']
        if g not in groups: groups[g] = {}
        for t in [m['home'], m['away']]:
            if t not in groups[g]: groups[g][t] = {'pts': 0, 'gd': 0, 'gs': 0, 'gc': 0, 'p': 0}
        if m.get('result'):
            hg, ag = map(int, m['result'].split(':'))
            groups[g][m['home']]['p'] += 1; groups[g][m['away']]['p'] += 1
            groups[g][m['home']]['gs'] += hg; groups[g][m['home']]['gc'] += ag
            groups[g][m['away']]['gs'] += ag; groups[g][m['away']]['gc'] += hg
            groups[g][m['home']]['gd'] = groups[g][m['home']]['gs'] - groups[g][m['home']]['gc']
            groups[g][m['away']]['gd'] = groups[g][m['away']]['gs'] - groups[g][m['away']]['gc']
            if hg > ag: groups[g][m['home']]['pts'] += 3
            elif ag > hg: groups[g][m['away']]['pts'] += 3
            else: groups[g][m['home']]['pts'] += 1; groups[g][m['away']]['pts'] += 1

    # ===== 模型准确率 =====
    ft_matches = [m for m in matches if m.get('status') == 'FT']
    correct = 0
    for m in ft_matches:
        h, a, r = m['home'], m['away'], m['result']
        hg, ag = map(int, r.split(':'))
        p = predict(h, a)
        pred = 'win' if p['win'] > max(p['draw'], p['loss']) else ('draw' if p['draw'] > max(p['win'], p['loss']) else 'loss')
        actual = 'win' if hg > ag else ('draw' if hg == ag else 'loss')
        if pred == actual: correct += 1
    acc_rate = round(correct / len(ft_matches) * 100, 1) if ft_matches else 0

    # ===== 蒙特卡洛小组出线概率 =====
    N = 3000
    team_qual = {}
    remaining = [m for m in matches if not m.get('result') and m.get('status') != 'FT']
    for _ in range(N):
        sim = {g: {t: {'pts': s['pts'], 'gd': s['gd']} for t, s in teams.items()} for g, teams in groups.items()}
        for m in remaining:
            g = m['group']
            p = predict(m['home'], m['away'])
            r = random.random()
            if r < p['win'] / 100:
                hg = max(1, int(p['xh'] + random.gauss(0, 0.5)))
                ag = max(0, int(p['xa'] + random.gauss(0, 0.5)))
                if hg <= ag: hg = ag + 1
                sim[g][m['home']]['pts'] += 3
            elif r < (p['win'] + p['draw']) / 100:
                hg = ag = max(0, int((p['xh'] + p['xa']) / 2))
                sim[g][m['home']]['pts'] += 1; sim[g][m['away']]['pts'] += 1
            else:
                ag = max(1, int(p['xa'] + random.gauss(0, 0.5)))
                hg = max(0, int(p['xh'] + random.gauss(0, 0.5)))
                if ag <= hg: ag = hg + 1
                sim[g][m['away']]['pts'] += 3
            sim[g][m['home']]['gd'] += hg - ag; sim[g][m['away']]['gd'] += ag - hg
        for g in sorted(sim.keys()):
            for team, _ in sorted(sim[g].items(), key=lambda x: (-x[1]['pts'], -x[1]['gd']))[:2]:
                team_qual[team] = team_qual.get(team, 0) + 1

    mc_top = sorted(team_qual.items(), key=lambda x: -x[1])[:20]
    FLAGS = {
        "阿根廷": "🇦🇷", "法国": "🇫🇷", "巴西": "🇧🇷", "英格兰": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "西班牙": "🇪🇸",
        "葡萄牙": "🇵🇹", "德国": "🇩🇪", "荷兰": "🇳🇱", "意大利": "🇮🇹", "乌拉圭": "🇺🇾",
        "克罗地亚": "🇭🇷", "哥伦比亚": "🇨🇴", "摩洛哥": "🇲🇦", "美国": "🇺🇸", "墨西哥": "🇲🇽",
        "塞内加尔": "🇸🇳", "日本": "🇯🇵", "韩国": "🇰🇷", "伊朗": "🇮🇷", "澳大利亚": "🇦🇺",
        "加拿大": "🇨🇦", "巴拉圭": "🇵🇾", "厄瓜多尔": "🇪🇨", "智利": "🇨🇱", "秘鲁": "🇵🇪",
        "波黑": "🇧🇦", "塞尔维亚": "🇷🇸", "丹麦": "🇩🇰", "瑞典": "🇸🇪", "挪威": "🇳🇴",
        "波兰": "🇵🇱", "乌克兰": "🇺🇦", "土耳其": "🇹🇷", "比利时": "🇧🇪", "捷克": "🇨🇿",
        "卡塔尔": "🇶🇦", "瑞士": "🇨🇭", "奥地利": "🇦🇹", "苏格兰": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "埃及": "🇪🇬", "南非": "🇿🇦", "科特迪瓦": "🇨🇮", "加纳": "🇬🇭", "突尼斯": "🇹🇳",
        "阿尔及利亚": "🇩🇿", "刚果民主共和国": "🇨🇩", "喀麦隆": "🇨🇲", "尼日利亚": "🇳🇬",
        "佛得角": "🇨🇻", "库拉索": "🇨🇼", "海地": "🇭🇹", "巴拿马": "🇵🇦",
        "沙特阿拉伯": "🇸🇦", "阿联酋": "🇦🇪", "伊拉克": "🇮🇶", "约旦": "🇯🇴",
        "乌兹别克斯坦": "🇺🇿", "新西兰": "🇳🇿", "希腊": "🇬🇷", "威尔士": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    }

    # ===== 生成 HTML =====
    # 小组积分
    group_html = ""
    for g in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
        teams = sorted(groups[g].items(), key=lambda x: (-x[1]['pts'], -x[1]['gd'], -x[1]['gs']))
        group_html += f'<div class="group-card"><div class="gn">{g}组</div>'
        for i, (team, s) in enumerate(teams):
            flag = FLAGS.get(team, '')
            bold = 'style="font-weight:700"' if i < 2 else ''
            group_html += f'<div class="gr" {bold}><span>{flag} {team}</span><span>{s["p"]}场 {s["pts"]}分 {s["gd"]:+d}</span></div>'
        group_html += '</div>'

    # 蒙特卡洛 TOP10
    mc_html = ""
    for team, count in mc_top[:10]:
        pct = round(count / N * 100, 1)
        bar = '█' * max(1, int(pct / 2))
        mc_html += f'<div class="mc-row"><span class="mc-team">{FLAGS.get(team, "")} {team}</span><span class="mc-bar">{bar}</span><span class="mc-pct">{pct}%</span></div>'

    html = f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>
.dashboard {{ padding: 8px 0; }}
.dash-section {{ margin: 12px 0; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden; }}
.dash-title {{ background: #111; color: #fff; padding: 6px 10px; font-size: 12px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }}
.dash-title span {{ font-size: 10px; color: #0f0; }}
.groups-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 8px; }}
.group-card {{ border: 1px solid #eee; font-size: 10px; padding: 4px; }}
.gn {{ font-weight: 700; font-size: 11px; margin-bottom: 3px; }}
.gr {{ display: flex; justify-content: space-between; padding: 1px 0; }}
.mc-row {{ display: flex; align-items: center; padding: 4px 10px; gap: 8px; font-size: 12px; }}
.mc-team {{ min-width: 80px; }}
.mc-bar {{ flex: 1; color: #390; font-size: 10px; letter-spacing: -1px; }}
.mc-pct {{ font-weight: 700; min-width: 40px; text-align: right; }}
</style>
<div class="dashboard">
  <div class="dash-section">
    <div class="dash-title">📊 小组积分 <span>{acc_rate}%准确 · MC{N}次</span></div>
    <div class="groups-grid">{group_html}</div>
  </div>
  <div class="dash-section">
    <div class="dash-title">🎲 出线概率 TOP10</div>
    {mc_html}
  </div>
</div>
"""
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 仪表盘: {acc_rate}%准确 | MC{N}次 | 小组+出线概率")

if __name__ == "__main__":
    gen_dashboard()
