"""
ESPN API 自动抓比分 — 无需浏览器，GitHub Actions可运行
"""
import json, os, requests
from datetime import datetime, timedelta

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')
ESPN_URL = 'https://site.web.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard'


def fetch_scores(date_str=None):
    """从ESPN API抓取指定日期的比分"""
    if not date_str:
        date_str = datetime.now().strftime('%Y%m%d')

    url = f'{ESPN_URL}?dates={date_str}'
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        return r.json()
    except Exception as e:
        print(f'ESPN API failed for {date_str}: {e}')
        return None


def update_scores():
    with open(SCHEDULE, encoding='utf-8') as f:
        matches = json.load(f)

    updated = 0

    # 抓最近3天的比分（时区可能跨天）
    for days_ago in range(3):
        d = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
        data = fetch_scores(d)
        if not data:
            continue

        for ev in data.get('events', []):
            status = ev.get('status', {}).get('type', {}).get('description', '')
            if status in ('Full Time', 'FT', 'Finished'):
                pass  # 继续处理已结束比赛
            elif status not in ('Scheduled',):
                # 进行中的比赛
                live_clock = ev.get('status', {}).get('displayClock', '')
                for m in matches:
                    if m.get('status') != 'FT' and m.get('status') != 'LIVE':
                        h=m['home']; a=m['away']
                        if (h in home_abbr or home_abbr in h.upper()) and (a in away_abbr or away_abbr in a.upper()):
                            live_score = f'{home_score}:{away_score}'
                            m['live_score'] = live_score
                            m['live_clock'] = live_clock
                            m['status'] = 'LIVE'
                            print(f'🔴 LIVE {h} {live_score} {a} [{live_clock}]')
                continue
            else:
                continue

            comps = ev.get('competitions', [{}])[0].get('competitors', [])
            if len(comps) < 2:
                continue

            home_abbr = comps[0].get('team', {}).get('abbreviation', '')
            away_abbr = comps[1].get('team', {}).get('abbreviation', '')
            home_score = comps[0].get('score', '')
            away_score = comps[1].get('score', '')

            score = f'{home_score}:{away_score}'

            # 匹配schedule.json中的比赛
            for m in matches:
                if m.get('status') == 'FT':
                    continue
                # ESPN缩写可能是3字母，schedule里是中文名，用部分匹配
                h = m['home']
                a = m['away']
                if (h in home_abbr or home_abbr in h.upper()) and \
                   (a in away_abbr or away_abbr in a.upper()):
                    if m.get('result') != score:
                        m['result'] = score
                        m['status'] = 'FT'
                        updated += 1
                        print(f'⚡ {h} {score} {a}')

    if updated:
        with open(SCHEDULE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        print(f'✅ {updated}场已更新')
        return True
    return False


if __name__ == '__main__':
    if update_scores():
        import live_data
        live_data.gen()
