# MOD-004: Sheet 列布局自动检测
# 不同 Sheet 可能使用不同的列布局，根据表头关键词自动映射

import logging
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

# 列布局模板: 定义每种布局的 {field: col_index}
# col_index 为 1-based
LAYOUT_TEMPLATES = {
    # 布局 A (萤石 Sheet): 紧凑布局
    "layout_a": {
        "sn": 1, "batch_no": 2, "carrier": 3, "destination": 4,
        "container_qty": 5, "container_detail": 6, "container_type": 7,
        "weight": 8, "bl_no": 9, "vessel": 10,
        "etd": 11, "atd": 12, "eta_ata": 13,
        "current_location": 14, "next_step": 15, "query_status": 16,
        "contract_req": 17, "grade": 18, "constraints": 19,
        "land_status": 20, "customs_status": 21, "land_progress": 23,
        "loading_status": 24, "transit": 25, "arrival_time": 26,
    },
    # 布局 B (铬 Sheet): 展开布局，多了箱型箱量合并列
    "layout_b": {
        "sn": 1, "batch_no": 2, "carrier": 3,
        # E = 目的港, F = 箱量, G = (空/备用), H = 箱型箱量
        "destination": 5,
        "container_qty": 6,
        "container_detail": 8,
        "container_type": 7,
        "weight": 9,  # 费用/单价
        "bl_no": 10, "vessel": 11,
        "etd": 12, "atd": 13, "eta_ata": 14,
        "current_location": 15, "next_step": 16, "query_status": 17,
        "contract_req": 18, "grade": 19, "constraints": 20,
        "land_status": 21, "customs_status": 22, "land_progress": 24,
        "loading_status": 25, "transit": 26, "arrival_time": 27,
    },
}

# 布局检测规则: 检查指定列的表头关键词
LAYOUT_DETECTION = {
    "layout_a": {
        # 布局A: 列E表头含"箱量", 列F含"箱型箱量"
        5: ["箱量", "量", "QTY"],
        6: ["箱型箱量", "箱型"],
    },
    "layout_b": {
        # 布局B: 列E表头含"目的港"/"起运港", 列H含"箱型"
        5: ["目的港", "起运港", "PORT", "DEST"],
        8: ["箱型箱量", "40HQ", "箱型"],
    },
}


def detect_layout(headers: Dict[int, str]) -> Optional[str]:
    """根据表头关键词自动检测布局类型

    Args:
        headers: {col_index: header_text}

    Returns:
        布局名称 ("layout_a" / "layout_b") 或 None
    """
    scores = {}

    for layout_name, rules in LAYOUT_DETECTION.items():
        score = 0
        for col_idx, keywords in rules.items():
            header = headers.get(col_idx, "").upper()
            if any(kw.upper() in header for kw in keywords):
                score += 1
        scores[layout_name] = score

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            log.info(f"检测到布局: {best} (score={scores[best]})")
            return best

    # 默认使用布局A
    log.warning("无法检测布局，使用默认 layout_a")
    return "layout_a"


def get_column_map_for_sheet(headers: Dict[int, str]) -> Dict[str, Dict[str, Any]]:
    """根据检测到的布局返回该 Sheet 的列映射"""
    layout = detect_layout(headers)
    col_map = LAYOUT_TEMPLATES.get(layout, LAYOUT_TEMPLATES["layout_a"])

    result = {}
    for field, col_idx in col_map.items():
        result[field] = {
            "col": col_idx,
            "label": headers.get(col_idx, ""),
            "type": float if field in ("container_qty", "weight") else str,
        }
    return result
