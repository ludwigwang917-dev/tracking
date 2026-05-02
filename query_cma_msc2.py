# -*- coding: utf-8 -*-
"""CMA + MSC 查询 — 加强反检测"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

CMA_BL = "ABQ0117757"
MSC_BL = "MEDUH7002122"

async def query(name, url, bl_no):
    async with async_playwright() as p:
        # 使用 playwright-stealth 替代方案
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={"width": 1920, "height": 1080},
            locale='en-US',
            timezone_id='Asia/Shanghai',
        )
        page = await ctx.new_page()
        
        # 注入反检测脚本
        await page.add_init_script("""
            // Overwrite navigator properties
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en','zh-CN']});
            
            // Remove chrome runtime
            window.chrome = { runtime: {} };
            
            // Overwrite permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
            );
        """)
        
        print(f"\n{'='*60}")
        print(f"{name}: {url}")
        print(f"单号: {bl_no}")
        print(f"{'='*60}")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(10)
            title = await page.title()
            print(f"标题: {title}")
            
            # 检测是否被拦截
            body = await page.inner_text("body")
            if "Access Denied" in body or "access denied" in body.lower():
                print("⚠ 被拦截")
                await page.screenshot(path=rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_blocked.png")
                await browser.close()
                return
            
            if len(body) < 50:
                print(f"页面内容极少 ({len(body)} 字符)，可能仍在加载或需要更多等待")
                await asyncio.sleep(10)
                body = await page.inner_text("body")
                print(f"再次检查: {len(body)} 字符")
            
            # Cookie 弹窗
            for txt in ["Deny", "Reject All", "Reject", "Accept All", "Accept", "OK", "Got it", "I understand"]:
                try:
                    btn = await page.wait_for_selector(
                        f'button:has-text("{txt}"), a:has-text("{txt}"), [aria-label*="{txt}"]',
                        timeout=2000
                    )
                    if btn:
                        await btn.click()
                        print(f"Cookie: {txt}")
                        await asyncio.sleep(2)
                        break
                except:
                    pass
            
            await page.screenshot(path=rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_page.png", full_page=True)
            
            # 找输入框
            inputs = await page.evaluate("""
            (function() {
                let all = document.querySelectorAll('input:not([type="hidden"])');
                return Array.from(all).map(inp => ({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '', 
                    visible: inp.offsetParent !== null && inp.offsetWidth > 0
                }));
            })()
            """)
            print(f"输入框: {inputs}")
            
            # 填单号
            fill_result = await page.evaluate(f"""
            (function() {{
                let inputs = document.querySelectorAll('input:not([type="hidden"])');
                for (let inp of inputs) {{
                    if (inp.offsetParent !== null && inp.offsetWidth > 0 && !inp.readOnly) {{
                        inp.focus();
                        inp.value = '';
                        inp.value = '{bl_no}';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('blur', {{bubbles: true}}));
                        return {{filled: true, id: inp.id, placeholder: inp.placeholder}};
                    }}
                }}
                return {{filled: false}};
            }})()
            """)
            print(f"填入: {fill_result}")
            
            if fill_result.get('filled'):
                await asyncio.sleep(1)
                
                # 点搜索
                await page.evaluate("""
                (function() {
                    let clicks = document.querySelectorAll('button, [role="button"], input[type="submit"], a.btn');
                    for (let c of clicks) {
                        let t = (c.textContent || c.value || '').trim().toLowerCase();
                        if (t.includes('search') || t.includes('track') || t.includes('go') || t.includes('submit')) {
                            c.click();
                            return;
                        }
                    }
                })()
                """)
                
                print("等待结果...")
                await asyncio.sleep(12)
                try:
                    await page.wait_for_load_state("networkidle", timeout=20000)
                except:
                    pass
                await asyncio.sleep(3)
                
                await page.screenshot(path=rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_result.png", full_page=True)
                
                result = await page.inner_text("body")
                with open(rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_result.txt", "w", encoding="utf-8") as f:
                    f.write(result)
                
                print(f"\n结果 (前4000):")
                print(result[:4000])
            else:
                print("未找到输入框")
                # 保存 HTML 分析
                html = await page.content()
                import re
                forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL)
                print(f"HTML 中表单数: {len(forms)}")
                for fm in forms[:2]:
                    print(f"  {fm[:500]}")
        
        except Exception as e:
            print(f"错误: {e}")
        
        await browser.close()

async def main():
    await query("CMA", "https://www.cma-cgm.com/ebusiness/tracking", CMA_BL)
    await query("MSC", "https://www.msc.com/track-a-shipment", MSC_BL)

asyncio.run(main())
