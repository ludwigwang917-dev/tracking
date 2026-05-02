# -*- coding: utf-8 -*-
"""PIL 官网查询 - 直接找跟踪表单"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("1. 打开 pilship.com ...")
        await page.goto("https://www.pilship.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # 保存主页 HTML
        html = await page.content()
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_home.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   HTML保存 ({len(html)} 字节)")
        
        # 找所有链接和按钮
        clickable = await page.query_selector_all('a, button, [role="button"], [onclick]')
        print(f"\n2. 可点击元素 ({len(clickable)} 个):")
        track_candidates = []
        for el in clickable:
            try:
                text = (await el.inner_text()).strip()
                href = await el.get_attribute('href') or ''
                if text:
                    print(f"   {text[:60]}")
                if any(kw in (text+href).lower() for kw in ['track', 'trace', 'booking', 'ebusiness', 'e-business', 'login', 'sign']):
                    track_candidates.append(el)
            except:
                pass
        
        # 优先尝试明确的跟踪链接
        print(f"\n3. 跟踪候选 ({len(track_candidates)} 个):")
        for el in track_candidates:
            text = (await el.inner_text()).strip()
            href = await el.get_attribute('href') or ''
            print(f"   [{text[:40]}] -> {href[:100]}")
        
        # 尝试直接点击 TRACK 相关的
        for el in track_candidates:
            try:
                text = (await el.inner_text()).strip().lower()
                if 'track' in text or 'trace' in text:
                    print(f"\n4. 点击: {text}")
                    await el.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    await asyncio.sleep(3)
                    
                    new_url = page.url
                    new_title = await page.title()
                    print(f"   新页面: {new_title}")
                    print(f"   URL: {new_url}")
                    
                    # 查找输入框
                    inputs = await page.query_selector_all('input:not([type="hidden"])')
                    print(f"   输入框: {len(inputs)} 个")
                    for inp in inputs:
                        pid = await inp.get_attribute('id') or ''
                        name = await inp.get_attribute('name') or ''
                        placeholder = await inp.get_attribute('placeholder') or ''
                        itype = await inp.get_attribute('type') or ''
                        print(f"     id={pid!r} name={name!r} type={itype!r} placeholder={placeholder!r}")
                        
                        if itype in ('text', 'search', '') or not itype:
                            try:
                                await inp.click()
                                await inp.fill(BL_NO)
                                filled = await inp.input_value()
                                print(f"     >>> 填入: {filled}")
                                
                                # 找提交按钮
                                await page.keyboard.press("Enter")
                                await asyncio.sleep(5)
                                await page.wait_for_load_state("networkidle", timeout=15000)
                                
                                # 结果截图
                                await page.screenshot(
                                    path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_final.png",
                                    full_page=True
                                )
                                
                                # 提取结果文本
                                result_text = await page.inner_text("body")
                                with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result.txt", "w", encoding="utf-8") as f:
                                    f.write(result_text)
                                
                                print(f"\n5. 查询完成!")
                                print(f"   结果页面 URL: {page.url}")
                                await browser.close()
                                return
                            except Exception as e:
                                print(f"     错误: {e}")
                    break
            except Exception as e:
                print(f"  点击失败: {e}")
        
        print("\n未找到可直接填写的跟踪表单")
        await browser.close()

asyncio.run(main())
