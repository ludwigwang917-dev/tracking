# -*- coding: utf-8 -*-
"""PIL Track & Trace — 键盘导航方式填写"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
TRACK_URL = "https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        await page.goto(TRACK_URL, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(6)
        print("页面已加载")

        # 先处理 Cookie（页面可能有 consent banner）
        # 尝试按 Escape 关闭弹窗
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # 点击 "Enter Reference Number:" 文字附近来聚焦
        # 先找到包含这个文字的元素
        ref_label = await page.query_selector('text="Enter Reference Number"')
        if ref_label:
            box = await ref_label.bounding_box()
            if box:
                # 点击 label 下方（输入框应该在 label 后面/下面）
                x = box['x'] + box['width'] + 20
                y = box['y'] + box['height'] / 2
                print(f"点击 Reference Number 附近: ({x}, {y})")
                await page.mouse.click(x, y)
                await asyncio.sleep(1)
            else:
                print("label 不可见，尝试 Tab 导航")
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.5)
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.5)
        else:
            print("未找到 Reference Number label，尝试 Tab 导航")
            # 点击页面中间激活
            await page.mouse.click(960, 400)
            await asyncio.sleep(0.5)
            # Tab 多次跳到 Reference Number 输入框
            for i in range(8):
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.3)

        # 清空并输入
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await page.keyboard.type(BL_NO)
        await asyncio.sleep(0.5)
        print(f"已输入: {BL_NO}")

        # 截图看看
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_typed.png")

        # Tab 到 Search 按钮然后 Enter
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Enter")
        print("已提交")

        # 等待结果
        await asyncio.sleep(8)
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            pass

        # 截图结果
        await page.screenshot(
            path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_final.png",
            full_page=True
        )

        result = await page.inner_text("body")
        print(f"\n{'='*60}")
        print(f"查询结果 (BEW500183600)")
        print(f"{'='*60}")
        print(result[:5000])

        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result.txt", "w", encoding="utf-8") as f:
            f.write(result)

        await browser.close()
        print("\n完成")

asyncio.run(main())
