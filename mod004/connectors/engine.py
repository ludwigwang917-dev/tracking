# MOD-004 M4: 统一查询引擎
# PIL(无头) + CMA/MSC(有头+反检测) 三个连接器

import asyncio, re, os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

EVIDENCE = Path(r"D:\hermes\MODS\MOD004\data\evidence")
EVIDENCE.mkdir(parents=True, exist_ok=True)


@dataclass
class QueryResult:
    carrier: str
    batch_no: str = ""
    bl_no: str = ""
    success: bool = False
    status: str = ""           # 空箱已归还 / 已卸船 / 运输中 / ...
    containers: list = field(default_factory=list)
    dates: list = field(default_factory=list)
    locations: list = field(default_factory=list)
    raw_text: str = ""
    error: str = ""


class PILConnector:
    """PIL 无头查询 — 已验证稳定"""
    
    async def query(self, page, bl_no: str, batch_no: str) -> QueryResult:
        result = QueryResult(carrier="PIL", batch_no=batch_no, bl_no=bl_no)
        
        try:
            await page.goto("https://www.pilship.com", timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # 切换为 B/L Number
            await page.evaluate("""
                document.querySelector('#customDropdownHome .custom-dropdown-selected')?.click();
            """)
            await asyncio.sleep(0.3)
            await page.evaluate("""
                let opts = document.querySelectorAll('#customDropdownHome .custom-dropdown-options li');
                for (let o of opts) {
                    if (o.getAttribute('data-value') === 'TrackTraceBL') { o.click(); break; }
                }
            """)
            await asyncio.sleep(0.3)
            
            await page.fill('#refNoHome', '')
            await page.fill('#refNoHome', bl_no)
            await page.click('#homeCttSubmit')
            await asyncio.sleep(6)
            
            text = await page.inner_text("body")
            result.raw_text = text
            result.success = True
            
            # 解析
            result.containers = list(set(re.findall(r'\b(PCIU|TCLU|BMOU|TCNU|TRLU)\d+\b', text)))
            s = text.upper()
            if "EMPTY" in s and "RETURN" in s:
                result.status = "空箱已归还"
            elif "DISCHARGED" in s:
                result.status = "已卸船"
            elif "LOADED" in s:
                result.status = "已装船"
            else:
                result.status = "查询完成"
            
            result.dates = re.findall(r'(\d{2}-[A-Z][a-z]{2}-\d{4})', text)
            
        except Exception as e:
            result.error = str(e)
        
        return result


class CMAConnector:
    """CMA 有头查询 — 需反检测"""
    
    async def query(self, page, bl_no: str, batch_no: str) -> QueryResult:
        result = QueryResult(carrier="CMA", batch_no=batch_no, bl_no=bl_no)
        
        try:
            await page.goto("https://www.cma-cgm.com/ebusiness/tracking",
                          timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(8)
            
            # 填提单号
            await page.fill("#Reference", bl_no)
            await asyncio.sleep(0.5)
            await page.keyboard.press("Enter")
            await asyncio.sleep(12)
            
            text = await page.inner_text("body")
            result.raw_text = text
            result.success = True
            
            # 解析
            result.containers = list(set(re.findall(r'\b([A-Z]{4}\d{7})\b', text)))
            result.dates = re.findall(r'(\d{2}-[A-Z]{3}-\d{4}|\d{4}-\d{2}-\d{2})', text)
            
            s = text.upper()
            if "EMPTY IN DEPOT" in s:
                result.status = "空箱已归还"
            elif "DISCHARGED" in s:
                result.status = "已卸船"
            elif "LOADED" in s:
                result.status = "已装船"
            elif "GATE OUT" in s:
                result.status = "已提柜"
            elif "UNDER WAY" in s or "SAILING" in s:
                result.status = "航行中"
            else:
                result.status = "查询完成"
            
            # 提取位置
            ports = re.findall(r'(TIANJIN|SHANGHAI|NINGBO|QINGDAO|SINGAPORE|CHONGQING|YANTIAN|ROTTERDAM|HAMBURG|ANTWERP)', text, re.I)
            result.locations = list(set(ports))
            
        except Exception as e:
            result.error = str(e)
        
        return result


class MSCConnector:
    """MSC 有头查询 — 需反检测"""
    
    async def query(self, page, bl_no: str, batch_no: str) -> QueryResult:
        result = QueryResult(carrier="MSC", batch_no=batch_no, bl_no=bl_no)
        
        try:
            await page.goto("https://www.msc.com/track-a-shipment",
                          timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(6)
            
            # 找输入框并填入
            info = await page.evaluate("""
                (function() {
                    let inputs = document.querySelectorAll('input:not([type="hidden"])');
                    return Array.from(inputs)
                        .filter(inp => inp.offsetParent !== null)
                        .map(inp => ({id: inp.id, name: inp.name, type: inp.type || 'text'}));
                })()
            """)
            
            filled = False
            for inp in info:
                sel = f"#{inp['id']}" if inp.get('id') else f"[name='{inp['name']}']" if inp.get('name') else None
                if sel:
                    try:
                        await page.click(sel)
                        await page.fill(sel, "")
                        await page.fill(sel, bl_no)
                        val = await page.input_value(sel)
                        if val == bl_no:
                            filled = True
                            break
                    except:
                        pass
            
            if not filled:
                # Fallback: JS injection
                await page.evaluate(f"""
                    let inputs = document.querySelectorAll('input');
                    for (let inp of inputs) {{
                        if (inp.offsetParent !== null) {{ inp.value = '{bl_no}'; inp.dispatchEvent(new Event('input', {{bubbles: true}})); break; }}
                    }}
                """)
            
            await asyncio.sleep(0.5)
            await page.keyboard.press("Enter")
            await asyncio.sleep(15)
            
            text = await page.inner_text("body")
            result.raw_text = text
            result.success = True
            
            # 解析
            result.containers = list(set(re.findall(r'\b([A-Z]{4}\d{7})\b', text)))
            result.dates = re.findall(r'(\d{2}-[A-Z]{3}-\d{4})', text)
            
            s = text.upper()
            if "EMPTY RETURN" in s:
                result.status = "空箱已归还"
            elif "DISCHARGED" in s:
                result.status = "已卸船"
            elif "LOADED" in s:
                result.status = "已装船"
            elif "GATE OUT" in s:
                result.status = "已提柜"
            elif "TRANSIT" in s or "SAILING" in s:
                result.status = "运输中"
            else:
                result.status = "查询完成"
            
        except Exception as e:
            result.error = str(e)
        
        return result


# 导出
CONNECTORS = {
    "PIL": PILConnector(),
    "CMA": CMAConnector(),
    "MSC": MSCConnector(),
}
