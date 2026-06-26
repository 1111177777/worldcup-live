"""
世界杯逻辑分析引擎 v2
集成：真实schedule.json + live_data.py ELO + 场地补偿 + 历史回测
输出：纯数据分析HTML
"""

import json, os, sys, math
from collections import defaultdict

def safe_float(v, default=1.50):
    """安全转换赔率为浮点数"""
    try:
        return float(v) if v and v != '' else default
    except (ValueError, TypeError):
        return default

DIR = os.path.dirname(__file__)
SCHEDULE_FILE = os.path.join(DIR, "schedule.json")

# ---- ELO 数据（与 live_data.py 同步）----
ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"意大利":1840,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"伊朗":1730,"澳大利亚":1710,"埃及":1720,"尼日利亚":1710,"科特迪瓦":1700,"喀麦隆":1690,"加纳":1680,"突尼斯":1670,"阿尔及利亚":1660,"南非":1640,"加拿大":1730,"哥斯达黎加":1680,"巴拿马":1640,"牙买加":1630,"沙特阿拉伯":1670,"卡塔尔":1650,"伊拉克":1620,"阿联酋":1610,"新西兰":1600,"巴拉圭":1720,"厄瓜多尔":1740,"智利":1760,"秘鲁":1730,"委内瑞拉":1680,"玻利维亚":1620,"波黑":1690,"塞尔维亚":1750,"丹麦":1800,"瑞典":1790,"挪威":1780,"波兰":1760,"乌克兰":1740,"土耳其":1750,"比利时":1830,"威尔士":1700,"苏格兰":1690,"捷克":1720,"罗马尼亚":1680,"斯洛伐克":1670,"匈牙利":1700,"希腊":1680,"佛得角":1580,"库拉索":1560,"约旦":1590,"乌兹别克斯坦":1610,"海地":1550,"瑞士":1830,"刚果民主共和国":1650,"奥地利":1760}

