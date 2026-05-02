# -*- coding: utf-8 -*-
"""patchright CI 查询 CMA/MSC — 加强错误处理"""
import asyncio, sys, os, json, traceback
from patchright.async_api import async_playwright, TimeoutError as PRTimeout

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
    }.get(carrier, [])

    result = {"carrier": carrier, "bl": bl_no, "status": "starting", "urls_tried": [], "error": None}
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width":1920,"height":1080})
            
            for url in urls:
                result["urls_tried"].append(url)
                try:
                    print(f"\n{carrier}: {url}")
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(6)
                    
                    title = await page.title()
                    body = await page.inner_text("body")
                    print(f"  Title: {title}")
                    print(f"  Body: {len(body)} chars")
                    
                    if "Access Denied" in body or "denied" in body.lower():
                        print(f"  BLOCKED by CDN")
                        result["status"] = "blocked"
                        continue
                    
                    if len(body) < 30:
                        print(f"  EMPTY - likely SPA or blocked")
                        result["status"] = "empty"
                        continue
                    
                    # Valid page
                    result["status"] = "ok"
                    result["title"] = title
                    result["body_sample"] = body[:300]
                    
                    # Get structure
                    structure = await page.evaluate("""
                    (function() {
                        return {
                            url: location.href,
                            inputs: Array.from(document.querySelectorAll('input:not([type="hidden"])'))
                                .map(i => ({id:i.id||'', name:i.name||'', type:i.type||'text', placeholder:i.placeholder||'', visible:i.offsetParent!==null})),
                            buttons: Array.from(document.querySelectorAll('button,input[type="submit"],[role="button"],a.btn'))
                                .map(b => (b.textContent||b.value||'').trim()).filter(t=>t&&t.length<60).slice(0,15)
                        }
                    })()
                    """)
                    result["structure"] = structure
                    print(json.dumps(structure, indent=2, ensure_ascii=False)[:2000])
                    
                    # Try fill
                    for inp in structure.get("inputs", []):
                        if inp.get("visible"):
                            sel = f"#{inp['id']}" if inp['id'] else f"[name='{inp['name']}']" if inp['name'] else None
                            if sel:
                                try:
                                    await page.fill(sel, bl_no)
                                    print(f"  FILLED: {sel}")
                                    break
                                except: pass
                    
                    # Click search or press Enter
                    for btn in structure.get("buttons", []):
                        if any(kw in btn.lower() for kw in ['search','track','go','submit']):
                            try:
                                await page.click(f'button:has-text("{btn}")')
                                print(f"  CLICKED: {btn}")
                                break
                            except: pass
                    else:
                        await page.keyboard.press("Enter")
                        print("  Pressed Enter")
                    
                    await asyncio.sleep(8)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=20000)
                    except:
                        pass
                    
                    result_text = await page.inner_text("body")
                    result["result_text"] = result_text[:5000]
                    result["result_length"] = len(result_text)
                    
                    await page.screenshot(path=f"evidence/{carrier.lower()}_result.png", full_page=True)
                    with open(f"evidence/{carrier.lower()}_result.txt", "w", encoding="utf-8") as f:
                        f.write(result_text)
                    
                    print(f"\nRESULT ({len(result_text)} chars):")
                    print(result_text[:3000])
                    
                    await browser.close()
                    break  # Success, stop trying URLs
                    
                except PRTimeout:
                    print(f"  TIMEOUT")
                    result["status"] = "timeout"
                except Exception as e:
                    print(f"  ERROR: {e}")
                    result["status"] = "error"
                    result["error"] = str(e)
            
            if "browser" in dir():
                try: await browser.close()
                except: pass
    
    except Exception as e:
        result["status"] = "fatal"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"FATAL: {e}")
        print(traceback.format_exc())
    
    # Always write result
    with open(f"evidence/{carrier.lower()}_structure.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nFINAL STATUS: {result['status']}")
    return result

async def main():
    carrier = sys.argv[1].upper()
    bl = sys.argv[2]
    
    if carrier == "BOTH":
        print("=== CMA ===")
        await query("CMA", bl)
        print("\n=== MSC ===")
        await query("MSC", bl)
    else:
        await query(carrier, bl)

if __name__ == "__main__":
    asyncio.run(main())
