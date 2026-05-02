# -*- coding: utf-8 -*-
"""patchright CI 查询 CMA/MSC"""
import asyncio, sys, os, json
from patchright.async_api import async_playwright

os.makedirs("evidence", exist_ok=True)

async def query(carrier, bl_no):
    urls = {
        "CMA": [
            "https://www.cma-cgm.com/ebusiness/tracking",
            "https://www.cma-cgm.com",
        ],
        "MSC": [
            "https://www.msc.com/track-a-shipment",
            "https://www.msc.com/en/track-a-shipment",
            "https://www.msc.com",
        ],
    }[carrier]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":1920,"height":1080})
        
        for url in urls:
            print(f"\n{carrier}: {url}")
            try:
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(8)
                title = await page.title()
                body = await page.inner_text("body")
                
                print(f"  标题: {title}")
                print(f"  正文: {len(body)} 字符")
                
                if "Access Denied" in body or "access denied" in body.lower():
                    print(f"  BLOCKED")
                    continue
                
                if len(body) < 50:
                    print(f"  EMPTY - SPA, trying next URL")
                    continue
                
                print(f"  VALID! {body[:200]}")
                
                # Dump structure
                structure = await page.evaluate("""
                (function() {
                    return {
                        url: location.href,
                        title: document.title,
                        inputs: Array.from(document.querySelectorAll('input:not([type="hidden"])'))
                            .filter(i => i.offsetParent !== null)
                            .map(i => ({id:i.id, name:i.name, type:i.type||'text', placeholder:i.placeholder||''})),
                        buttons: Array.from(document.querySelectorAll('button,input[type="submit"],[role="button"]'))
                            .map(b => (b.textContent||b.value||'').trim().substring(0,50))
                            .filter(t => t && t.length > 0)
                    }
                })()
                """)
                structure["carrier"] = carrier
                structure["status"] = "ok"
                
                with open(f"evidence/{carrier.lower()}_structure.json", "w") as f:
                    json.dump(structure, f, ensure_ascii=False, indent=2)
                
                print(json.dumps(structure, ensure_ascii=False)[:2000])
                
                # Try to fill and search
                for inp in structure.get("inputs", []):
                    sel = None
                    if inp.get("id"): sel = f"#{inp['id']}"
                    elif inp.get("name"): sel = f"[name='{inp['name']}']"
                    if sel:
                        try:
                            await page.fill(sel, bl_no)
                            print(f"  FILLED: {sel} = {bl_no}")
                            break
                        except: pass
                
                await page.keyboard.press("Enter")
                await asyncio.sleep(10)
                
                await page.screenshot(path=f"evidence/{carrier.lower()}_result.png", full_page=True)
                
                result = await page.inner_text("body")
                with open(f"evidence/{carrier.lower()}_result.txt", "w", encoding="utf-8") as f:
                    f.write(result)
                
                print(f"\nRESULT ({len(result)} 字符):")
                print(result[:3000])
                
                await browser.close()
                return
                
            except Exception as e:
                print(f"  ERROR: {e}")
        
        # All failed
        structure = {"carrier": carrier, "status": "blocked", "urls_tried": urls}
        with open(f"evidence/{carrier.lower()}_structure.json", "w") as f:
            json.dump(structure, f)
        
        await page.screenshot(path=f"evidence/{carrier.lower()}_result.png", full_page=True)
        await browser.close()

async def main():
    carrier = sys.argv[1].upper()
    bl = sys.argv[2]
    
    if carrier == "BOTH":
        await query("CMA", bl)
        await query("MSC", bl)
    else:
        await query(carrier, bl)

asyncio.run(main())
