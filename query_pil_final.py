# -*- coding: utf-8 -*-
"""PIL Track & Trace — 完整查询流程"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
TRACK_URL = "https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={"width": 1920, "height": 1080},
            locale='en-US',
        )
        page = await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print("1. 打开 PIL Track & Trace ...")
        await page.goto(TRACK_URL, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)  # 等 JS 渲染完

        title = await page.title()
        url = page.url
        print(f"   标题: {title}")
        print(f"   URL: {url}")

        # ============================================================
        # Step 1: 接受 Cookie
        # ============================================================
        print("\n2. 处理 Cookie 弹窗 ...")
        cookie_handled = False
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'button:has-text("I Agree")',
            'button:has-text("Allow")',
            'button:has-text("Got it")',
            '[id*="accept"]',
            '[id*="cookie"] button',
            '[class*="cookie"] button',
            'a:has-text("Accept")',
        ]

        for sel in cookie_selectors:
            try:
                btn = await page.wait_for_selector(sel, timeout=3000)
                if btn:
                    text = (await btn.inner_text()).strip()
                    print(f"   找到 Cookie 按钮: [{text}]")
                    await btn.click()
                    print(f"   ✓ 已点击接受 Cookie")
                    cookie_handled = True
                    await asyncio.sleep(2)
                    break
            except:
                continue

        if not cookie_handled:
            print("   未找到 Cookie 弹窗（可能已接受或无弹窗）")

        # 截图看看当前页面状态
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_step1_cookie.png")
        print("   截图: pil_step1_cookie.png")

        # ============================================================
        # Step 2: 找输入框填入 Booking 号
        # ============================================================
        print(f"\n3. 查找 Booking 输入框 ...")

        # 先看看有没有 iframe，PIL 的跟踪表单可能在 iframe 里
        frames = page.frames
        print(f"   页面有 {len(frames)} 个 frame")
        for f in frames:
            f_url = f.url[:100]
            print(f"     Frame: {f_url}")

        input_found = False
        target_frame = page  # 默认主页面

        # 检查每个 frame
        for frame in frames:
            inputs = await frame.query_selector_all(
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"])'
            )
            if inputs:
                print(f"\n   在 frame [{frame.url[:80]}] 找到 {len(inputs)} 个输入框:")
                for inp in inputs[:5]:
                    pid = await inp.get_attribute('id') or ''
                    name = await inp.get_attribute('name') or ''
                    placeholder = await inp.get_attribute('placeholder') or ''
                    itype = await inp.get_attribute('type') or 'text'
                    print(f"     id={pid!r} name={name!r} placeholder={placeholder!r} type={itype!r}")
                    
                    # 尝试填入
                    if not input_found:
                        try:
                            await inp.click()
                            await inp.fill("")
                            await inp.fill(BL_NO)
                            await asyncio.sleep(0.5)
                            filled = await inp.input_value()
                            if filled == BL_NO:
                                print(f"     ✓ 已填入 {BL_NO}")
                                input_found = True
                                target_frame = frame
                        except:
                            pass

        if not input_found:
            # 最后手段：直接用键盘输入
            print("\n   未自动找到输入框，尝试全局键盘输入 ...")
            # 点击页面任意位置激活
            await page.mouse.click(500, 300)
            await asyncio.sleep(1)
            # 选中所有文字然后输入
            await page.keyboard.press("Control+a")
            await page.keyboard.type(BL_NO)
            print(f"   已输入: {BL_NO}")

        # ============================================================
        # Step 3: 提交查询
        # ============================================================
        print(f"\n4. 提交查询 ...")

        # 找提交按钮
        btn_selectors = [
            'button:has-text("Track")',
            'button:has-text("Search")',
            'button:has-text("Submit")',
            'button:has-text("Go")',
            'input[type="submit"]',
            '[role="button"]:has-text("Track")',
            'button[type="submit"]',
        ]

        btn_clicked = False
        for sel in btn_selectors:
            try:
                btn = await page.wait_for_selector(sel, timeout=2000)
                if btn:
                    text = (await btn.inner_text()).strip()
                    print(f"   找到按钮: [{text}]")
                    await btn.click()
                    print(f"   ✓ 已点击")
                    btn_clicked = True
                    break
            except:
                continue

        if not btn_clicked:
            print("   未找到按钮，按 Enter 提交")
            await page.keyboard.press("Enter")

        # ============================================================
        # Step 4: 等待结果
        # ============================================================
        print(f"\n5. 等待查询结果 ...")
        await asyncio.sleep(6)
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            print("   页面持续加载中，继续...")
        await asyncio.sleep(3)

        # 最终截图
        await page.screenshot(
            path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_final.png",
            full_page=True
        )
        print("   截图: pil_result_final.png")

        # 提取所有文本
        result_text = await page.inner_text("body")
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result.txt", "w", encoding="utf-8") as f:
            f.write(result_text)

        print(f"\n{'='*60}")
        print(f"查询结果 (BEW500183600)")
        print(f"{'='*60}")
        print(result_text[:4000])

        await browser.close()
        print(f"\n✓ 完成")

asyncio.run(main())
