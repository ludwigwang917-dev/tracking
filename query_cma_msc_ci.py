# -*- coding: utf-8 -*-
"""CMA/MSC 查询 — GitHub Actions CI 版本
Usage: python query_cma_msc_ci.py CMA ABQ0117757
       python query_cma_msc_ci.py MSC MEDUH7002122
"""
import asyncio, sys, os, json
from datetime import datetime

os.makedirs("evidence", exist_ok=True)

async def query_cma(bl_no):
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print(f"CMA 查询: {bl_no}")
        print("打开 CMA 首页...")
        
        await page.goto("https://www.cma-cgm.com", timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        title = await page.title()
        body = await page.inner_text("body")
        print(f"标题: {title} | 正文: {len(body)} 字符")
        
        if len(body) < 50:
            print("页面内容极少，尝试直接访问 tracking 页面...")
            await page.goto("https://www.cma-cgm.com/ebusiness/tracking", timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(10)
            body = await page.inner_text("body")
            print(f"Tracking 页面: {len(body)} 字符")
        
        await page.screenshot(path="evidence/cma_page.png", full_page=True)
        
        # 找输入框
        inputs = await page.evaluate("""
            (function() {
                return Array.from(document.querySelectorAll('input:not([type="hidden"])')).map(inp => ({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '',
                    visible: inp.offsetParent !== null
                }));
            })()
        """)
        print(f"输入框: {json.dumps(inputs, ensure_ascii=False)}")
        
        # 填单号
        filled = False
        for inp_info in inputs:
            if inp_info['visible']:
                try:
                    await page.fill(f"#{inp_info['id']}", bl_no)
                    print(f"填入 {inp_info['id']}: {bl_no}")
                    filled = True
                    break
                except:
                    pass
        
        if not filled:
            # JS 注入
            fill_result = await page.evaluate(f"""
                (function() {{
                    let inputs = document.querySelectorAll('input:not([type="hidden"])');
                    for (let inp of inputs) {{
                        if (inp.offsetParent !== null) {{
                            inp.value = '{bl_no}';
                            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                            return {{filled: true}};
                        }}
                    }}
                    return {{filled: false}};
                }})()
            """)
            print(f"JS填入: {fill_result}")
        
        if filled or (isinstance(locals().get('fill_result'), dict) and locals().get('fill_result', {}).get('filled')):
            # 搜索
            await page.evaluate("""
                (function() {
                    let btns = document.querySelectorAll('button, [role="button"], input[type="submit"]');
                    for (let b of btns) {
                        let t = (b.textContent || b.value || '').trim().toLowerCase();
                        if (t.includes('search') || t.includes('track') || t.includes('submit')) {
                            b.click();
                            return true;
                        }
                    }
                })()
            """)
            await asyncio.sleep(12)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
        
        await page.screenshot(path="evidence/cma_result.png", full_page=True)
        result_text = await page.inner_text("body")
        
        with open("evidence/cma_result.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        
        print(f"\n结果 ({len(result_text)} 字符):")
        print(result_text[:3000])
        
        await browser.close()


async def query_msc(bl_no):
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        # Anti-detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        """)
        
        print(f"\nMSC 查询: {bl_no}")
        
        # 尝试多个 MSC URL
        urls = [
            "https://www.msc.com/track-a-shipment",
            "https://www.msc.com/en/track-a-shipment",
            "https://www.msc.com",
        ]
        
        for url in urls:
            print(f"尝试: {url}")
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(8)
                title = await page.title()
                body = await page.inner_text("body")
                print(f"标题: {title} | 正文: {len(body)} 字符")
                
                if "Access Denied" not in body and len(body) > 50:
                    print("✓ 页面加载成功")
                    break
                else:
                    print("✗ 被拦截")
            except Exception as e:
                print(f"  错误: {e}")
        
        await page.screenshot(path="evidence/msc_page.png", full_page=True)
        
        # 找输入框
        inputs = await page.evaluate("""
            (function() {
                return Array.from(document.querySelectorAll('input:not([type="hidden"])')).map(inp => ({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '',
                    visible: inp.offsetParent !== null
                }));
            })()
        """)
        print(f"输入框: {json.dumps(inputs, ensure_ascii=False)}")
        
        # 找表单
        forms = await page.evaluate("""
            (function() {
                return Array.from(document.querySelectorAll('form')).map(f => ({
                    id: f.id, action: f.getAttribute('action') || '',
                    inputs: Array.from(f.querySelectorAll('input')).map(inp => ({
                        id: inp.id, name: inp.name, type: inp.type || 'text',
                        placeholder: inp.placeholder || ''
                    }))
                }));
            })()
        """)
        print(f"表单: {json.dumps(forms, ensure_ascii=False)[:2000]}")
        
        # 填单号
        for inp_info in inputs:
            if inp_info['visible']:
                try:
                    await page.fill(f"#{inp_info['id']}", bl_no)
                    print(f"填入 {inp_info['id']}: {bl_no}")
                    break
                except:
                    pass
        
        await page.keyboard.press("Enter")
        await asyncio.sleep(12)
        
        await page.screenshot(path="evidence/msc_result.png", full_page=True)
        result_text = await page.inner_text("body")
        
        with open("evidence/msc_result.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        
        print(f"\n结果 ({len(result_text)} 字符):")
        print(result_text[:3000])
        
        await browser.close()


async def main():
    if len(sys.argv) < 3:
        print("Usage: python query_cma_msc_ci.py <CMA|MSC> <BL_NUMBER>")
        sys.exit(1)
    
    carrier = sys.argv[1].upper()
    bl_no = sys.argv[2]
    
    if carrier == "CMA":
        await query_cma(bl_no)
    elif carrier == "MSC":
        await query_msc(bl_no)
    else:
        print(f"Unknown carrier: {carrier}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
