"""
闲鱼自动上架脚本 — 打开浏览器预填表单，你手动点发布
用法：python xianyu_publish.py
"""
import time

# 读取文案
with open('闲鱼文案_合规版.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 提取标题（第一行 ### 后的内容）
lines = text.strip().split('\n')
title = ''
desc_lines = []
in_desc = False
for line in lines:
    if line.startswith('> ') and not title:
        title = line[2:].strip()
    elif line.startswith('## 描述'):
        in_desc = True
        continue
    elif line.startswith('## 价格'):
        break
    elif in_desc and line.strip():
        if not line.startswith('##'):
            desc_lines.append(line.strip())

desc = '\n'.join(desc_lines)

print(f'标题: {title}')
print(f'描述长度: {len(desc)} 字')
print()
print('正在打开浏览器...')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 连接到已有浏览器或用持久化上下文（保留登录状态）
    browser = p.chromium.launch_persistent_context(
        user_data_dir=r'C:\Users\zhouyujie\AppData\Local\Google\Chrome\User Data',
        channel='chrome',
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    # 打开闲鱼发布页
    page.goto('https://goofish.com/publish')
    time.sleep(3)

    print('浏览器已打开，请在页面中手动操作填写表单。')
    print(f'标题已复制到剪贴板: {title}')

    # 复制标题到剪贴板
    import pyperclip
    pyperclip.copy(title)
    print('📋 标题已复制，Ctrl+V 粘贴')

    print()
    print('描述内容：')
    print('-' * 40)
    print(desc[:500])
    print('...' if len(desc) > 500 else '')
    print()
    print('请手动粘贴描述，上传截图，设置价格 ¥49.9，然后点击发布。')
    input('完成后按回车关闭...')

    browser.close()
