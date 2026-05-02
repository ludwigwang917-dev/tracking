# -*- coding: utf-8 -*-
"""PIL 首页 Track & Trace — 直接操作 #trackTraceFormHome"""
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
        await asyncio.sleep(6)

        # 处理 Cookie
        try:
            cookie_btn = await page.wait_for_selector('button:has-text("Deny"), button:has-text("Allow all")', timeout=5000)
            if cookie_btn:
                text = (await cookie_btn.inner_text()).strip()
                await cookie_btn.click()
                print(f"Cookie: 点击了 [{text}]")
                await asyncio.sleep(2)
        except:
            print("无 Cookie 弹窗")

        # 滚动到 Track & Trace 区域
        print("\n2. 滚动到 Track & Trace ...")
        await page.evaluate("""
            let el = document.querySelector('#trackAndTrace, #asmTrack');
            if (el) {
                el.scrollIntoView({behavior: 'instant', block: 'center'});
            }
        """)
        await asyncio.sleep(2)
        await page.screenshot(path=r"D:\hermes\MODS\MOD004\data\evidence\pil_home_track.png")
        
        # 检查表单结构
        form_info = await page.evaluate("""
        () => {
            let form = document.querySelector('#trackTraceFormHome');
            if (!form) return {error: 'form not found'};
            
            let inputs = form.querySelectorAll('input:not([type="hidden"])');
            let result = [];
            inputs.forEach(inp => {
                result.push({
                    id: inp.id || '',
                    name: inp.name || '',
                    type: inp.type || 'text',
                    placeholder: inp.placeholder || '',
                    visible: inp.offsetParent !== null,
                });
            });
            
            // Also find the container label
            let labels = form.querySelectorAll('label');
            let labelTexts = [];
            labels.forEach(l => labelTexts.push(l.textContent.trim()));
            
            return {
                formId: form.id,
                formVisible: form.offsetParent !== null,
                inputs: result,
                labels: labelTexts,
                innerHTML: form.innerHTML.substring(0, 2000),
            };
        }
        """)
        
        print(f"表单信息: {form_info}")
        
        # 直接通过 JS 提交表单
        print(f"\n3. 通过 JS 填入 Reference Number 并提交 ...")
        
        submit_result = await page.evaluate(f"""
        () => {{
            let form = document.querySelector('#trackTraceFormHome');
            if (!form) return {{error: 'form not found'}};
            
            // 查找所有输入框
            let inputs = form.querySelectorAll('input');
            let filled = false;
            
            for (let inp of inputs) {{
                let id = (inp.id || '').toLowerCase();
                let name = (inp.name || '').toLowerCase();
                let placeholder = (inp.placeholder || '').toLowerCase();
                
                // 找到 Reference Number 或类似的输入框
                if (id.includes('ref') || name.includes('ref') || 
                    placeholder.includes('ref') || id.includes('booking') ||
                    placeholder.includes('number')) {{
                    inp.value = '{BL_NO}';
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                    inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                    filled = true;
                    break;
                }}
            }}
            
            // 如果没找到，找 module 切换为 Booking 查询
            let moduleInput = form.querySelector('#moduleHome, [name="module"]');
            if (moduleInput) {{
                // 尝试切换为 booking reference
                let currentModule = moduleInput.value;
                // PIL 可能用不同 module: TrackContStatus, TrackBLStatus 等
            }}
            
            return {{filled: filled}};
        }}
        """)
        
        print(f"填入结果: {submit_result}")
        
        # 获取完整 HTML 分析表单字段
        form_html = await page.evaluate("""
            let form = document.querySelector('#trackTraceFormHome');
            return form ? form.outerHTML : 'not found';
        """)
        
        with open(r"D:\hermes\MODS\MOD004\data\evidence\pil_form.html", "w", encoding="utf-8") as f:
            f.write(form_html)
        
        print(f"\n表单 HTML 已保存 (前3000字符):")
        print(form_html[:3000])
        
        await browser.close()

asyncio.run(main())
