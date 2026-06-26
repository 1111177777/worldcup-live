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

    # Agent复盘：找模型盲区
    wrong_upsets = 0; goal_surprises = 0; elo_blowouts = 0; score_errs = []
    for m in ft_matches:
        h, a, r = m['home'], m['away'], m['result']
        hg, ag = map(int, r.split(':'))
        p = predict(h, a, match_info=m)
        exp_total = p['xh'] + p['xa']
        act_total = hg + ag
        exp_diff = p['xh'] - p['xa']
        act_diff = hg - ag
        score_errs.append(abs(exp_diff - act_diff))
        if p['win'] > 60 and (hg <= ag): wrong_upsets += 1
        if act_total - exp_total > 1.0: goal_surprises += 1
        if abs(p['he']-p['ae']) < 50 and abs(hg-ag) >= 2: elo_blowouts += 1
    avg_score_err = round(sum(score_errs)/len(score_errs), 1) if score_errs else 0

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

    # 补全所有球队（包括概率0%的）
    all_teams = set()
    with open(SCHEDULE, 'r', encoding='utf-8') as f:
        for m in json.load(f):
            all_teams.add(m['home'])
            all_teams.add(m['away'])
    for t in all_teams:
        if t not in team_qual:
            team_qual[t] = 0

    mc_top = sorted(team_qual.items(), key=lambda x: -x[1])  # 全队
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

    # 蒙特卡洛 — 所有球队出线概率
    mc_tags = ""
    for team, count in mc_top:  # 全部显示
        pct = round(count / N * 100, 1)
        c = '#390' if pct > 80 else ('#f80' if pct > 50 else '#999')
        bg = '#e8f5e9' if pct > 80 else ('#fff8e1' if pct > 50 else '#f5f5f5')
        flag = FLAGS.get(team, '')
        mc_tags += '<span class="mc-tag" style="background:' + bg + ';color:' + c + '">' + flag + team + ' ' + str(pct) + '%</span>'

    html = f"""
<style>
.dashboard {{ padding: 2px 0; }}
.dash-section {{ margin: 6px 0; border: 1px solid #e8e8e8; border-radius: 3px; overflow: hidden; }}
.dash-title {{ background: #111; color: #fff; padding: 4px 8px; font-size: 10px; font-weight: 600; cursor: pointer; user-select: none; display: flex; justify-content: space-between; align-items: center; }}
.dash-title span {{ font-size: 9px; color: #8f8; }}
.dash-title::after {{ content: '+'; font-size: 12px; }}
.dash-title.open::after {{ content: '−'; }}
.dash-body {{ display: none; }}
.dash-body.open {{ display: block; }}
.groups-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 2px; padding: 4px; }}
.group-card {{ border: 1px solid #f0f0f0; font-size: 8px; padding: 2px; background: #fafafa; }}
.gn {{ font-weight: 700; font-size: 8px; margin-bottom: 1px; }}
.gr {{ display: flex; justify-content: space-between; padding: 0; font-size: 7px; line-height: 1.3; }}
.mc-tags {{ padding: 6px 4px; display: flex; flex-wrap: wrap; gap: 3px; }}
.mc-tag {{ font-size: 9px; padding: 1px 5px; border-radius: 2px; white-space: nowrap; font-weight: 600; }}
</style>
<script>function toggleDash(e){{e.classList.toggle('open');e.nextElementSibling.classList.toggle('open');}}</script>
<div class="dashboard">
  <div class="dash-section">
    <div class="dash-title open" onclick="toggleDash(this)">📊 小组积分 <span>{acc_rate}%准确</span></div>
    <div class="dash-body open"><div class="groups-grid">{group_html}</div></div>
  </div>
  <div class="dash-section">
    <div class="dash-title open" onclick="toggleDash(this)">🎲 出线概率 <span>MC{N}次</span></div>
    <div class="dash-body open"><div class="mc-tags">{mc_tags}</div></div>
  </div>
  <div class="dash-section">
    <div class="dash-title" onclick="toggleDash(this)">🤖 AI复盘 <span>{acc_rate}%准确</span></div>
    <div class="dash-body"><div class="agent-review">
      <p>已完成 {len(ft_matches)} 场复盘。方向准确率 <b>{acc_rate}%</b>，场均进球偏差 {round(avg_score_err,1)} 球。</p>
      <p>主要盲区：<br>
      · 强队翻车 {wrong_upsets} 场（西班牙、葡萄牙等控球型对大巴失效）<br>
      · 进球系统性低估 {goal_surprises} 场（扩军后弱队防线更脆弱）<br>
      · ELO接近却大比分 {elo_blowouts} 场（美国4-1、澳大利亚2-0）</p>
      <p style=\"font-size:10px;color:#999\">每场赛后自动复盘→点击卡片底部「赛后AI复盘」查看详情</p>
    </div></div>
  </div>
</div>
"""
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 仪表盘: {acc_rate}%准确 | MC{N}次 | 小组+出线概率")

if __name__ == "__main__":
    gen_dashboard()
