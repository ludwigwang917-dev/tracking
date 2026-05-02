# -*- coding: utf-8 -*-
"""CMA/MSC 查询 — CI 增强版 (含调试输出)"""
import asyncio, sys, os, json

os.makedirs("evidence", exist_ok=True)

async def query_cma(bl_no):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":1920,"height":1080})
        # Anti-detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = { runtime: {} };
        """)
        
        print(f"=== CMA 查询: {bl_no} ===")
        
        # Try multiple CMA tracking URLs
        urls = [
            "https://www.cma-cgm.com/ebusiness/tracking",
            "https://www.cma-cgm.com/ebusiness/tracking/search",
            "https://www.cma-cgm.com/ebusiness/schedules/tracking",
            "https://www.cma-cgm.com",
        ]
        
        for url in urls:
            try:
                print(f"\n尝试: {url}")
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(6)
                
                title = await page.title()
                body = await page.inner_text("body")
                print(f"  标题: {title}")
                print(f"  正文: {len(body)} 字符")
                
                if len(body) > 100 and "Access Denied" not in body:
                    print(f"  > 页面有效: {body[:200]}")
                    break
                elif len(body) < 10:
                    print("  > 页面为空(SPA)")
                else:
                    print(f"  > {body[:100]}")
            except Exception as e:
                print(f"  > 错误: {e}")
        
        await page.screenshot(path="evidence/cma_page.png", full_page=True)
        
        # Dump HTML structure
        html_snippet = await page.evaluate("""
            (function() {
                let result = {url: location.href, title: document.title};
                let forms = document.querySelectorAll('form');
                result.forms = Array.from(forms).map(f => ({
                    id: f.id, action: f.getAttribute('action') || '',
                    method: f.getAttribute('method') || 'get',
                    inputs: Array.from(f.querySelectorAll('input')).map(inp => ({
                        id: inp.id, name: inp.name, type: inp.type || 'text',
                        placeholder: inp.placeholder || ''
                    })),
                    buttons: Array.from(f.querySelectorAll('button')).map(b => ({
                        text: b.textContent.trim().substring(0,40), type: b.type
                    }))
                }));
                result.allInputs = Array.from(document.querySelectorAll('input:not([type="hidden"])')).map(inp => ({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '',
                    visible: inp.offsetParent !== null
                }));
                result.allButtons = Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"]')).map(b => ({
                    text: (b.textContent || b.value || '').trim().substring(0,40)
                }));
                return result;
            })()
        """)
        print(f"\n=== 页面结构 ===")
        print(json.dumps(html_snippet, ensure_ascii=False, indent=2)[:4000])
        
        # Try to fill and search
        fill_done = False
        for inp in html_snippet.get('allInputs', []):
            if inp.get('visible') and inp.get('id'):
                try:
                    sel = f"#{inp['id']}"
                    await page.fill(sel, bl_no)
                    print(f"\n填入: {sel} = {bl_no}")
                    fill_done = True
                    break
                except:
                    pass
        
        if fill_done:
            # Find and click search
            for btn in html_snippet.get('allButtons', []):
                txt = btn.get('text', '').lower()
                if any(kw in txt for kw in ['search','track','go','submit','find']):
                    try:
                        sel = f'button:has-text("{btn["text"]}")'
                        await page.click(sel)
                        print(f"点击: {btn['text']}")
                        break
                    except:
                        pass
            
            await asyncio.sleep(10)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
        else:
            print("\n未找到可填写输入框 — 页面可能被拦截或需要 JS 交互")
        
        await page.screenshot(path="evidence/cma_result.png", full_page=True)
        result_text = await page.inner_text("body")
        with open("evidence/cma_result.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"\n=== 最终结果 ({len(result_text)} 字符) ===")
        print(result_text[:3000])
        await browser.close()


async def query_msc(bl_no):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":1920,"height":1080})
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = { runtime: {} };
        """)
        
        print(f"\n\n=== MSC 查询: {bl_no} ===")
        
        urls = [
            "https://www.msc.com/en/track-a-shipment",
            "https://www.msc.com/track-a-shipment",
            "https://www.msc.com",
        ]
        
        for url in urls:
            try:
                print(f"\n尝试: {url}")
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(6)
                title = await page.title()
                body = await page.inner_text("body")
                print(f"  标题: {title}")
                print(f"  正文: {len(body)} 字符")
                if len(body) > 100 and "Access Denied" not in body:
                    print(f"  > 页面有效: {body[:200]}")
                    break
                else:
                    print(f"  > {body[:150]}")
            except Exception as e:
                print(f"  > 错误: {e}")
        
        await page.screenshot(path="evidence/msc_page.png", full_page=True)
        
        html_snippet = await page.evaluate("""
            (function() {
                let result = {url: location.href, title: document.title};
                result.allInputs = Array.from(document.querySelectorAll('input:not([type="hidden"])')).map(inp => ({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '', visible: inp.offsetParent !== null
                }));
                result.allButtons = Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"]')).map(b => ({
                    text: (b.textContent || b.value || '').trim().substring(0,40)
                }));
                return result;
            })()
        """)
        print(f"\n=== 页面结构 ===")
        print(json.dumps(html_snippet, ensure_ascii=False, indent=2)[:4000])
        
        fill_done = False
        for inp in html_snippet.get('allInputs', []):
            if inp.get('visible') and inp.get('id'):
                try:
                    await page.fill(f"#{inp['id']}", bl_no)
                    print(f"\n填入: #{inp['id']} = {bl_no}")
                    fill_done = True
                    break
                except:
                    pass
        
        if fill_done:
            for btn in html_snippet.get('allButtons', []):
                txt = btn.get('text', '').lower()
                if any(kw in txt for kw in ['search','track','go','submit','find']):
                    try:
                        await page.click(f'button:has-text("{btn["text"]}")')
                        print(f"点击: {btn['text']}")
                        break
                    except:
                        pass
            await asyncio.sleep(10)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
        
        await page.screenshot(path="evidence/msc_result.png", full_page=True)
        result_text = await page.inner_text("body")
        with open("evidence/msc_result.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"\n=== 最终结果 ({len(result_text)} 字符) ===")
        print(result_text[:3000])
        await browser.close()


async def main():
    if len(sys.argv) < 3:
        print("Usage: python query_cma_msc_ci.py <CMA|MSC> <BL>")
        sys.exit(1)
    carrier = sys.argv[1].upper()
    bl = sys.argv[2]
    if carrier == "CMA":
        await query_cma(bl)
    elif carrier == "MSC":
        await query_msc(bl)

asyncio.run(main())
