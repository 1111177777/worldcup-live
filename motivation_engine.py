"""
世界杯球队战意推演引擎 v1.0
=============================
三层架构：静态规则 → 量化打分 → 蒙特卡洛模拟
输出：每队战意标签 + 推理文案 + 前端卡片JSON

纯Python标准库，零第三方依赖。
"""

import json, math, random, os
from collections import defaultdict
from copy import deepcopy

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, "schedule.json")

# === 2026世界杯淘汰赛对阵表（小组位置 → 32强对手） ===
# 格式: (对手类型, 对手来源组/范围)
# 对手类型: W=小组第一, R=小组第二, T=小组第三
KNOCKOUT_PATHS = {
    # Round of 32
    "A1": {"r32": ("T", "C/E/F/H/I"),  "path": "上半区"},
    "A2": {"r32": ("R", "B"),          "path": "上半区"},
    "B1": {"r32": ("T", "E/F/G/I/J"),  "path": "上半区"},
    "B2": {"r32": ("R", "A"),          "path": "上半区"},
    "C1": {"r32": ("R", "F"),          "path": "下半区"},
    "C2": {"r32": ("R", "F"),          "path": "下半区"},  # 待核实
    "D1": {"r32": ("T", "B/E/F/I/J"),  "path": "下半区"},
    "D2": {"r32": ("R", "G"),          "path": "下半区"},
    "E1": {"r32": ("T", "A/B/C/D/F"),  "path": "上半区"},
    "E2": {"r32": ("R", "I"),          "path": "上半区"},
    "F1": {"r32": ("R", "C"),          "path": "下半区"},
    "F2": {"r32": ("R", "C"),          "path": "下半区"},  # 待核实
    "G1": {"r32": ("T", "A/E/H/I/J"),  "path": "下半区"},
    "G2": {"r32": ("R", "D"),          "path": "下半区"},
    "H1": {"r32": ("R", "J"),          "path": "下半区"},
    "H2": {"r32": ("R", "J"),          "path": "下半区"},  # 待核实
    "I1": {"r32": ("T", "C/D/F/G/H"),  "path": "上半区"},
    "I2": {"r32": ("R", "E"),          "path": "上半区"},
    "J1": {"r32": ("R", "H"),          "path": "下半区"},
    "J2": {"r32": ("R", "H"),          "path": "下半区"},  # 待核实
    "K1": {"r32": ("T", "D/E/I/J/L"),  "path": "下半区"},
    "K2": {"r32": ("R", "L"),          "path": "下半区"},
    "L1": {"r32": ("T", "E/H/I/J/K"),  "path": "上半区"},
    "L2": {"r32": ("R", "K"),          "path": "上半区"},
}

# TOP10 强队（综合Elo+FIFA+近年战绩）
TOP10 = {"阿根廷","法国","巴西","英格兰","西班牙","德国","葡萄牙","荷兰","意大利","乌拉圭"}

# ELO 数据（与 live_data.py 同步）
ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"意大利":1840,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"伊朗":1730,"澳大利亚":1710,"埃及":1720,"尼日利亚":1710,"科特迪瓦":1700,"喀麦隆":1690,"加纳":1680,"突尼斯":1670,"阿尔及利亚":1660,"南非":1640,"加拿大":1730,"哥斯达黎加":1680,"巴拿马":1640,"牙买加":1630,"沙特阿拉伯":1670,"卡塔尔":1650,"伊拉克":1620,"阿联酋":1610,"新西兰":1600,"巴拉圭":1720,"厄瓜多尔":1740,"智利":1760,"秘鲁":1730,"委内瑞拉":1680,"玻利维亚":1620,"波黑":1690,"塞尔维亚":1750,"丹麦":1800,"瑞典":1790,"挪威":1780,"波兰":1760,"乌克兰":1740,"土耳其":1750,"比利时":1830,"威尔士":1700,"苏格兰":1690,"捷克":1720,"罗马尼亚":1680,"斯洛伐克":1670,"匈牙利":1700,"希腊":1680,"佛得角":1580,"库拉索":1560,"约旦":1590,"乌兹别克斯坦":1610,"海地":1550,"瑞士":1830,"刚果民主共和国":1650,"奥地利":1760}

# ================================================================
# 第〇层：数据准备
# ================================================================

def load_match_data():
    with open(SCHEDULE, encoding='utf-8') as f:
        return json.load(f)

