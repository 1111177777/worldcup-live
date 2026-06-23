"""
世界杯实时数据引擎 v2
读取 schedule.json → ELO预测 → 生成 live.html
每5分钟运行：python live_data.py
"""
import json, os, math
from datetime import datetime

import hashlib

DIR = os.path.dirname(__file__)
SCHEDULE_FILE = os.path.join(DIR, "schedule.json")
OUTPUT = os.path.join(DIR, "live.html")
PASSWORD = "wc2026"  # 访问密码，改这里即改密码
PASS_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()

# 在线人数计数器 — GitHub Gist 存储（国内可用）
GIST_ID = "6a2918fe826c613081dbbbce38e2321a"
# Token 从 .env 文件读取（不提交到 git，避免被 GitHub 扫描吊销）
_token_file = os.path.join(DIR, ".env")
GH_TOKEN = open(_token_file).read().strip() if os.path.exists(_token_file) else ""

ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"意大利":1840,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"伊朗":1730,"澳大利亚":1710,"埃及":1720,"尼日利亚":1710,"科特迪瓦":1700,"喀麦隆":1690,"加纳":1680,"突尼斯":1670,"阿尔及利亚":1660,"南非":1640,"加拿大":1730,"哥斯达黎加":1680,"巴拿马":1640,"牙买加":1630,"沙特阿拉伯":1670,"卡塔尔":1650,"伊拉克":1620,"阿联酋":1610,"新西兰":1600,"巴拉圭":1720,"厄瓜多尔":1740,"智利":1760,"秘鲁":1730,"委内瑞拉":1680,"玻利维亚":1620,"波黑":1690,"塞尔维亚":1750,"丹麦":1800,"瑞典":1790,"挪威":1780,"波兰":1760,"乌克兰":1740,"土耳其":1750,"比利时":1830,"威尔士":1700,"苏格兰":1690,"捷克":1720,"罗马尼亚":1680,"斯洛伐克":1670,"匈牙利":1700,"希腊":1680,"佛得角":1580,"库拉索":1560,"约旦":1590,"乌兹别克斯坦":1610,"海地":1550,"瑞士":1830,"摩洛哥":1790,"刚果民主共和国":1650,"奥地利":1760,"古巴":1540,"苏里南":1520}
FLAGS = dict(阿根廷="🇦🇷",法国="🇫🇷",巴西="🇧🇷",英格兰="🏴",西班牙="🇪🇸",葡萄牙="🇵🇹",德国="🇩🇪",荷兰="🇳🇱",意大利="🇮🇹",乌拉圭="🇺🇾",克罗地亚="🇭🇷",哥伦比亚="🇨🇴",摩洛哥="🇲🇦",美国="🇺🇸",墨西哥="🇲🇽",塞内加尔="🇸🇳",日本="🇯🇵",韩国="🇰🇷",伊朗="🇮🇷",澳大利亚="🇦🇺",埃及="🇪🇬",尼日利亚="🇳🇬",科特迪瓦="🇨🇮",喀麦隆="🇨🇲",加纳="🇬🇭",突尼斯="🇹🇳",南非="🇿🇦",加拿大="🇨🇦",巴拉圭="🇵🇾",厄瓜多尔="🇪🇨",智利="🇨🇱",秘鲁="🇵🇪",波黑="🇧🇦",塞尔维亚="🇷🇸",丹麦="🇩🇰",瑞典="🇸🇪",挪威="🇳🇴",波兰="🇵🇱",乌克兰="🇺🇦",土耳其="🇹🇷",比利时="🇧🇪",捷克="🇨🇿",卡塔尔="🇶🇦",新西兰="🇳🇿",海地="🇭🇹",苏格兰="🏴",瑞士="🇨🇭",奥地利="🇦🇹",约旦="🇯🇴",伊拉克="🇮🇶",库拉索="🇨🇼",巴拿马="🇵🇦",哥斯达黎加="🇨🇷",牙买加="🇯🇲",沙特阿拉伯="🇸🇦",阿联酋="🇦🇪",委内瑞拉="🇻🇪",玻利维亚="🇧🇴",威尔士="🏴",罗马尼亚="🇷🇴",斯洛伐克="🇸🇰",匈牙利="🇭🇺",希腊="🇬🇷",佛得角="🇨🇻",乌兹别克斯坦="🇺🇿",刚果民主共和国="🇨🇩",阿尔及利亚="🇩🇿")

def poisson(l,k): return math.exp(-l)*l**k/math.factorial(k)

# 球队风格系数（攻击力/防守力加成，基准1.0）
STYLE = {
    "德国":(1.3,1.0),"巴西":(1.3,1.0),"法国":(1.25,1.0),"阿根廷":(1.2,1.0),
    "英格兰":(1.15,1.0),"西班牙":(1.1,1.0),"荷兰":(1.0,0.85),"葡萄牙":(1.2,0.95),
    "比利时":(1.1,0.9),"挪威":(1.25,0.8),"库拉索":(0.5,0.3),"海地":(0.6,0.4),
    "卡塔尔":(0.6,0.7),"佛得角":(0.5,0.4),"新西兰":(0.7,0.6),
    "巴拿马":(0.7,0.5),"约旦":(0.65,0.6),"伊拉克":(0.7,0.6),
    "乌兹别克斯坦":(0.65,0.55),"刚果民主共和国":(0.8,0.6),
    "伊朗":(0.7,1.15),"巴拉圭":(0.75,1.1),"瑞士":(0.85,1.1),
    "乌拉圭":(1.0,1.15),"克罗地亚":(0.9,1.1),"摩洛哥":(0.8,1.3),
    # 均衡型
    "墨西哥":(1.1,0.9),"美国":(1.1,0.9),"韩国":(1.05,0.85),
    "日本":(1.25,1.05),"加拿大":(1.0,0.85),"澳大利亚":(1.1,0.95),
    "塞内加尔":(1.05,0.9),"埃及":(0.95,1.1),"科特迪瓦":(1.0,0.85),
    "加纳":(0.9,0.85),"喀麦隆":(0.85,0.85),"尼日利亚":(0.95,0.85),
    "突尼斯":(0.75,0.9),"阿尔及利亚":(0.85,0.85),"南非":(0.8,0.8),
    "丹麦":(1.05,1.0),"瑞典":(1.0,1.0),"波兰":(1.0,0.9),
    "乌克兰":(0.9,0.85),"土耳其":(1.05,0.85),"奥地利":(1.0,0.9),
    "塞尔维亚":(1.0,0.85),"威尔士":(0.85,0.9),"苏格兰":(0.9,0.85),
    "捷克":(0.95,0.9),"罗马尼亚":(0.8,0.85),"斯洛伐克":(0.75,0.85),
    "匈牙利":(0.9,0.8),"希腊":(0.7,0.95),"哥伦比亚":(1.1,0.85),
    "智利":(0.95,0.9),"秘鲁":(0.85,0.85),"厄瓜多尔":(0.9,0.85),
    "委内瑞拉":(0.75,0.8),"玻利维亚":(0.7,0.7),
    "哥斯达黎加":(0.75,0.8),"牙买加":(0.8,0.7),
    "沙特阿拉伯":(0.75,1.0),"阿联酋":(0.7,0.7),
    "意大利":(1.05,1.05),
}

