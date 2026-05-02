# MOD-004 M5: 查询结果解析模块
# 职责: 将 QueryResult 转换为可写回 Excel 的字段，检测重大变化

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .config import ETA_CHANGE_THRESHOLD_DAYS
from .connectors.base import QueryResult

log = logging.getLogger(__name__)


def parse_result(result: QueryResult) -> Dict[str, Any]:
    """将查询结果转换为写回 Excel 的字段字典

    返回字段:
        - etd, atd, eta_ata: 日期字符串
        - current_location: 现在位置
        - next_step: 下一步预计
        - query_status: 查询状态 (ok / no_result / error / ...)
        - vessel: 船名 (如果查询返回不同船名)
    """
    updates = {
        "etd":           result.etd or "",
        "atd":           result.atd or "",
        "eta_ata":       result.eta or result.ata or "",
        "vessel":        result.vessel or "",
        "current_location": result.current_location or "",
        "next_step":     result.next_step or "",
        "query_status":  result.status or "ok",
    }

    # 清理空值
    updates = {k: v for k, v in updates.items() if v is not None}
    return updates


def detect_changes(
    updates: Dict[str, Any],
    old_row: Dict[str, Any],
) -> List[Dict[str, str]]:
    """检测新旧值的重大差异，返回需要人工确认的变更列表

    触发确认的条件:
        1. ETA 变化超过阈值天数
        2. 船名发生变化
        3. 目的港不一致 (预留)
    """
    alerts = []

    # ETA 变化检测
    new_eta = updates.get("eta_ata", "")
    old_eta = str(old_row.get("eta_ata", "")).strip()

    if new_eta and old_eta:
        try:
            new_date = _parse_date(new_eta)
            old_date = _parse_date(old_eta)
            if new_date and old_date:
                diff = abs((new_date - old_date).days)
                if diff > ETA_CHANGE_THRESHOLD_DAYS:
                    alerts.append({
                        "type": "eta_change",
                        "field": "eta_ata",
                        "old": old_eta,
                        "new": new_eta,
                        "diff_days": diff,
                        "message": f"ETA 变化 {diff} 天: {old_eta} -> {new_eta}",
                    })
        except Exception:
            pass

    # 船名变化检测
    new_vessel = updates.get("vessel", "")
    old_vessel = str(old_row.get("vessel", "")).strip()

    if new_vessel and old_vessel:
        # 简单比较 (忽略大小写和空格)
        if new_vessel.upper().replace(" ", "") != old_vessel.upper().replace(" ", ""):
            alerts.append({
                "type": "vessel_change",
                "field": "vessel",
                "old": old_vessel,
                "new": new_vessel,
                "message": f"船名变化: {old_vessel} -> {new_vessel}",
            })

    return alerts


def _parse_date(date_str: str) -> Optional[datetime]:
    """尝试解析多种日期格式"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%m/%d/%Y",
    ]
    
    date_str = date_str.strip().split()[0]  # 去掉时间部分
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def summarize_results(results: List[QueryResult]) -> Dict[str, int]:
    """汇总查询结果统计"""
    stats = {"total": len(results), "ok": 0, "no_result": 0, "error": 0, "needs_review": 0}
    for r in results:
        stats[r.status] = stats.get(r.status, 0) + 1
        if r.needs_review:
            stats["needs_review"] += 1
    return stats