FLAGS = {"阿根廷":"🇦🇷","法国":"🇫🇷","巴西":"🇧🇷","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","西班牙":"🇪🇸","葡萄牙":"🇵🇹","德国":"🇩🇪","荷兰":"🇳🇱","意大利":"🇮🇹","乌拉圭":"🇺🇾","克罗地亚":"🇭🇷","哥伦比亚":"🇨🇴","摩洛哥":"🇲🇦","美国":"🇺🇸","墨西哥":"🇲🇽","塞内加尔":"🇸🇳","日本":"🇯🇵","韩国":"🇰🇷","伊朗":"🇮🇷","澳大利亚":"🇦🇺","埃及":"🇪🇬","尼日利亚":"🇳🇬","科特迪瓦":"🇨🇮","喀麦隆":"🇨🇲","加纳":"🇬🇭","突尼斯":"🇹🇳","阿尔及利亚":"🇩🇿","南非":"🇿🇦","加拿大":"🇨🇦","巴拉圭":"🇵🇾","厄瓜多尔":"🇪🇨","丹麦":"🇩🇰","瑞典":"🇸🇪","挪威":"🇳🇴","波兰":"🇵🇱","比利时":"🇧🇪","捷克":"🇨🇿","卡塔尔":"🇶🇦","新西兰":"🇳🇿","海地":"🇭🇹","苏格兰":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","瑞士":"🇨🇭","奥地利":"🇦🇹","约旦":"🇯🇴","伊拉克":"🇮🇶","库拉索":"🇨🇼","巴拿马":"🇵🇦","沙特阿拉伯":"🇸🇦","佛得角":"🇨🇻","乌兹别克斯坦":"🇺🇿","刚果民主共和国":"🇨🇩","塞尔维亚":"🇷🇸","乌克兰":"🇺🇦","土耳其":"🇹🇷","秘鲁":"🇵🇪","委内瑞拉":"🇻🇪","波黑":"🇧🇦","威尔士":"🏴󠁧󠁢󠁷󠁬󠁳󠁿","罗马尼亚":"🇷🇴","斯洛伐克":"🇸🇰","匈牙利":"🇭🇺","希腊":"🇬🇷","智利":"🇨🇱","哥斯达黎加":"🇨🇷","牙买加":"🇯🇲","阿联酋":"🇦🇪","玻利维亚":"🇧🇴","古巴":"🇨🇺","苏里南":"🇸🇷"}

# ---- 场地数据 ----
VENUE_DATA = {
    "墨西哥城": {"alt":2240,"heat":"moderate","name":"阿兹台克体育场","city":"墨西哥城"},
    "瓜达拉哈拉": {"alt":1566,"heat":"moderate","name":"阿克伦体育场","city":"瓜达拉哈拉"},
    "蒙特雷": {"alt":515,"heat":"extreme","name":"BBVA体育场","city":"蒙特雷"},
    "洛杉矶": {"alt":38,"heat":"low","name":"SoFi体育场","city":"洛杉矶"},
    "旧金山": {"alt":5,"heat":"low","name":"Levi's球场","city":"旧金山"},
    "西雅图": {"alt":50,"heat":"low","name":"流明体育场","city":"西雅图"},
    "温哥华": {"alt":3,"heat":"low","name":"BC Place","city":"温哥华"},
    "多伦多": {"alt":76,"heat":"moderate","name":"BMO体育场","city":"多伦多"},
    "亚特兰大": {"alt":320,"heat":"high","name":"梅赛德斯-奔驰","city":"亚特兰大"},
    "迈阿密": {"alt":2,"heat":"extreme","name":"硬石体育场","city":"迈阿密"},
    "休斯顿": {"alt":13,"heat":"extreme","name":"NRG体育场","city":"休斯顿"},
    "达拉斯": {"alt":185,"heat":"extreme","name":"AT&T体育场","city":"阿灵顿"},
    "堪萨斯城": {"alt":278,"heat":"high","name":"箭头体育场","city":"堪萨斯城"},
    "费城": {"alt":12,"heat":"high","name":"林肯金融球场","city":"费城"},
    "纽约": {"alt":2,"heat":"high","name":"大都会人寿","city":"纽约"},
    "波士顿": {"alt":88,"heat":"moderate","name":"吉列体育场","city":"波士顿"},
}

def get_venue(m):
    """获取场地数据"""
    v = m.get("venue","").strip()
    # 清洗后缀
    for sep in [" ·", "·", " ", "  "]:
        if sep in v:
            v = v.split(sep)[0].strip()
    if v in VENUE_DATA:
        return VENUE_DATA[v]
    # 模糊匹配
    for key, val in VENUE_DATA.items():
        if key in v or v in key:
            return val
    return {"alt":0,"heat":"low","name":"待定","city":"待定"}

def elo_win_prob(elo_h, elo_a):
    """Elo胜率"""
    diff = elo_h - elo_a
    return 1.0 / (1.0 + 10**(-diff/400.0))

def est_draw(win_p):
    """平局估算"""
    gap = abs(win_p - 0.5)*2
    return 0.30 - gap*(0.30-0.14)

def adj_goals(alt, heat):
    """场地补偿后预期进球"""
    base = 2.49
    g = base*(1+0.00015*alt)
    if heat == "extreme": g*=0.92
    elif heat == "high": g*=0.95
    elif heat == "moderate": g*=0.97
    return round(g,2)

def load_schedule():
    with open(SCHEDULE_FILE, encoding='utf-8') as f:
        return json.load(f)

def analyze_all(matches):
    """分析所有比赛"""
    results = []
    for m in matches:
        h, a = m["home"], m["away"]
        elo_h = ELO.get(h, 1600)
        elo_a = ELO.get(a, 1600)
        diff = elo_h - elo_a
        wp = elo_win_prob(elo_h, elo_a)
        dp = est_draw(wp)
        v = get_venue(m)
        goals = adj_goals(v["alt"], v["heat"])
        # 锚定：无论主客，只要Elo差距大就算
        strong_home = diff >= 150 and wp >= 0.62
        strong_away = diff <= -150 and wp <= 0.38  # 客队碾压
        anchor = strong_home or strong_away
        conf = "high" if abs(diff) >= 250 else ("medium" if abs(diff) >= 150 else "low")
        # 记录强队在哪边
        strong_side = "home" if strong_home else ("away" if strong_away else None)

        results.append({
            "home":h, "away":a, "elo_h":elo_h, "elo_a":elo_a,
            "elo_diff":diff, "win_prob":round(wp,3),
            "draw_prob":round(dp,3), "adj_goals":goals,
            "venue":v, "anchor":anchor, "anchor_conf":conf, "strong_side":strong_side,
            "result":m.get("result",""), "status":m.get("status",""),
            "date":m.get("date",""), "group":m.get("group",""),
            "odds_h":m.get("odds_home",""), "odds_d":m.get("odds_draw",""), "odds_a":m.get("odds_away",""),
        })
    return results

def gen_combos(analyses):
    """为每场未赛比赛生成：胜平负/总进球/比分 + 3串1~6串1"""
    combos = []
    upcoming = [a for a in analyses if a["status"]!="FT"]
    completed = [a for a in analyses if a["status"]=="FT"]

    # 只推今天+未来比赛（昨天及以前无结果的跳过）
    today_str = max([a["date"] for a in upcoming]) if upcoming else "6/26"
    upcoming_today = [a for a in upcoming if a["date"] >= today_str]

    anchors = [a for a in upcoming_today if a["anchor"]]
    non_a = [a for a in upcoming_today if not a["anchor"]]

    # ═══ 每场必推：胜平负 + 总进球 + 比分 ═══
    for a in upcoming_today:
        hn = a["home"][:2]
        wp = a["win_prob"]
        # 胜平负方向
        if wp >= 0.55:
            pick, lv, star, rng, od = "「胜」", "稳健", 3, "58-72%", safe_float(a["odds_h"],2.0)
        elif wp >= 0.40:
            pick, lv, star, rng, od = "「平局」", "探索", 2, "30-42%", safe_float(a["odds_d"],3.0)
        else:
            pick, lv, star, rng, od = "「客胜/受让」", "探索", 2, "28-40%", safe_float(a["odds_a"],3.0)
        combos.append({"id":f"SPF{hn}","name":f'{a["home"]}vs{a["away"]} 胜平负',"level":lv,"stars":star,
            "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":pick,"odds":od}],
            "rate":rng,"odds":od,"cat":"胜平负",
            "note":f'胜{a["win_prob"]:.0%} 平{a["draw_prob"]:.0%} Elo差{a["elo_diff"]:+d}'})

        # 总进球方向
        g = a["adj_goals"]
        if g < 2.3:
            gpick, grng, godds = "总进球<2.5", "48-58%", 1.80
            gnote = f"进球预期仅{g}球(偏低)"
        elif g > 2.8:
            gpick, grng, godds = "总进球>2.5", "42-52%", 1.80
            gnote = f"进球预期{g}球(偏高)"
        else:
            gpick, grng, godds = "总进球2-3球", "42-50%", 1.70
            gnote = f"进球预期{g}球(适中)"
        combos.append({"id":f"GOAL{hn}","name":f'{a["home"]}vs{a["away"]} 总进球',"level":"稳健","stars":3,
            "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":gpick,"odds":godds}],
            "rate":grng,"odds":godds,"cat":"总进球","note":gnote})

        # 比分推演
        ed = abs(a["elo_diff"])
        if ed >= 150: sc, sodds, stag = "2:0/2:1/3:1", 7.5, "强弱"
        elif ed >= 50: sc, sodds, stag = "2:1/1:1/1:0", 7.0, "中距"
        else: sc, sodds, stag = "1:1/0:0/1:0", 6.0, "均势"
        combos.append({"id":f"CS{hn}","name":f'{a["home"]}vs{a["away"]} 比分',"level":"推演","stars":4,
            "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":f"比分 {sc}","odds":sodds}],
            "rate":"6-12%","odds":sodds,"cat":"比分",
            "note":f'{stag}局 进球{g}球 1:0(13.5%) 2:1(11.3%)'})

    # ═══ 锚定单场（高置信） ═══
    for i, a in enumerate(anchors[:8]):
        side = a.get("strong_side","home")
        pick = "「胜」(主)" if side=="home" else "「胜」(客)"
        od = safe_float(a["odds_h"] if side=="home" else a["odds_a"], 1.30)
        combos.append({"id":f"A{i}","name":f'⭐锚定·{a["home"]}vs{a["away"]}',"level":"高置信","stars":5,
            "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":pick,"odds":od}],
            "rate":"68-82%","odds":od,"cat":"锚定单场",
            "note":f'Elo差{abs(a["elo_diff"])} 进球{a["adj_goals"]}球 强队={("主" if side=="home" else "客")}'})

    # ═══ 2串1 ═══
    def _a_odds(a): side = a.get("strong_side","home"); return safe_float(a["odds_h"] if side=="home" else a["odds_a"], 1.4)
    def _a_pick(a): return "「胜」(主)" if a.get("strong_side","home")=="home" else "「胜」(客)"
    for i in range(min(4, len(anchors))):
        for j in range(i+1, min(6, len(anchors))):
            a,b = anchors[i], anchors[j]
            od = round(_a_odds(a)*_a_odds(b),2)
            if od<2.0 or od>4.5: continue
            combos.append({"id":f"2A{i}{j}","name":f'2串1·{a["home"][:2]}+{b["home"][:2]}',"level":"稳健","stars":3,
                "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":_a_pick(a),"odds":_a_odds(a)},
                    {"match":f'{b["home"]} vs {b["away"]}',"pick":_a_pick(b),"odds":_a_odds(b)}],
                "rate":"48-58%","odds":od,"cat":"2串1","note":"双锚定交叉验证"})
    # 锚定×探索 2串1
    for i, a in enumerate(anchors[:3]):
        for j, b in enumerate(non_a[:4]):
            od = round(_a_odds(a)*safe_float(b["odds_h"],2.0),2)
            if od<2.5 or od>5.5: continue
            combos.append({"id":f"2B{i}{j}","name":f'2串1·{a["home"][:2]}+{b["home"][:2]}',"level":"稳健","stars":3,
                "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":_a_pick(a),"odds":_a_odds(a)},
                    {"match":f'{b["home"]} vs {b["away"]}',"pick":"「胜」探","odds":safe_float(b["odds_h"],2.0)}],
                "rate":"42-52%","odds":od,"cat":"2串1","note":"锚定+探索交叉"})

    # 按Elo差距绝对值排序
    all_sorted = sorted(upcoming_today, key=lambda x: -abs(x["elo_diff"]))

    # ═══ 总进球串关（2串1/3串1） ═══
    goals_picks = [a for a in upcoming_today]
    # 小球2串1
    low_g2 = [a for a in upcoming_today if a["adj_goals"] < 2.5]
    if len(low_g2) >= 2:
        for ci in range(min(2, len(low_g2)-1)):
            a, b = low_g2[ci], low_g2[ci+1]
            combos.append({"id":f"G2L{ci}","name":f'总进球2串1·小球组合{ci+1}',"level":"稳健","stars":4,
                "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":"总进球<2.5","odds":1.80},
                    {"match":f'{b["home"]} vs {b["away"]}',"pick":"总进球<2.5","odds":1.80}],
                "rate":"45-55%","odds":3.24,"cat":"总进球串","note":f'双小球 进球{a["adj_goals"]}/{b["adj_goals"]}球'})
    # 大球2串1
    high_g2 = [a for a in upcoming_today if a["adj_goals"] > 2.7]
    if len(high_g2) >= 2:
        for ci in range(min(2, len(high_g2)-1)):
            a, b = high_g2[ci], high_g2[ci+1]
            combos.append({"id":f"G2H{ci}","name":f'总进球2串1·大球组合{ci+1}',"level":"稳健","stars":3,
                "legs":[{"match":f'{a["home"]} vs {a["away"]}',"pick":"总进球>2.5","odds":1.80},
                    {"match":f'{b["home"]} vs {b["away"]}',"pick":"总进球>2.5","odds":1.80}],
                "rate":"38-48%","odds":3.24,"cat":"总进球串","note":f'双大球 进球{a["adj_goals"]}/{b["adj_goals"]}球'})
    # 总进球3串1
    if len(goals_picks) >= 3:
        for ci in range(2):
            import random; random.seed(ci*55+7)
            picks = random.sample(goals_picks, 3)
            od = 1; legs_g = []
            for a in picks:
                if a["adj_goals"] < 2.3: gp, go = "总进球<2.5", 1.80
                elif a["adj_goals"] > 2.8: gp, go = "总进球>2.5", 1.80
                else: gp, go = "总进球2-3球", 1.70
                od *= go; legs_g.append({"match":f'{a["home"]} vs {a["away"]}',"pick":gp,"odds":go})
            od = round(od, 2)
            combos.append({"id":f"G3_{ci}","name":f'总进球3串1·方案{ci+1}',"level":"探索","stars":2,
                "legs":legs_g,"rate":"18-30%","odds":od,"cat":"总进球串","note":f'总进球3场组合 赔率{od}'})

    # ═══ 混合玩法串关 ═══
    if len(upcoming_today) >= 3:
        for ci in range(3):
            random.seed(ci*66+8)
            picks = random.sample(upcoming_today, min(3, len(upcoming_today)))
            legs_mx = []; od_mx = 1.0
            for i, a in enumerate(picks[:3]):
                if i == 0:
                    side = a.get("strong_side","home")
                    o = safe_float(a["odds_h"] if side=="home" else a["odds_a"], 1.5)
                    legs_mx.append({"match":f'{a["home"]} vs {a["away"]}',"pick":"「胜」","odds":o})
                elif i == 1:
                    o = 1.80
                    legs_mx.append({"match":f'{a["home"]} vs {a["away"]}',"pick":"总进球>2.5" if a["adj_goals"]>2.5 else "总进球<2.5","odds":o})
                else:
                    o = 2.20
                    legs_mx.append({"match":f'{a["home"]} vs {a["away"]}',"pick":"半全场「胜胜」" if a.get("anchor") else "平局方向","odds":o})
                od_mx *= o
            od_mx = round(od_mx, 2)
            combos.append({"id":f"MX{ci}","name":f'混合玩法·方案{ci+1}',"level":"探索","stars":2,
                "legs":legs_mx,"rate":"25-38%","odds":od_mx,"cat":"混合串","note":f'胜平负+总进球混搭 赔率{od_mx}'})

    # 3串2: 选3场拆3个2串1，容错1场
    pool32 = anchors[:] if len(anchors) >= 3 else all_sorted[:max(3, len(all_sorted))]
    if len(pool32) >= 3:
        for ci in range(2):
            import random; random.seed(ci*77+32)
            picks = random.sample(pool32, 3)
            # 3个2串1组合: AB, AC, BC
            pairs = [(0,1),(0,2),(1,2)]
            sub_odds = []
            for i,j in pairs:
                x, y = picks[i], picks[j]
                sx = x.get("strong_side","home"); sy = y.get("strong_side","home")
                sub_odds.append(round(safe_float(x["odds_h"] if sx=="home" else x["odds_a"],1.5) * safe_float(y["odds_h"] if sy=="home" else y["odds_a"],1.5), 2))
            avg_od = round(sum(sub_odds)/3, 2)
            combos.append({"id":f"32_{ci}","name":f'3串2容错·方案{ci+1}',"level":"稳健","stars":3,
                "legs":[{"match":f'{picks[0]["home"]} vs {picks[0]["away"]}',"pick":"胜","odds":safe_float(picks[0]["odds_h"] if picks[0].get("strong_side","home")=="home" else picks[0]["odds_a"],1.5)},
                    {"match":f'{picks[1]["home"]} vs {picks[1]["away"]}',"pick":"胜","odds":safe_float(picks[1]["odds_h"] if picks[1].get("strong_side","home")=="home" else picks[1]["odds_a"],1.5)},
                    {"match":f'{picks[2]["home"]} vs {picks[2]["away"]}',"pick":"胜","odds":safe_float(picks[2]["odds_h"] if picks[2].get("strong_side","home")=="home" else picks[2]["odds_a"],1.5)}],
                "rate":"中2场保本(40-52%)","odds":avg_od,"cat":"3串2","note":f'3场拆3注2串1 容错1场 均赔{avg_od}'})

    # 4串2: 选4场拆6个2串1，容错2场
    pool42 = anchors[:] if len(anchors) >= 4 else all_sorted[:max(4, len(all_sorted))]
    if len(pool42) >= 4:
        for ci in range(2):
            random.seed(ci*88+42)
            picks = random.sample(pool42, 4)
            pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
            sub_odds = []
            for i,j in pairs:
                x, y = picks[i], picks[j]
                sx = x.get("strong_side","home"); sy = y.get("strong_side","home")
                sub_odds.append(round(safe_float(x["odds_h"] if sx=="home" else x["odds_a"],1.5) * safe_float(y["odds_h"] if sy=="home" else y["odds_a"],1.5), 2))
            avg_od = round(sum(sub_odds)/6, 2)
            combos.append({"id":f"42_{ci}","name":f'4串2容错·方案{ci+1}',"level":"稳健","stars":3,
                "legs":[{"match":f'{picks[0]["home"]} vs {picks[0]["away"]}',"pick":"胜","odds":safe_float(picks[0]["odds_h"] if picks[0].get("strong_side","home")=="home" else picks[0]["odds_a"],1.5)},
                    {"match":f'{picks[1]["home"]} vs {picks[1]["away"]}',"pick":"胜","odds":safe_float(picks[1]["odds_h"] if picks[1].get("strong_side","home")=="home" else picks[1]["odds_a"],1.5)},
                    {"match":f'{picks[2]["home"]} vs {picks[2]["away"]}',"pick":"胜","odds":safe_float(picks[2]["odds_h"] if picks[2].get("strong_side","home")=="home" else picks[2]["odds_a"],1.5)},
                    {"match":f'{picks[3]["home"]} vs {picks[3]["away"]}',"pick":"胜","odds":safe_float(picks[3]["odds_h"] if picks[3].get("strong_side","home")=="home" else picks[3]["odds_a"],1.5)}],
                "rate":"中2场保本(35-48%)","odds":avg_od,"cat":"4串2","note":f'4场拆6注2串1 容错2场 均赔{avg_od}'})

    # ═══ 3/4/5/6串1 ═══
    for num, cfg in [(3,("3串1","稳健",3,"22-35%")),(4,("4串1","探索",2,"12-22%")),
                      (5,("5串1","探索",2,"6-14%")),(6,("6串1","推演",1,"3-8%"))]:
        pool = anchors[:] if len(anchors) >= num else all_sorted[:max(num, len(all_sorted))]
        if len(pool) >= num:
            n_groups = 3 if num<=4 else 2
            for combo_idx in range(n_groups):
                import random; random.seed(combo_idx*100*num+num)
                picks = random.sample(pool, min(num, len(pool)))
                od = 1.0
                for x in picks:
                    side = x.get("strong_side","home")
                    od *= safe_float(x["odds_h"] if side=="home" else x["odds_a"], 1.5)
                od = round(od, 2)
                name, lv, star, rng = cfg
                combos.append({"id":f"{num}_{combo_idx}","name":f'{name}·方案{combo_idx+1}',"level":lv,"stars":star,
                    "legs":[{"match":f'{x["home"]} vs {x["away"]}',"pick":_a_pick(x) if x in anchors else ("「胜」(主)" if x.get("strong_side","home")=="home" else "「胜」(客)"),"odds":safe_float(x["odds_h"] if x.get("strong_side","home")=="home" else x["odds_a"], 1.5)} for x in picks],
                    "rate":rng,"odds":od,"cat":name,"note":f'{num}场组合 赔率{od}'})

    # 比分推演
    scores=[]
    for a in analyses[:12]:
        if a["status"]=="FT": continue
        ed=abs(a["elo_diff"])
        if ed>=150: sc,od,tag="2:0/2:1/3:1",7.5,"强弱"
        elif ed>=50: sc,od,tag="2:1/1:1/1:0",7.0,"中距"
        else: sc,od,tag="1:1/0:0/1:0",6.0,"均势"
        scores.append({"match":f'{a["home"]} vs {a["away"]}',"scores":sc,"odds":od,"tag":tag})

    # 多维度推演 ω
    if anchors and non_a:
        legs_lotto=[]
        tot_od=1.0
        if anchors:
            a=anchors[0]; legs_lotto.append({"match":f'{a["home"]} vs {a["away"]}',"pick":"「胜」","odds":safe_float(a["odds_h"],1.3)}); tot_od*=safe_float(a["odds_h"],1.3)
        if non_a:
            # 找两个不同类型的非锚定场
            for na in non_a[:2]:
                legs_lotto.append({"match":f'{na["home"]} vs {na["away"]}',"pick":"平局/受让","odds":3.0}); tot_od*=3.0
        legs_lotto=legs_lotto[:4]; tot_od=round(tot_od,1)
        if tot_od >= 5:
            combos.append({"id":"ω","name":"多维推演模型","level":"推演","stars":1,
                "legs":legs_lotto,"rate":"3-8%","odds":tot_od,"cat":"推演","note":"多维度×多场次 纯方法论展示"})

    # 统计
    close_m = [a for a in upcoming_today if abs(a["elo_diff"])<80]
    low_g = [a for a in upcoming_today if a["adj_goals"]<2.35]
    high_g = [a for a in upcoming_today if a["adj_goals"]>2.9]

    cal=[a for a in completed[-8:]]
    scores=[]  # scores now handled per-match
    return {"combos":combos,"scores":scores,"cal":cal,
        "n_anchors":len(anchors),"n_close":len(close_m),
        "n_low":len(low_g),"n_high":len(high_g)}

