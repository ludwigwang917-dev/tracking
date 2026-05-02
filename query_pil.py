# -*- coding: utf-8 -*-
"""PIL 官网实时查询 BEW500183600"""
import asyncio
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
URL = "https://www.pilship.com/track-by-booking"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print(f"打开 PIL 跟踪页面...")
        await page.goto(URL, timeout=30000, wait_until="networkidle")
        
        # 截图初始页面
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_initial.png")
        
        # 找输入框 - 尝试多种选择器
        print(f"查找输入框...")
        
        # 先打印页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 尝试常见的输入框选择器
        selectors = [
            'input[type="text"]',
            'input[name*="booking"]',
            'input[name*="track"]',
            'input[name*="bl"]',
            'input[name*="search"]',
            'input[id*="track"]',
            'input[id*="booking"]',
            'input[id*="search"]',
            'input[placeholder*="Booking"]',
            'input[placeholder*="B/L"]',
            'input[placeholder*="track"]',
            'input[placeholder*="search"]',
            'input:not([type="hidden"])',
        ]
        
        input_found = False
        for sel in selectors:
            try:
                inputs = await page.query_selector_all(sel)
                for inp in inputs:
                    name = await inp.get_attribute('name') or ''
                    pid = await inp.get_attribute('id') or ''
                    placeholder = await inp.get_attribute('placeholder') or ''
                    input_type = await inp.get_attribute('type') or ''
                    
                    print(f"  找到输入框: name={name!r} id={pid!r} placeholder={placeholder!r} type={input_type!r}")
                    
                    # 填入提单号
                    if input_type in ('text', 'search', '') or not input_type:
                        try:
                            await inp.fill(BL_NO)
                            print(f"  ✓ 已填入 {BL_NO}")
                            input_found = True
                            break
                        except:
                            pass
                if input_found:
                    break
            except:
                continue
        
        if not input_found:
            print("未找到输入框，保存页面 HTML")
            html = await page.content()
            with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            await browser.close()
            return
        
        # 查找并点击提交按钮
        print(f"\n查找提交按钮...")
        btn_selectors = [
            'button[type="submit"]',
            'button',
            'input[type="submit"]',
            'a[role="button"]',
            '[onclick*="submit"]',
        ]
        
        btn_found = False
        for sel in btn_selectors:
            try:
                btns = await page.query_selector_all(sel)
                for btn in btns:
                    text = await btn.inner_text()
                    text = text.strip()[:50]
                    print(f"  按钮: {text!r}")
                    if text and any(kw in text.upper() for kw in ['TRACK', 'SEARCH', 'SUBMIT', 'GO', '查询', '搜索', '提交']):
                        await btn.click()
                        print(f"  ✓ 点击了: {text!r}")
                        btn_found = True
                        break
                if btn_found:
                    break
            except:
                continue
        
        if not btn_found:
            # 尝试按回车提交
            print("未找到按钮，尝试回车提交...")
            await page.keyboard.press("Enter")
        
        # 等待结果加载
        print(f"\n等待结果...")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle", timeout=15000)
        
        # 截图结果
        await page.screenshot(
            path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result.png",
            full_page=True
        )
        print("结果截图保存: pil_result.png")
        
        # 提取页面文本
        body = await page.inner_text("body")
        print(f"\n=== 页面文本 (前3000字符) ===")
        print(body[:3000])
        
        # 保存完整文本
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result.txt", "w", encoding="utf-8") as f:
            f.write(body)
        
        await browser.close()
        print("\n查询完成")

asyncio.run(main())
