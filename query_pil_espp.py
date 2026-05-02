# -*- coding: utf-8 -*-
"""PIL ESPP 门户查询 Booking"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
ESPP_URL = "https://espp.pilship.com/espp/login/loginPage.do"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        # ===== 先试 PIL 主页，找 Booking 跟踪入口 =====
        print("1. 打开 PIL 主页，找 Booking 跟踪 ...")
        await page.goto("https://www.pilship.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # 保存 HTML 分析
        html = await page.content()
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_full_home.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # 找所有含 track/trace/booking 的链接
        import re
        all_hrefs = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html)
        tracking = set()
        for h in all_hrefs:
            hl = h.lower()
            if any(kw in hl for kw in ['track', 'trace', 'booking', 'ebl', 'e/bl', 'espp', 'eip', 'pocketpil', 'login', 'sign']):
                tracking.add(h)
        
        print(f"\n跟踪/登录相关链接:")
        for h in sorted(tracking):
            print(f"  {h}")
        
        # 找按钮和链接文本
        links = re.findall(r'<a[^>]*href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        print(f"\n相关链接:")
        for href, text in links:
            text = re.sub(r'<[^>]+>', '', text).strip()
            hl = href.lower()
            if any(kw in hl for kw in ['track', 'trace', 'espp', 'eip', 'pocketpil']) or \
               any(kw in text.lower() for kw in ['track', 'trace', 'espp', 'portal', 'login']):
                print(f"  [{text[:60]}] -> {href}")

        # ===== 尝试 ESPP =====
        print(f"\n2. 尝试 ESPP 门户 ...")
        await page.goto(ESPP_URL, timeout=60000, wait_until="networkidle")
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"   标题: {title}")
        print(f"   URL: {page.url}")
        
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_espp.png", full_page=True)
        
        body = await page.inner_text("body")
        print(f"\n   页面内容 (前2000):")
        print(body[:2000])
        
        # 找输入框
        inputs = await page.query_selector_all('input:not([type="hidden"])')
        print(f"\n   输入框 ({len(inputs)} 个):")
        for inp in inputs:
            pid = await inp.get_attribute('id') or ''
            name = await inp.get_attribute('name') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            itype = await inp.get_attribute('type') or ''
            print(f"     id={pid!r} name={name!r} type={itype!r} placeholder={placeholder!r}")
        
        await browser.close()

asyncio.run(main())