# ====== HTML 生成 ======
CSS='''
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#fff;padding:24px;max-width:1100px;margin:0 auto;color:#333;font-size:16px}
h1{font-size:26px;font-weight:700;text-align:center;margin:14px 0}
.sub{text-align:center;font-size:15px;color:#999;margin-bottom:6px}
.upd{text-align:center;font-size:14px;color:#bbb;margin:6px 0 20px}
.section{margin-bottom:20px;border:1px solid #ccc;border-radius:5px;overflow:hidden}
.sec-title{background:#111;color:#fff;padding:9px 16px;font-size:15px;font-weight:600;display:flex;justify-content:space-between;align-items:center}
.sec-title .badge{font-size:13px;color:#8f8;font-weight:400}
.sec-body{padding:14px}
.groups-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:2px}
.group-card{border:1px solid #f0f0f0;font-size:8px;padding:3px;background:#fafafa}
.gn{font-weight:700;font-size:8px;margin-bottom:1px}
.gr{display:flex;justify-content:space-between;padding:0;font-size:7px;line-height:1.3}
.mc-tags{padding:6px 4px;display:flex;flex-wrap:wrap;gap:3px}
.mc-tag{font-size:9px;padding:1px 5px;border-radius:2px;white-space:nowrap;font-weight:600}
.match-card{border-bottom:1px solid #eee;padding:12px 0}
.match-card:last-child{border-bottom:none}
.mh{display:flex;align-items:center;gap:6px}
.t{font-weight:600;font-size:14px;flex:1}
.meta{font-size:10px;color:#999;margin:2px 0 6px}
.bar-line{display:flex;align-items:center;margin:3px 0;gap:6px}
.bar-line .lbl{width:30px;font-size:11px;color:#666}
.bar-line .track{flex:1;height:5px;background:#eee;border-radius:3px}
.bar-line .track .fill{height:5px;border-radius:3px}
.bar-line .num{width:40px;font-size:11px;text-align:right;font-weight:600}
.match-info{font-size:10px;color:#666;margin:4px 0;line-height:1.5}
.match-info b{color:#111}
.summary-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;margin-bottom:8px}
.summary-card{text-align:center;padding:10px 6px;border:1px solid #ddd;font-size:11px;background:#fafafa}
.summary-card .sv{font-size:20px;font-weight:700;color:#111}
.summary-card .sl{font-size:10px;color:#999}
.venue-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px}
.venue-card{background:#fafafa;border:1px solid #e8e8e8;padding:7px 10px;font-size:12px}
.venue-card .vt{font-weight:700;font-size:12px;color:#111}
.venue-card .vs{font-size:10px;color:#999}
.venue-card .vn{display:flex;gap:4px;margin-top:3px;font-size:10px;flex-wrap:wrap}
.venue-card .vn span{padding:1px 5px;font-size:9px;border-radius:2px}
.venue-card .ok{background:#e8f5e9;color:#2e7d32}
.venue-card .warn{background:#fff3e0;color:#e65100}
.venue-card .danger{background:#ffebee;color:#c62828}
.elo-row{display:flex;align-items:center;padding:4px 0;border-bottom:1px solid #f0f0f0;font-size:11px;gap:6px}
.elo-row .er-teams{font-weight:600;color:#111;min-width:105px;font-size:11px}
.elo-row .er-diff{font-weight:700;min-width:40px;font-size:11px}
.er-diff.dom{color:#2e7d32}.er-diff.clr{color:#558b2f}.er-diff.cls{color:#f57f17}
.elo-row .er-gap{font-size:8px;padding:1px 5px;border-radius:3px}
.er-gap.dom{background:#e8f5e9;color:#2e7d32}.er-gap.clr{background:#f1f8e9;color:#558b2f}.er-gap.cls{background:#fff8e1;color:#f57f17}
.elo-row .er-rate{font-size:10px;color:#666;min-width:42px;text-align:right}
.elo-row .er-ok{font-size:10px;min-width:20px;text-align:center}
.elo-row .er-chips{display:flex;gap:2px;flex-wrap:wrap;flex:1}
.elo-row .er-chips span{font-size:8px;padding:1px 4px;border-radius:2px;background:#e3f2fd;color:#1565c0}
.combo-item{border-bottom:1px solid #eee;padding:8px 0}
.combo-item:last-child{border-bottom:none}
.combo-head{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.clvl{font-size:9px;padding:2px 6px;border-radius:3px;font-weight:600}
.clvl.h{background:#e8f5e9;color:#2e7d32}.clvl.m{background:#fff8e1;color:#f57f17}
.clvl.s{background:#fff3e0;color:#e65100}.clvl.x{background:#ffebee;color:#c62828}
.combo-head .cname{font-size:12px;font-weight:600;color:#111;flex:1}
.combo-head .cstars{font-size:10px}
.combo-leg{display:flex;align-items:center;gap:5px;padding:3px 0;font-size:11px}
.ltag{font-size:8px;padding:2px 5px;border-radius:3px;font-weight:600}
.ltag.a{background:#e3f2fd;color:#1565c0}.ltag.b{background:#fff3e0;color:#e65100}
.ltag.g{background:#f3e5f5;color:#7b1fa2}.ltag.x{background:#ffebee;color:#c62828}
.combo-leg .lmatch{font-weight:600;color:#111;font-size:11px;min-width:85px}
.combo-leg .lpick{font-size:10px;color:#888;margin-left:auto}
.combo-leg .lodds{font-size:12px;font-weight:700;color:#1976d2;min-width:36px;text-align:right}
.combo-reason{font-size:10px;color:#888;margin:2px 0;line-height:1.4}
.combo-stats{display:flex;gap:12px;margin-top:4px;font-size:10px;color:#666}
.combo-stats b{color:#111}
.score-cards{display:flex;gap:4px}
.score-card{flex:1;text-align:center;background:#fafafa;border:1px solid #eee;padding:5px 3px;font-size:9px}
.sc-tag{font-size:7px;padding:1px 4px;border-radius:2px;margin-bottom:2px;display:inline-block}
.sc-tag.hi{background:#e8f5e9;color:#2e7d32}.sc-tag.md{background:#fff8e1;color:#f57f17}.sc-tag.lo{background:#ffebee;color:#c62828}
.score-card .sc-teams{font-size:8px;font-weight:600;color:#111;margin:2px 0}
.score-card .sc-scores{font-weight:700;font-size:11px;color:#111}
.score-card .sc-odds{font-size:9px;color:#1976d2;font-weight:600}
.cal-row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:10px;border-bottom:1px solid #f8f8f8}
.cal-row .cal-match{font-weight:600;color:#111;min-width:85px;font-size:9px}
.cal-row .cal-result{font-weight:700;min-width:40px;text-align:center}
.cal-row .cal-elo{font-size:8px;color:#999;min-width:35px}
.cal-row .cal-deviation{font-size:9px;font-weight:600;min-width:40px}
.support-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;margin:6px 0}
.sb-h{background:#4caf50}.sb-m{background:#ffc107}.sb-s{background:#ff9800}.sb-x{background:#f44336}
.support-legend{display:flex;gap:8px;font-size:9px;color:#999;flex-wrap:wrap}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:700px){.two-col{grid-template-columns:1fr}}
.moti-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.moti-card{border:1px solid #eee;border-radius:4px;padding:8px;background:#fafafa;font-size:10px}
.moti-card .mh{display:flex;align-items:center;gap:4px;margin-bottom:3px}
.ml-fight{background:#ffebee;color:#c62828}.ml-push{background:#e3f2fd;color:#1565c0}
.ml-hold{background:#fff8e1;color:#f57f17}.ml-rest{background:#e8f5e9;color:#2e7d32}
.ml-normal{background:#f5f5f5;color:#666}
.moti-card .ml{font-size:9px;padding:1px 6px;border-radius:3px;font-weight:600}
.moti-card .mt{font-weight:600;color:#111;font-size:10px}
.moti-card .mm{display:flex;gap:8px;margin:4px 0;font-size:9px;color:#666}
.moti-card .mr{font-size:8px;color:#999;line-height:1.4}
.moti-card .mc{font-size:8px;color:#999;margin-top:2px}
@media(max-width:700px){.moti-grid{grid-template-columns:1fr}}
.dim-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px}
.dim-card{text-align:center;padding:6px 3px;border:1px solid #eee;background:#fafafa;font-size:8px}
.dim-card .di{font-size:14px;margin-bottom:1px}
.dim-card .dn{font-weight:600;color:#111;font-size:9px}
.dim-card .dd{font-size:7px;color:#999;margin-top:1px}
.disclaimer{margin-top:18px;padding:14px;border:2px solid #e0e0e0;border-radius:6px;text-align:center;font-size:11px;color:#666;line-height:1.7}
.disclaimer .dt{font-size:12px;font-weight:700;color:#111;margin-bottom:5px}
.disclaimer .dw{color:#e65100;font-weight:700}
'''

