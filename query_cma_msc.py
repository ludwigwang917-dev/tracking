# -*- coding: utf-8 -*-
"""CMA + MSC 同时查询"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

CMA_BL = "ABQ0117757"
MSC_BL = "MEDUH7002122"

async def query_carrier(name, url, bl_no, search_selectors):
    """通用查询函数"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            viewport={"width": 1920, "height": 1080},
            locale='en-US',
        )
        page = await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        print(f"\n{'='*60}")
        print(f"{name}: {url}")
        print(f"{'='*60}")
        
        # Load with longer wait
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(10)  # Wait for JS rendering
        
        title = await page.title()
        url_final = page.url
        print(f"标题: {title}")
        print(f"URL: {url_final}")
        
        # Cookie
        for txt in ["Deny", "Reject All", "Reject", "Accept All", "Accept", "OK", "Got it"]:
            try:
                btn = await page.wait_for_selector(f'button:has-text("{txt}"), a:has-text("{txt}")', timeout=2000)
                if btn:
                    await btn.click()
                    print(f"Cookie: {txt}")
                    await asyncio.sleep(2)
                    break
            except:
                pass
        
        # Screenshot
        await page.screenshot(
            path=rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_page.png",
            full_page=True
        )
        
        # Save HTML
        html = await page.content()
        with open(rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # Find all forms and inputs
        form_data = await page.evaluate("""
        (function() {
            let forms = document.querySelectorAll('form');
            let result = {forms: [], inputs: []};
            
            forms.forEach(f => {
                let action = f.getAttribute('action') || '';
                let inputs = [];
                f.querySelectorAll('input:not([type="hidden"])').forEach(inp => {
                    inputs.push({
                        id: inp.id, name: inp.name, type: inp.type || 'text',
                        placeholder: inp.placeholder || '', visible: inp.offsetParent !== null
                    });
                });
                result.forms.push({action, inputs, visible: f.offsetParent !== null});
            });
            
            // also standalone inputs
            document.querySelectorAll('input:not([type="hidden"]):not(form input)').forEach(inp => {
                result.inputs.push({
                    id: inp.id, name: inp.name, type: inp.type || 'text',
                    placeholder: inp.placeholder || '', visible: inp.offsetParent !== null
                });
            });
            
            return result;
        })()
        """)
        
        print(f"表单: {len(form_data['forms'])} 个")
        for f in form_data['forms']:
            print(f"  action={f['action']} visible={f['visible']} inputs={f['inputs']}")
        print(f"独立输入框: {form_data['inputs']}")
        
        # Try to fill
        fill_result = await page.evaluate(f"""
        (function() {{
            let allInputs = document.querySelectorAll('input[type="text"], input:not([type])');
            for (let inp of allInputs) {{
                if (inp.offsetParent !== null && !inp.readOnly) {{
                    let placeholder = (inp.placeholder || '').toLowerCase();
                    let name = (inp.name || inp.id || '').toLowerCase();
                    // Prefer tracking/reference inputs
                    if (placeholder.includes('track') || placeholder.includes('search') ||
                        placeholder.includes('reference') || placeholder.includes('number') ||
                        placeholder.includes('booking') || placeholder.includes('bl') ||
                        name.includes('search') || name.includes('track') || name.includes('ref')) {{
                        inp.focus();
                        inp.value = '{bl_no}';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return {{filled: true, id: inp.id, placeholder: inp.placeholder}};
                    }}
                }}
            }}
            // fallback: first visible text input
            for (let inp of allInputs) {{
                if (inp.offsetParent !== null) {{
                    inp.value = '{bl_no}';
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return {{filled: true, id: inp.id, placeholder: inp.placeholder, fallback: true}};
                }}
            }}
            return {{filled: false}};
        }})()
        """)
        
        print(f"填入: {fill_result}")
        
        if fill_result.get('filled'):
            await asyncio.sleep(1)
            
            # Click search
            await page.evaluate("""
                (function() {
                    let btns = document.querySelectorAll('button, [role="button"], input[type="submit"]');
                    for (let b of btns) {
                        let t = (b.textContent || b.value || '').trim().toLowerCase();
                        if (t.includes('track') || t.includes('search') || t.includes('go') || t.includes('submit')) {
                            b.click();
                            return;
                        }
                    }
                })()
            """)
            
            await asyncio.sleep(10)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
            await asyncio.sleep(3)
            
            # Result screenshot
            await page.screenshot(
                path=rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_result.png",
                full_page=True
            )
            
            result_text = await page.inner_text("body")
            with open(rf"D:\hermes\MODS\MOD004\data\evidence\{name.lower()}_result.txt", "w", encoding="utf-8") as f:
                f.write(result_text)
            
            print(f"\n结果 (前4000字符):")
            print(result_text[:4000])
        
        await browser.close()
        return True


async def main():
    # CMA
    await query_carrier("CMA", "https://www.cma-cgm.com/ebusiness/tracking", CMA_BL, {})
    
    # MSC
    await query_carrier("MSC", "https://www.msc.com/track-a-shipment", MSC_BL, {})

asyncio.run(main())