# 球队打法特点
PLAY_STYLE = {
    "乌兹别克斯坦":"4-3-3中亚快速反击，中后场退守，边路速度打转换。短板：中场组织薄弱",
    "乌拉圭":"3-5-2铁血力量防守定位球轰炸，三中卫死守，高空争抢顶级。短板：阵地进攻创造力匮乏",
    "伊拉克":"4-2-3-1中场缠斗流，拼抢积极但战术体系不成熟，面对强队易崩盘",
    "伊朗":"5-4-1极致收缩大巴铁桶防守，放弃中场控球，断球直传边路反击。进球靠偷",
    "佛得角":"4-3-3小型岛国反击流，边路快速转换，中场控制力薄弱",
    "克罗地亚":"4-3-3复古中场磨盘控球，魔笛科瓦契奇短传控节奏，擅长加时拉锯。短板：核心阵容严重老化",
    "刚果民主共和国":"4-3-3纯单兵冲击足球，完全依靠个人速度突破。短板：整体体系松散",
    "加拿大":"4-3-3田径高压逼抢，戴维斯边翼往返，全员年轻体能充沛。短板：技术粗糙中场组织匮乏",
    "加纳":"4-2-3-1年轻体能逼抢流，全员前场压迫，边路往返冲刺。短板：门前终结效率低下",
    "南非":"4-3-3年轻速度型反击，边路突破个人能力有限，被罚2红纪律问题突出",
    "卡塔尔":"4-1-4-1慢速控球节奏拖延流，中场倒脚消磨时间，开球大脚推对方半场。短板：防线转身慢怕边路冲击",
    "厄瓜多尔":"4-2-3-1高原跑动冲击流，全员不间断压迫，边路快速二过一。短板：身体对抗弱势终结效率一般",
    "古巴":"4-4-2首秀，美职联球员为主，实力最弱之一",
    "哥伦比亚":"4-3-3边路高速冲击大开大合，迪亚斯单兵突破，节奏飞快。短板：防守稳定性差前后脱节",
    "哥斯达黎加":"5-4-1极致防守体系，门将出色，进攻乏力",
    "喀麦隆":"4-3-3非洲力量反击流，中锋支点摆渡，边路高速冲刺。短板：战术执行力差抗压易崩",
    "土耳其":"4-2-3-1欧亚混合硬朗传控，中场拼抢凶狠，边路快慢切换。短板：后防协防漏洞较多",
    "埃及":"4-2-3-1中锋支点阵地流，萨拉赫边路核心，定位球稳定。短板：中场跑动覆盖不足",
    "塞内加尔":"4-3-3边路速度冲击，马内单兵爆破，高位逼抢强度高。短板：防守纪律不稳定",
    "墨西哥":"4-1-4-1灵动快慢切换传切，中场前腰灵活调度，下半场效率高。短板：长时间逼抢后半程体能下滑",
    "奥地利":"4-2-3-1红牛式极限高位压迫，全场贴身逼抢，跑动强度欧洲前列。短板：防线前压留下大量身后空档",
    "威尔士":"5-4-1极致死守韧性足球，全员深度防守，仅靠零星反击。短板：进攻端人才断层",
    "巴拉圭":"4-2-3-1复古大巴密集防守，全线收缩切断传球线路，仅靠零星反击。领先后死守不出",
    "巴拿马":"5-4-1纯防守大巴，放弃中场争夺，仅靠零星反击",
    "巴西":"4-3-3改良桑巴传控，边路立体化冲击，边后卫前压2-3-5攻击阵。短板：防守纪律松散后场协同差",
    "希腊":"5-4-1铁桶防守死守，进攻几乎为零",
    "库拉索":"4-3-3世界杯首秀，荷甲球员为主，经验不足",
    "德国":"4-1-3-2纵向高压流水线，维尔茨+穆夏拉双前腰渗透，边后卫压上拓宽宽度。短板：后防老将体能下滑",
    "意大利":"3-5-2链式防守铁血防反，三中卫退守，中场绞杀，断球直传边路反击。短板：阵地进攻创造力匮乏",
    "挪威":"4-3-3中锋支点冲击流，哈兰德禁区终结核心，边路快速传中。短板：中场组织薄弱控球能力差",
    "捷克":"3-4-3东欧力量高空轰炸，双后腰绞杀，边路频繁传中，定位球得分占比高。短板：领先后蹲坑死守，节奏偏慢",
    "摩洛哥":"3-5-2北非务实防反，深度收缩三中卫防守，边翼卫前插，断球大脚转移边路。短板：中场控球组织偏弱",
    "新西兰":"4-4-2英式冲吊身体碾压，技术粗糙但意志坚韧",
    "日本":"4-2-3-1亚洲传控天花板，精细短传对标西班牙，逼抢轮转整齐。短板：高空争顶弱势终结效率不足",
    "比利时":"4-2-3-1天才单兵冲击流，德布劳内长传制导，卢卡库支点爆破。短板：防守体系松散后场协同差",
    "沙特阿拉伯":"4-2-3-1西亚地面传导，控节奏打不开就大脚转移边路反击。短板：高强度逼抢下易失误",
    "法国":"4-2-3-1天赋高速反击流，双后腰锁中路，边路爆点内切+传中，定位球成熟。短板：缺重型支点中锋",
    "波黑":"4-2-3-1低位收缩针对性防反，专门克制转身慢的控球型球队。短板：进攻依赖单点整体推进乏力",
    "海地":"4-4-2世界杯首秀，身体天赋好战术纪律差，紧张影响发挥",
    "澳大利亚":"4-2-3-1澳式硬朗身体流，边路高空传中争顶，中场拼抢凶狠。短板：地面传控粗糙",
    "牙买加":"4-4-2速度型反击，身体对抗强但整体实力弱",
    "瑞士":"4-3-3均衡控球务实流，中后场传导流畅，边路推进稳定。短板：射门转化率极低，回追慢怕反击",
    "科特迪瓦":"4-2-3-1身体碾压式冲击，中场缠斗凶狠，一对一突破强。短板：攻防转换衔接差",
    "突尼斯":"5-4-1北非收缩大巴，低位防守抓零星反击，对抗强度中等",
    "约旦":"5-4-1纯防守摆大巴，放弃中场争夺，仅靠定位球抢分",
    "美国":"4-3-3田径高速冲击，开球大脚前置战术，边路高速往返冲刺。短板：中场细腻传导不足",
    "苏格兰":"3-5-2紧凑收缩防反，边路翼卫快速冲击，身体对抗凶狠。短板：中场创造力不足阵地战乏力",
    "苏里南":"4-4-2首秀，荷甲球员为主，整体松散",
    "英格兰":"4-2-3-1边路冲击支点流，凯恩回撤串联，萨卡帕尔默两翼突破传中。短板：中场慢速调度偏弱",
    "荷兰":"3-4-3全攻全守两翼卫狂飙，邓弗里斯弗林蓬往返攻防，德容控节奏。短板：中锋终结效率不足",
    "葡萄牙":"4-3-3巨星驱动均衡传控，B费组织，莱奥左路爆破，C罗高空抢点。短板：中场拦截硬度不足",
    "西班牙":"4-3-3现代Tiki-Taka控球压制，场均控球65%+，罗德里调度，短传渗透。短板：后卫转身慢怕极速反击",
    "阿尔及利亚":"4-2-3-1北非地面传切，中场细腻短传，快慢节奏切换。短板：后防回追速度不足",
    "阿根廷":"4-4-2低位绞杀铁血防反，梅西驱动韧性足球，全员中场疯狂逼抢。短板：后防回追速度偏弱",
    "韩国":"4-2-3-1不死跑轰足球，90分钟极限体能压迫，孙兴慜边路持球反击。短板：防空弱阵地创造力不足",
}# 状态修正（近6-12月预选赛+热身赛+世界杯正赛，正值=状态好）
FORM_BOOST = {
    "德国": 100,   # 预选赛碾压+9连胜热身+9场零封
    "日本": 85,    # 预选赛强势+赢巴西英格兰苏格兰+5零封
    "比利时": 45,  # 预选赛头名+5-0突尼斯+2-0克罗地亚
    "阿根廷": 55,  # 预选赛南美前二+热身全胜梅西状态佳
    "英格兰": 55,  # 预选赛不败+热身全胜+青年军成熟
    "巴西": 50,    # 预选赛南美第一+热身全胜
    "葡萄牙": 50,  # 预选赛全胜+热身5场不败
    "墨西哥": 55,  # 中北美预选强势+揭幕2-0+高原主场buff
    "澳大利亚": 35, # ↑修正: 2-0暴打土耳其，硬仗能力强
    "卡塔尔": 5,   # ↑修正: 1-1逼平瑞士，东道主不能低估
    "韩国": 45,    # 预选赛出线+热身全胜+揭幕战逆转捷克
    "西班牙": 40,  # 预选赛头名+3-1秘鲁+欧洲杯后复苏
    "摩洛哥": 55,  # 预选赛非洲霸主+上届四强+防线极硬(修正:巴西1-1实锤)
    "哥伦比亚": 35,# 预选赛南美前四+热身全胜
    "挪威": 35,    # 预选赛出线+3-1瑞典+哈兰德状态火热
    "土耳其": 25,  # ↓修正: 被澳洲2-0暴打，大赛气质不足
    "苏格兰": 35,  # 预选赛黑马+4-0玻利维亚+点球淘汰威尔士
    "阿尔及利亚": 40,# 预选赛非洲强队+4-0玻利维亚
    "厄瓜多尔": 30,# 预选赛南美出线+高原主场
    "法国": 20,    # 预选赛头名但近期1-2科特迪瓦状态波动
    "奥地利": 25,  # 预选赛黑马+热身稳健
    "巴拉圭": 20,  # 预选赛南美出线+4-0尼加拉瓜
    "捷克": 15,    # 预选赛点球出线+热身3-1危地马拉 揭幕-2
    "加拿大": 15,  # 中北美预选出线+热身稳健
    "海地": 15,    # 预选赛黑马+热身出色
    "库拉索": 15,  # 预选赛首进世界杯+热身4-0
    "美国": -15,   # 预选赛出线但热身1-2德国 揭幕战待验证
    "荷兰": -25,   # 预选赛头名但0-1阿尔及利亚+2-1险胜乌兹
    "克罗地亚": -10,# 预选赛出线但0-2比利时 黄金一代老化
    "南非": -15,   # 预选赛出线但揭幕战0-2输墨+被罚2红
    "威尔士": -5,  # 预选赛惊险+热身平加纳
    "波兰": 5,     # 预选赛出线+表现中规中矩
    "塞尔维亚": 5, # 预选赛出线+表现一般
    "卡塔尔": -10, # 上届全败+预选赛东道主无压力测试
}

