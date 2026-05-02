# -*- coding: utf-8 -*-
"""PIL Track & Trace — 获取表单结构后精确查询"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        print("1. 打开 PIL 首页 ...")
        await page.goto("https://www.pilship.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(6)

        # Cookie
        try:
            for text in ["Deny", "Allow all", "Accept"]:
                btn = await page.query_selector(f'button:has-text("{text}")')
                if btn:
                    await btn.click()
                    print(f"Cookie: {text}")
                    await asyncio.sleep(2)
                    break
        except:
            pass

        # 获取表单 HTML
        form_html = await page.evaluate("""
            (function() {
                var form = document.querySelector('#trackTraceFormHome');
                if (form) return form.outerHTML;
                form = document.querySelector('form[id*="track"]');
                if (form) return form.outerHTML;
                return 'not found';
            })()
        """)
        
        print(f"\n2. 表单 HTML:")
        print(form_html[:4000])
        
        # 保存到文件方便分析
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_form.html", "w", encoding="utf-8") as f:
            f.write(form_html)
        
        # 分析表单字段
        import re
        inputs_found = re.findall(r'<input[^>]*>', form_html)
        print(f"\n  输入字段 ({len(inputs_found)}):")
        for inp in inputs_found:
            print(f"    {inp}")
        
        selects = re.findall(r'<select[^>]*>.*?</select>', form_html, re.DOTALL)
        print(f"\n  下拉框 ({len(selects)}):")
        for s in selects:
            print(f"    {s[:200]}")
        
        await browser.close()

asyncio.run(main())
