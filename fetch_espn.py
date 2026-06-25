"""
ESPN API 自动抓比分 — 无需浏览器，GitHub Actions可运行
v2.1: 修复API端点 + 增加多源回退 + 容错加固
"""
import json, os, sys, requests
from datetime import datetime, timedelta

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')

# ESPN API 端点（2026世界杯）
ESPN_URLS = [
    'https://site.web.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard',
    'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard',  # 备选域名
]

# FIFA 官方 API 回退
FIFA_API = 'https://api.fifa.com/api/v3/calendar/285026?language=en'  # 2026 WC ID

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}


def fetch_espn(date_str=None):
    """从ESPN API抓取指定日期的比分，失败返回None"""
    if not date_str:
        date_str = datetime.now().strftime('%Y%m%d')

    for base_url in ESPN_URLS:
        url = f'{base_url}?dates={date_str}'
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get('events'):
                    print(f'  ESPN OK: {base_url.split("/")[2]}')
                    return data
            else:
                print(f'  ESPN {base_url.split("/")[2]} HTTP {r.status_code}')
        except Exception as e:
            print(f'  ESPN {base_url.split("/")[2]} error: {e}')

    return None


def fetch_fifa(date_str=None):
    """FIFA官方API回退方案"""
    try:
        r = requests.get(FIFA_API, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f'  FIFA API error: {e}')
    return None


def match_team(name, candidates):
    """智能匹配球队名（支持中文名/英文缩写/全名）"""
    name_upper = name.upper().strip()
    for c in candidates:
        c_upper = c.upper().strip()
        if name_upper == c_upper:
            return c
        if len(name_upper) >= 3 and name_upper in c_upper:
            return c
        if len(c_upper) >= 3 and c_upper in name_upper:
            return c
    return None


def update_scores():
    """从ESPN抓取最新比分并更新schedule.json"""
    if not os.path.exists(SCHEDULE):
        print('❌ schedule.json 不存在，跳过比分抓取')
        return False

    with open(SCHEDULE, encoding='utf-8') as f:
        try:
            matches = json.load(f)
        except json.JSONDecodeError as e:
            print(f'❌ schedule.json 解析失败: {e}')
            return False

    updated = 0
    today = datetime.now()

    # 抓最近4天的比分
    for days_ago in range(4):
        d = (today - timedelta(days=days_ago)).strftime('%Y%m%d')
        print(f'📡 抓取 {d} ...')
        data = fetch_espn(d)

        if not data:
            print(f'  ⚠️ ESPN {d} 无数据，尝试FIFA回退...')
            data = fetch_fifa(d)

        if not data:
            print(f'  ⚠️ {d} 所有数据源失败，跳过')
            continue

        for ev in data.get('events', []):
            status_desc = ev.get('status', {}).get('type', {}).get('description', '')
            comps = ev.get('competitions', [{}])[0].get('competitors', [])

            if len(comps) < 2:
                continue

            home_abbr = comps[0].get('team', {}).get('abbreviation', '')
            away_abbr = comps[1].get('team', {}).get('abbreviation', '')
            home_score = comps[0].get('score', '')
            away_score = comps[1].get('score', '')

            # 跳过没有比分的比赛
            if home_score == '' or away_score == '':
                continue

            score = f'{home_score}:{away_score}'

            # 匹配 schedule.json 中的比赛
            for m in matches:
                if m.get('status') == 'FT':
                    continue

                h = m['home']
                a = m['away']

                # 多策略匹配
                home_match = (h in home_abbr or home_abbr in h.upper() or
                             match_team(h, [home_abbr]))
                away_match = (a in away_abbr or away_abbr in a.upper() or
                             match_team(a, [away_abbr]))

                if home_match and away_match:
                    if status_desc in ('Full Time', 'FT', 'Finished', 'Final'):
                        if m.get('result') != score:
                            m['result'] = score
                            m['status'] = 'FT'
                            updated += 1
                            print(f'  ⚡ FT: {h} {score} {a}')
                    elif status_desc not in ('Scheduled', 'Pre-Game'):
                        # 比赛中
                        m['live_score'] = score
                        m['live_clock'] = ev.get('status', {}).get('displayClock', '')
                        m['status'] = 'LIVE'
                        updated += 1
                        print(f'  🔴 LIVE: {h} {score} {a}')

    if updated:
        # 原子写入：先写临时文件再替换
        tmp = SCHEDULE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        os.replace(tmp, SCHEDULE)
        print(f'✅ {updated}场比赛已更新，schedule.json已保存')
        return True

    print('ℹ️ 未发现需要更新的比赛')
    return False


if __name__ == '__main__':
    print(f'🏟 世界杯比分自动抓取 · {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    success = update_scores()

    if success:
        # 比分有更新 → 重新生成所有页面
        print('🔄 比分已更新，重新生成页面...')
        try:
            import live_data
            live_data.gen()
            print('✅ live.html 已重新生成')
        except Exception as e:
            print(f'❌ live_data.gen() 失败: {e}')
            sys.exit(1)

        try:
            import dashboard
            dashboard.gen()
        except Exception as e:
            print(f'⚠️ dashboard 生成失败(非致命): {e}')

    print('✅ 抓取流程完成')