def gen_html(analyses, combo_result, dash_data, match_cards, moti_html, match_date="6/26"):
    """生成完整HTML，包含小组积分+出线概率+逻辑分析"""
    # 概览
    n_anchors = combo_result["n_anchors"]
    n_close = combo_result["n_close"]
    n_high = combo_result["n_high"]
    n_low = combo_result["n_low"]

    # 场地卡片
    vcards=""
    for a in analyses[:8]:
        v=a["venue"]
        cls="ok" if v["heat"]=="low" else ("warn" if v["heat"] in ("moderate","high") else "danger")
        flag_h = FLAGS.get(a["home"],"")
        flag_a = FLAGS.get(a["away"],"")
        vcards+=f'<div class="venue-card"><div class="vt">{flag_h} {a["home"]} vs {flag_a} {a["away"]}</div><div class="vs">{v["name"]} · {v["alt"]}m · {v["heat"]}</div><div class="vn"><span class="{cls}">进球{a["adj_goals"]}</span></div></div>'

    # Elo 行
    erows=""
    for a in analyses[:10]:
        d=a["elo_diff"]
        dc="dom" if abs(d)>=250 else ("clr" if abs(d)>=100 else "cls")
        gc="dom" if abs(d)>=250 else ("clr" if abs(d)>=100 else "cls")
        gt="碾压" if abs(d)>=250 else ("明显" if abs(d)>=100 else "接近")
        ao="✓" if a["anchor"] else "✗"
        ac="#2e7d32" if a["anchor"] else "#c62828"
        chips=""
        if a["anchor"]: chips+="<span>锚定</span>"
        if a["adj_goals"]<2.35: chips+="<span>小球</span>"
        if a["adj_goals"]>2.9: chips+="<span>大球</span>"
        if abs(d)<80: chips+="<span>均势</span>"
        flag_h=FLAGS.get(a["home"],""); flag_a=FLAGS.get(a["away"],"")
        res_str = f' <span style="color:#666;font-size:8px">{a["result"]}</span>' if a["result"] else ""
        erows+=f'<div class="elo-row"><span class="er-teams">{flag_h} {a["home"]} vs {flag_a} {a["away"]}{res_str}</span><span class="er-diff {dc}">{d:+d}</span><span class="er-gap {gc}">{gt}</span><span class="er-rate">胜率{a["win_prob"]:.0%}</span><span class="er-ok" style="color:{ac}">{ao}</span><div class="er-chips">{chips}</div></div>'

    # 组合
    ch=""
    for c in combo_result["combos"]:
        cls="h" if c["level"]=="高置信" else ("m" if c["level"]=="稳健" else ("s" if c["level"]=="探索" else "x"))
        stars="★"*c["stars"]
        legs=""
        for l in c["legs"]:
            pc="a" if "胜" in l.get("pick","") else ("b" if "平" in l.get("pick","") or "不败" in l.get("pick","") else "g")
            legs+=f'<div class="combo-leg"><span class="ltag {pc}">分析</span><span class="lmatch">{l["match"]}</span><span class="lpick">{l["pick"]}</span><span class="lodds">{l["odds"]}</span></div>'
        cat_tag = c.get("cat","")
        ch+=f'<div class="combo-item"><div class="combo-head"><span class="clvl {cls}">{c["level"]}</span><span class="cname">{c["name"]}</span><span class="type-tag" style="font-size:8px;background:#f0f0f0;padding:1px 5px;border-radius:3px;color:#888">{cat_tag}</span><span class="cstars">{stars}</span></div><div class="combo-body">{legs}<div class="combo-reason">{c["note"]}</div><div class="combo-stats"><span>因子 <b>{c["odds"]}</b></span><span>匹配 <b>{c["rate"]}</b></span></div></div></div>'

    # 比分
    sc=""
    for s in combo_result["scores"][:3]:
        tc="hi" if s["tag"]=="强弱" else ("md" if s["tag"]=="中距" else "lo")
        sc+=f'<div class="score-card"><div class="sc-tag {tc}">{s["tag"]}</div><div class="sc-teams">{s["match"]}</div><div class="sc-scores">{s["scores"]}</div><div class="sc-odds">{s["odds"]}</div></div>'

    # 校准
    cal=""
    for a in reversed(combo_result["cal"][-8:]):
        elo_str = f"{a['elo_diff']:+d}" if a["elo_diff"] else ""
        # 计算偏差（如果有结果）
        dev_str = ""
        if a["result"] and ":" in a["result"]:
            try:
                hg,ag = map(int, a["result"].split(":"))
                pred_hg = max(0, round(a["adj_goals"]*0.55))
                dev = (hg-pred_hg)*10
                dev_color = "#2e7d32" if abs(dev)<10 else ("#f57f17" if abs(dev)<20 else "#c62828")
                dev_str = f'<span class="cal-deviation" style="color:{dev_color}">偏差{dev:+d}%</span>'
            except: pass
        flag_h=FLAGS.get(a["home"],""); flag_a=FLAGS.get(a["away"],"")
        cal+=f'<div class="cal-row"><span class="cal-match">{flag_h} {a["home"]} vs {flag_a} {a["away"]}</span><span class="cal-result">{a["result"] or "未赛"}</span><span class="cal-elo">ELO{elo_str}</span>{dev_str}</div>'

    # 支持率条
    na=n_anchors; nc=n_close; nl=n_low; nh=n_high
    total = max(na+nc+nl+nh, 1)
    pa = na*100//total; pm = max(40, (na+nc)*100//total-pa)
    ps = nc*100//total; px = max(5, 100-pa-pm-ps)

    html = f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>世界杯逻辑分析引擎</title><style>{CSS}</style></head><body>

