# MOD-004 海运动态自动化系统 - 配置文件
# 版本: v1.0
# 日期: 2026-05-03

import os
from pathlib import Path

# ============================================================
# 文件路径配置
# ============================================================
BASE_DIR = Path(r"D:\hermes\MODS\MOD004")
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "data" / "backups"
LOG_DIR = BASE_DIR / "data" / "logs"
EVIDENCE_DIR = BASE_DIR / "data" / "evidence"
REPORT_DIR = BASE_DIR / "data" / "reports"

# Excel 主表路径
EXCEL_PATH = Path(r"D:\hermes\2026-02-04海运动态.xlsx")

# 创建必要目录
for d in [DATA_DIR, BACKUP_DIR, LOG_DIR, EVIDENCE_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# Excel 列映射 (基于实际表头)
# 列索引从 1 开始，对应 Excel 的 A=1, B=2, ...
# ============================================================
COLUMN_MAP = {
    # 基础信息
    "sn":               {"col": 1,  "label": "S/N",              "type": int},
    "batch_no":         {"col": 2,  "label": "批次号 BATCH NO",   "type": str},
    "carrier":          {"col": 3,  "label": "船公司",            "type": str},
    "destination":      {"col": 4,  "label": "目的港",            "type": str},
    "container_qty":    {"col": 5,  "label": "箱量",              "type": float},
    "container_detail": {"col": 6,  "label": "箱型箱量",          "type": str},
    "container_type":   {"col": 7,  "label": "箱型",              "type": str},
    "weight":           {"col": 8,  "label": "重量(吨)",          "type": float},
    
    # 运输信息
    "bl_no":            {"col": 9,  "label": "提单号",            "type": str},
    "vessel":           {"col": 10, "label": "船名",              "type": str},
    "etd":              {"col": 11, "label": "ETD",              "type": str},
    "atd":              {"col": 12, "label": "ATD",              "type": str},
    "eta_ata":          {"col": 13, "label": "ETA/ATA",          "type": str},
    
    # 动态跟踪 (系统写入字段)
    "current_location": {"col": 14, "label": "现在位置",          "type": str},
    "next_step":        {"col": 15, "label": "下一步预计",        "type": str},
    "query_status":     {"col": 16, "label": "查询状态",          "type": str},
    
    # 业务约束
    "contract_req":     {"col": 17, "label": "合同要求",          "type": str},
    "grade":            {"col": 18, "label": "品位",              "type": str},
    "constraints":      {"col": 19, "label": "约束条件",          "type": str},
    
    # 陆运 / 报关
    "land_status":      {"col": 20, "label": "陆运状态",          "type": str},
    "customs_status":   {"col": 21, "label": "报关状态",          "type": str},
    "land_progress":    {"col": 23, "label": "陆运进展",          "type": str},
    
    # 海运进展
    "loading_status":   {"col": 24, "label": "装船情况",          "type": str},
    "transit":          {"col": 25, "label": "中转",              "type": str},
    "arrival_time":     {"col": 26, "label": "到达时间",          "type": str},
}

# 写回保护字段 — 这些字段只允许人工修改，系统不自动写回
PROTECTED_COLUMNS = [
    "contract_req",     # Q: 合同要求
    "grade",            # R: 品位
    "constraints",      # S: 约束条件
    "container_qty",    # E: 箱量 (业务数据)
    "bl_no",            # I: 提单号
    "destination",      # D: 目的港
]

# ============================================================
# 船司标准化映射 (M2)
# ============================================================
CARRIER_NORMALIZE = {
    "PIL":   "PIL",
    "pil":   "PIL",
    "CMA":   "CMA",
    "CMA CGM": "CMA",
    "cma":   "CMA",
    "MSC":   "MSC",
    "msc":   "MSC",
    "MAERSK": "MAERSK",
    "MSK":   "MAERSK",
    "maersk": "MAERSK",
    "UNIFEEDER": "UNIFEEDER",
    "UFC":   "UNIFEEDER",
}

# 已实现连接器的船司
SUPPORTED_CARRIERS = ["PIL", "CMA", "MSC"]

# ============================================================
# WhatsApp 摘要格式 (PRD 5.5 节)
# ============================================================
SUMMARY_HEADER = "{date} 请各位领导查收{category}发运动态"
SUMMARY_LINE = "{batch_no}\t{container_detail}\t{eta_ata}\t{current_location}\t{next_step}"

# 摘要输出字段映射 (从 Excel 列到摘要字段)
SUMMARY_FIELDS = {
    "batch_no":         "batch_no",
    "container_detail": "container_detail",
    "eta_ata":          "eta_ata",
    "current_location": "current_location",
    "next_step":        "next_step",
}

# ============================================================
# 查询规则
# ============================================================
# 哪些状态下不需要查询
SKIP_QUERY_STATUSES = [
    "已完成", "DONE", "COMPLETED",
    "暂停", "PAUSED", "HOLD",
    "无需查询",
]

# ETA 变化告警阈值
ETA_CHANGE_THRESHOLD_DAYS = 3  # ETA 变化超过 3 天需人工确认

# ============================================================
# 浏览器配置 (M3/M4)
# ============================================================
# Playwright 配置 — 部署到 VPS 后启用
BROWSER_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "viewport": {"width": 1920, "height": 1080},
}

# 各船司官网查询 URL (待实测后补全)
CARRIER_URLS = {
    "PIL": "https://www.pilship.com/track-by-booking",
    "CMA": "https://www.cma-cgm.com/ebusiness/tracking",
    "MSC": "https://www.msc.com/track-a-shipment",
}

# ============================================================
# 日志配置
# ============================================================
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
