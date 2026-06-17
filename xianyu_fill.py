"""连接已打开的Chrome，自动填闲鱼表单"""
import time, sys, os
os.chdir(os.path.dirname(__file__))

# 读文案
with open('闲鱼文案_合规版.md', 'r', encoding='utf-8') as f:
    text = f.read()
title = [l[2:].strip() for l in text.split('\n') if l.startswith('> ')][0]
desc_start = text.find('## 描述')
desc_end = text.find('## 价格')
desc = text[desc_start:desc_end].strip()
# 去掉 "## 描述" 行
desc = '\n'.join(l for l in desc.split('\n') if not l.startswith('##') and l.strip())

print(f'标题: {title[:50]}...')
print(f'描述: {len(desc)}字')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9222')
    page = browser.contexts[0].pages[0]
    print(f'已连接: {page.url}')

    # 确保在发布页
    if 'publish' not in page.url and 'goofish' not in page.url:
        page.goto('https://goofish.com/publish')
        time.sleep(3)

    print('等待你登录/完成验证...看到发布表单后按回车')
    input()

    # 尝试填表单
    # Xianyu uses React - find by common selectors
    selectors = {
        'title': ['[placeholder*="标题"]', 'input[name="title"]', '.title-input input', 'input[maxlength]'],
        'desc': ['textarea', '[contenteditable]', '.desc-editor textarea', '[role="textbox"]'],
        'price': ['input[type="number"]', '[placeholder*="价格"]', '.price-input input']
    }

    for field, sels in selectors.items():
        for sel in sels:
            try:
                el = page.locator(sel).first
                el.click()
                time.sleep(0.5)
                if field == 'title':
                    el.fill(title)
                    print(f'✅ 标题已填')
                elif field == 'desc':
                    el.fill(desc)
                    print(f'✅ 描述已填')
                elif field == 'price':
                    el.fill('49.9')
                    print(f'✅ 价格已填 ¥49.9')
                break
            except:
                continue
        else:
            print(f'⚠️ {field}: 未找到输入框，请手动填')

    print('\n表单填完。上传图片后点发布。')
    input('按回车退出...')
    browser.close()
