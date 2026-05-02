# -*- coding: utf-8 -*-
"""PIL Track & Trace — JS注入方式"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BL_NO = "BEW500183600"
TRACK_URL = "https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        print("加载页面...")
        await page.goto(TRACK_URL, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)
        
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_js_step0.png")
        
        # 用 JS 搜索所有输入框（包括 shadow DOM）
        result = await page.evaluate("""
        () => {
            // 递归搜索 shadow DOM
            function findAllInputs(root, depth) {
                if (depth > 10) return [];
                let results = [];
                
                // 当前 root 下的 input
                let inputs = root.querySelectorAll('input:not([type="hidden"])');
                inputs.forEach(inp => {
                    let label = '';
                    let parent = inp.closest('label');
                    if (parent) label = parent.textContent.trim();
                    if (!label) {
                        let id = inp.getAttribute('id');
                        if (id) {
                            let lb = root.querySelector('label[for="'+id+'"]');
                            if (lb) label = lb.textContent.trim();
                        }
                    }
                    results.push({
                        tag: inp.tagName,
                        id: inp.getAttribute('id') || '',
                        name: inp.getAttribute('name') || '',
                        type: inp.getAttribute('type') || 'text',
                        placeholder: inp.getAttribute('placeholder') || '',
                        label: label,
                        value: inp.value || '',
                        visible: inp.offsetParent !== null,
                    });
                });
                
                // 递归 shadow roots
                let allElements = root.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.shadowRoot) {
                        results = results.concat(findAllInputs(el.shadowRoot, depth + 1));
                    }
                });
                
                return results;
            }
            
            return findAllInputs(document, 0);
        }
        """)
        
        print(f"\n找到 {len(result)} 个输入框:")
        for r in result:
            print(f"  id={r['id']!r} name={r['name']!r} type={r['type']!r} "
                  f"placeholder={r['placeholder']!r} label={r['label'][:60]!r} "
                  f"visible={r['visible']}")
        
        # 尝试找到 Reference Number 输入框并填入
        print(f"\n尝试填入 BL 号 ...")
        
        fill_result = await page.evaluate(f"""
        () => {{
            function findAllInputs(root, depth) {{
                if (depth > 10) return [];
                let results = [];
                let inputs = root.querySelectorAll('input:not([type="hidden"])');
                inputs.forEach(inp => results.push(inp));
                let allElements = root.querySelectorAll('*');
                allElements.forEach(el => {{
                    if (el.shadowRoot) {{
                        results = results.concat(findAllInputs(el.shadowRoot, depth + 1));
                    }}
                }});
                return results;
            }}
            
            let allInputs = findAllInputs(document, 0);
            let filled = false;
            
            for (let inp of allInputs) {{
                let label = '';
                let parent = inp.closest('label');
                if (parent) label = parent.textContent;
                if (!label && inp.id) {{
                    let lb = document.querySelector('label[for="'+inp.id+'"]');
                    if (lb) label = lb.textContent;
                }}
                
                let placeholder = (inp.getAttribute('placeholder') || '').toLowerCase();
                let isRef = label.toLowerCase().includes('reference') ||
                            label.toLowerCase().includes('booking') ||
                            placeholder.includes('reference') ||
                            placeholder.includes('booking');
                
                if (isRef || (!filled && inp.offsetParent !== null && 
                    (placeholder.includes('reference') || label.toLowerCase().includes('number')))) {{
                    inp.focus();
                    inp.value = '';
                    inp.value = '{BL_NO}';
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    filled = true;
                    return {{success: true, id: inp.id, label: label}};
                }}
            }}
            
            // 如果没找到 reference，尝试填第一个可见的 text 输入框
            for (let inp of allInputs) {{
                if (inp.offsetParent !== null && (inp.type === 'text' || !inp.type)) {{
                    inp.focus();
                    inp.value = '{BL_NO}';
                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return {{success: true, id: inp.id, fallback: true}};
                }}
            }}
            
            return {{success: false}};
        }}
        """)
        
        print(f"填入结果: {fill_result}")
        
        if fill_result.get('success'):
            await asyncio.sleep(1)
            await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_js_filled.png")
            
            # 点 Search 按钮
            click_result = await page.evaluate("""
            () => {
                let buttons = document.querySelectorAll('button, [role="button"], input[type="submit"]');
                for (let btn of buttons) {
                    let text = (btn.textContent || btn.value || '').trim();
                    if (text.toLowerCase().includes('search') || 
                        text.toLowerCase().includes('track')) {
                        btn.click();
                        return {clicked: true, text: text};
                    }
                }
                return {clicked: false};
            }
            """)
            print(f"点击按钮: {click_result}")
            
            await asyncio.sleep(8)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
            
            await page.screenshot(
                path=r"D:\hermes\MODS\MOD004\data\evidence\pil_js_result.png",
                full_page=True
            )
            
            result_text = await page.inner_text("body")
            print(f"\n{'='*60}")
            print(f"查询结果")
            print(f"{'='*60}")
            print(result_text[:5000])
            
            with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_js_result.txt", "w", encoding="utf-8") as f:
                f.write(result_text)
        
        await browser.close()
        print("\n完成")

asyncio.run(main())
