"""
FlashScore 实时比分监控 — 自动更新 schedule.json
用法: python live_score.py
"""
import json, os, re, time, requests
from datetime import datetime

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')

def fetch_scores():
    """从FlashScore抓取已完成比赛比分"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = 'https://www.flashscore.com/football/world/world-cup/'
    try:
        r = requests.get(url, headers=headers, timeout=15)
        text = r.text
    except:
        print('FlashScore不可达')
        return {}

    # 用OpenClaw browser snapshot解析（更可靠）
    # 先用简单正则尝试
    scores = {}
    # 找已完成比赛的模式: 队名...数字...数字...队名
    matches = re.findall(r'(\d+\.\d+\.\s+\d+:\d+)\s*\n.*?([A-Za-z\s]+?)\s*\n.*?(\d)\s*\n.*?(\d)\s*\n.*?([A-Za-z\s]+)', text, re.DOTALL)
    return scores

def update_from_flashscore():
    """用OpenClaw抓取FlashScore"""
    import subprocess
    # 用openclaw browser snapshot获取页面内容
    result = subprocess.run(
        ['openclaw', 'browser', 'snapshot', '--limit', '200'],
        capture_output=True, text=True, timeout=30
    )
    text = result.stdout
    if not text:
        print('FlashScore snapshot failed')
        return

    with open(SCHEDULE, encoding='utf-8') as f:
        matches = json.load(f)

    updated = 0
    for m in matches:
        if m.get('status') == 'FT':
            continue
        home = m['home']
        away = m['away']
        # 在snapshot中搜索两队名字和比分
        # FlashScore格式: home_team ... number ... number ... away_team
        pattern = rf'{home}.*?(\d+)[^\d]*(\d+).*?{away}'
        found = re.findall(pattern, text, re.IGNORECASE)
        if found:
            score = f'{found[0][0]}:{found[0][1]}'
            if score != m.get('result', ''):
                m['result'] = score
                m['status'] = 'FT'
                updated += 1
                print(f'⚡ {home} {score} {away}')

    if updated:
        with open(SCHEDULE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        print(f'✅ {updated}场已更新')
        # 重新生成页面
        subprocess.run(['python', os.path.join(DIR, 'live_data.py')])
    else:
        print('⏳ 无新比分')

if __name__ == '__main__':
    update_from_flashscore()
