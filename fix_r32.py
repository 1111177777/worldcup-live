"""
一键修复 R32 对阵表：删除所有错误R32 → 插入正确16场 → 更新schedule.json
"""
import json, os

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')

# 修正后的排名
W = {'A':'墨西哥','B':'瑞士','C':'巴西','D':'美国','E':'德国','F':'荷兰','G':'比利时','H':'西班牙','I':'法国','J':'阿根廷','K':'哥伦比亚','L':'英格兰'}
R = {'A':'南非','B':'加拿大','C':'摩洛哥','D':'澳大利亚','E':'科特迪瓦','F':'日本','G':'埃及','H':'佛得角','I':'挪威','J':'奥地利','K':'葡萄牙','L':'克罗地亚'}
T = ['刚果民主共和国','瑞典','厄瓜多尔','加纳','波黑','阿尔及利亚','巴拉圭','塞内加尔']

# 正确R32对阵
bracket = [
    (73, R['A'], R['B'], '6/29', '温哥华'),     # 2A vs 2B
    (74, W['E'], T[0],  '6/30', '休斯顿'),      # 1E vs 3rd
    (75, W['F'], R['C'], '6/30', '费城'),        # 1F vs 2C
    (76, W['C'], R['F'], '6/30', '纽约'),        # 1C vs 2F
    (77, W['I'], T[1],  '7/1', '波士顿'),        # 1I vs 3rd
    (78, R['E'], R['I'], '7/1', '达拉斯'),       # 2E vs 2I
    (79, W['A'], T[2],  '7/1', '墨西哥城'),       # 1A vs 3rd
    (80, W['L'], T[3],  '7/2', '迈阿密'),        # 1L vs 3rd
    (81, W['D'], T[4],  '7/2', '西雅图'),        # 1D vs 3rd
    (82, W['G'], T[5],  '7/2', '洛杉矶'),        # 1G vs 3rd
    (83, R['K'], R['L'], '7/3', '亚特兰大'),     # 2K vs 2L
    (84, W['H'], R['J'], '7/3', '旧金山'),        # 1H vs 2J
    (85, W['B'], T[6],  '7/3', '堪萨斯城'),       # 1B vs 3rd
    (86, W['J'], R['H'], '7/4', '多伦多'),        # 1J vs 2H
    (87, W['K'], T[7],  '7/4', '休斯顿'),        # 1K vs 3rd
    (88, R['D'], R['G'], '7/4', '瓜达拉哈拉'),   # 2D vs 2G
]

# 加载赛程
with open(SCHEDULE, 'r', encoding='utf-8') as f:
    schedule = json.load(f)

# 删除所有R32比赛
old_r32 = [m for m in schedule if m['group'] == 'R32']
schedule = [m for m in schedule if m['group'] != 'R32']

print(f'删除 {len(old_r32)} 场旧R32比赛')

# 插入正确比赛
for num, h, a, date, venue in bracket:
    schedule.append({
        'home': h, 'away': a, 'date': date, 'group': 'R32',
        'venue': venue, 'time': '',
        'intel': f'淘汰赛R32。{h}小组第1出线对阵{a}。',
        'odds_home':'','odds_draw':'','odds_away':'',
        'result':'','status':'','injury':'','risk':[],'value':''
    })

# 按比赛号排序
schedule.sort(key=lambda m: (
    m['date'].split('/')[0].zfill(2),
    m['date'].split('/')[1].zfill(2),
    ['A','B','C','D','E','F','G','H','I','J','K','L','R32'].index(m['group'])
))

with open(SCHEDULE, 'w', encoding='utf-8') as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)

print(f'插入 {len(bracket)} 场正确R32比赛')
print(f'总场次: {len(schedule)}')

print()
print('=== 修正后的 R32 对阵 ===')
for num, h, a, date, venue in bracket:
    print(f'#{num} {date} {h} vs {a} @ {venue}')

print()
print('✅ schedule.json 已修复')
