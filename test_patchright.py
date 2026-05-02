# -*- coding: utf-8 -*-
"""patchright 反检测测试 — CMA + MSC"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from patchright.async_api import async_playwright

async def test(carrier, url, bl):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":1920,"height":1080})
        
        print(f"{carrier}: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        title = await page.title()
        body = await page.inner_text("body")
        print(f"  标题: {title} | 正文: {len(body)} 字符")
        
        if len(body) > 100 and "Access Denied" not in body and "denied" not in body.lower():
            print(f"  ✓ 通过! {body[:200]}")
            
            # 找输入框
            inputs = await page.evaluate("""
                Array.from(document.querySelectorAll('input:not([type="hidden"])'))
                    .filter(i => i.offsetParent !== null)
                    .map(i => ({id:i.id,name:i.name,placeholder:i.placeholder||'',type:i.type||'text'}))
            """)
            print(f"  输入框: {inputs}")
            
            # 找按钮
            btns = await page.evaluate("""
                Array.from(document.querySelectorAll('button,input[type="submit"],[role="button"]'))
                    .map(b => (b.textContent||b.value||'').trim().substring(0,50))
                    .filter(t => t)
            """)
            print(f"  按钮: {btns[:8]}")
            
            await page.screenshot(path=rf"D:\hermes\MODS\MOD004\data\evidence\pr_{carrier.lower()}.png")
        else:
            print(f"  ✗ 失败: {body[:200]}")
        
        await browser.close()

async def main():
    await test("CMA", "https://www.cma-cgm.com/ebusiness/tracking", "ABQ0117757")
    await test("MSC", "https://www.msc.com/track-a-shipment", "MEDUH7002122")

asyncio.run(main())
