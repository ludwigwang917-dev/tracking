# -*- coding: utf-8 -*-
"""PIL Track & Trace — 精确查询 BEW500183600"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        print("1. 打开 PIL 首页 ...")
        await page.goto("https://www.pilship.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Cookie
        for text in ["Deny", "Allow all"]:
            try:
                btn = await page.wait_for_selector(f'button:has-text("{text}")', timeout=3000)
                await btn.click()
                print(f"Cookie: {text}")
                await asyncio.sleep(2)
                break
            except:
                pass
        
        # ============================================================
        # Step 1: 切换到 B/L Number 模式
        # ============================================================
        print("\n2. 切换搜索模式为 B/L Number ...")
        
        # 点击自定义下拉框
        await page.evaluate("""
            document.querySelector('#customDropdownHome .custom-dropdown-selected').click();
        """)
        await asyncio.sleep(1)
        
        # 选择 B/L Number
        await page.evaluate("""
            let options = document.querySelectorAll('#customDropdownHome .custom-dropdown-options li');
            for (let opt of options) {
                if (opt.getAttribute('data-value') === 'TrackTraceBL') {
                    opt.click();
                    break;
                }
            }
        """)
        await asyncio.sleep(1)
        
        # 验证 module 值
        module_val = await page.evaluate("document.querySelector('#moduleHome').value")
        print(f"   Module: {module_val}")
        
        # 更新 Help 链接文本
        await page.evaluate("""
            let help = document.querySelector('#info-help');
            if (help) help.textContent = 'Where can I find B/L Number?';
        """)
        
        # ============================================================
        # Step 2: 填入 B/L 号
        # ============================================================
        print(f"\n3. 填入 B/L Number: {BL_NO}")
        
        await page.fill('#refNoHome', BL_NO)
        await asyncio.sleep(0.5)
        filled = await page.input_value('#refNoHome')
        print(f"   实际值: {filled}")
        
        # 截图表单状态
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_form_filled.png")
        
        # ============================================================
        # Step 3: 点击 Search
        # ============================================================
        print(f"\n4. 点击 Search ...")
        await page.click('#homeCttSubmit')
        
        # 等待结果
        await asyncio.sleep(8)
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            pass
        await asyncio.sleep(3)
        
        # ============================================================
        # Step 4: 获取结果
        # ============================================================
        await page.screenshot(
            path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_BL.png",
            full_page=True
        )
        print("   截图: pil_result_BL.png")
        
        result_text = await page.inner_text("body")
        
        print(f"\n{'='*60}")
        print(f"PIL 查询结果 — B/L: {BL_NO}")
        print(f"{'='*60}")
        print(result_text[:5000])
        
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result_BL.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        
        await browser.close()
        print("\n✓ 完成")

asyncio.run(main())