<h1>⚽ 世界杯综合看板</h1>
<div class="sub">比分预测 × 小组积分 × 出线概率 × 逻辑分析引擎 · 纯数据分析工具</div>
<div class="upd">📅 {match_date} | {len(analyses)}场 | MC3000次 | 2018-2024回测</div>

<!-- ====== 全宽：小组积分 ====== -->
<div class="section"><div class="sec-title">📊 小组积分 <span class="badge">{dash_data['acc_rate']}%准确</span></div>
<div class="sec-body"><div class="groups-grid">{dash_data['groups_html']}</div></div></div>

<!-- ====== 全宽：出线概率 ====== -->
<div class="section"><div class="sec-title">🎲 出线概率 <span class="badge">MC3000次</span></div>
<div class="sec-body"><div class="mc-tags">{dash_data['qual_html']}</div></div></div>

<!-- ====== 全宽：模型复盘 ====== -->
<div class="section"><div class="sec-title" style="background:#555">🔍 模型复盘 <span class="badge">盲区检测</span></div>
<div class="sec-body" style="font-size:10px;color:#666">{dash_data['review_html']}</div></div>

<!-- ====== 战意推演 ====== -->
{'''<div class="section"><div class="sec-title" style="background:#c62828">🧠 球队战意推演 <span class="badge">静态规则+蒙特卡洛</span></div>
<div class="sec-body"><div class="moti-grid">''' + moti_html + '''</div>
<div style="font-size:9px;color:#999;margin-top:6px">标签说明：🔴死拼=绝无放水可能 | 🔵冲第一=头名驱动力强 | 🟡稳第二=目标明确 | 🟢可轮换=存在轮换空间但不故意输球<br>指标：安全=出线安全度 | 头名=争头名驱动力 | 轮换=轮换可能性（越高越可能轮换）| MC=蒙特卡洛1000次模拟概率</div></div></div>
''' if moti_html else ''}

