# -*- coding: utf-8 -*-
"""PIL 官网查询 - pilship.com 带完整浏览器特征"""
import asyncio
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={"width": 1920, "height": 1080},
            locale='en-US',
        )
        page = await ctx.new_page()
        
        # 隐藏 webdriver 特征
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        """)
        
        print("打开 pilship.com ...")
        try:
            await page.goto("https://www.pilship.com", timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            title = await page.title()
            print(f"标题: {title}")
            print(f"URL: {page.url}")
            
            # 截图
            await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_home.png", full_page=True)
            
            # 打印所有可见文本
            body = await page.inner_text("body")
            print(f"\n页面文本:")
            print(body[:3000])
            
            # 找搜索/跟踪入口
            links = await page.query_selector_all('a[href*="track"], a[href*="trace"], a[href*="search"], a[href*="ecom"]')
            print(f"\n相关链接:")
            for a in links:
                href = await a.get_attribute('href') or ''
                text = (await a.inner_text()).strip()[:60]
                print(f"  {text} -> {href}")
            
        except Exception as e:
            print(f"错误: {e}")
        
        await browser.close()

asyncio.run(main())
