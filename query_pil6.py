# -*- coding: utf-8 -*-
"""PIL 官网 Track & Trace 直接查询"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
TRACK_URL = "https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"打开: {TRACK_URL}")
        await page.goto(TRACK_URL, timeout=60000, wait_until="networkidle")
        await asyncio.sleep(5)
        
        print(f"标题: {await page.title()}")
        print(f"URL: {page.url}")
        
        # 截图
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_track_page.png", full_page=True)
        
        # 保存 HTML 分析结构
        html = await page.content()
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_track.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # 找所有输入框
        inputs = await page.query_selector_all('input:not([type="hidden"]), textarea')
        print(f"\n输入框 ({len(inputs)} 个):")
        for inp in inputs:
            tag = await inp.evaluate("el => el.tagName")
            pid = await inp.get_attribute('id') or ''
            name = await inp.get_attribute('name') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            itype = await inp.get_attribute('type') or ''
            print(f"  <{tag}> id={pid!r} name={name!r} type={itype!r} placeholder={placeholder!r}")
        
        # 尝试查找 iframe
        frames = page.frames
        print(f"\nFrames: {len(frames)} 个")
        for f in frames:
            print(f"  {f.url[:120]}")
            frame_inputs = await f.query_selector_all('input:not([type="hidden"])')
            if frame_inputs:
                print(f"    -> {len(frame_inputs)} inputs in this frame")
        
        # 如果找到输入框，填入并查询
        for inp in inputs:
            itype = await inp.get_attribute('type') or ''
            if itype in ('text', 'search', '') or not itype:
                try:
                    await inp.click()
                    await inp.fill(BL_NO)
                    print(f"\n填入提单号: {BL_NO}")
                    
                    # 找提交按钮
                    btns = await page.query_selector_all('button, input[type="submit"], [role="button"]')
                    for btn in btns:
                        text = (await btn.inner_text()).strip()
                        if text and any(kw in text.upper() for kw in ['TRACK', 'SEARCH', 'SUBMIT', 'GO']):
                            print(f"点击: {text}")
                            await btn.click()
                            break
                    else:
                        print("按 Enter 提交...")
                        await page.keyboard.press("Enter")
                    
                    await asyncio.sleep(5)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    
                    # 结果截图
                    await page.screenshot(
                        path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_final.png",
                        full_page=True
                    )
                    
                    result_text = await page.inner_text("body")
                    print(f"\n=== 查询结果 ===")
                    print(result_text[:3000])
                    
                    with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result.txt", "w", encoding="utf-8") as f:
                        f.write(result_text)
                    
                    await browser.close()
                    return
                except Exception as e:
                    print(f"错误: {e}")
        
        # 没有标准输入框，打印可见文本
        body = await page.inner_text("body")
        print(f"\n页面文本:")
        print(body[:2000])
        
        await browser.close()

asyncio.run(main())