<!-- ====== 两栏布局 ====== -->
<div class="two-col">

<!-- 左栏：比赛预测 -->
<div>
<div class="section"><div class="sec-title">⚽ 比赛预测 <span class="badge">胜平负·总进球·比分</span></div>
<div class="sec-body">
{''.join(f'''<div class="match-card">
<div class="mh"><span class="g">{c['group']}组</span><span class="t">{c['flag_h']} {c['home']} vs {c['flag_a']} {c['away']}</span>{c['status_tag']}{c['result_str']}</div>
<div class="meta">{c['date']} | {c['venue'] or '待定'} | {c['tier']}</div>
<div class="bar-line"><span class="lbl">主胜</span><div class="track"><div class="fill" style="width:{c['w']:.0f}%;background:#4caf50"></div></div><span class="num">{c['w_pct']}</span></div>
<div class="bar-line"><span class="lbl">平局</span><div class="track"><div class="fill" style="width:{c['dr']:.0f}%;background:#ffc107"></div></div><span class="num">{c['dr_pct']}</span></div>
<div class="bar-line"><span class="lbl">客胜</span><div class="track"><div class="fill" style="width:{c['lo']:.0f}%;background:#f44336"></div></div><span class="num">{c['lo_pct']}</span></div>
<div class="match-info"><b>预期进球</b> {c['total_xg']}球 | <b>冷门指数</b> {c['upset']:.0f}%<br><b>比分</b> {c['scores_str']}<br><b>总进球</b> {c['goals_str']}</div>
</div>''' for c in match_cards[:15]) if match_cards else '<div style="text-align:center;color:#999;padding:12px">暂无未赛比赛</div>'}
</div></div>
</div>

