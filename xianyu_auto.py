"""
闲鱼自动上架 — 打开浏览器 → 你扫码登录 → 自动填表单
"""
import time, sys, os
os.chdir(os.path.dirname(__file__))

# 读文案
with open('闲鱼文案_合规版.md', 'r', encoding='utf-8') as f:
    text = f.read()
# 提取标题
title = ''
for line in text.split('\n'):
    if line.startswith('> '):
        title = line[2:].strip()
        break
# 提取描述（从"## 描述"到"## 价格"之间）
desc_lines = []
in_desc = False
for line in text.split('\n'):
    if '## 描述' in line:
        in_desc = True
        continue
    if '## 价格' in line:
        break
    if in_desc and line.strip() and not line.startswith('#'):
        desc_lines.append(line.strip())
desc = '\n'.join(desc_lines)

print(f'标题: {title}')
print(f'描述: {len(desc)}字')
print()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context()
    page = ctx.new_page()

    # 直接去闲鱼发布页（复用已有登录态）
    print('📋 打开闲鱼发布页...')
    page.goto('https://goofish.com/publish', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    print(f'  当前URL: {page.url}')
    print('📋 开始填写...')

    # 填标题
    try:
        title_input = page.locator('[placeholder*="标题"], input[name="title"]').first
        title_input.click()
        title_input.fill(title)
        print(f'✅ 标题已填')
    except Exception as e:
        print(f'⚠️ 标题: {e}')

    # 填描述
    try:
        desc_box = page.locator('textarea, [contenteditable="true"], div[placeholder*="描述"]').first
        desc_box.click()
        time.sleep(0.5)
        desc_box.fill(desc)
        print(f'✅ 描述已填 ({len(desc)}字)')
    except Exception as e:
        print(f'⚠️ 描述: {e}')

    # 填价格
    try:
        price_input = page.locator('[placeholder*="价格"], input[type="number"], input[name="price"]').first
        price_input.fill('49.9')
        print('✅ 价格已填 49.9')
    except Exception as e:
        print(f'⚠️ 价格: {e}')

    print()
    print('='*50)
    print('表单已填完。上传图片后点击"发布"。')
    print('按 Ctrl+C 退出...')
    input()
    browser.close()
