# -*- coding: utf-8 -*-
"""通过 Ship24 第三方聚合追踪查询 PIL"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def try_tracker(name, url, input_selector, btn_selector=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print(f"\n{'='*50}")
        print(f"尝试 {name}: {url}")
        
        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await asyncio.sleep(3)
            
            print(f"标题: {await page.title()}")
            
            # 填入提单号
            inp = await page.query_selector(input_selector)
            if inp:
                await inp.fill(BL_NO)
                print(f"已填入: {BL_NO}")
            else:
                print("未找到输入框")
                await browser.close()
                return False
            
            # 点击提交
            if btn_selector:
                btn = await page.query_selector(btn_selector)
                if btn:
                    await btn.click()
                    print("已点击提交")
            else:
                await page.keyboard.press("Enter")
                print("已按 Enter")
            
            await asyncio.sleep(5)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 结果
            await page.screenshot(
                path=rf"D:\hermes\MODS\MOD004\data\evidence\pil_{name.lower()}.png",
                full_page=True
            )
            
            body = await page.inner_text("body")
            print(f"\n结果 (前1000字符):")
            print(body[:1000])
            
            with open(rf"D:\hermes\MODS\MOD004\data\evidence\pil_{name.lower()}.txt", "w", encoding="utf-8") as f:
                f.write(body)
            
            await browser.close()
            return True
        except Exception as e:
            print(f"失败: {e}")
            await browser.close()
            return False

async def main():
    trackers = [
        ("Ship24", "https://www.ship24.com/", 'input[placeholder*="tracking"]', 'button[type="submit"]'),
        ("TrackingMore", "https://www.trackingmore.com/", 'input[id*="track"]', None),
        ("17Track", "https://www.17track.net/", 'input[id*="track"]', None),
    ]
    
    for name, url, inp_sel, btn_sel in trackers:
        ok = await try_tracker(name, url, inp_sel, btn_sel)
        if ok:
            print(f"\n✓ {name} 查询成功!")
            break

asyncio.run(main())