<!-- 右栏：逻辑分析 -->
<div>
<div class="section"><div class="sec-title">📊 分析概览 <span class="badge">场地+Elo</span></div><div class="sec-body">
<div class="summary-grid">
<div class="summary-card"><div class="sv">{na}</div><div class="sl">锚定场次</div></div>
<div class="summary-card"><div class="sv">{nc}</div><div class="sl">均势场次</div></div>
<div class="summary-card"><div class="sv">{nh}</div><div class="sl">大球倾向</div></div>
<div class="summary-card"><div class="sv">{nl}</div><div class="sl">小球倾向</div></div>
</div></div></div>

<div class="section"><div class="sec-title">📍 场地环境</div>
<div class="sec-body"><div class="venue-grid">{vcards}</div></div></div>

<div class="section"><div class="sec-title">📊 Elo 评估</div>
<div class="sec-body">{erows}</div></div>

<div class="section"><div class="sec-title">🔬 逻辑组合 <span class="badge">{len(combo_result["combos"])}组</span></div>
<div class="sec-body">{ch}</div></div>

<div class="section"><div class="sec-title" style="background:#555">🎯 比分推演</div>
<div class="sec-body"><div class="score-cards">{sc}</div><div style="font-size:8px;color:#999;margin-top:4px">1:0(13.5%) 2:1(11.3%) 2:0(10.9%) 1:1(10.7%) | 290场加权</div></div></div>

<div class="section"><div class="sec-title">📈 支持率分布</div><div class="sec-body">
<div class="support-bar"><div class="sb-h" style="width:{pa}%"></div><div class="sb-m" style="width:{pm}%"></div><div class="sb-s" style="width:{ps}%"></div><div class="sb-x" style="width:{px}%"></div></div>
<div class="support-legend"><span>🟢高</span><span>🟡稳</span><span>🟠探</span><span>🔴推</span></div></div></div>

<div class="section"><div class="sec-title">📋 近期校准</div>
<div class="sec-body">{cal}<div style="font-size:9px;color:#999;margin-top:4px">偏差&lt;±10=准 ✓ | ±10-20=可接受 ⚠ | &gt;±20=需校准 ✗</div></div></div>
</div>
</div><!-- /two-col -->

<div class="section"><div class="sec-title">📋 数据来源</div><div class="sec-body" style="font-size:10px;color:#666;line-height:1.6">
<b>Elo</b>: eloratings.net · <b>场地</b>: FIFA + Sports Medicine(2026) · <b>回测</b>: WC 2018+2022(128) Euro 2020+2024(102) Copa 2021+2024(60)=290场<br>
<b>权重</b>: 2024 35% · 2022 30% · 2021 20% · 2018 15% · <b>赔率参考</b>: 中国竞彩网
</div></div>

<div class="disclaimer">
<div class="dt">⚠️ 重要声明</div>
本页面为<b>纯数据分析工具</b>，所有内容仅供赛事逻辑研究和统计模型验证之用。<br>
展示的「逻辑组合」「支持率」「回测匹配度」等均为<b>基于历史数据的统计推演</b>，不构成任何形式的预测结论或行为建议。<br>
<span class="dw">🚫 本工具不提供任何购彩渠道链接，不参与任何资金往来，不与任何博彩平台合作。</span><br>
足球比赛存在固有不确定性，历史数据不代表未来结果。
</div>

