"""
FlashScore 实时比分监控 — 自动更新 schedule.json + push
用法: python live_score.py
"""
import json, os, re, subprocess, sys
from datetime import datetime

DIR = os.path.dirname(__file__)
SCHEDULE = os.path.join(DIR, 'schedule.json')


def get_flashscore_snapshot():
    """用OpenClaw浏览器打开FlashScore并抓取页面内容"""
    try:
        # 打开FlashScore世界杯页
        subprocess.run(['openclaw','browser','open','https://www.flashscore.com/football/world/world-cup/'],
                      capture_output=True, timeout=15)
        # 等加载
        import time; time.sleep(5)
        # 抓取snapshot
        result = subprocess.run(['openclaw','browser','snapshot','--limit','300'],
                              capture_output=True, text=True, timeout=30)
        return result.stdout
    except Exception as e:
        print(f'FlashScore抓取失败：{e}')
        return ''


def parse_scores(text, matches):
    """从FlashScore snapshot中提取比分"""
    updated = 0
    for m in matches:
        if m.get('status') == 'FT':
            continue  # 已结束的不再更新

        home = m['home']
        away = m['away']

        # 在snapshot中搜索：队名后面紧跟数字的模式
        # FlashScore格式: "TeamName" 后可能出现 "2" "1" "TeamName2"
        # 简化：搜home名后面紧挨着的两个数字
        patterns = [
            rf'{home}.*?(\d)\s*\n\s*-\s*\n\s*(\d).*?{away}',  # dash格式
            rf'{home}.*?(\d+)\s*-\s*(\d+).*?{away}',  # 比分格式
        ]

        for pat in patterns:
            found = re.findall(pat, text, re.IGNORECASE | re.DOTALL)
            if found:
                score = f'{found[0][0]}:{found[0][1]}'
                if score != m.get('result', ''):
                    m['result'] = score
                    m['status'] = 'FT'
                    updated += 1
                    print(f'⚡ {home} {score} {away}')
                break

    return updated


def main():
    with open(SCHEDULE, encoding='utf-8') as f:
        matches = json.load(f)

    print(f'📡 抓取FlashScore...')
    text = get_flashscore_snapshot()

    if not text:
        print('⚠️ 无法获取比分数据')
        # 尝试直接用evaluate读取页面核心内容
        try:
            result = subprocess.run(
                ['openclaw','browser','evaluate','--fn',
                 '() => { const els = document.querySelectorAll("[class*=score],[class*=result]"); '
                 'return Array.from(els).map(e=>e.textContent).join("|"); }'],
                capture_output=True, text=True, timeout=15
            )
            text = result.stdout
            print(f'页面核心内容: {text[:200]}')
        except:
            pass

    updated = parse_scores(text, matches)

    if updated:
        with open(SCHEDULE, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)

        # 重新生成页面
        subprocess.run(['python', os.path.join(DIR, 'live_data.py')])

        # Git提交
        subprocess.run(['git', 'add', 'schedule.json', 'live.html'], cwd=DIR)
        subprocess.run(['git', 'commit', '-m', f'⚡ 自动比分更新 {datetime.now().strftime("%m/%d %H:%M")}'], cwd=DIR)

        # 尝试push（可能失败如果网络不通）
        push_result = subprocess.run(['git', 'push', 'origin', 'gh-pages'], cwd=DIR, capture_output=True)
        if push_result.returncode == 0:
            print('✅ 已推送到GitHub')
        else:
            print('⚠️ Push失败（网络不通），下次自动重试')
    else:
        print('⏳ 无新比分')


if __name__ == '__main__':
    main()
