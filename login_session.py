# -*- coding: utf-8 -*-
"""CMA/MSC 人工登录 — 保存会话态供后续无头复用
用法:
  python login_session.py CMA   # 弹出浏览器，你手动登录/过验证
  python login_session.py MSC
"""
import asyncio, sys, os

STATE_DIR = r"D:\hermes\MODS\MOD004\data\sessions"
os.makedirs(STATE_DIR, exist_ok=True)

CARRIER_CONFIG = {
    "CMA": {
        "url": "https://www.cma-cgm.com/ebusiness/tracking",
        "state_file": "cma_state.json",
    },
    "MSC": {
        "url": "https://www.msc.com/track-a-shipment",
        "state_file": "msc_state.json",
    },
    "PIL": {
        "url": "https://www.pilship.com",
        "state_file": "pil_state.json",
    },
}

async def login_session(carrier: str):
    cfg = CARRIER_CONFIG[carrier]
    state_path = os.path.join(STATE_DIR, cfg["state_file"])
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # 如果有已保存的 state，先加载
        if os.path.exists(state_path):
            print(f"加载已有会话: {state_path}")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=os.path.join(STATE_DIR, f"{carrier.lower()}_profile"),
                headless=False,
                viewport={"width": 1920, "height": 1080},
            )
        else:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                storage_state=state_path if os.path.exists(state_path) else None,
            )
        
        page = await context.new_page()
        
        print(f"\n{'='*60}")
        print(f"  {carrier} 人工登录")
        print(f"{'='*60}")
        print(f"\n  浏览器已打开: {cfg['url']}")
        print(f"\n  请在浏览器中完成:")
        print(f"    1. 接受 Cookie")
        print(f"    2. 如果被拦截，完成人机验证")
        print(f"    3. 确认跟踪页面正常加载")
        print(f"    4. 回到这里按 Enter 保存会话")
        print(f"\n  (5分钟后自动超时)")
        
        await page.goto(cfg["url"], timeout=60000, wait_until="domcontentloaded")
        
        # 等待用户操作（最多 5 分钟）
        try:
            input("  >>> 完成后按 Enter 保存会话...")
        except (EOFError, KeyboardInterrupt):
            print("\n  超时，保存当前状态...")
        
        # 保存 storage state（cookies, localStorage）
        await context.storage_state(path=state_path)
        print(f"\n  ✓ 会话已保存到: {state_path}")
        
        # 验证：用保存的 state 做一次无头查询
        print(f"\n  验证无头模式...")
        await context.close()
        
        # 无头验证
        browser2 = await p.chromium.launch(headless=True)
        ctx2 = await browser2.new_context(
            viewport={"width": 1920, "height": 1080},
            storage_state=state_path,
        )
        page2 = await ctx2.new_page()
        await page2.goto(cfg["url"], timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        title = await page2.title()
        body = await page2.inner_text("body")
        print(f"  无头模式: 标题={title} | 正文={len(body)}字符")
        
        if len(body) > 100 and "Access Denied" not in body:
            print(f"  ✓ 无头模式可用!")
        else:
            print(f"  ⚠ 无头模式可能仍有问题: {body[:100]}")
        
        await browser2.close()

async def main():
    if len(sys.argv) < 2:
        print("用法: python login_session.py <CMA|MSC|PIL>")
        sys.exit(1)
    await login_session(sys.argv[1].upper())

if __name__ == "__main__":
    asyncio.run(main())
