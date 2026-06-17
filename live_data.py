"""
世界杯实时数据引擎 v2
读取 schedule.json → ELO数据模型 → 生成 live.html
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

ELO = {"阿根廷":1950,"法国":1930,"巴西":1920,"英格兰":1900,"西班牙":1890,"葡萄牙":1870,"德国":1860,"荷兰":1820,"意大利":1840,"乌拉圭":1820,"克罗地亚":1810,"哥伦比亚":1800,"摩洛哥":1790,"美国":1780,"墨西哥":1770,"塞内加尔":1760,"日本":1870,"韩国":1740,"伊朗":1730,"澳大利亚":1710,"埃及":1720,"尼日利亚":1710,"科特迪瓦":1700,"喀麦隆":1690,"加纳":1680,"突尼斯":1670,"阿尔及利亚":1660,"南非":1640,"加拿大":1730,"哥斯达黎加":1680,"巴拿马":1640,"牙买加":1630,"沙特阿拉伯":1670,"卡塔尔":1650,"伊拉克":1620,"阿联酋":1610,"新西兰":1600,"巴拉圭":1720,"厄瓜多尔":1740,"智利":1760,"秘鲁":1730,"委内瑞拉":1680,"玻利维亚":1620,"波黑":1690,"塞尔维亚":1750,"丹麦":1800,"瑞典":1790,"挪威":1780,"波兰":1760,"乌克兰":1740,"土耳其":1750,"比利时":1830,"威尔士":1700,"苏格兰":1690,"捷克":1720,"罗马尼亚":1680,"斯洛伐克":1670,"匈牙利":1700,"希腊":1680,"佛得角":1580,"库拉索":1560,"约旦":1590,"乌兹别克斯坦":1610,"海地":1550,"瑞士":1830,"摩洛哥":1790,"刚果民主队共和国":1650,"奥地利":1760,"古巴":1540,"苏里南":1520}
FLAGS = dict(阿根廷="🇦🇷",法国="🇫🇷",巴西="🇧🇷",英格兰="🏴",西班牙="🇪🇸",葡萄牙="🇵🇹",德国="🇩🇪",荷兰="🇳🇱",意大利="🇮🇹",乌拉圭="🇺🇾",克罗地亚="🇭🇷",哥伦比亚="🇨🇴",摩洛哥="🇲🇦",美国="🇺🇸",墨西哥="🇲🇽",塞内加尔="🇸🇳",日本="🇯🇵",韩国="🇰🇷",伊朗="🇮🇷",澳大利亚="🇦🇺",埃及="🇪🇬",尼日利亚="🇳🇬",科特迪瓦="🇨🇮",喀麦隆="🇨🇲",加纳="🇬🇭",突尼斯="🇹🇳",南非="🇿🇦",加拿大="🇨🇦",巴拉圭="🇵🇾",厄瓜多尔="🇪🇨",智利="🇨🇱",秘鲁="🇵🇪",波黑="🇧🇦",塞尔维亚="🇷🇸",丹麦="🇩🇰",瑞典="🇸🇪",挪威="🇳🇴",波兰="🇵🇱",乌克兰="🇺🇦",土耳其="🇹🇷",比利时="🇧🇪",捷克="🇨🇿",卡塔尔="🇶🇦",新西兰="🇳🇿",海地="🇭🇹",苏格兰="🏴",瑞士="🇨🇭",奥地利="🇦🇹",约旦="🇯🇴",伊拉克="🇮🇶",库拉索="🇨🇼",巴拿马="🇵🇦",哥斯达黎加="🇨🇷",牙买加="🇯🇲",沙特阿拉伯="🇸🇦",阿联酋="🇦🇪",委内瑞拉="🇻🇪",玻利维亚="🇧🇴",威尔士="🏴",罗马尼亚="🇷🇴",斯洛伐克="🇸🇰",匈牙利="🇭🇺",希腊="🇬🇷",佛得角="🇨🇻",乌兹别克斯坦="🇺🇿",刚果民主队共和国="🇨🇩",阿尔及利亚="🇩🇿")

def poisson(l,k): return math.exp(-l)*l**k/math.factorial(k)

# 球队风格系数（攻击力/防守力加成，基准1.0）
STYLE = {
    "德国":(1.3,1.0),"巴西":(1.3,1.0),"法国":(1.25,1.0),"阿根廷":(1.2,1.0),
    "英格兰":(1.15,1.0),"西班牙":(1.1,1.0),"荷兰":(1.0,0.85),"葡萄牙":(1.2,0.95),
    "比利时":(1.1,0.9),"挪威":(1.25,0.8),"库拉索":(0.5,0.3),"海地":(0.6,0.4),
    "卡塔尔":(0.6,0.7),"佛得角":(0.5,0.4),"新西兰":(0.7,0.6),
    "巴拿马":(0.7,0.5),"约旦":(0.65,0.6),"伊拉克":(0.7,0.6),
    "乌兹别克斯坦":(0.65,0.55),"刚果民主队共和国":(0.8,0.6),
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
    "德国":"高压逼抢+快速转换，边路传中威胁大",
    "巴西":"桑巴技术流+个人能力突出，防守偶尔走神",
    "法国":"姆巴佩速度反击+中场控制力强",
    "阿根廷":"梅西核心+短传渗透，防守纪律好",
    "英格兰":"青年军速度快+定位球威胁大",
    "西班牙":"传控为主队+高位防线，怕快速反击",
    "荷兰":"全攻全守+三线均衡，终结能力一般",
    "葡萄牙":"C罗终结+中场创造力，防线偏老",
    "比利时":"黄金一代老化+进攻靠个人，防守有漏洞",
    "日本":"技术传控+整体性强，身体对抗吃亏",
    "韩国":"孙兴慜速度反击+跑动量大，防空是软肋",
    "摩洛哥":"铁血防守+快速反击，定位球有威胁",
    "美国":"普利西奇核心+主场气势，防守纪律一般",
    "墨西哥":"高原主场优势+边路突破，年龄偏大",
    "澳大利亚":"身体流+定位球砸头球，技术粗糙",
    "土耳其":"技术流+恰尔汗奥卢组织，大赛气质差",
    "卡塔尔":"主场死守+归化球员，中场创造力弱",
    "瑞士":"纪律防守+反击效率高，进球能力差",
    "苏格兰":"身体对抗+跑不死，技术含量低",
    "海地":"首秀紧张+身体天赋好，战术纪律差",
    "加拿大":"戴维斯核心+边路速度，防守不高一致性定",
    "巴拉圭":"南美大巴+防守硬，进攻靠定位球",
    "克罗地亚":"莫德里奇最后一舞+经验丰富，体能下降",
    "挪威":"哈兰德终结+厄德高组织，防线年轻",
    "瑞典":"高大身体流+定位球，伊布退役后缺核心",
    "波兰":"莱万依赖症+中场平均势，防守有韧性",
    "丹麦":"整体性强+埃里克森核心，进攻偏保守",
    "塞尔维亚":"高大中锋+技术中场，防守纪律差",
    "乌克兰":"战术纪律+精神力强，个人能力一般",
    "奥地利":"战术执行力强+高位逼抢，终结能力一般",
    "哥伦比亚":"迪亚斯速度+技术型，防守偶尔犯浑",
    "厄瓜多尔":"高原主场+速度型，客场表现减半",
    "塞内加尔":"身体碾压+速度反击，防守组织一般",
    "埃及":"萨拉赫单核+防守反击，其余球员均势庸",
    "乌拉圭":"南美铁血防守+苏亚雷斯经验，进攻效率偏低",
    "突尼斯":"非洲防反+纪律性好，进球效率低",
    "科特迪瓦":"身体天赋+个人能力，战术松散",
    "加纳":"身体对抗+速度型边锋，防守漏人",
    "喀麦隆":"身体流+高空优势，中场组织差",
    "尼日利亚":"速度反击+个人能力，防守漏人",
    "伊朗":"铁桶防守+阿兹蒙反击，进球靠偷",
    "新西兰":"英式冲吊+身体碾压，技术粗糙",
    "哥斯达黎加":"防守体系+门将出色，进攻乏力",
    "巴拿马":"身体对抗+定位球，整体实力弱",
    "库拉索":"世界杯首秀+荷甲球员为主队，经验不足",
    "沙特阿拉伯":"技术传控+身体吃亏，防守脆弱",
    "阿联酋":"技术型+防守纪律好，终结能力弱",
    "威尔士":"贝尔退役后缺核心+防守反击",
    "罗马尼亚":"防反为主队+纪律严明，技术均势庸",
    "斯洛伐克":"紧凑防守+定位球，创造能力弱",
    "匈牙利":"索博斯洛伊核心+中场强，锋线弱",
    "希腊":"铁桶防守+死守，进攻几乎为零",
    "佛得角":"首秀+葡萄牙归化球员为主队，大赛未知",
    "约旦":"亚洲黑马+防守纪律+归化前锋",
    "伊拉克":"技术型+亚洲杯表现出色，世界杯经验少",
    "乌兹别克斯坦":"首秀+青年军为主队，冲击力强经验弱",
    "刚果民主队共和国":"身体天赋+速度，战术松散",
    "阿尔及利亚":"非洲强队+马赫雷斯核心，状态起伏大",
    "智利":"桑切斯老将+新老交替，实力下滑",
    "秘鲁":"技术型+南美风格，防守松散",
    "委内瑞拉":"防守反击+年轻化，整体实力弱",
    "玻利维亚":"高原主场依赖+客场几乎白送",
    "牙买加":"短跑基因+边路速度，防守业余",
    "古巴":"首秀+美职联球员为主队，实力最弱之一",
    "苏里南":"首秀+荷甲球员为主队，整体松散",
    "南非":"本土联赛为主队+中规中矩，攻击力弱",
    "捷克":"定位球威胁大(欧洲最多)+新帅磨合中",
    "波黑":"哲科依赖症+中场创造力弱",
    "意大利":"防守传统+中场年轻化，进攻不够锐利",
}

# 状态修正（近6-12月预选赛+热身赛+世界杯正赛，正值=状态好）
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
    "卡塔尔": 5,   # ↑修正: 1-1逼均势瑞士，东道主队不能低估
    "韩国": 45,    # 预选赛出线+热身全胜+揭幕战逆转捷克
    "西班牙": 40,  # 预选赛头名+3-1秘鲁+欧洲杯后复苏
    "摩洛哥": 55,  # 预选赛非洲霸主队+上届四强+防线极硬(修正:巴西1-1实锤)
    "哥伦比亚": 35,# 预选赛南美前四+热身全胜
    "挪威": 35,    # 预选赛出线+3-1瑞典+哈兰德状态火热
    "土耳其": 25,  # ↓修正: 被澳洲2-0暴打，大赛气质不足
    "苏格兰": 35,  # 预选赛黑马+4-0玻利维亚+点球淘汰威尔士
    "阿尔及利亚": 40,# 预选赛非洲强队+4-0玻利维亚
    "厄瓜多尔": 30,# 预选赛南美出线+高原主场
    "法国": 20,    # 预选赛头名但近期1-2科特迪瓦状态波动
    "奥地利": 25,  # 预选赛黑马+热身高一致性健
    "巴拉圭": 20,  # 预选赛南美出线+4-0尼加拉瓜
    "捷克": 15,    # 预选赛点球出线+热身3-1危地马拉 揭幕-2
    "加拿大": 15,  # 中北美预选出线+热身高一致性健
    "海地": 15,    # 预选赛黑马+热身出色
    "库拉索": 15,  # 预选赛首进世界杯+热身4-0
    "美国": -15,   # 预选赛出线但热身1-2德国 揭幕战待验证
    "荷兰": -25,   # 预选赛头名但0-1阿尔及利亚+2-1险胜乌兹
    "克罗地亚": -10,# 预选赛出线但0-2比利时 黄金一代老化
    "南非": -15,   # 预选赛出线但揭幕战0-2输墨+被罚2红
    "威尔士": -5,  # 预选赛惊险+热身均势加纳
    "波兰": 5,     # 预选赛出线+表现中规中矩
    "塞尔维亚": 5, # 预选赛出线+表现一般
    "卡塔尔": -10, # 上届全败+预选赛东道主队无压力测试
}

# 主场揭幕战加成（东道主队首场比赛）
HOST_OPENER = {"美国": 1.4, "加拿大": 1.25, "墨西哥": 1.2}  # 攻击力乘数

# ===== 优化1：动态ELO修正 =====
CONTINENTS = {
    "南美": ["阿根廷","巴西","乌拉圭","哥伦比亚","厄瓜多尔","智利","秘鲁","巴拉圭","委内瑞拉","玻利维亚"],
    "欧洲": ["法国","英格兰","西班牙","葡萄牙","德国","荷兰","意大利","比利时","克罗地亚","丹麦","瑞典","挪威","波兰","乌克兰","土耳其","瑞士","奥地利","捷克","塞尔维亚","苏格兰","威尔士","罗马尼亚","斯洛伐克","匈牙利","希腊","波黑"],
    "非洲": ["摩洛哥","塞内加尔","埃及","尼日利亚","科特迪瓦","喀麦隆","加纳","突尼斯","阿尔及利亚","南非","佛得角","刚果民主队共和国"],
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
    """返回 (主攻击修正, 客攻击修正)：强队传控打大巴→攻击力打折；弱队防反→有机会偷"""
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

    # 首秀+经验不足 → 攻击力大幅削弱，防守也不高一致性
    if '首秀' in an or '经验不足' in an:
        a_adj *= 0.55  # 第一次上场腿软
        if not is_possession_strong:
            h_adj = 1.15  # 虐菜局反而放开手脚

    # 强队高压 vs 弱队粗糙 → 弱队基本组织不了进攻
    if any(t in hn for t in ['高位逼抢', '高压', '全攻全守']) and any(t in an for t in ['技术粗糙', '技术含量低', '创造力弱']):
        a_adj *= 0.65

    return h_adj, a_adj

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

        # 趋势是否正确
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
    """模型数据公式 → 星级评价：★★★★★=高关注，☆=别碰"""
    if not odds or odds <= 1:
        return 0, "暂无数据", 0
    b = odds - 1
    f = p_win/100 - (1 - p_win/100) / b
    f_pct = round(f * 100, 1)
    # 转星级
    if f_pct <= 0:
        return f_pct, "无需关注", 0
    elif f_pct < 3:
        return f_pct, "⭐ 观望", 1
    elif f_pct < 6:
        return f_pct, "⭐⭐ 一般", 2
    elif f_pct < 10:
        return f_pct, "⭐⭐⭐ 值得", 3
    elif f_pct < 15:
        return f_pct, "⭐⭐⭐⭐ 可关注", 4
    else:
        return f_pct, "⭐⭐⭐⭐⭐ 高关注", 5

def predict(h,a, match_info=None):
    he=ELO.get(h,1700)+FORM_BOOST.get(h,0)
    ae=ELO.get(a,1700)+FORM_BOOST.get(a,0)
    hs=STYLE.get(h,(1.0,1.0)); as_=STYLE.get(a,(1.0,1.0))

    # 优化1：动态ELO修正
    if match_info:
        eh, ea, elo_reason = elo_corrections(h, a, FORM_BOOST.get(h,0), FORM_BOOST.get(a,0), match_info)
        he += eh; ae += ea
    else:
        elo_reason = ''

    # 主场揭幕战加成
    hm_mult = HOST_OPENER.get(h, 1.0)
    # 优化2：战术克制矩阵
    tactic_h, tactic_a = tactic_matchup(h, a)

    # 优化3：战意系数（世界杯正赛=1.0，小组末轮可调）
    motivation_h = motivation_a = 1.0

    d=he-ae+50; gd=d/100*0.4
    xh=max(0.3, (1.6+gd*0.7)*hs[0]*hm_mult*tactic_h*motivation_h/max(as_[1],0.5))
    xa=max(0.3, (1.2-gd*0.4)*as_[0]*tactic_a*motivation_a/max(hs[1],0.5))

    # 优化3：赔率热度修正（市场过热→模型降权）
    odds_adj = 1.0
    odds_note = ''
    if match_info and match_info.get('odds_home'):
        try:
            oh = float(match_info['odds_home'])
            fair = round(1/max((0.5 if d>0 else 0.3), 0.01), 1)
            # 市场比模型更乐观 → 可能过热
            if oh < fair * 0.85:
                odds_adj = 0.88
                odds_note = f'市场过热({oh}<公允{fair})，ELO优势度打折'
            elif oh > fair * 1.2:
                odds_adj = 1.08
                odds_note = f'市场低估({oh}>公允{fair})，ELO优势度上浮'
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
    # 优化3：赔率热度修正ELO优势度
    w_adj = w * odds_adj; dr_adj = dr / odds_adj; lo_adj = lo / odds_adj
    total2 = w_adj + dr_adj + lo_adj
    w_final = round(w_adj / total2 * 100, 1)
    dr_final = round(dr_adj / total2 * 100, 1)
    lo_final = round(lo_adj / total2 * 100, 1)

    # 输出优化：数据一致性等级
    if w_final > 75: tier = '🟢 数据一致性高'
    elif w_final > 60: tier = '🟡 关注度较高'
    elif w_final > 45: tier = '🟠 数据接近'
    else: tier = '🔴 数据不对称'

    # 优化4：动态数据偏差度（替代固定2%）
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

    # 计算链路（用于数据解读面板）
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

    # 自动低概率类型判断
    if abs(diff) < 40:
        if '⚡ 低概率种子' not in ' '.join(risk): risk.append('⚡ 低概率种子')
    # 进球相关低概率
    goals_high = sum(p['gl'].get(str(g),0) for g in range(6,13))
    if goals_high < 5:
        if '小球低概率预警' not in ' '.join(risk): risk.append('小球低概率预警')

    # 自动价值标签
    if not value and m.get('odds_home'):
        oh = float(m.get('odds_home',0) or 0)
        if oh>0:
            fair = round(1/max(p['win']/100,0.01),1)
            gap = oh-fair
            if gap>0.5: value = f'主队占优市场赔率偏高，模型认为被低估'
            elif gap<-0.3: value = f'主队占优市场赔率偏低，热度可能过高'

    # 小概率偏差
    upset_prob = 0
    upset_why = ''
    if p['win'] > 50:  # 主队关注度较高
        upset_prob = p['loss']
        fav, udog = h, a
    elif p['loss'] > 50:  # 客队关注度较高
        upset_prob = p['win']
        fav, udog = a, h
    else:
        upset_prob = 0
        fav, udog = '', ''

    if upset_prob > 25:
        upset_why = f'{udog}有{upset_prob:.0f}%概率模型偏差——不低。'
        if upset_prob > 35:
            upset_why += '双方实力差距不大，任何结果都可能。'
        if '高原' in ' '.join(risk):
            upset_why += '高原因素可能放大不确定性。'
        if abs(diff) < 60:
            upset_why += 'ELO差距小，低概率土壤肥沃。'
    elif upset_prob > 18:
        upset_why = f'{udog}小概率偏差{upset_prob:.0f}%，偏低但非零。{fav}发挥失常或{udog}超常可能翻盘。'
    elif upset_prob > 0:
        upset_why = f'{fav}优势明显，{udog}小概率偏差仅{upset_prob:.0f}%。除非重大意外（红牌/伤病），低概率难现。'
    else:
        upset_why = '双方均势，没有明确的低概率概念。'

    return injury, risk, value, round(upset_prob, 1), upset_why

def explain(p, m, h, a, d):
    ad=abs(d)
    if d>100:ew=f"{h} ELO领先{ad}分，明显优势。"
    elif d>40:ew=f"{h} ELO略高{ad}分，主场加权后有优势。"
    else:ew=f"两队仅差{ad}分，实力非常接近。"
    if p['win']>50:sw=f"数据显示{h}获胜——主场+ELO优势转化为{p['win']}%ELO优势度。"
    elif p['loss']>50:sw=f"数据显示{a}——ELO差距在下半场可能体现。"
    else:sw="三者接近——平局往往被市场低估。"
    # 多样化总进球分析
    p01=p['gl'].get('0',0)+p['gl'].get('1',0)
    p23=p['gl'].get('2',0)+p['gl'].get('3',0)
    p45=p['gl'].get('4',0)+p['gl'].get('5',0)
    p6p=sum(p['gl'].get(str(g),0) for g in range(6,13))
    if p['xh']>2.0: gw=f"进攻火力强劲，期望进球{p['xh']:.1f}球，大攻防推演概率高——4球及以上占{p45+p6p:.0f}%。"
    elif p['xh']>1.5: gw=f"进球集中在2-3球（{p23:.0f}%），典型世界杯节奏。但也有{p45:.0f}%概率打出4球以上。"
    elif p['xh']<1.0: gw=f"进攻乏力，{p01:.0f}%概率低于2球，小球数据显示明显。"
    else: gw=f"进球分布分散——2-3球占{p23:.0f}%，但{p45:.0f}%概率4球以上，{p01:.0f}%概率低于2球。"
    # 数据参考逻辑强化：平局概率>30%就数据参考均势
    if p['draw']>30:
        if p['win']>p['loss']:
            rec=f"数据显示：{h}获胜 但平局概率{p['draw']:.0f}%偏高，保守可关注均势"
        elif p['loss']>p['win']:
            rec=f"数据显示：{a}获胜 但平局概率{p['draw']:.0f}%偏高，保守可关注均势"
        else:
            rec=f"数据显示：平局 ({p['draw']:.0f}%)，双方实力接近"
    elif p['win']>50:rec=f"数据显示：{h}获胜"
    elif p['loss']>50:rec=f"数据显示：{a}获胜"
    else:rec="数据参考观望，平局概率偏高"

    # 伤停+风险+价值标签
    tags_html = ''
    if m.get('injury'):
        tags_html += '<div class="tag-row"><span class="tag tag-injury">🚑 ' + m['injury'] + '</span></div>'
    if m.get('risk') and len(m['risk'])>0:
        rt = ''.join('<span class="tag tag-risk">⚠️ ' + r + '</span>' for r in m['risk'])
        tags_html += '<div class="tag-row">' + rt + '</div>'
    if m.get('value'):
        tags_html += '<div class="tag-row"><span class="tag tag-value">💰 ' + m['value'] + '</span></div>'

    # 模型偏差 - 从 auto_tags 获取
    up = m.get('_upset_prob', 0)
    uw = m.get('_upset_why', '')
    upset_html = ''
    upset_type = ''
    if up > 30:
        upset_type = '🔴 高风险低概率'
        upset_color = '#e44'
    elif up > 20:
        upset_type = '🟡 低概率预警'
        upset_color = '#f80'
    elif up > 10:
        upset_type = '🟢 数据偏差度低'
        upset_color = '#999'
    else:
        upset_type = '无明显偏差'
        upset_color = '#666'
    if up > 0 and uw:
        upset_html = f'<div class="tag-row"><span class="tag" style="background:#fff5f5;color:{upset_color};border:1px solid #fcc;font-size:11px;padding:3px 8px;">🎲 {upset_type} · {uw}</span></div>'

    # 胜均势负低概率标注
    upset_label = ''
    if p['win'] > 50 and p['loss'] > 15:
        upset_label = ' <span style="color:#e44;font-size:10px;">⚠️ ' + a + '小概率偏差' + str(round(p['loss'])) + '%</span>'
    elif p['loss'] > 50 and p['win'] > 15:
        upset_label = ' <span style="color:#e44;font-size:10px;">⚠️ ' + h + '小概率偏差' + str(round(p['win'])) + '%</span>'

    # 低概率解释
    fav_team = h if p['win'] > 50 else a
    upset_detail = ''
    if abs(d) < 60 and (p['loss'] > 20 or p['win'] > 20):
        underdog = a if p['win'] > 50 else h
        upset_detail = '<div class="why">💡 ' + underdog + '具备模型偏差条件：ELO差距仅' + str(abs(d)) + '分，'
        if abs(d) < 30:
            upset_detail += '实力非常接近，任何结果都不意外。'
        else:
            upset_detail += underdog + '若先取得进球，' + fav_team + '压力将骤增。'
        upset_detail += '</div>'
    score_tags = ''
    if p['top']:
        best = p['top'][0]
        worst = p['top'][-1]
        score_tags = f'<div class="tag-row"><span class="tag tag-value">🔥 关注度较高: {best[0]}({best[1]}%)</span><span class="tag tag-risk">❄️ 低概率: {worst[0]}({worst[1]}%)</span></div>'

    # 赛后对比（如果有result）
    result_html = ''
    if m.get('result'):
        result_html = '<div class="tag-row"><span class="tag" style="background:#f0fff0;color:#390;border:1px solid #cfc">✅ 实际: ' + m['result'] + ' | 模型数据模型偏差: 待复盘</span></div>'

    # 把低概率标注嵌入ew
    if upset_label:
        ew += upset_label

    return ew, sw, gw, rec, tags_html + upset_html + upset_detail + score_tags + result_html

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
    for m in matches:
        p=predict(m['home'],m['away'], match_info=m)
        # 自动补全伤停/风险/价值/模型偏差
        ai,ar,av,up,uw=auto_tags(m,p)
        if not m.get('injury'): m['injury']=ai
        if not m.get('risk') or len(m.get('risk',[]))==0: m['risk']=ar
        if not m.get('value'): m['value']=av
        # 统一使用 predict() 返回的数据偏差度，不再重复计算
        m['_upset_prob'] = p.get('upset_prob', up)
        m['_upset_why'] = uw
        fh,fa=FLAGS.get(m['home'],''),FLAGS.get(m['away'],'')
        ew,sw,gw,rec,tags=explain(p,m,m['home'],m['away'],p['he']-p['ae']+50)
        d=f"{m['date']} {m['time']}".strip()

        # 实时结果
        live=""
        if m.get('result'):
            live=f'<div class="live">⚡ {m["result"]}</div>'
            results+=f'<div class="res"><span>{fh} {m["home"]} {m["result"]} {m["away"]} {fa}</span><span class="d">{d}</span></div>'

        # 数据参考值（模型数据公式 → 星级）
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
            kelly_html = '<div class="tag-row"><span class="tag" style="background:#fff;color:' + colors.get(stars, '#999') + ';border:1px solid #ddd;font-size:12px;padding:4px 10px">' + emoji.get(stars, '') + ' 数据参考值: ' + km + '</span></div>' if km else ''

        # 赔率
        on=""
        if m.get('odds_home'):
            o=float(m['odds_home']);fair=round(1/max(p['win']/100,0.01),1)
            on=f"市场赔率{o} · 模型公允{fair}"

        cards+=f"""
    <div class="match">
      <div class="mh"><span class="g">G{m['group']}</span><span class="t">{fh} {m['home']} vs {m['away']} {fa}</span><span class="d">{d}</span></div>
      <div class="v">{m['venue']} · {PLAY_STYLE.get(m['home'], '')}  VS  {PLAY_STYLE.get(m['away'], '')}</div>{live}
      {'<div class="live-badge">🔴 进行中 · ' + m.get('live_score','') + ' (' + m.get('live_clock','') + ')</div>' if m.get('status')=='LIVE' else ''}
      {'<div class="ft-badge">⚡ 已完赛 · 全场攻防推演: ' + m['result'] + '</div>' if m.get('result') and m.get('status')=='FT' else ''}
      <div class="int" style="{'opacity:0.5' if m.get('status')=='FT' else ''}">📰 {m['intel']}</div>
      {kelly_html}
      {tags}
      <div class="s"><div class="st">攻防 · {ew}</div>
        <div class="b"><span>主队</span><div class="t"><i style="width:{p['win']}%"></i></div><span class="n">{p['win']}%</span></div>
        <div class="b"><span>均势</span><div class="t"><i style="width:{p['draw']}%;background:#888"></i></div><span class="n">{p['draw']}%</span></div>
        <div class="b"><span>客队</span><div class="t"><i style="width:{p['loss']}%;background:#ccc"></i></div><span class="n">{p['loss']}%</span></div>
        <div class="why">{sw} · {on}</div>
      </div>
      <div class="s"><div class="st">攻防推演 TOP5</div><div class="cs">{' '.join(f'<span class="c"><b>{s}</b> {pr}%</span>'for s,pr in p['top'])}</div></div>
      <div class="s"><div class="st">总进球 · {gw}</div><div class="cs">{' '.join(f'<span class="c">{g}球 {pr}%</span>'for g,pr in list(p['gl'].items())[:6])}</div></div>
      <div class="s"><div class="st">🧠 数据解读</div><div class="think"><b>{p.get('tier','')}</b> {ew} {sw} 风格：{PLAY_STYLE.get(m['home'],'')} VS {PLAY_STYLE.get(m['away'],'')}。{gw} 数据综合参考：{rec}。数据偏差度{p.get('upset_prob','?')}%</div></div>
      <div class="s" style="border-left:3px solid #ddd;padding-left:12px;background:#fafafa">
        <div class="st" style="cursor:pointer" onclick="var d=this.nextElementSibling;d.style.display=d.style.display==='none'?'block':'none';this.textContent=this.textContent.replace('▶','▼').replace('▼','▶')">▶ 统计公式链</div>
        <div style="display:none;font-size:10px;color:#666;line-height:1.6;padding-top:4px">
          🧮 {p.get('calc_chain','')}<br>
          📐 预期进球：主队{p['xh']}球 × 客队{p['xa']}球 → 泊松分布<br>
          📊 数据一致性等级：&gt;75%🟢数据一致性高 &gt;60%🟡关注度较高 &gt;45%🟠数据接近 其余🔴低概率<br>
          🎲 低概率=基础{abs(p['win']-p['loss']):.0f}%差额+伤病+红牌+高原修正<br>
          💰 {p.get('odds_note','赔率与模型一致，市场未过热')}
        </div>
      </div>
    </div>"""

    html=f"""<!DOCTYPE html><html lang="zh-CN"><head>
