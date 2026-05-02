# MOD-004: WhatsApp 摘要生成器 (v3)
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .config import SUMMARY_HEADER, SUMMARY_LINE

log = logging.getLogger(__name__)


def generate_daily_summary(
    sheets: Dict[str, List[Dict[str, Any]]],
    date: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> str:
    """生成每日发运动态文字摘要 (PRD 5.5 格式)"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    lines = []
    for sheet_name, rows in sheets.items():
        if not rows or sheet_name == "Sheet1":
            continue

        active_rows = [
            r for r in rows
            if r.get("batch_no") and str(r.get("batch_no")).strip()
        ]
        if not active_rows:
            continue

        if categories and sheet_name not in categories:
            continue

        lines.append(SUMMARY_HEADER.format(date=date, category=sheet_name))
        for row in active_rows:
            detail = _format_detail_line(row)
            if detail:
                lines.append(detail)
        lines.append("")

    return "\n".join(lines).strip()


def _format_detail_line(row: Dict[str, Any]) -> str:
    """格式化单行摘要"""
    batch_no = str(row.get("batch_no", "")).strip()
    if not batch_no:
        return ""

    # 箱型箱量: 优先 container_detail, 若不含 * 或数字则用 container_type
    container = str(row.get("container_detail", "")).strip()
    ctype = str(row.get("container_type", "")).strip()
    # 如果 container_detail 只是简单箱型(如"20GP"), container_type 含完整信息(如"30*20GP"), 用后者
    if container and ctype and '*' in ctype and '*' not in container:
        if len(ctype) > len(container):
            container = ctype
    # 如果还为空，尝试 container_qty + container_type 拼装
    if not container:
        ctype = str(row.get("container_type", "")).strip()
        cqty = row.get("container_qty")
        if cqty is not None and ctype:
            try:
                container = f"{ctype}*{int(float(str(cqty)))}"
            except (ValueError, TypeError):
                container = str(cqty)

    # ETA/ATA: 清理已有前缀，统一加 ETA 前缀
    eta_raw = str(row.get("eta_ata", "")).strip()
    eta_formatted = _format_eta(eta_raw)

    location = str(row.get("current_location", "")).strip() or "—"
    next_step = str(row.get("next_step", "")).strip() or "—"

    return SUMMARY_LINE.format(
        batch_no=batch_no,
        container_detail=container,
        eta_ata=eta_formatted,
        current_location=location,
        next_step=next_step,
    )


def _format_eta(value: str) -> str:
    """格式化 ETA 显示值: 去掉冗余前缀, 加标准 ETA 前缀"""
    value = value.strip()
    if not value:
        return ""

    # 去掉已有的 ETA/ATA/ETD/ATD 前缀
    for prefix in ["ETA ", "ETA", "ATA ", "ATA", "ETD ", "ETD", "ATD ", "ATD"]:
        upper = value.upper()
        if upper.startswith(prefix) and len(value) > len(prefix):
            value = value[len(prefix):].strip()
            break

    # 如果清理后只有数字或日期，前面加 ETA 前缀
    # 如果清理后是中文文本（如"已到达目的港"），也加 ETA 前缀
    if value:
        # 检查是否已经是纯中文描述（不含日期数字）
        has_alpha = any(c.isalpha() and ord(c) > 127 for c in value)
        if has_alpha:
            return f"ETA{value}"
        return f"ETA{value}"
    return ""


def generate_detail_report(
    sheets: Dict[str, List[Dict[str, Any]]],
    batch_no_filter: Optional[str] = None,
) -> str:
    """生成单票详细报告"""
    lines = []
    for sheet_name, rows in sheets.items():
        for row in rows:
            batch = str(row.get("batch_no", "")).strip()
            if batch_no_filter and batch != batch_no_filter:
                continue
            lines.append(f"[Booking] {batch}")
            lines.append(f"  船公司: {row.get('carrier', '—')}")
            lines.append(f"  目的港: {row.get('destination', '—')}")
            lines.append(f"  箱型箱量: {row.get('container_detail', row.get('container_type', '—'))}")
            lines.append(f"  提单号: {row.get('bl_no', '—')}")
            lines.append(f"  船名: {row.get('vessel', '—')}")
            lines.append(f"  ETD: {row.get('etd', '—')}")
            lines.append(f"  ETA: {row.get('eta_ata', '—')}")
            lines.append(f"  现在位置: {row.get('current_location', '—')}")
            lines.append(f"  下一步: {row.get('next_step', '—')}")
            lines.append("")
    return "\n".join(lines).strip()
