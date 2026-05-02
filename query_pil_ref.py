# -*- coding: utf-8 -*-
"""PIL Track & Trace — 填写 Booking Reference 查询"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
TRACK_URL = "https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("1. 打开 PIL Track & Trace ...")
        await page.goto(TRACK_URL, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(6)
        
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_ref_page.png")
        
        # 找所有输入框（包括 iframe 内的）
        frames = page.frames
        print(f"Frames: {len(frames)}")
        
        for frame in frames:
            inputs = await frame.query_selector_all('input:not([type="hidden"]):not([type="submit"])')
            if not inputs:
                continue
            
            f_url = frame.url[:80]
            print(f"\nFrame [{f_url}] 输入框:")
            
            for inp in inputs:
                pid = await inp.get_attribute('id') or ''
                name = await inp.get_attribute('name') or ''
                placeholder = await inp.get_attribute('placeholder') or ''
                label_text = ''
                
                # 找关联 label
                try:
                    label = await inp.evaluate("""
                        el => {
                            let l = el.closest('label');
                            if (l) return l.textContent.trim();
                            let id = el.getAttribute('id');
                            if (id) {
                                let lb = document.querySelector('label[for="'+id+'"]');
                                if (lb) return lb.textContent.trim();
                            }
                            return '';
                        }
                    """)
                    if label:
                        label_text = label
                except:
                    pass
                
                print(f"  id={pid!r} name={name!r} placeholder={placeholder!r} label={label_text[:60]!r}")
                
                # 找 "Reference Number" 相关的输入框
                is_ref = any(kw in (placeholder + label_text + name + pid).lower() 
                           for kw in ['reference', 'booking', 'bl', 'b/l', 'bill'])
                
                if is_ref or 'reference' in (placeholder + label_text).lower():
                    print(f"  >>> 这是 Reference Number 输入框!")
                    try:
                        await inp.click()
                        await inp.fill("")
                        await inp.fill(BL_NO)
                        await asyncio.sleep(1)
                        filled = await inp.input_value()
                        print(f"  >>> 已填入: {filled}")
                        
                        # 找 Search 按钮
                        search_btn = await frame.query_selector(
                            'button:has-text("Search"), button:has-text("Track"), '
                            'input[type="submit"], [role="button"]:has-text("Search")'
                        )
                        if search_btn:
                            await search_btn.click()
                            print(f"  >>> 已点击 Search")
                        else:
                            print(f"  >>> 按 Enter 提交")
                            await inp.press("Enter")
                        
                        await asyncio.sleep(8)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=15000)
                        except:
                            pass
                        
                        # 截图结果
                        await page.screenshot(
                            path=r"D:\hermes\MODS\MOD004\data\evidence\pil_result_ref.png",
                            full_page=True
                        )
                        
                        result = await page.inner_text("body")
                        print(f"\n{'='*60}")
                        print(f"查询结果")
                        print(f"{'='*60}")
                        print(result[:5000])
                        
                        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_result_ref.txt", "w", encoding="utf-8") as f:
                            f.write(result)
                        
                        await browser.close()
                        return
                    except Exception as e:
                        print(f"  >>> 错误: {e}")
        
        print("\n未找到 Reference Number 输入框，保存页面 HTML 分析")
        html = await page.content()
        # 提取包含 input 的片段
        import re
        for m in re.finditer(r'<input[^>]+>', html):
            print(f"  {m.group()[:150]}")
        
        await browser.close()

asyncio.run(main())
