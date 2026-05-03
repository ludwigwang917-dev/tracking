# -*- coding: utf-8 -*-
"""MOD-004 一键批量查询 v2 — 统一引擎"""
import asyncio, sys, shutil
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from mod004.connectors.engine import CONNECTORS, QueryResult
from mod004.reader import read_all_sheets, filter_query_candidates

EXCEL = Path(r"D:\hermes\2026-02-04海运动态.xlsx")
BACKUP = Path(r"D:\hermes\MODS\MOD004\data\backups")
BACKUP.mkdir(parents=True, exist_ok=True)


def update_excel(results: list):
    """批量写回 Excel"""
    import openpyxl
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(EXCEL, BACKUP / f"海运动态_{ts}.xlsx")
    wb = openpyxl.load_workbook(EXCEL)
    updated = 0

    for r in results:
        if not r.success:
            continue

        for ws in wb.worksheets:
            for row in range(2, ws.max_row + 1):
                cell_val = str(ws.cell(row=row, column=2).value or '')
                if r.batch_no in cell_val:
                    hdr_e = str(ws.cell(row=1, column=5).value or '')
                    is_b = any(kw in hdr_e.upper() for kw in ['PORT', '目的港'])
                    loc_c, st_c = (15, 17) if is_b else (14, 16)

                    summary = f"{r.status} | {len(r.containers)}柜"
                    if r.containers:
                        summary += f" | {r.containers[0]}"
                    if r.locations:
                        summary += f" @{r.locations[0]}"

                    ws.cell(row=row, column=loc_c, value=summary[:50])
                    ws.cell(row=row, column=st_c, value=f"{r.carrier}查询完成")
                    updated += 1
                    break

    wb.save(EXCEL)
    print(f"\n✓ 更新 {updated} 行")


async def main():
    print("=" * 50)
    print("  MOD-004 海运一键查询")
    print("=" * 50)

    # 读取待查 booking
    sheets = read_all_sheets()
    candidates = filter_query_candidates(sheets)

    # 每个船司取一批
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    queries = {}
    for c in candidates:
        carrier = c.get('_carrier_norm', '')
        if carrier not in queries and carrier in CONNECTORS:
            queries[carrier] = []
        if carrier in queries and len(queries[carrier]) < count:
            queries[carrier].append({
                'batch_no': c['batch_no'],
                'bl_no': str(c.get('bl_no', '')),
            })

    print(f"待查: { {k: len(v) for k, v in queries.items()} }")

    results = []

    # PIL — 无头批量
    if 'PIL' in queries:
        print("\n--- PIL (无头) ---")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            for q in queries['PIL']:
                r = await CONNECTORS['PIL'].query(page, q['bl_no'], q['batch_no'])
                results.append(r)
                print(f"  {r.batch_no}: {r.status} | {len(r.containers)}柜")
            await browser.close()

    # CMA/MSC — 有头
    head_carriers = {k: v for k, v in queries.items() if k in ('CMA', 'MSC')}
    if head_carriers:
        print("\n--- CMA/MSC (有头) ---")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                window.chrome = { runtime: {} };
            """)

            for carrier, items in head_carriers.items():
                for q in items:
                    r = await CONNECTORS[carrier].query(page, q['bl_no'], q['batch_no'])
                    results.append(r)
                    print(f"  {r.batch_no}: {r.status} | {len(r.containers)}柜")

            await browser.close()

    # 写回
    update_excel(results)

    # 摘要
    print("\n" + "=" * 50)
    for r in results:
        icon = "✅" if r.success else "❌"
        print(f"  {icon} {r.carrier} {r.batch_no}: {r.status} | {len(r.containers)}柜")
        if r.containers:
            print(f"     箱号: {r.containers[:3]}{'...' if len(r.containers)>3 else ''}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