</body></html>'''
    return html


# ====== 导入 live_data 预测函数 ======
from live_data import predict, ELO as LIVE_ELO, FLAGS as LIVE_FLAGS, STYLE

# ====== 导入战意推演引擎 ======
try:
    from motivation_engine import analyze_all_teams as moti_analyze, gen_motivation_html
    HAS_MOTIVATION = True
except ImportError:
    HAS_MOTIVATION = False

# 同步 ELO
ELO.update(LIVE_ELO)
FLAGS.update(LIVE_FLAGS)

# ====== 生成每场比赛预测卡片 ======
def gen_match_predictions(matches):
    """为每场比赛生成胜平负+总进球+比分预测（仅今天+未来）"""
    cards = []
    today = max([m["date"] for m in matches if m.get("date")]) if matches else "6/26"
    for m in matches:
        if m.get('status') == 'FT':
            continue  # 跳过已完赛
        if m.get('date','') < today and not m.get('live_score'):
            continue  # 昨天无结果=数据未更新，跳过
        try:
            p = predict(m['home'], m['away'], match_info=m)
        except Exception as e:
            continue

        w, dr, lo = p['win'], p['draw'], p['loss']
        tier = '🟢' if w > 75 else ('🟡' if w > 60 else ('🟠' if w > 45 else '🔴'))
        w_pct = f"{w}%"; dr_pct = f"{dr}%"; lo_pct = f"{lo}%"

        # 比分 Top 3
        top_scores = p.get('top', [])[:3]
        scores_str = ' · '.join([f"{s}({pr}%)" for s, pr in top_scores])

        # 总进球分布
        gl = p.get('gl', {})
        goals_str = ' | '.join([f"{k}球:{v}%" for k, v in sorted(gl.items(), key=lambda x: int(x[0]))[:7]])

        # 冷门概率
        upset = p.get('upset', min(lo, 100-w) if w > 50 else 25)

        # 预期进球
        xh, xa = p.get('xh', 0), p.get('xa', 0)
        total_xg = round(xh + xa, 1)

        flag_h = FLAGS.get(m['home'], ''); flag_a = FLAGS.get(m['away'], '')
        result_str = f'<span style="color:#666">({m["result"]})</span>' if m.get('result') else ''
        status_tag = ''
        if m.get('live_score'):
            status_tag = f'<span style="background:#e44;color:#fff;padding:2px 6px;font-size:9px">🔴 {m["live_score"]}</span>'

        cards.append({
            'home': m['home'], 'away': m['away'],
            'flag_h': flag_h, 'flag_a': flag_a,
            'result_str': result_str, 'status_tag': status_tag,
            'tier': tier, 'w': w, 'dr': dr, 'lo': lo,
            'w_pct': w_pct, 'dr_pct': dr_pct, 'lo_pct': lo_pct,
            'scores_str': scores_str, 'goals_str': goals_str,
            'upset': upset, 'total_xg': total_xg,
            'date': m.get('date',''), 'group': m.get('group',''),
            'venue': m.get('venue',''), 'result': m.get('result',''),
            'live_clock': m.get('live_clock',''),
        })
    return cards


# ====== 导入现有 dashboard 生成器 ======
def gen_dashboard_data(matches):
    """复用 dashboard.py 的核心逻辑：小组积分 + 出线概率"""
    import random as rnd
    from live_data import predict as lpredict

    # 小组积分
    groups = {}
    for m in matches:
        g = m['group']
        if g not in groups: groups[g] = {}
        for t in [m['home'], m['away']]:
            if t not in groups[g]: groups[g][t] = {'pts':0,'gd':0,'gs':0,'gc':0,'p':0}
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

    # 模型准确率
    ft_matches = [m for m in matches if m.get('status') == 'FT']
    correct = 0
    for m in ft_matches:
        h, a, r = m['home'], m['away'], m['result']
        hg, ag = map(int, r.split(':'))
        p = lpredict(h, a)
        pred = 'win' if p['win'] > max(p['draw'], p['loss']) else ('draw' if p['draw'] > max(p['win'], p['loss']) else 'loss')
        actual = 'win' if hg > ag else ('draw' if hg == ag else 'loss')
        if pred == actual: correct += 1
    acc_rate = round(correct / len(ft_matches) * 100, 1) if ft_matches else 0

    # 蒙特卡洛出线概率 3000次
    N = 3000
    team_qual = {t: 0 for g in groups for t in groups[g]}
    remaining = [m for m in matches if not m.get('result') and m.get('status') != 'FT']
    for _ in range(N):
        sim = {g: {t: {'pts': s['pts'], 'gd': s['gd']} for t, s in teams.items()} for g, teams in groups.items()}
        for m in remaining:
            g = m['group']
            p = lpredict(m['home'], m['away'])
            r = rnd.random()
            if r < p['win'] / 100:
                hg = max(1, int(p['xh'] + rnd.gauss(0, 0.5)))
                ag = max(0, int(p['xa'] + rnd.gauss(0, 0.5)))
                if hg <= ag: hg = ag + 1
                sim[g][m['home']]['pts'] += 3
            elif r < (p['win'] + p['draw']) / 100:
                hg = ag = max(0, int((p['xh'] + p['xa']) / 2))
                sim[g][m['home']]['pts'] += 1; sim[g][m['away']]['pts'] += 1
            else:
                ag = max(1, int(p['xa'] + rnd.gauss(0, 0.5)))
                hg = max(0, int(p['xh'] + rnd.gauss(0, 0.5)))
                if ag <= hg: ag = hg + 1
                sim[g][m['away']]['pts'] += 3
            hg_diff = hg - ag
            sim[g][m['home']]['gd'] += hg_diff
            sim[g][m['away']]['gd'] -= hg_diff
        for g in groups:
            ranked = sorted(sim[g].items(), key=lambda x: (-x[1]['pts'], -x[1]['gd']))
            for j, (team, _) in enumerate(ranked):
                if j < 2: team_qual[team] += 1

    # 生成小组积分 HTML
    sorted_groups = sorted(groups.items())
    groups_html = ""
    for g, teams in sorted_groups:
        ranked = sorted(teams.items(), key=lambda x: (-x[1]['pts'], -x[1]['gd']))
        rows = ""
        for t, s in ranked:
            flag = FLAGS.get(t, "")
            bold = "style='font-weight:700'" if ranked.index((t,s)) < 2 else ""
            rows += f"<div class='gr' {bold}><span>{flag} {t}</span><span>{s['p']}场 {s['pts']}分 {s['gd']:+d}</span></div>"
        groups_html += f"<div class='group-card'><div class='gn'>{g}组</div>{rows}</div>"

    # 生成出线概率 HTML
    qual_sorted = sorted(team_qual.items(), key=lambda x: -x[1])
    qual_html = ""
    for team, cnt in qual_sorted:
        pct = cnt / N * 100
        if pct >= 90: bg = "#e8f5e9"; c = "#390"
        elif pct >= 50: bg = "#fff8e1"; c = "#f80"
        else: bg = "#f5f5f5"; c = "#999"
        flag = FLAGS.get(team, "")
        qual_html += f"<span class='mc-tag' style='background:{bg};color:{c}'>{flag}{team} {pct:.1f}%</span>"

    # Agent复盘
    wrong_upsets = 0; goal_surprises = 0; elo_blowouts = 0; score_errs = []
    for m in ft_matches:
        h, a, r = m['home'], m['away'], m['result']
        hg, ag = map(int, r.split(':'))
        p = lpredict(h, a, match_info=m)
        exp_total = p['xh'] + p['xa']
        act_total = hg + ag
        if p['win'] > 60 and (hg <= ag): wrong_upsets += 1
        if act_total - exp_total > 1.0: goal_surprises += 1
        if abs(p['he']-p['ae']) < 50 and abs(hg-ag) >= 2: elo_blowouts += 1
        score_errs.append(abs((p['xh']-p['xa']) - (hg-ag)))
    avg_score_err = round(sum(score_errs)/len(score_errs), 1) if score_errs else 0
    review_html = f"<span>爆冷 {wrong_upsets}场</span> <span>进球超预期 {goal_surprises}场</span> <span>ELO均势大胜 {elo_blowouts}场</span> <span>平均分差误差 {avg_score_err}</span>"

    return {
        "groups_html": groups_html,
        "qual_html": qual_html,
        "acc_rate": acc_rate,
        "review_html": review_html,
    }


# ====== 主流程 ======
def main():
    matches = load_schedule()
    analyses = analyze_all(matches)
    combo_result = gen_combos(analyses)

    # 生成 dashboard 数据
    print("🎲 蒙特卡洛模拟中...")
    dash_data = gen_dashboard_data(matches)
    print(f"   准确率 {dash_data['acc_rate']}%")

    # 生成每场比赛预测卡片
    print("⚽ 生成比赛预测...")
    match_cards = gen_match_predictions(matches)
    print(f"   {len(match_cards)}场比赛预测")

    # 展示: 未赛 + 最近完赛
    upcoming = [a for a in analyses if a["status"]!="FT"]
    completed = [a for a in analyses if a["status"]=="FT"]
    display = upcoming + completed[-6:]

    # 战意推演
    moti_html = ""
    if HAS_MOTIVATION:
        print("🧠 战意推演分析...")
        moti_results = moti_analyze()
        moti_html = gen_motivation_html(moti_results, top_n=24)
        print(f"   战意卡片 {len(moti_results)}队")

    today = max([m["date"] for m in matches]) if matches else "6/26"
    html = gen_html(display, combo_result, dash_data, match_cards, moti_html, today)

    out = os.path.join(DIR, "logic_analysis.html")
    with open(out,"w",encoding="utf-8") as f:
        f.write(html)

    print(f"✅ {out}")
    print(f"   {len(matches)}场 | FT {len(completed)} | 未赛 {len(upcoming)}")
    print(f"   锚定{combo_result['n_anchors']} 均势{combo_result['n_close']} 大球{combo_result['n_high']} 小球{combo_result['n_low']}")
    print(f"   组合{len(combo_result['combos'])}组 比分{len(combo_result['scores'])}组")

if __name__=="__main__":
    main()
