# -*- coding: utf-8 -*-
"""统一查询 — 自动使用已保存的登录态，无头模式批量查"""
import asyncio, sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

STATE_DIR = r"D:\hermes\MODS\MOD004\data\sessions"
EVIDENCE_DIR = r"D:\hermes\MODS\MOD004\data\evidence"
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)


async def query_with_state(carrier: str, bl_no: str, url: str, state_file: str):
    """用保存的登录态查询"""
    state_path = os.path.join(STATE_DIR, state_file)
    
    async with async_playwright() as p:
        # 加载登录态
        if os.path.exists(state_path):
            print(f"  加载会话: {state_file}")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=os.path.join(STATE_DIR, f"{carrier.lower()}_profile"),
                headless=True,
                viewport={"width": 1920, "height": 1080},
                args=['--no-sandbox'],
            )
            page = await context.new_page()
        else:
            print(f"  (无保存会话，纯无头模式)")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            # 反检测
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        
        print(f"  打开: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        title = await page.title()
        body = await page.inner_text("body")
        print(f"  标题: {title} | 正文: {len(body)}字符")
        
        # PIL 特殊处理：用已知的表单
        if carrier == "PIL":
            return await query_pil(page, bl_no)
        else:
            return await query_generic(page, carrier, bl_no)


async def query_pil(page, bl_no):
    """PIL 首页 Track & Trace 表单"""
    # 切换 B/L Number 模式
    await page.evaluate("""
        document.querySelector('#customDropdownHome .custom-dropdown-selected')?.click();
    """)
    await asyncio.sleep(1)
    await page.evaluate("""
        let opts = document.querySelectorAll('#customDropdownHome .custom-dropdown-options li');
        for (let o of opts) {
            if (o.getAttribute('data-value') === 'TrackTraceBL') { o.click(); break; }
        }
    """)
    await asyncio.sleep(0.5)
    
    # 填入并搜索
    await page.fill('#refNoHome', bl_no)
    await page.click('#homeCttSubmit')
    await asyncio.sleep(8)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass
    
    await page.screenshot(path=os.path.join(EVIDENCE_DIR, f"pil_{bl_no}.png"), full_page=True)
    result = await page.inner_text("body")
    with open(os.path.join(EVIDENCE_DIR, f"pil_{bl_no}.txt"), "w", encoding="utf-8") as f:
        f.write(result)
    return result


async def query_generic(page, carrier, bl_no):
    """通用查询：找输入框填单号"""
    # 找输入框
    info = await page.evaluate("""
        (function() {
            let inputs = Array.from(document.querySelectorAll('input:not([type="hidden"])'));
            let visible = inputs.filter(inp => inp.offsetParent !== null);
            let btns = Array.from(document.querySelectorAll('button, input[type="submit"]'))
                .map(b => (b.textContent || b.value || '').trim().substring(0,50))
                .filter(t => t);
            return {
                inputs: visible.map(inp => ({
                    id: inp.id, name: inp.name, placeholder: inp.placeholder || ''
                })),
                buttons: btns,
                pageText: document.body.innerText.substring(0, 300)
            };
        })()
    """)
    print(f"  输入框: {info['inputs']}")
    print(f"  按钮: {info['buttons'][:5]}")
    
    # 填入
    filled = False
    for inp in info['inputs']:
        try:
            sel = f"#{inp['id']}" if inp['id'] else f"input[name='{inp['name']}']" if inp['name'] else None
            if sel:
                await page.fill(sel, bl_no)
                print(f"  填入: {sel} = {bl_no}")
                filled = True
                break
        except:
            pass
    
    if filled:
        # 搜索
        for btxt in info['buttons']:
            if any(kw in btxt.lower() for kw in ['search','track','go','submit','find']):
                try:
                    await page.click(f'button:has-text("{btxt}")')
                    print(f"  点击: {btxt}")
                    break
                except:
                    pass
        await asyncio.sleep(8)
    
    await page.screenshot(path=os.path.join(EVIDENCE_DIR, f"{carrier.lower()}_{bl_no}.png"), full_page=True)
    result = await page.inner_text("body")
    with open(os.path.join(EVIDENCE_DIR, f"{carrier.lower()}_{bl_no}.txt"), "w", encoding="utf-8") as f:
        f.write(result)
    return result


async def main():
    if len(sys.argv) < 3:
        print("用法: python query_unified.py <PIL|CMA|MSC> <BL_NUMBER>")
        sys.exit(1)
    
    carrier = sys.argv[1].upper()
    bl = sys.argv[2]
    
    configs = {
        "PIL":  ("https://www.pilship.com", "pil_state.json"),
        "CMA":  ("https://www.cma-cgm.com/ebusiness/tracking", "cma_state.json"),
        "MSC":  ("https://www.msc.com/track-a-shipment", "msc_state.json"),
    }
    
    if carrier not in configs:
        print(f"不支持的船司: {carrier}")
        sys.exit(1)
    
    url, state_file = configs[carrier]
    
    print(f"\n{'='*60}")
    print(f"  {carrier} 查询: {bl}")
    print(f"{'='*60}")
    
    result = await query_with_state(carrier, bl, url, state_file)
    print(f"\n结果 ({len(result)} 字符):")
    print(result[:3000])

if __name__ == "__main__":
    asyncio.run(main())