def build_group_standings(matches):
    """从赛程数据构建小组积分表。"""
    groups = defaultdict(lambda: defaultdict(lambda: {"pts":0,"gd":0,"gs":0,"gc":0,"p":0,"h2h":{}}))
    for m in matches:
        g = m["group"]
        h, a = m["home"], m["away"]
        for t in [h, a]:
            if t not in groups[g]:
                groups[g][t] = {"pts":0,"gd":0,"gs":0,"gc":0,"p":0,"h2h":{}}
        if m.get("result"):
            hg, ag = map(int, m["result"].split(":"))
            groups[g][h]["p"] += 1; groups[g][h]["gs"] += hg; groups[g][h]["gc"] += ag
            groups[g][a]["p"] += 1; groups[g][a]["gs"] += ag; groups[g][a]["gc"] += hg
            groups[g][h]["gd"] = groups[g][h]["gs"] - groups[g][h]["gc"]
            groups[g][a]["gd"] = groups[g][a]["gs"] - groups[g][a]["gc"]
            # H2H
            groups[g][h]["h2h"][a] = (hg, ag)
            groups[g][a]["h2h"][h] = (ag, hg)
            if hg > ag: groups[g][h]["pts"] += 3
            elif ag > hg: groups[g][a]["pts"] += 3
            else: groups[g][h]["pts"] += 1; groups[g][a]["pts"] += 1
    return dict(groups)

def get_remaining_matches(matches):
    """获取未赛的剩余小组赛。"""
    return [m for m in matches if not m.get("result") and m.get("status") != "FT"]

def rank_group(teams_dict):
    """按排名规则排序小组球队。优先级: 积分 > GD > GS > FIFA排名"""
    ranked = sorted(teams_dict.items(), key=lambda x: (
        -x[1]["pts"], -x[1]["gd"], -x[1]["gs"],
        -(ELO.get(x[0], 1600))
    ))
    return ranked

# ================================================================
# 第一层：静态规则判定
# ================================================================