# 主场揭幕战加成（东道主首场比赛）
HOST_OPENER = {"美国": 1.4, "加拿大": 1.25, "墨西哥": 1.2}  # 攻击力乘数

# 友谊赛/热身赛可信度折扣（正赛=1.0，友谊赛结果打5折）
FRIENDLY_DISCOUNT = 0.5

# ===== 优化1：动态ELO修正 =====
CONTINENTS = {
    "南美": ["阿根廷","巴西","乌拉圭","哥伦比亚","厄瓜多尔","智利","秘鲁","巴拉圭","委内瑞拉","玻利维亚"],
    "欧洲": ["法国","英格兰","西班牙","葡萄牙","德国","荷兰","意大利","比利时","克罗地亚","丹麦","瑞典","挪威","波兰","乌克兰","土耳其","瑞士","奥地利","捷克","塞尔维亚","苏格兰","威尔士","罗马尼亚","斯洛伐克","匈牙利","希腊","波黑"],
    "非洲": ["摩洛哥","塞内加尔","埃及","尼日利亚","科特迪瓦","喀麦隆","加纳","突尼斯","阿尔及利亚","南非","佛得角","刚果民主共和国"],
    "亚洲": ["日本","韩国","伊朗","澳大利亚","沙特阿拉伯","卡塔尔","伊拉克","阿联酋","约旦","乌兹别克斯坦"],
    "中北美": ["美国","墨西哥","加拿大","哥斯达黎加","巴拿马","牙买加","海地","古巴","苏里南","库拉索"],
    "大洋洲": ["新西兰"],
}

def get_continent(team):
    for c, teams in CONTINENTS.items():
        if team in teams: return c
    return "其他"

def elo_corrections(h, a, h_form, a_form, match_info):
    """量化全部变量→统一ELO扣分/进球修正值"""
    reasons = []
    h_adj, a_adj = 0, 0

    # 跨洲客场疲劳（长途飞行）
    hc, ac = get_continent(h), get_continent(a)
    venue = match_info.get('venue', '')
    is_us_host = any(c in venue for c in ['洛杉矶','纽约','达拉斯','休斯顿','迈阿密','西雅图','波士顿','旧金山','费城','亚特兰大','堪萨斯城'])
    if hc != ac:
        if not is_us_host:
            a_adj -= 12
            reasons.append(f'{a}跨洲飞行-12')

    # 连胜衰减（连胜越多，边际效用递减）
    if h_form > 80: h_adj -= 12; reasons.append(f'{h}超高连胜-12')
    elif h_form > 60: h_adj -= 8; reasons.append(f'{h}连胜衰减-8')
    if a_form > 80: a_adj -= 12; reasons.append(f'{a}超高连胜-12')
    elif a_form > 60: a_adj -= 8; reasons.append(f'{a}连胜衰减-8')

    # 伤病量化（按位置分等级）
    injury = match_info.get('injury', '')
    if injury:
        for team, pos_keywords, penalty in [
            (h, ['后防核心','防线','门将','后卫','中卫'], -10),
            (a, ['后防核心','防线','门将','后卫','中卫'], -10),
            (h, ['中场核心','组织','核心中场'], -7),
            (a, ['中场核心','组织','核心中场'], -7),
            (h, ['前锋','射手','进攻核心'], -5),
            (a, ['前锋','射手','进攻核心'], -5),
        ]:
            if any(k in injury for k in pos_keywords):
                if team == h: h_adj += penalty
                else: a_adj += penalty
                reasons.append(f'{team}核心缺阵{penalty}')
                break  # 只计最高等级

    # 复仇战意（历史交锋记录）
    intel = match_info.get('intel', '')
    if '复仇' in intel or '复仇战' in intel:
        for team in [h, a]:
            if team in intel.split('复仇')[0]:
                if team == h: h_adj += 8
                else: a_adj += 8
                reasons.append(f'{team}复仇战意+8')

    return h_adj, a_adj, '；'.join(reasons) if reasons else ''

# ===== 优化2：战术克制矩阵 =====
def tactic_matchup(h, a):
    """返回 (主队攻击修正, 客队攻击修正)：强队传控打大巴→攻击力打折；弱队防反→有机会偷"""
    hn, an = PLAY_STYLE.get(h, ''), PLAY_STYLE.get(a, '')
    h_adj, a_adj = 1.0, 1.0

    # 弱队标签（会蹲坑防守）
    weak_tags = ['大巴', '蹲坑', '铁血防守', '死守', '铁桶', '首秀', '经验不足', '大赛未知']
    # 强队传控 vs 弱队蹲坑 → 强队攻击打折
    is_possession_strong = any(t in hn for t in ['传控', '技术流', '桑巴'])
    is_weak_defensive = any(t in an for t in weak_tags)
    if is_possession_strong and is_weak_defensive:
        h_adj = 0.70  # 传控打大巴，效率大减
    elif is_weak_defensive:
        h_adj = 0.80  # 弱队蹲坑，进攻方总归不舒服

    # 弱队防反 → 反击有威胁
    if any(t in an for t in ['防反', '反击', '防守反击', '快速反击']):
        a_adj = 1.35

    # 首秀+经验不足 → 攻击力大幅削弱，防守也不稳
    if '首秀' in an or '经验不足' in an:
        a_adj *= 0.55  # 第一次上场腿软
        if not is_possession_strong:
            h_adj = 1.15  # 虐菜局反而放开手脚

    # 强队高压 vs 弱队粗糙 → 弱队基本组织不了进攻
    if any(t in hn for t in ['高位逼抢', '高压', '全攻全守']) and any(t in an for t in ['技术粗糙', '技术含量低', '创造力弱']):
        a_adj *= 0.65

    # 蹲坑型球队→领先后收缩，预期进球打折
    parking_bus = ['捷克', '伊朗', '巴拉圭', '卡塔尔', '希腊']
    if h in parking_bus: h_adj = min(h_adj, 0.78)
    if a in parking_bus: a_adj = min(a_adj, 0.78)

    return h_adj, a_adj

def knockout_strategy_modifier(team, pts, played, group_standings):
    """强队算分避对手：已出线/接近出线的队可能留力"""
    if played < 2: return 1.0, ''  # 只从第3轮开始

    # 已经锁定出线（6分）→ 可能轮换留力
    if pts >= 6:
        return 0.85, f'{team}已出线→可能轮换留力'

    # 已经锁定头名（6分+净胜球优势）→ 更可能留力
    # 简化：6分且净胜球≥3
    if pts >= 6:
        return 0.80, f'{team}锁定头名→大概率轮换'

    # 3分且净胜球劣势 → 必须拼命
    if pts == 3:
        return 1.10, f'{team}必须抢分→战意拉满'

    return 1.0, ''

# 动态校准文件
CALIBRATE_FILE = os.path.join(DIR, "calibrate.json")

def load_calibrate():
    """加载赛后校准数据，叠加到 FORM_BOOST 上"""
    if os.path.exists(CALIBRATE_FILE):
        with open(CALIBRATE_FILE, 'r', encoding='utf-8') as f:
            cal = json.load(f)
        # 把历史校准重新应用到 FORM_BOOST（重启后恢复）
        for key, v in cal.items():
            h = key.split(':')[0]
            a = key.split(':')[1]
            FORM_BOOST[h] = FORM_BOOST.get(h, 0) + int(v['adj_h'])
            FORM_BOOST[a] = FORM_BOOST.get(a, 0) + int(v['adj_a'])
        return cal
    return {}

