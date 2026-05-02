# -*- coding: utf-8 -*-
"""CMA + MSC — 从主页进入"""
import asyncio, sys, re
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

CMA_BL = "ABQ0117757"
MSC_BL = "MEDUH7002122"

async def query_cma():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36',
            viewport={"width":1920,"height":1080},
        )
        page = await ctx.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        
        print("CMA: 打开首页...")
        await page.goto("https://www.cma-cgm.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        title = await page.title()
        body = await page.inner_text("body")
        print(f"标题: {title} | 正文: {len(body)} 字符")
        print(f"前500: {body[:500]}")
        
        html = await page.content()
        # Find tracking links
        link_matches = re.findall(r'href="([^"]+)"', html)
        track = [l for l in link_matches if any(kw in l.lower() for kw in ['track','trace','search','booking','ebusiness'])]
        print(f"\n跟踪链接: {set(track)}")
        
        # Find inputs
        inputs = await page.query_selector_all('input:not([type="hidden"])')
        print(f"\n输入框: {len(inputs)}")
        for inp in inputs:
            pid = await inp.get_attribute('id') or ''
            name = await inp.get_attribute('name') or ''
            ph = await inp.get_attribute('placeholder') or ''
            print(f"  id={pid!r} name={name!r} placeholder={ph!r}")
        
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\cma_home.png", full_page=True)
        await browser.close()


async def query_msc():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36',
            viewport={"width":1920,"height":1080},
        )
        page = await ctx.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        
        print("\n\nMSC: 打开首页...")
        await page.goto("https://www.msc.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        title = await page.title()
        body = await page.inner_text("body")
        print(f"标题: {title} | 正文: {len(body)} 字符")
        if len(body) > 0:
            print(f"前500: {body[:500]}")
        
        if "Access Denied" in body:
            print("MSC 首页被拦截: Access Denied")
        else:
            html = await page.content()
            link_matches = re.findall(r'href="([^"]+)"', html)
            track = [l for l in link_matches if any(kw in l.lower() for kw in ['track','trace','search','booking'])]
            print(f"跟踪链接: {set(track)}")
            await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\msc_home.png", full_page=True)
        
        await browser.close()


async def main():
    await query_cma()
    await query_msc()

asyncio.run(main())
