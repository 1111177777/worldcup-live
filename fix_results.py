"""
赛果修正工具 — 永远不用假比分
用法：python fix_results.py
"""
import json, os, re
from datetime import datetime

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')

# 🔴 铁律：只有确认过的真实比分才能放在这里
# 格式：(日期, 主队, 客队, 比分)
VERIFIED_RESULTS = [
    ("6/11", "墨西哥", "南非", "2:0"),
    ("6/11", "韩国", "捷克", "2:1"),
    # 新比赛赛后在此添加
]

def fix():
    with open(SCHEDULE, encoding='utf-8') as f:
        matches = json.load(f)

    updated = 0
    for m in matches:
        for date, home, away, score in VERIFIED_RESULTS:
            if m['date'] == date and m['home'] == home and m['away'] == away:
                if m.get('result') != score:
                    m['result'] = score
                    m['status'] = 'FT'
                    updated += 1
                    print(f'✅ {home} {score} {away}')

    # 清理未确认的假比分
    for m in matches:
        if m.get('result') and m.get('status') != 'FT':
            print(f'⚠️ 移除未确认比分: {m["home"]} {m["result"]} {m["away"]}')
            m['result'] = ''
            m['status'] = ''

    with open(SCHEDULE, 'w', encoding='utf-8') as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f'\n{updated}场比赛已修正，{len(matches)}场总计')

if __name__ == '__main__':
    fix()