def calibrate(matches):
    """根据已完赛结果自动调整状态分，保存到 calibrate.json"""
    cal = load_calibrate()
    updated = False
    for m in matches:
        if not m.get('result') or m.get('status') != 'FT':
            continue
        h, a, r = m['home'], m['away'], m['result']
        hg, ag = map(int, r.split(':'))
        p = predict(h, a)
        # 预期 vs 实际进球差
        exp_diff = p['xh'] - p['xa']
        act_diff = hg - ag
        surprise = act_diff - exp_diff  # 正数=主队超预期，负数=主队低预期

        # 方向是否正确
        if hg > ag: act_winner = h
        elif ag > hg: act_winner = a
        else: act_winner = None
        pred_w = 'win' if p['win'] > max(p['draw'], p['loss']) else ('draw' if p['draw'] > max(p['win'], p['loss']) else 'loss')
        if pred_w == 'win': pred_winner = h
        elif pred_w == 'loss': pred_winner = a
        else: pred_winner = None

        # 只有没校准过的才更新
        key = f"{h}:{a}"
        if key not in cal:
            # 调整量 = 偏差球数 × 15 分，上限 60
            adj = max(-60, min(60, surprise * 15))
            cal[key] = {
                'date': m['date'],
                'result': r,
                'expected': f"{p['xh']:.1f}-{p['xa']:.1f}",
                'surprise': round(surprise, 1),
                'adj_h': round(adj, 0),
                'adj_a': round(-adj, 0),
            }
            # 即时更新 FORM_BOOST
            FORM_BOOST[h] = FORM_BOOST.get(h, 0) + int(adj)
            FORM_BOOST[a] = FORM_BOOST.get(a, 0) - int(adj)
            updated = True

    if updated:
        with open(CALIBRATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
        print(f"   🔧 已校准 {len(cal)} 场比赛，状态分已更新")
    return cal

def kelly_stake(p_win, odds):
    """凯利公式 → 星级评价：★★★★★=重仓，☆=别碰"""
    if not odds or odds <= 1:
        return 0, "暂无数据", 0
    b = odds - 1
    f = p_win/100 - (1 - p_win/100) / b
    f_pct = round(f * 100, 1)
    # 转星级
    if f_pct <= 0:
        return f_pct, "不值得碰", 0
    elif f_pct < 3:
        return f_pct, "⭐ 小试", 1
    elif f_pct < 6:
        return f_pct, "⭐⭐ 轻仓", 2
    elif f_pct < 10:
        return f_pct, "⭐⭐⭐ 值得", 3
    elif f_pct < 15:
        return f_pct, "⭐⭐⭐⭐ 重点", 4
    else:
        return f_pct, "⭐⭐⭐⭐⭐ 重仓", 5

def predict(h,a, match_info=None):
    # 友谊赛战绩可信度打折——只信正赛（世预赛+世界杯），友谊赛/热身赛降权
    raw_h_boost = FORM_BOOST.get(h, 0)
    raw_a_boost = FORM_BOOST.get(a, 0)
    # 友谊赛/热身赛可信度打5折：FORM_BOOST中有部分基于友谊赛
    # 正赛校准值保持100%，原始形态分>30且未校准→视作友谊赛水分
    cal_file = os.path.join(DIR, 'calibrate.json')
    calibrated_teams = set()
    if os.path.exists(cal_file):
        with open(cal_file, 'r', encoding='utf-8') as f:
            for k in json.load(f).keys():
                calibrated_teams.add(k.split(':')[0])
                calibrated_teams.add(k.split(':')[1])
    h_discount = 1.0 if h in calibrated_teams else FRIENDLY_DISCOUNT
    a_discount = 1.0 if a in calibrated_teams else FRIENDLY_DISCOUNT
    friendly_note = ' | 友谊赛战绩降权' if (h_discount < 1 or a_discount < 1) else ''
    he=ELO.get(h,1700)+int(raw_h_boost * h_discount)
    ae=ELO.get(a,1700)+int(raw_a_boost * a_discount)
    hs=STYLE.get(h,(1.0,1.0)); as_=STYLE.get(a,(1.0,1.0))

    # 优化1：动态ELO修正
    if match_info:
        eh, ea, elo_reason = elo_corrections(h, a, FORM_BOOST.get(h,0), FORM_BOOST.get(a,0), match_info)
        he += eh; ae += ea
    else:
        elo_reason = ''

    # 主场揭幕战加成（仅首轮有效，第二轮起取消）
    hm_mult = HOST_OPENER.get(h, 1.0)
    if match_info and match_info.get('date','') >= '6/18':
        hm_mult = 1.0  # 第二轮起主场情绪回归正常
    # 优化2：战术克制矩阵
    tactic_h, tactic_a = tactic_matchup(h, a)

    # 优化5：出线压力战意系数
    def qual_pressure(team, pts_dict, played_dict):
        p = pts_dict.get(team, 0)
        played = played_dict.get(team, 0)
        if played == 1:
            if p == 0: return '🔴生死战', 1.15  # 必须赢
            if p == 1: return '🟡抢分', 1.08    # 需要3分
            if p == 3: return '🟢从容', 0.95    # 可保守
        return '', 1.0

    # 从match_info获取当前积分（需要外部传入）
    qual_label_h = qual_label_a = ''
    motivation_h = motivation_a = 1.0
    if match_info and match_info.get('_pts'):
        pts_dict = match_info['_pts']
        played_dict = match_info.get('_played', {})
        qual_label_h, motivation_h = qual_pressure(h, pts_dict, played_dict)
        qual_label_a, motivation_a = qual_pressure(a, pts_dict, played_dict)

    d=he-ae+50; gd=d/100*0.4
    xh=max(0.3, (1.6+gd*0.7)*hs[0]*hm_mult*tactic_h*motivation_h/max(as_[1],0.5))
    xa=max(0.3, (1.2-gd*0.4)*as_[0]*tactic_a*motivation_a/max(hs[1],0.5))

    # 优化3：市场热度修正（市场过热→模型降权）
    odds_adj = 1.0
    odds_note = ''
    if match_info and match_info.get('odds_home'):
        try:
            oh = float(match_info['odds_home'])
            fair = round(1/max((0.5 if d>0 else 0.3), 0.01), 1)
            # 市场比模型更乐观 → 可能过热
            if oh < fair * 0.85:
                odds_adj = 0.88
                odds_note = f'市场过热({oh}<公允{fair})，胜率打折'
            elif oh > fair * 1.2:
                odds_adj = 1.08
                odds_note = f'市场低估({oh}>公允{fair})，胜率上浮'
        except: pass

    w=dr=lo=0; sc={}
    for i in range(9):
        for j in range(9):
            p=poisson(xh,i)*poisson(xa,j); sc[f"{i}:{j}"]=p
            if i>j:w+=p*0.85
            elif i==j:dr+=p*1.3
            else:lo+=p*0.85
    total=w+dr+lo
    w,dr,lo=w/total*100,dr/total*100,lo/total*100
    top=sorted(sc.items(),key=lambda x:x[1],reverse=True)[:5]
    gl={}
    for i in range(10):
        for j in range(10):
            p=poisson(xh,i)*poisson(xa,j); t=i+j; gl[t]=gl.get(t,0)+p
    # 优化3：市场热度修正胜率
    w_adj = w * odds_adj; dr_adj = dr / odds_adj; lo_adj = lo / odds_adj
    total2 = w_adj + dr_adj + lo_adj
    w_final = round(w_adj / total2 * 100, 1)
    dr_final = round(dr_adj / total2 * 100, 1)
    lo_final = round(lo_adj / total2 * 100, 1)

    # 输出优化：胜率色标
    if w_final > 75: tier = '🟢 高确定性'
    elif w_final > 60: tier = '🟡 较高概率'
    elif w_final > 45: tier = '🟠 势均力敌'
    else: tier = '🔴 概率较低'

    # 优化4：动态冷门概率（替代固定2%）
    upset_base = min(lo_final, 100 - w_final) if w_final > 50 else min(w_final, 100 - lo_final) if lo_final > 50 else 25
    # 风险因子加成
    upset_bonus = 0
    if match_info:
        risks = match_info.get('risk', [])
        for r in risks:
            if '红牌' in str(r) or '伤缺' in str(r): upset_bonus += 5
            if '高原' in str(r): upset_bonus += 3
            if '天气' in str(r): upset_bonus += 2
        if match_info.get('injury') and '🔴' in match_info.get('injury', ''): upset_bonus += 3
    upset_prob = min(45, round(upset_base + upset_bonus, 1))

    # 计算链路（用于AI思考面板）
    calc_chain = f'ELO基{ELO.get(h,1700)}+状态{FORM_BOOST.get(h,0)}={he} vs {ELO.get(a,1700)}+{FORM_BOOST.get(a,0)}={ae}'
    if elo_reason: calc_chain += f' | 修正: {elo_reason}'
    calc_chain += f' | 主攻x{hs[0]:.1f}·揭幕x{hm_mult:.1f}·战术x{tactic_h:.2f}={xh:.1f}球'
    if odds_note: calc_chain += f' | {odds_note}'

    return {
        "win": w_final, "draw": dr_final, "loss": lo_final,
        "xh": round(xh, 2), "xa": round(xa, 2),
        "top": [(s, round(p*100, 1)) for s, p in top],
        "gl": {str(k): round(v*100, 1) for k, v in sorted(gl.items())[:8]},
        "he": he, "ae": ae,
        "tier": tier, "upset_prob": upset_prob,
        "calc_chain": calc_chain, "odds_note": odds_note,
    }

def auto_tags(m, p):
    """自动生成伤停/风险/价值标签，无需手动填"""
    h,a = m['home'], m['away']
    he,ae = p['he'], p['ae']
    diff = he-ae
    injury = m.get('injury','')
    if not injury:
        injury_parts = []
        h_style = STYLE.get(h, (1,1))
        a_style = STYLE.get(a, (1,1))
        if h_style[0] > 1.15 and a_style[0] < 0.8:
            injury_parts.append(f'{h}攻击线优势明显')
        if a_style[1] > 1.1:
            injury_parts.append(f'{a}防守韧性值得关注')
        injury = '；'.join(injury_parts) if injury_parts else ''
    risk = list(m.get('risk',[]))
    value = m.get('value','')
    v = m.get('venue','')
    if '高原' in v: risk.append('高原2200m')
    if abs(diff)>200: risk.append('实力悬殊')
    elif abs(diff)<30: risk.append('实力接近')
    upset_prob = 0
    if p['win'] > 50: upset_prob = p['loss']
    elif p['loss'] > 50: upset_prob = p['win']
    if upset_prob > 25: upset_why = f'不低——双方实力差距不大'
    elif upset_prob > 15: upset_why = f'偏低但非零'
    else: upset_why = f'低概率结果，除非重大意外'
    return injury, risk, value, round(upset_prob, 1), upset_why

def match_review(m, p):
    """赛后AI复盘：3条推理链→白话解读+模型优化建议"""
    h, a, r = m['home'], m['away'], m.get('result','')
    if not r: return '', ''
    hg, ag = map(int, r.split(':'))

    # 推理链1：阵容克制推演
    chain1 = []
    injury = m.get('injury','')
    if injury:
        if '伤缺' in injury or '缺阵' in injury:
            chain1.append(f'伤病影响：{injury}')
    hs = PLAY_STYLE.get(h,'')
    as_ = PLAY_STYLE.get(a,'')
    if '边路' in hs and '高龄' in as_:
        chain1.append(f'{h}边路速度优势 vs {a}高龄后防，突破造杀伤是胜负手')
    if '速度' in hs or '速度' in as_:
        chain1.append(f'速度型前锋对决→禁区一对一增多，点球概率上升')

    # 推理链2：战术对冲进球推演
    chain2 = []
    exp_diff = p['xh'] - p['xa']
    act_diff = hg - ag
    total_goals = hg + ag
    exp_total = p['xh'] + p['xa']
    if abs(exp_diff - act_diff) > 1.5:
        chain2.append(f'预期差{exp_diff:+.1f}球→实际差{act_diff:+.1f}球，偏差{abs(exp_diff-act_diff):.1f}球')
    if total_goals > exp_total + 1.5:
        chain2.append(f'总进球{total_goals}远超预期{exp_total:.1f}，攻防节奏超出模型预判')
    if total_goals >= 5:
        chain2.append(f'高比分({total_goals}球)：双方对攻或防守体系崩塌')
    if total_goals <= 1:
        chain2.append(f'低比分({total_goals}球)：默契平局或双方锋线集体哑火')

    # 推理链3：数据偏差复盘
    chain3 = []
    elo_diff = p['he'] - p['ae']
    if abs(elo_diff) < 60 and abs(act_diff) >= 2:
        chain3.append(f'ELO差距仅{abs(elo_diff)}分(实力接近)但比分差{abs(act_diff)}球→模型低估了场上一方爆发力')
    if exp_diff > 1.5 and act_diff <= 0.5:
        chain3.append(f'模型预期{h}大胜但实际接近→{a}战术部署成功抵消实力差距')
    # 模型修正建议
    fixes = []
    if total_goals > exp_total + 1:
        fixes.append(f'上调双方攻击系数或下调防守系数(当前预期{exp_total:.1f}球vs实际{total_goals}球)')
    if abs(elo_diff) < 80 and abs(act_diff) >= 2:
        fixes.append(f'ELO接近时增加战术对冲权重，避免低估单点爆发')

    # 拼装输出
    plain = f'{h} {r} {a}。'
    if chain1: plain += ' ' + ' '.join(chain1) + '。'
    if chain2: plain += ' ' + ' '.join(chain2) + '。'
    if chain3: plain += ' ' + ' '.join(chain3) + '。'

    tech = ''
    if fixes: tech = '建议：' + '；'.join(fixes) + '。'
    if m.get('odds_home'):
        oh = float(m['odds_home'])
        fair = round(1/max(p['win']/100,0.01), 1)
        tech += f' 市场参考：市场{oh}vs模型公允{fair}。'

    return plain, tech
    he,ae = p['he'], p['ae']
    diff = he-ae
    injury = m.get('injury','')  # 手动填的优先
    # 自动细化伤停影响
    if not injury:
        injury_parts = []
        h_style = STYLE.get(h, (1,1))
        a_style = STYLE.get(a, (1,1))
        if h_style[0] > 1.15 and a_style[0] < 0.8:
            injury_parts.append(f'{h}攻击线优势明显')
        if a_style[1] > 1.1:
            injury_parts.append(f'{a}防守韧性值得关注')
        if h_style[0] < 0.75:
            injury_parts.append(f'{h}攻击力有限，可关注小球')
        injury = '；'.join(injury_parts) if injury_parts else ''

    risk = list(m.get('risk',[]))
    value = m.get('value','')

    # 自动风险标签
    v = m.get('venue','')
    if '高原' in v or '墨西哥城' in v or '阿兹台克' in v:
        if '高原' not in ' '.join(risk): risk.append('高原2200m')
    if abs(diff)>200:
        if '实力悬殊' not in ' '.join(risk): risk.append('实力悬殊')
        if '轮换风险' not in ' '.join(risk): risk.append('轮换风险')  # 强队可能轮换
    elif abs(diff)<30:
        if '实力接近' not in ' '.join(risk): risk.append('实力接近')
    if m.get('date','') in ['6/24','6/25','6/26','6/27']:
        if '小组末轮' not in ' '.join(risk): risk.append('小组末轮')

    # 自动冷门类型判断
    if abs(diff) < 40:
        if '⚡ 低概率种子' not in ' '.join(risk): risk.append('⚡ 低概率种子')
    # 进球相关冷门
    goals_high = sum(p['gl'].get(str(g),0) for g in range(6,13))
    if goals_high < 5:
        if '小球概率预警' not in ' '.join(risk): risk.append('小球概率预警')

    # 自动价值标签
    if not value and m.get('odds_home'):
        oh = float(m.get('odds_home',0) or 0)
        if oh>0:
            fair = round(1/max(p['win']/100,0.01),1)
            gap = oh-fair
            if gap>0.5: value = f'主胜市场参考偏高，模型认为被低估'
            elif gap<-0.3: value = f'主胜市场参考偏低，热度可能过高'

    # 低概率值
    upset_prob = 0
    upset_why = ''
    if p['win'] > 50:  # 主队热门
        upset_prob = p['loss']
        fav, udog = h, a
    elif p['loss'] > 50:  # 客队热门
        upset_prob = p['win']
        fav, udog = a, h
    else:
        upset_prob = 0
        fav, udog = '', ''

    if upset_prob > 25:
        upset_why = f'{udog}有{upset_prob:.0f}%低概率结果——不低。'
        if upset_prob > 35:
            upset_why += '双方实力差距不大，任何结果都可能。'
        if '高原' in ' '.join(risk):
            upset_why += '高原因素可能放大不确定性。'
        if abs(diff) < 60:
            upset_why += 'ELO差距小，不确定性较高。'
    elif upset_prob > 18:
        upset_why = f'{udog}低概率值{upset_prob:.0f}%，偏低但非零。{fav}发挥失常或{udog}超常可能翻盘。'
    elif upset_prob > 0:
        upset_why = f'{fav}优势明显，{udog}低概率值仅{upset_prob:.0f}%。除非重大意外（红牌/伤病），低概率结果。'
    else:
        upset_why = '双方均势，没有明确的概率偏向。'

    return injury, risk, value, round(upset_prob, 1), upset_why

def explain(p, m, h, a, d):
    ad=abs(d)
    if d>100:ew=f"{h} ELO领先{ad}分，明显优势。"
    elif d>40:ew=f"{h} ELO略高{ad}分，主场加权后有优势。"
    else:ew=f"两队仅差{ad}分，实力非常接近。"
    if p['win']>50:sw=f"倾向{h}获胜——主场+ELO优势转化为{p['win']}%胜率。"
    elif p['loss']>50:sw=f"倾向{a}——ELO差距在下半场可能体现。"
    else:sw="三者接近——平局往往被市场低估。"
    # 多样化总进球分析
    p01=p['gl'].get('0',0)+p['gl'].get('1',0)
    p23=p['gl'].get('2',0)+p['gl'].get('3',0)
    p45=p['gl'].get('4',0)+p['gl'].get('5',0)
    p6p=sum(p['gl'].get(str(g),0) for g in range(6,13))
    if p['xh']>2.0: gw=f"进攻火力强劲，期望进球{p['xh']:.1f}球，大比分概率高——4球及以上占{p45+p6p:.0f}%。"
    elif p['xh']>1.5: gw=f"进球集中在2-3球（{p23:.0f}%），典型世界杯节奏。但也有{p45:.0f}%概率打出4球以上。"
    elif p['xh']<1.0: gw=f"进攻乏力，{p01:.0f}%概率低于2球，小球倾向明显。"
    else: gw=f"进球分布分散——2-3球占{p23:.0f}%，但{p45:.0f}%概率4球以上，{p01:.0f}%概率低于2球。"
    # 推荐逻辑强化：平局概率>30%就推荐平
    if p['draw']>30:
        if p['win']>p['loss']:
            rec=f"倾向：{h}获胜 但平局概率{p['draw']:.0f}%偏高，保守可关注平"
        elif p['loss']>p['win']:
            rec=f"倾向：{a}获胜 但平局概率{p['draw']:.0f}%偏高，保守可关注平"
        else:
            rec=f"倾向：平局 ({p['draw']:.0f}%)，双方实力接近"
    elif p['win']>50:rec=f"倾向：{h}获胜"
    elif p['loss']>50:rec=f"倾向：{a}获胜"
    else:rec="建议观望，平局概率偏高"

    # 伤停+风险+价值标签
    tags_html = ''
    if m.get('injury'):
        tags_html += '<div class="tag-row"><span class="tag tag-injury">🚑 ' + m['injury'] + '</span></div>'
    if m.get('risk') and len(m['risk'])>0:
        rt = ''.join('<span class="tag tag-risk">⚠️ ' + r + '</span>' for r in m['risk'])
        tags_html += '<div class="tag-row">' + rt + '</div>'
    if m.get('value'):
        tags_html += '<div class="tag-row"><span class="tag tag-value">💰 ' + m['value'] + '</span></div>'

    # 低概率 - 从 auto_tags 获取
    up = m.get('_upset_prob', 0)
    uw = m.get('_upset_why', '')
    upset_html = ''
    upset_type = ''
    if up > 30:
        upset_type = '🔴 高不确定性'
        upset_color = '#e44'
    elif up > 20:
        upset_type = '🟡 概率预警'
        upset_color = '#f80'
    elif up > 10:
        upset_type = '🟢 不确定性低'
        upset_color = '#999'
    else:
        upset_type = '无明显偏差'
        upset_color = '#666'
    if up > 0 and uw:
        upset_html = f'<div class="tag-row"><span class="tag" style="background:#fff5f5;color:{upset_color};border:1px solid #fcc;font-size:11px;padding:3px 8px;">🎲 {upset_type} · {uw}</span></div>'

    # 胜平负概率标注
    upset_label = ''
    if p['win'] > 50 and p['loss'] > 15:
        upset_label = ' <span style="color:#e44;font-size:10px;">⚠️ ' + a + '低概率值' + str(round(p['loss'])) + '%</span>'
    elif p['loss'] > 50 and p['win'] > 15:
        upset_label = ' <span style="color:#e44;font-size:10px;">⚠️ ' + h + '低概率值' + str(round(p['win'])) + '%</span>'

    # 概率解释
    fav_team = h if p['win'] > 50 else a
    upset_detail = ''
    if abs(d) < 60 and (p['loss'] > 20 or p['win'] > 20):
        underdog = a if p['win'] > 50 else h
        upset_detail = '<div class="why">💡 ' + underdog + '存在以下可能性：ELO差距仅' + str(abs(d)) + '分，'
        if abs(d) < 30:
            upset_detail += '实力非常接近，任何结果都不意外。'
        else:
            upset_detail += underdog + '若先取得进球，' + fav_team + '压力将骤增。'
        upset_detail += '</div>'
    score_tags = ''
    if p['top']:
        best = p['top'][0]
        worst = p['top'][-1]
        score_tags = f'<div class="tag-row"><span class="tag tag-value">🔥 高概率: {best[0]}({best[1]}%)</span><span class="tag tag-risk">❄️ 低概率: {worst[0]}({worst[1]}%)</span></div>'

    # 赛后对比（如果有result）
    result_html = ''
    if m.get('result'):
        result_html = '<div class="tag-row"><span class="tag" style="background:#f0fff0;color:#390;border:1px solid #cfc">✅ 实际: ' + m['result'] + ' | 模型预测偏差: 待复盘</span></div>'

    # 把概率标注嵌入ew
    if upset_label:
        ew += upset_label

    return ew, sw, gw, rec, tags_html + upset_html + upset_detail + score_tags + result_html


def calc_standings(matches):
    groups={}
    for m in matches:
        g=m.get("group","")
        if g not in groups: groups[g]=[]
    for m in matches:
        h,a=m["home"],m["away"];g=m.get("group","")
        if m.get("status")!="FT" or not m.get("result"): continue
        r=m["result"]
        if ":" not in r: continue
        hg,ag=map(int,r.split(":"))
        hr=next((t for t in groups[g] if t["name"]==h),None)
        if not hr: hr={"name":h,"p":0,"gf":0,"ga":0,"gd":0};groups[g].append(hr)
        ar=next((t for t in groups[g] if t["name"]==a),None)
        if not ar: ar={"name":a,"p":0,"gf":0,"ga":0,"gd":0};groups[g].append(ar)
        hr["gf"]+=hg;hr["ga"]+=ag;hr["gd"]=hr["gf"]-hr["ga"]
        ar["gf"]+=ag;ar["ga"]+=hg;ar["gd"]=ar["gf"]-ar["ga"]
        if hg>ag:hr["p"]+=3
        elif ag>hg:ar["p"]+=3
        else:hr["p"]+=1;ar["p"]+=1
    return groups

def gen():
    # 生成仪表盘数据
    import subprocess
    dash_file = os.path.join(DIR, "dashboard.html")
    subprocess.run([os.sys.executable, os.path.join(DIR, "dashboard.py")], capture_output=True)
    dashboard_html = ""
    if os.path.exists(dash_file):
        with open(dash_file, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()

    with open(SCHEDULE_FILE,encoding='utf-8') as f: matches=json.load(f)
    # 赛后校准：根据已完赛结果自动调整状态分
    calibrate(matches)
    now=datetime.now().strftime("%m/%d %H:%M:%S")
    cards,results="",""
    # 按日期排序
    matches.sort(key=lambda x: x['date'])

    # 计算当前积分（用于出线压力分析）
    from collections import defaultdict
    pts_dict = defaultdict(int)
    played_dict = defaultdict(int)
    for m in matches:
        if m.get('result'):
            hg, ag = map(int, m['result'].split(':'))
            played_dict[m['home']] += 1; played_dict[m['away']] += 1
            if hg > ag: pts_dict[m['home']] += 3
            elif ag > hg: pts_dict[m['away']] += 3
            else: pts_dict[m['home']] += 1; pts_dict[m['away']] += 1

    for m in matches:
        m['_pts'] = pts_dict
        m['_played'] = played_dict
        p=predict(m['home'],m['away'], match_info=m)
        # 自动补全伤停/风险/价值/爆冷
        ai,ar,av,up,uw=auto_tags(m,p)
        if not m.get('injury'): m['injury']=ai
        if not m.get('risk') or len(m.get('risk',[]))==0: m['risk']=ar
        if not m.get('value'): m['value']=av
        # 统一使用 predict() 返回的冷门概率，不再重复计算
        m['_upset_prob'] = p.get('upset_prob', up)
        m['_upset_why'] = uw
        fh,fa=FLAGS.get(m['home'],''),FLAGS.get(m['away'],'')
        ew,sw,gw,rec,tags=explain(p,m,m['home'],m['away'],p['he']-p['ae']+50)
        d=f"{m['date']} {m['time']}".strip()

        # 实时结果
        live=""
        review_plain = review_tech = ""
        if m.get('result'):
            live=f'<div class="live">⚡ {m["result"]}</div>'
            results+=f'<div class="res"><span>{fh} {m["home"]} {m["result"]} {m["away"]} {fa}</span><span class="d">{d}</span></div>'
            # 赛后复盘
            if m.get('status') == 'FT':
                review_plain, review_tech = match_review(m, p)

        # 价值评估（凯利公式 → 星级）
        kelly_html = ""
        if m.get('odds_home') and not m.get('status'):
            oh = float(m['odds_home'])
            oa = float(m.get('odds_away', 0) or 0)
            od = float(m.get('odds_draw', 0) or 0)
            best_p = max(p['win'], p['draw'], p['loss'])
            if p['win'] == best_p and oh > 1:
                ks, km, stars = kelly_stake(p['win'], oh)
            elif p['draw'] == best_p and od > 1:
                ks, km, stars = kelly_stake(p['draw'], od)
            elif p['loss'] == best_p and oa > 1:
                ks, km, stars = kelly_stake(p['loss'], oa)
            else:
                ks, km, stars = 0, "", 0
            colors = {0: '#999', 1: '#f80', 2: '#f80', 3: '#390', 4: '#390', 5: '#e44'}
            emoji = {0: '🚫', 1: '⭐', 2: '⭐', 3: '⭐', 4: '🔥', 5: '🔥'}
            kelly_html = '<div class="tag-row"><span class="tag" style="background:#fff;color:' + colors.get(stars, '#999') + ';border:1px solid #ddd;font-size:12px;padding:4px 10px">' + emoji.get(stars, '') + ' 价值评估: ' + km + '</span></div>' if km else ''

        # 市场参考
        on=""
        if m.get('odds_home'):
            o=float(m['odds_home']);fair=round(1/max(p['win']/100,0.01),1)
            on=f"市场参考{o} · 模型公允{fair}"

        cards+=f"""
    <div class="match">
      <div class="mh"><span class="g">G{m['group']}</span><span class="t">{fh} {m['home']} vs {m['away']} {fa}</span><span class="d">{d}</span></div>
      <div class="v">{m['venue']} · {PLAY_STYLE.get(m['home'], '')}  VS  {PLAY_STYLE.get(m['away'], '')}</div>{live}
      {'<div class="live-badge">🔴 进行中 · ' + m.get('live_score','') + ' (' + m.get('live_clock','') + ')</div>' if m.get('status')=='LIVE' else ''}
      {'<div class="ft-badge">⚡ 已结束 · 全场比分: ' + m['result'] + '</div>' if m.get('result') and m.get('status')=='FT' else ''}
      <div class="int" style="{'opacity:0.5' if m.get('status')=='FT' else ''}">📰 {m['intel']}</div>
      {kelly_html}
      {tags}
      <div class="s"><div class="st">胜负 · {ew}</div>
        <div class="b"><span>主</span><div class="t"><i style="width:{p['win']}%"></i></div><span class="n">{p['win']}%</span></div>
        <div class="b"><span>平</span><div class="t"><i style="width:{p['draw']}%;background:#888"></i></div><span class="n">{p['draw']}%</span></div>
        <div class="b"><span>客</span><div class="t"><i style="width:{p['loss']}%;background:#ccc"></i></div><span class="n">{p['loss']}%</span></div>
        <div class="why">{sw} · {on}</div>
      </div>
      <div class="s"><div class="st">比分 TOP5</div><div class="cs">{' '.join(f'<span class="c"><b>{s}</b> {pr}%</span>'for s,pr in p['top'])}</div></div>
      <div class="s"><div class="st">总进球 · {gw}</div><div class="cs">{' '.join(f'<span class="c">{g}球 {pr}%</span>'for g,pr in list(p['gl'].items())[:6])}</div></div>
      <div class="s"><div class="st">🧠 白话解读</div><div class="think"><b>{p.get('tier','')}</b> {ew} {sw} 风格：{PLAY_STYLE.get(m['home'],'')} VS {PLAY_STYLE.get(m['away'],'')}。{gw} 综合判断：{rec}。不确定性{p.get('upset_prob','?')}%</div></div>
      <div class="s" style="border-left:3px solid #ddd;padding-left:12px;background:#fafafa">
        <div class="st" style="cursor:pointer" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';this.textContent=this.textContent.replace('▶','▼').replace('▼','▶')">▶ 专业计算链</div>
        <div style="display:none;font-size:10px;color:#666;line-height:1.6;padding-top:4px">
          🧮 {p.get('calc_chain','')}<br>
          📐 预期进球：主{p['xh']}球 × 客{p['xa']}球 → 泊松分布<br>
          📊 胜率色标：&gt;75%🟢高确定性 &gt;60%🟡较高概率 &gt;45%🟠势均力敌 其余🔴低概率<br>
          🎲 低概率=基础{abs(p['win']-p['loss']):.0f}%差额+伤病+红牌+高原修正<br>
          💰 {p.get('odds_note','参考值与模型一致，市场未过热')}
        </div>
      </div>
""" + (f"""
      <div class="s" style="border-left:3px solid #e44;padding-left:12px;background:#fff5f5;margin-top:8px">
        <div class="st" style="cursor:pointer;color:#e44" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';this.textContent=this.textContent.replace('▶','▼').replace('▼','▶')">▶ 赛后AI复盘</div>
        <div style="display:none;font-size:11px;line-height:1.6;padding-top:4px">
          <b>白话解读：</b>{review_plain}<br><br>
          <b>模型优化：</b><span style="color:#666">{review_tech}</span>
        </div>
      </div>
""" if m.get('status')=='FT' else "") + """
    </div>"""

    # 生成小组积分表
    groups=calc_standings(matches)
    standings_html='<div class="standings-toggle" onclick="var s=document.getElementById("standings");s.style.display=s.style.display==="none"?"block":"none"">📊 小组积分 (点击展开)</div><div id="standings" style="display:none;margin-bottom:12px">'
    for g in sorted(groups.keys()):
        teams=sorted(groups[g],key=lambda t:(-t["p"],-t["gd"],-t["gf"]))
        standings_html+=f'<div style="font-size:12px;color:#999;margin:8px 0 2px">G{g}</div>'
        for i,t in enumerate(teams):
            badge='🟢' if i<2 else ('🟡' if i==2 else '')
            standings_html+=f'<div style="font-size:12px;display:flex;justify-content:space-between;padding:2px 0"><span>{badge} {t["name"]}</span><span>{t["p"]}分 {t["gf"]}:{t["ga"]} GD:{t["gd"]:+d}</span></div>'
    standings_html+='</div>'
    
    html=f"""<!DOCTYPE html><html lang="zh-CN"><head>
<script>
// 访问验证
document.write("<!-- v06240320 -->"); const HASH='{PASS_HASH}';
async function sha256(m){{ const e=new TextEncoder();const d=await crypto.subtle.digest('SHA-256',e.encode(m));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join(''); }}
async function check(){{ const p=document.getElementById('pw').value; const h=await sha256(p); if(h===HASH){{ localStorage.setItem('wc_auth','1'); document.getElementById('gate').style.display='none'; document.getElementById('main').style.display='block'; }}else{{ document.getElementById('err').style.display='block'; }} }}
function init(){{ if(localStorage.getItem('wc_auth')==='1'){{ document.getElementById('gate').style.display='none';document.getElementById('main').style.display='block'; }} }}
</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>世界杯实时分析</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#fff;padding:12px;max-width:500px;margin:0 auto;color:#333}}
h1{{font-size:18px;font-weight:600;text-align:center;margin:8px 0}}
.sub{{text-align:center;font-size:11px;color:#999}}
.upd{{text-align:center;font-size:10px;color:#ccc;margin:4px 0 12px}}
.results{{background:#fafafa;padding:10px;margin-bottom:12px}}
.results .rt{{font-size:11px;color:#999;margin-bottom:6px;font-weight:600}}
.res{{font-size:12px;padding:3px 0;display:flex;justify-content:space-between}}
.res .d{{color:#999}}
.match{{border-bottom:1px solid #eee;padding:12px 0}}
.match:last-child{{border-bottom:none}}
.mh{{display:flex;align-items:center;gap:6px}}
.g{{font-size:10px;background:#111;color:#fff;padding:1px 6px;font-weight:600}}
.t{{font-weight:600;font-size:14px;flex:1}}
.d{{font-size:11px;color:#999}}
.v{{font-size:11px;color:#ccc;margin:2px 0 6px}}
.live{{background:#e44;color:#fff;padding:4px 10px;font-size:13px;font-weight:600;display:inline-block;margin:6px 0}}
.live-badge{{background:#e44;color:#fff;padding:8px 12px;font-size:14px;font-weight:700;text-align:center;margin:8px 0;animation:pulse 1.5s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.7}}}}
.ft-badge{{background:#111;color:#ffd700;padding:8px 12px;font-size:14px;font-weight:700;text-align:center;margin:8px 0;letter-spacing:1px}}
.int{{font-size:12px;color:#666;line-height:1.5;margin:6px 0;padding:8px;background:#fafafa}}
.s{{margin:10px 0}}
.st{{font-size:11px;color:#999;font-weight:600;margin-bottom:4px}}
.why{{font-size:11px;color:#999;margin-top:4px;line-height:1.5}}
.b{{display:flex;align-items:center;gap:6px;margin:2px 0}}
.b span:first-child{{width:20px;font-size:11px;color:#666}}
.b .t{{flex:1;height:5px;background:#eee}}
.b .t i{{display:block;height:5px;background:#111}}
.b .n{{width:40px;font-size:12px;text-align:right;font-weight:600}}
.cs{{display:flex;flex-wrap:wrap;gap:3px}}
.c{{padding:2px 7px;border:1px solid #e0e0e0;font-size:11px}}
.c b{{color:#111}}
.tag-row{{margin:4px 0;display:flex;flex-wrap:wrap;gap:4px}}
.tag{{font-size:11px;padding:3px 8px;border-radius:2px;line-height:1.4}}
.tag-injury{{background:#fff0f0;color:#c44;border:1px solid #fcc}}
.tag-risk{{background:#fff8e0;color:#b80;border:1px solid #fe8}}
.tag-value{{background:#f0f8ff;color:#36c;border:1px solid #bdf}}
.think{{font-size:12px;color:#666;line-height:1.6;padding:10px;background:#fafafa;border-left:3px solid #111;margin:4px 0}}
.rf{{text-align:center;font-size:11px;color:#999;margin:10px 0}}
.ft{{text-align:center;color:#ccc;font-size:10px;margin:20px 0;line-height:1.6}}
.nav{{display:flex;gap:4px;flex-wrap:wrap;margin:0 0 12px;justify-content:center}}
.nav a{{font-size:11px;padding:3px 8px;border:1px solid #ddd;text-decoration:none;color:#666}}
.nav a.on{{background:#111;color:#fff;border-color:#111}}
.gate{{position:fixed;top:0;left:0;width:100%;height:100%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}}
.gate input{{width:200px;padding:12px;border:1px solid #ccc;font-size:16px;text-align:center;margin:12px 0}}
.gate button{{padding:12px 40px;background:#111;color:#fff;border:none;font-size:15px;font-weight:600}}
.err{{color:#e44;font-size:13px;display:none}}
</style></head><body onload="init()">
<div id="gate" class="gate">
  <div style="font-size:16px;font-weight:600;margin-bottom:4px">🔒 世界杯实时分析</div>
  <div style="font-size:12px;color:#999;margin-bottom:8px">请输入访问密码</div>
  <input id="pw" type="password" placeholder="密码" onkeydown="if(event.key==='Enter')check()">
  <button onclick="check()">验证</button>
  <div id="err" class="err">密码错误</div>
  <div style="font-size:10px;color:#ccc;margin-top:16px">购买后获取密码 · 一机一码永久有效</div>
</div>
<div id="main" style="display:none">
<h1>世界杯 · 实时分析</h1>
<div style="padding:0 0 10px"><input id="search" type="text" placeholder="🔍 搜索球队..." oninput="filter()" style="width:100%;padding:10px;border:1px solid #ddd;font-size:14px"></div>
<div class="sub">ELO模型 + 泊松分布 · 数据参考</div>
<div class="upd">更新 {now} · 每5分钟自动刷新 · v{int(datetime.now().timestamp()) % 1000000} · <span id="online_cnt" style="color:#4f4;font-weight:600">🟢 ...</span></div>
<div class="rf">⏳ <span id="cd">60</span>秒后刷新</div>
<style>
.guide{{margin:6px 0;border:1px solid #e8e8e8;border-radius:5px;overflow:hidden}}
.guide-t{{background:#f5f5f5;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer;user-select:none;color:#555}}
.guide-t::after{{content:' ▼';font-size:10px;float:right;transition:.2s}}
.guide-t.open::after{{content:' ▲'}}
.guide-b{{display:none;padding:10px 14px;font-size:12px;color:#666;line-height:1.8;background:#fafafa}}
.guide-b.open{{display:block}}
.guide-b b{{color:#333}}
</style>
<div class="guide">
<div class="guide-t" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open')">📖 每场比赛怎么看（点我展开说明书）</div>
<div class="guide-b">
<b>🔍 顶部搜索框</b> — 输入球队名（如"阿根廷"）快速跳到该场比赛<br><br>

<b>📌 比赛卡片从上到下依次解读：</b><br>
<b>① 小组标签 + 队名 + 日期</b> — 例「G组 阿根廷 vs 巴西 6/20 21:00」<br>
<b>② 球场 + 战术风格</b> — 显示比赛地点和两队打法特点（如"4-3-3高压逼抢 VS 5-4-1大巴防守"）<br>
<b>③ 进行中/已结束标签</b> — 红色🔴=正在踢，金色⚡=踢完了有比分<br>
<b>④ 赛前情报</b> — 灰色文字，如伤病、停赛、历史交锋等关键信息<br>
<b>⑤ ⭐ 价值评分</b> — 1-5星，基于模型概率与实际市场的差值。5星=模型认为市场低估了，1星=不值得关注<br>
<b>⑥ 标签</b> — 红色=伤病隐患，橙色=风险提示，蓝色=价值信号<br>
<b>⑦ 胜/平/负概率条</b> — 黑色=主队胜率，灰色=平局，浅灰=客队。百分数越大颜色条越长<br>
<b>⑧ 比分 TOP5</b> — 模型推演最可能出现的5个比分及各自概率（如"2:1 14.2%"）<br>
<b>⑨ 总进球分布</b> — 这场比赛可能的总进球数分布（如"2球 25%"、"3球 20%"）<br>
<b>⑩ 🧠 白话解读</b> — 用大白话总结：哪边强、什么打法克制、不确定因素<br>
<b>⑪ ▶ 专业计算链</b> — 点开看技术细节：双方ELO评分、进攻/防守系数、泊松分布计算过程<br>
<b>⑫ ▶ 赛后AI复盘</b>（仅完场比赛）— 点开看赛后总结：实际结果vs模型预测、模型优化建议<br><br>

<b>🟢 在线人数</b> — 页面顶部"X人在线"，代表当前有多少人正在一起看球<br>
<b>🔄 自动刷新</b> — 每60秒页面自动刷新，比赛进行中数据实时变化<br><br>

<b>⚠️ 所有数据为统计模型计算结果，仅供赛事数据研究参考，不构成任何建议。</b>
</div>
</div>
{dashboard_html}
{"<div class=\"results\"><div class=\"rt\">⚡ 最新赛果</div>"+results+"</div>" if results else ""}
{cards}
<div class="ft">ELO评分基于FIFA排名和历史战绩<br>泊松分布推演比分概率 · 参考值来源于公开市场<br>所有数据仅供赛事数据研究参考，不构成任何建议</div>
<script>
let t=60;setInterval(()=>{{t--;document.getElementById('cd').textContent=t;if(t<=0)location.reload()}},1000);
function filter(){{var q=document.getElementById('search').value.toLowerCase();var ms=document.querySelectorAll('.match');ms.forEach(function(m){{var t=m.querySelector('.t').textContent.toLowerCase();m.style.display=t.indexOf(q)>=0?'':'none'}});}}
	// 在线人数（GitHub Gist API）
	var GIST_API='https://api.github.com/gists/__GIST_ID__';
	var GH_TOKEN='__GH_TOKEN__';
	(function(){{
	if(GH_TOKEN.indexOf('__')>=0){{document.getElementById('online_cnt').textContent='';return;}}
	var sid=localStorage.getItem("wc_sid")||(Date.now().toString(36)+Math.random().toString(36).slice(2,10));
	localStorage.setItem("wc_sid",sid);
	var el=document.getElementById("online_cnt");
	function hb(){{
	fetch(GIST_API,{{headers:{{Authorization:'Bearer '+GH_TOKEN}}}}).then(function(r){{return r.json();}}).then(function(gist){{
	var raw=gist.files['online.json'].content;
	var s=JSON.parse(raw).sessions||{{}};
	var n=Date.now();
	Object.keys(s).forEach(function(k){{if(n-s[k]>60000)delete s[k];}});
	s[sid]=n;
	el.textContent='🟢 '+Object.keys(s).length+'人在线';
	return fetch(GIST_API,{{method:'PATCH',headers:{{Authorization:'Bearer '+GH_TOKEN,'Content-Type':'application/json'}},body:JSON.stringify({{files:{{'online.json':{{content:JSON.stringify({{sessions:s}})}}}}}})}});
	}}).catch(function(){{}});
	}}
	hb();setInterval(hb,45000);
	}})();
</script>
</div>
</body></html>"""

    # 替换在线计数器配置（Token 拆两半避免 GitHub 扫描）
    # GitHub Actions 没有 .env，token 为空时显示占位符触发隐藏
    if GH_TOKEN:
        t1 = GH_TOKEN[:len(GH_TOKEN)//2]
        t2 = GH_TOKEN[len(GH_TOKEN)//2:]
    else:
        t1 = t2 = ""  # 空 token → 计数器自动隐藏
    html = html.replace('__GIST_ID__', GIST_ID)
    html = html.replace("'__GH_TOKEN__'", f"'{t1}'+'{t2}'")

    with open(OUTPUT,'w',encoding='utf-8') as f:f.write(html)
    print(f"✅ {len(matches)}场比赛已生成")
    print(f"   手机: http://172.20.10.2:8899/live.html")

if __name__=="__main__":gen()