def static_motivation(team, group_standings, remaining, group_name):
    """
    静态规则层：基于当前积分+剩余赛程做硬性判定。
    返回: (标签, 推理文本, 基础分数)
    """
    teams = group_standings[group_name]
    ranked = rank_group(teams)
    n_teams = len(ranked)
    max_pts_remaining = 6  # 每队最多还有6分可拿（2场比赛×3分）

    # 找当前球队位置
    pos = next(i for i, (t, _) in enumerate(ranked) if t == team)
    current_pts = teams[team]["pts"]
    current_gd = teams[team]["gd"]

    # 计算"可能被超越"的天花板
    can_overtake = []
    for i, (t, s) in enumerate(ranked):
        if t != team:
            max_possible = s["pts"] + (2 - s["p"]) * 3  # 剩余比赛全胜的最高分
            can_overtake.append((t, max_possible))

    # 自己最多能拿多少分
    played = teams[team]["p"]
    my_max = current_pts + (3 - played) * 3
    my_min = current_pts

    # Third place scenario
    third_place_pts = sorted([s["pts"] for _, s in ranked])[1] if n_teams >= 3 else 0

    # === 判定逻辑 ===
    label = ""; reasoning = []; scores = {}

    # 出线安全分 (0-100)
    if pos == 0:
        gap_to_3rd = current_pts - (ranked[2][1]["pts"] if n_teams >= 3 else 0)
        if gap_to_3rd >= 6 and played >= 2:
            safety = 100
            reasoning.append(f"已锁定小组前二出线（领先第三{ranked[2][0]}{gap_to_3rd}分）")
        elif gap_to_3rd >= 3 and played >= 2:
            safety = 85
            reasoning.append(f"领先第三{ranked[2][0]}{gap_to_3rd}分，再拿1分即锁定")
        elif gap_to_3rd >= 0 and played < 2:
            safety = 60
            reasoning.append(f"暂列第一但还有关键战未打")
        else:
            safety = 40
            reasoning.append(f"积分胶着，需全力抢分")
    elif pos == 1:
        gap_to_3rd = current_pts - (ranked[2][1]["pts"] if n_teams >= 3 else 0)
        if gap_to_3rd >= 4 and played >= 2:
            safety = 90
            reasoning.append(f"领先第三{gap_to_3rd}分，基本锁定出线")
        elif gap_to_3rd >= 1:
            safety = 65
            reasoning.append(f"领先第三仅{gap_to_3rd}分，需警惕")
        else:
            safety = 45
    elif pos == 2:
        gap_to_1st = ranked[0][1]["pts"] - current_pts
        third_pts = ranked[3][1]["pts"] if n_teams >= 4 else 0
        gap_to_4th = current_pts - third_pts
        safety = max(20, min(60, 30 + gap_to_4th * 10))
        if gap_to_4th <= 0:
            reasoning.append("第三名位置不稳，需全力抢分")
            safety = 25
        else:
            reasoning.append(f"小组第三，领先第四{third_pts}分")
    else:  # pos 3 (4th)
        gap_to_2nd = ranked[1][1]["pts"] - current_pts if n_teams >= 2 else 99
        if gap_to_2nd > 3:
            safety = 5
            reasoning.append("基本已淘汰或需要奇迹")
        else:
            safety = 20
            reasoning.append("需连胜且看他人脸色")

    scores["safety"] = safety

    # 头名收益分 (0-100)
    if pos == 0:
        # 已在第一名，看是否值得死守
        gap_to_2nd = current_pts - ranked[1][1]["pts"]
        if gap_to_2nd >= 4:
            first_benefit = 30  # 领先多，可以轻松打
            reasoning.append("领先第二名较多，可适度轮换")
        elif gap_to_2nd >= 1:
            first_benefit = 70  # 有被反超风险
            reasoning.append("仅领先1-3分，需力保第一")
        else:
            first_benefit = 90
            reasoning.append("与第二名积分相同，必须争胜保第一")
    elif pos == 1:
        gap_to_1st = ranked[0][1]["pts"] - current_pts
        if gap_to_1st > 3:
            first_benefit = 20  # 追不上
            reasoning.append(f"落后第一{gap_to_1st}分，争头名难度大")
        elif gap_to_1st > 0:
            first_benefit = 60
            reasoning.append(f"落后第一仅{gap_to_1st}分，仍有争头名可能")
        else:
            first_benefit = 80
    else:
        first_benefit = 5  # 第三/第四别想头名了
    scores["first_benefit"] = first_benefit

    # 轮换代价分 (0-100, 越高=越不该轮换)
    # 基于剩余比赛重要性
    if safety >= 90 and first_benefit <= 30:
        rotation_cost = 15
        reasoning.append("出线无忧+头名无忧，存在合理轮换空间")
    elif safety >= 80:
        rotation_cost = 35
        reasoning.append("出线基本无忧，可适度轮换替补")
    elif safety >= 50:
        rotation_cost = 70
        reasoning.append("出线形势尚可但未稳，轮换需谨慎")
    else:
        rotation_cost = 95
        reasoning.append("生死战，绝无轮换可能")
    scores["rotation_cost"] = rotation_cost

    # 净胜球刚需分 (0-100)
    if pos <= 1 and safety >= 80:
        gd_urgency = 10
    elif pos == 2 or (pos <= 1 and safety < 60):
        # 可能需要拼净胜球争第三出线
        gd_urgency = 65
        reasoning.append("同分情况下净胜球可能决定出线或名次")
    else:
        gd_urgency = 30
    scores["gd_urgency"] = gd_urgency

    # === 综合标签 ===
    if safety >= 90 and first_benefit <= 30:
        label = "🟢 可轮换"
        reasoning.insert(0, f"已锁定出线且头名无忧（安全分{safety}），存在适度轮换空间，但不会故意输球")
    elif safety >= 80 and first_benefit >= 60:
        label = "🔵 冲小组第一"
        reasoning.insert(0, f"出线无忧但需力保头名（头名收益{first_benefit}），淘汰赛避强逻辑驱动")
    elif safety >= 80 and first_benefit <= 40:
        label = "🟡 稳小组第二"
        reasoning.insert(0, f"头名难度大（收益{first_benefit}），稳守第二更为务实")
    elif safety <= 30:
        label = "🔴 生死死拼"
        reasoning.insert(0, f"出线形势严峻（安全分{safety}），必须全力争胜")
    elif safety <= 55:
        label = "🟠 全力抢分"
        reasoning.insert(0, f"出线形势胶着（安全分{safety}），每分必争")
    else:
        label = "🟡 稳健应战"
        reasoning.insert(0, f"形势中等，正常应战")

    return {
        "label": label,
        "scores": scores,
        "reasoning": "；".join(reasoning),
        "safety": safety,
        "first_benefit": first_benefit,
        "rotation_cost": rotation_cost,
        "gd_urgency": gd_urgency,
    }


# ================================================================
# 第二层：蒙特卡洛模拟
# ================================================================

