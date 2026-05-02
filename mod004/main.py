# MOD-004 主流程编排器 (M0)
# 职责: 串联 M1→M2→M4→M5→M6，提供 CLI 入口

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import (
    EXCEL_PATH, LOG_DIR, LOG_FORMAT, LOG_DATE_FORMAT,
    SUPPORTED_CARRIERS, PROTECTED_COLUMNS,
)
from .reader import read_all_sheets, filter_query_candidates, print_summary
from .router import group_by_carrier, get_connector_class, normalize_carrier
from .parser import parse_result, detect_changes, summarize_results
from .writer import write_updates
from .summary import generate_daily_summary, generate_detail_report
from .connectors.base import QueryResult

# 设置日志
log = logging.getLogger("mod004")


def setup_logging(verbose: bool = False):
    """配置日志系统"""
    level = logging.DEBUG if verbose else logging.INFO
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"mod004_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


async def run_daily_update(
    excel_path: Optional[Path] = None,
    dry_run: bool = False,
    max_count: Optional[int] = None,
) -> Dict[str, Any]:
    """执行每日海运动态更新 (完整流程 M1→M6)

    Args:
        excel_path: Excel 文件路径
        dry_run: 仅模拟，不写 Excel
        max_count: 最大查询数量 (调试用)

    Returns:
        执行报告 dict
    """
    path = excel_path or EXCEL_PATH
    report = {
        "timestamp": datetime.now().isoformat(),
        "excel": str(path),
        "stages": {},
    }

    # ============ M1: 读取 Excel ============
    log.info("=" * 50)
    log.info("M1: 读取 Excel 主表")
    sheets = read_all_sheets(path)
    print_summary(sheets)

    candidates = filter_query_candidates(sheets)
    report["stages"]["M1_read"] = {
        "sheets": len(sheets),
        "total_rows": sum(len(r) for r in sheets.values()),
        "candidates": len(candidates),
    }

    if max_count:
        candidates = candidates[:max_count]
        log.info(f"限制查询数量: {max_count}")

    if not candidates:
        log.info("无待查询记录，流程结束")
        return report

    # ============ M2: 船司分组 ============
    log.info("M2: 船司路由分组")
    groups = group_by_carrier(candidates)
    report["stages"]["M2_router"] = {k: len(v) for k, v in groups.items()}

    # ============ M4: 执行查询 ============
    log.info("M4: 执行船司查询")
    all_results: List[QueryResult] = []

    for carrier, items in groups.items():
        if carrier not in SUPPORTED_CARRIERS:
            log.warning(f"跳过不支持的船司: {carrier}")
            continue

        ConnectorClass = get_connector_class(carrier)
        connector = ConnectorClass(headless=True)

        log.info(f"查询 {carrier}: {len(items)} 条记录")
        results = await connector.query_batch(items)
        all_results.extend(results)

    report["stages"]["M4_query"] = summarize_results(all_results)

    # ============ M5: 解析结果 + 差异检测 ============
    log.info("M5: 解析查询结果")
    updates = []
    alerts = []

    for result in all_results:
        if not result.success:
            log.warning(f"查询失败: {result.query_key} — {result.status}")
            updates.append({
                "_sheet": result._row_data.get("_sheet", ""),
                "_row": result._row_data.get("_row", 0),
                "query_status": result.status,
            })
            continue

        # 解析为 Excel 字段
        field_updates = parse_result(result)
        field_updates["_sheet"] = result._row_data.get("_sheet", "")
        field_updates["_row"] = result._row_data.get("_row", 0)

        # 差异检测
        changes = detect_changes(field_updates, result._row_data)
        if changes:
            field_updates["_needs_review"] = True
            alerts.append({
                "query_key": result.query_key,
                "carrier": result.carrier,
                "changes": changes,
            })
            log.warning(f"⚠ 需要确认: {result.query_key} — {[c['message'] for c in changes]}")

        updates.append(field_updates)

    report["stages"]["M5_parse"] = {
        "updates": len(updates),
        "alerts": len(alerts),
    }

    # ============ M6: 写回 Excel ============
    if not dry_run:
        # 检查是否有需要确认的变更
        if alerts:
            log.warning(f"有 {len(alerts)} 条记录需要人工确认，已跳过写回")
            report["stages"]["M6_write"] = {
                "status": "blocked",
                "reason": f"{len(alerts)} 条需要确认",
                "alerts": alerts,
            }
        else:
            log.info("M6: 写回 Excel 主表")
            write_stats = write_updates(updates, path, dry_run=False)
            report["stages"]["M6_write"] = write_stats
    else:
        log.info("M6: [DRY RUN] 跳过写回")
        report["stages"]["M6_write"] = {"status": "dry_run", "would_write": len(updates)}

    # ============ 生成摘要 ============
    log.info("生成 WhatsApp 文字摘要")
    summary = generate_daily_summary(sheets)
    report["summary_preview"] = summary[:500]

    log.info("=" * 50)
    log.info("流程完成")
    return report


# ============================================================
# CLI 命令
# ============================================================

def cmd_read(args=None):
    """仅读取 Excel 并打印摘要"""
    setup_logging(verbose=True)
    sheets = read_all_sheets()
    print_summary(sheets)

    candidates = filter_query_candidates(sheets)
    print(f"待查询: {len(candidates)} 条\n")
    for c in candidates[:10]:
        print(f"  [{c['_sheet']}] {c.get('batch_no')} | {c.get('carrier')} | "
              f"提单: {c.get('bl_no')} | 船名: {c.get('vessel')} | "
              f"ETA: {c.get('eta_ata')}")
    if len(candidates) > 10:
        print(f"  ... 共 {len(candidates)} 条")


def cmd_summary(args=None):
    """生成 WhatsApp 文字摘要"""
    setup_logging()
    sheets = read_all_sheets()
    text = generate_daily_summary(sheets)
    print(text)


def cmd_detail(batch_no: str):
    """查询单票详情"""
    setup_logging()
    sheets = read_all_sheets()
    text = generate_detail_report(sheets, batch_no_filter=batch_no)
    print(text)


def cmd_run(args=None):
    """执行完整每日更新流程 (默认 dry run)"""
    import argparse
    parser = argparse.ArgumentParser(description="MOD-004 海运动态自动更新")
    parser.add_argument("command", nargs="?", default="run",
                        choices=["run", "read", "summary", "detail"],
                        help="执行命令")
    parser.add_argument("--excel", type=str, help="Excel 文件路径")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="仅模拟，不写 Excel (默认)")
    parser.add_argument("--write", dest="dry_run", action="store_false",
                        help="实际写回 Excel")
    parser.add_argument("--max", type=int, help="最大查询数量")
    parser.add_argument("--batch", type=str, help="查询单票 (与 detail 命令配合)")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")

    args = parser.parse_args(args)

    setup_logging(verbose=args.verbose)

    if args.command == "read":
        cmd_read()
    elif args.command == "summary":
        cmd_summary()
    elif args.command == "detail":
        if not args.batch:
            print("请指定 --batch 参数")
            sys.exit(1)
        cmd_detail(args.batch)
    elif args.command == "run":
        excel_path = Path(args.excel) if args.excel else None
        asyncio.run(run_daily_update(
            excel_path=excel_path,
            dry_run=args.dry_run,
            max_count=args.max,
        ))
        # 始终打印摘要
        sheets = read_all_sheets(excel_path)
        print("\n" + "=" * 60)
        print(generate_daily_summary(sheets))


if __name__ == "__main__":
    cmd_run(sys.argv[1:])
