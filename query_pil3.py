# -*- coding: utf-8 -*-
"""PIL 官网查询 - pilnet.com"""
import asyncio
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("打开 pilnet.com/tracking ...")
        await page.goto("https://www.pilnet.com/tracking", timeout=30000, wait_until="networkidle")
        title = await page.title()
        print(f"标题: {title}")
        
        # 截图
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pilnet_page.png")
        
        # 找所有链接
        links = await page.query_selector_all('a')
        print(f"\n页面链接 ({len(links)} 个):")
        for a in links[:30]:
            href = await a.get_attribute('href') or ''
            text = (await a.inner_text()).strip()[:60]
            if href or text:
                print(f"  {text[:40]:40s} -> {href[:80]}")
        
        # 找所有输入框
        inputs = await page.query_selector_all('input:not([type="hidden"])')
        print(f"\n输入框 ({len(inputs)} 个):")
        for inp in inputs:
            pid = await inp.get_attribute('id') or ''
            name = await inp.get_attribute('name') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            itype = await inp.get_attribute('type') or ''
            print(f"  id={pid!r} name={name!r} type={itype!r} placeholder={placeholder!r}")
        
        body = await page.inner_text("body")
        print(f"\n页面文本 (前2000字符):")
        print(body[:2000])
        
        await browser.close()

asyncio.run(main())