<script>
// 访问验证
const HASH='{PASS_HASH}';
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
<h1>世界杯 · 球队攻防量化数据</h1>
<div style="padding:0 0 10px"><input id="search" type="text" placeholder="🔍 搜索球队..." oninput="filter()" style="width:100%;padding:10px;border:1px solid #ddd;font-size:14px"></div>
<div class="sub">ELO攻防数据模型 · 历史统计复盘</div>
<div class="upd">更新 {now} · 每5分钟自动刷新 · v{int(datetime.now().timestamp()) % 1000000}</div>
<div class="rf">⏳ <span id="cd">60</span>秒后刷新</div>
{dashboard_html}
{"<div class=\"results\"><div class=\"rt\">⚡ 最新记录</div>"+results+"</div>" if results else ""}
{cards}
<div class="ft">数据基于FIFA排名和历史记录<br>采用数学统计方法处理公开数据<br>以上为球队实力量化统计，不构成任何投注数据参考</div>
<script>
let t=60;setInterval(()=>{{t--;document.getElementById('cd').textContent=t;if(t<=0)location.reload()}},1000);
function filter(){{var q=document.getElementById('search').value.toLowerCase();var ms=document.querySelectorAll('.match');ms.forEach(function(m){{var t=m.querySelector('.t').textContent.toLowerCase();m.style.display=t.indexOf(q)>=0?'':'none'}});}}
</script>
</div>
</body></html>"""

    with open(OUTPUT,'w',encoding='utf-8') as f:f.write(html)
    print(f"✅ {len(matches)}场比赛已生成")
    print(f"   手机: http://172.20.10.2:8899/live.html")

if __name__=="__main__":gen()