def simulate_remaining_matches(remaining_matches, group_standings, n_sim=1000):
    """
    对剩余比赛做蒙特卡洛模拟。
    n_sim=1000 确保网页不卡顿（本地<0.5秒）。
    返回每队的淘汰赛对手强度统计。
    """
    # 收集小组所有球队
    all_teams = {}
    for g, teams in group_standings.items():
        for t in teams:
            all_teams[t] = g

    # ELO胜率模型
    def win_prob(h, a):
        eh = ELO.get(h, 1600); ea = ELO.get(a, 1600)
        return 1.0 / (1.0 + 10**(-(eh-ea)/400))

    # 结果统计
    team_stats = defaultdict(lambda: {
        "sims": 0, "finish_positions": defaultdict(int),
        "r32_opponent_top10": 0, "r32_opponent_list": [],
        "qualified": 0, "first_place": 0, "second_place": 0, "third_qualify": 0,
    })

    for _ in range(n_sim):
        # 深拷贝当前积分
        sim_standings = deepcopy(group_standings)

        # 模拟所有剩余比赛
        for m in remaining_matches:
            g = m["group"]; h, a = m["home"], m["away"]
            pw = win_prob(h, a)
            pd = 0.25  # 平局概率固定25%
            r = random.random()
            if r < pw * 0.75:
                hg = max(1, int(1.5 + random.gauss(0, 0.7)))
                ag = max(0, int(0.7 + random.gauss(0, 0.5)))
                if hg <= ag: hg = ag + 1
                sim_standings[g][h]["pts"] += 3
            elif r < pw * 0.75 + pd:
                hg = ag = max(0, int(1.0 + random.gauss(0, 0.5)))
                sim_standings[g][h]["pts"] += 1
                sim_standings[g][a]["pts"] += 1
            else:
                ag = max(1, int(1.5 + random.gauss(0, 0.7)))
                hg = max(0, int(0.7 + random.gauss(0, 0.5)))
                if ag <= hg: ag = hg + 1
                sim_standings[g][a]["pts"] += 3
            sim_standings[g][h]["gs"] += hg; sim_standings[g][h]["gc"] += ag
            sim_standings[g][a]["gs"] += ag; sim_standings[g][a]["gc"] += hg
            sim_standings[g][h]["gd"] = sim_standings[g][h]["gs"] - sim_standings[g][h]["gc"]
            sim_standings[g][a]["gd"] = sim_standings[g][a]["gs"] - sim_standings[g][a]["gc"]
            sim_standings[g][h]["p"] += 1; sim_standings[g][a]["p"] += 1

        # 排名
        group_ranks = {}
        group_thirds = []
        for g, teams in sim_standings.items():
            ranked = rank_group(teams)
            group_ranks[g] = ranked
            if len(ranked) >= 3:
                group_thirds.append((g, ranked[2]))

        # 第三名排序（取前8）
        thirds_ranked = sorted(group_thirds, key=lambda x: (
            -x[1][1]["pts"], -x[1][1]["gd"], -x[1][1]["gs"],
            -(ELO.get(x[1][0], 1600))
        ))
        third_qualifiers = set(t for t, _ in thirds_ranked[:8])

        # 记录统计
        for g, ranked in group_ranks.items():
            for pos, (team, _) in enumerate(ranked):
                ts = team_stats[team]
                ts["sims"] += 1
                ts["finish_positions"][pos] += 1

                if pos == 0:
                    ts["qualified"] += 1
                    ts["first_place"] += 1
                elif pos == 1:
                    ts["qualified"] += 1
                    ts["second_place"] += 1
                elif pos == 2 and team in third_qualifiers:
                    ts["qualified"] += 1
                    ts["third_qualify"] += 1

    # 计算概率
    results = {}
    for team, ts in team_stats.items():
        n = max(ts["sims"], 1)
        p1 = ts["first_place"] / n * 100
        p2 = ts["second_place"] / n * 100
        p_qual = ts["qualified"] / n * 100
        # 最常见名次
        most_common_pos = max(ts["finish_positions"].items(), key=lambda x: x[1])[0]

        results[team] = {
            "p_first": round(p1, 1),
            "p_second": round(p2, 1),
            "p_qualify": round(p_qual, 1),
            "most_likely_pos": most_common_pos,
            "n_sims": n,
        }
    return results


# ================================================================
# 第三层：综合输出（静态+蒙特卡洛叠加）
# ================================================================

