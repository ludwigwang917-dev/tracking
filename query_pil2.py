# -*- coding: utf-8 -*-
"""PIL 官网查询 - 使用正确的URL"""
import asyncio
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

# PIL 常见的跟踪URL
URLS = [
    "https://www.pilship.com/en-track-trace.html",
    "https://www.pilship.com/track-trace",
    "https://www.pilship.com/en/track-trace",
    "https://www.pilship.com",
    "https://ecommerce.pilship.com/ebusiness/track-trace",
]

async def try_url(p, url):
    print(f"\n尝试: {url}")
    try:
        page = await p.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(url, timeout=20000, wait_until="networkidle")
        title = await page.title()
        print(f"  标题: {title}")
        if "not found" in title.lower() or "404" in title:
            await page.close()
            return None
        # 找输入框
        inputs = await page.query_selector_all('input:not([type="hidden"])')
        for inp in inputs:
            pid = await inp.get_attribute('id') or ''
            name = await inp.get_attribute('name') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            print(f"  输入框: id={pid!r} name={name!r} placeholder={placeholder!r}")
        return page
    except Exception as e:
        print(f"  错误: {e}")
        return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for url in URLS:
            page = await try_url(browser, url)
            if page:
                if "track" in url.lower() or "trace" in url.lower():
                    print(f"\n✓ 找到跟踪页面: {url}")
                    
                    # 尝试输入
                    inputs = await page.query_selector_all('input:not([type="hidden"])')
                    for inp in inputs:
                        try:
                            await inp.fill(BL_NO)
                            text = await inp.input_value()
                            if text == BL_NO:
                                print(f"  已填入提单号")
                                break
                        except:
                            pass
                    
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(5)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    
                    # 截图
                    await page.screenshot(
                        path=r"D:\hermes\MODS\MOD004\data\evidence\pil_track.png",
                        full_page=True
                    )
                    
                    body = await page.inner_text("body")
                    print(f"\n=== 页面内容 ===")
                    print(body[:3000])
                    
                    with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_track.txt", "w", encoding="utf-8") as f:
                        f.write(body)
                    
                    await page.close()
                    break
                await page.close()
        
        await browser.close()
        print("\n完成")

asyncio.run(main())