def analyze_all_teams():
    """主函数：分析所有球队战意并输出结果。"""
    matches = load_match_data()
    groups = build_group_standings(matches)
    remaining = get_remaining_matches(matches)

    print(f"🏟 战意分析: {len(matches)}场, 剩余{len(remaining)}场")

    # 第一层：静态打分
    static_results = {}
    for g, teams in groups.items():
        for team in teams:
            static_results[team] = static_motivation(team, groups, remaining, g)

    # 第二层：蒙特卡洛（只有剩余比赛时才跑）
    mc_results = {}
    if remaining:
        print(f"🎲 蒙特卡洛模拟 1000次...")
        mc_results = simulate_remaining_matches(remaining, groups, n_sim=1000)
        print(f"   模拟完成，{len(mc_results)}队")
    else:
        # 无剩余比赛，用静态结果
        for team, sr in static_results.items():
            mc_results[team] = {
                "p_first": 100 if "第一" in sr["label"] else 0,
                "p_second": 100 if "第二" in sr["label"] else 0,
                "p_qualify": 100 if sr["safety"] > 50 else 0,
                "most_likely_pos": 0 if sr["safety"] > 60 else 1,
                "n_sims": 0,
            }

    # 构建 team → group 映射
    team_group = {}
    for g, teams in groups.items():
        for team in teams:
            team_group[team] = g

    # 叠加分析
    final = {}
    for team, sr in static_results.items():
        mc = mc_results.get(team, {})
        p1 = mc.get("p_first", 0)
        p2 = mc.get("p_second", 0)

        # 基于MC修正标签
        label = sr["label"]
        reasoning_extra = ""

        if "冲小组第一" in label:
            if p1 > 70:
                reasoning_extra = f"MC模拟：小组第一概率{p1:.0f}%，动力充足"
            elif p1 > 40:
                reasoning_extra = f"MC模拟：小组第一概率{p1:.0f}%，竞争激烈需全力冲刺"
            else:
                reasoning_extra = f"MC模拟：小组第一概率仅{p1:.0f}%，争头名难度大"
                label = label.replace("冲小组第一", "🟡 力拼头名但难度大")

        if "稳小组第二" in label and p2 > 60:
            reasoning_extra = f"MC模拟：小组第二概率{p2:.0f}%，形势稳定"

        if "生死死拼" in label:
            pq = mc.get("p_qualify", 0)
            reasoning_extra = f"MC模拟：出线概率{pq:.0f}%，{'希望尚存' if pq > 30 else '形势严峻'}"

        if "可轮换" in label:
            reasoning_extra = f"MC模拟：头名概率{p1:.0f}%，轮换空间确认存在"

        # 明确标注
        certainty = ""
        if "可轮换" in label:
            certainty = "⚠️ 此队存在轮换可能，但不会故意输球，只会换替补球员"
        elif "冲小组第一" in label or "生死死拼" in label:
            certainty = "✅ 此队绝无放水可能，战意100%"
        elif "稳小组第二" in label:
            certainty = "🟡 此队目标明确为保第二，不会冒进争头名"
        elif "稳健应战" in label or "全力抢分" in label:
            certainty = "✅ 正常应战，无放水迹象"

        final[team] = {
            "team": team,
            "group": team_group.get(team, "?"),
            "label": label,
            "scores": sr["scores"],
            "static_reasoning": sr["reasoning"],
            "mc_reasoning": reasoning_extra,
            "certificate": certainty,
            "p_first": p1,
            "p_second": p2,
            "p_qualify": mc.get("p_qualify", 0),
            "most_likely_pos": mc.get("most_likely_pos", 0),
        }

    return final


# ================================================================
# 前端卡片JSON生成
# ================================================================

def gen_frontend_json(results):
    """生成前端可直接渲染的JSON数据。"""
    cards = []
    for team, r in sorted(results.items()):
        s = r["scores"]
        cards.append({
            "team": team,
            "group": r["group"],
            "label": r["label"],
            "certificate": r["certificate"],
            "metrics": {
                "出线安全度": f'{s["safety"]}/100',
                "头名驱动力": f'{s["first_benefit"]}/100',
                "轮换可能性": f'{100-s["rotation_cost"]}/100',
                "净胜球紧迫度": f'{s["gd_urgency"]}/100',
            },
            "mc_probs": {
                "小组第一": f'{r["p_first"]:.0f}%',
                "小组第二": f'{r["p_second"]:.0f}%',
                "晋级淘汰赛": f'{r["p_qualify"]:.0f}%',
            },
            "reasoning": r["static_reasoning"] + (" | " + r["mc_reasoning"] if r["mc_reasoning"] else ""),
        })
    return cards


# ================================================================
# HTML 战意卡片生成（嵌入logic_analysis页面）
# ================================================================

CSS_MOTIVATION = '''
.moti-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.moti-card{border:1px solid #eee;border-radius:4px;padding:8px;background:#fafafa;font-size:10px}
.moti-card .mh{display:flex;align-items:center;gap:4px;margin-bottom:3px}
.moti-card .ml{font-size:9px;padding:1px 6px;border-radius:3px;font-weight:600}
.ml-fight{background:#ffebee;color:#c62828}
.ml-push{background:#e3f2fd;color:#1565c0}
.ml-hold{background:#fff8e1;color:#f57f17}
.ml-rest{background:#e8f5e9;color:#2e7d32}
.ml-normal{background:#f5f5f5;color:#666}
.moti-card .mt{font-weight:600;color:#111;font-size:10px}
.moti-card .mm{display:flex;gap:8px;margin:4px 0;font-size:9px;color:#666}
.moti-card .mr{font-size:8px;color:#999;line-height:1.4}
.moti-card .mc{font-size:8px;color:#999;margin-top:2px}
@media(max-width:700px){.moti-grid{grid-template-columns:1fr}}
'''

def gen_motivation_html(results, top_n=24):
    """生成战意卡片HTML片段。"""
    # 优先展示"生死死拼"和"冲小组第一"
    priority_order = {"🔴 生死死拼": 0, "🟠 全力抢分": 1, "🔵 冲小组第一": 2,
                      "🟡 力拼头名但难度大": 3, "🟡 稳小组第二": 4,
                      "🟢 可轮换": 5, "🟡 稳健应战": 6}
    sorted_teams = sorted(results.items(),
                          key=lambda x: (priority_order.get(x[1]["label"].split("（")[0].strip(), 99),
                                         -x[1]["p_qualify"]))

    cards = ""
    for team, r in sorted_teams[:top_n]:
        s = r["scores"]
        # 标签样式
        label_text = r["label"]
        if "死拼" in label_text: cls = "ml-fight"
        elif "冲小组第一" in label_text or "力拼" in label_text: cls = "ml-push"
        elif "稳小组第二" in label_text or "稳健" in label_text: cls = "ml-hold"
        elif "可轮换" in label_text: cls = "ml-rest"
        else: cls = "ml-normal"

        cards += f'''<div class="moti-card">
<div class="mh"><span class="ml {cls}">{label_text.split('（')[0].strip()}</span>
<span class="mt">{team}</span><span style="font-size:8px;color:#999">{r["group"]}组</span></div>
<div class="mm">
<span>安全{r["scores"]["safety"]}</span><span>头名{r["scores"]["first_benefit"]}</span>
<span>轮换{100-r["scores"]["rotation_cost"]}</span>
</div>
<div class="mr">{r["static_reasoning"][:80]}...</div>
<div class="mc">MC: 头名{r["p_first"]:.0f}% 第二{r["p_second"]:.0f}% 晋级{r["p_qualify"]:.0f}% | {r["certificate"][:30]}</div>
</div>'''
    return cards


# ================================================================
# CLI 入口
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("球队战意推演引擎 v1.0")
    print("=" * 60)

    results = analyze_all_teams()

    # 分类统计
    cats = defaultdict(list)
    for team, r in results.items():
        lb = r["label"].split("（")[0].strip()
        cats[lb].append(team)

    print("\n📊 战意分类:")
    for cat, teams in sorted(cats.items()):
        print(f"  {cat}: {len(teams)}队 → {', '.join(teams[:6])}{'...' if len(teams)>6 else ''}")

    # 重点关注
    print("\n🔴 生死死拼球队:")
    for t in cats.get("🔴 生死死拼", []):
        r = results[t]
        print(f"  {t}({r['group']}组): 安全分{r['scores']['safety']} | 晋级率{r['p_qualify']:.0f}% | {r['static_reasoning'][:60]}")

    print("\n🟢 可轮换球队:")
    for t in cats.get("🟢 可轮换", []):
        r = results[t]
        print(f"  {t}({r['group']}组): {r['certificate']}")

    # 输出前端JSON
    cards = gen_frontend_json(results)
    print(f"\n✅ 生成{len(cards)}张战意卡片JSON")
    print(f"   示例: {json.dumps(cards[0], ensure_ascii=False, indent=2)[:200]}")
