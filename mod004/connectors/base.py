# MOD-004 M4: 船司查询连接器 - 基类
# 职责: 定义统一的查询接口，各船司连接器继承此类

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """单次查询结果"""
    carrier: str                        # 船司代码
    query_key: str                      # 查询用的单号
    ref_type: str = "AUTO"              # Booking / BL / Container

    # 是否成功
    success: bool = False
    status: str = ""                    # ok / no_result / login_failed / captcha / error

    # 解析后的字段
    vessel: str = ""
    voyage: str = ""
    etd: str = ""
    atd: str = ""
    eta: str = ""
    ata: str = ""
    current_location: str = ""
    next_step: str = ""
    events: list = field(default_factory=list)  # 原始事件列表

    # 证据
    screenshot_path: str = ""
    page_url: str = ""
    raw_text: str = ""

    # 异常
    error_message: str = ""
    needs_review: bool = False
    review_reason: str = ""


class BaseConnector(ABC):
    """船司查询连接器基类"""

    carrier_code: str = "BASE"
    carrier_name: str = "Base"

    def __init__(self, headless: bool = True):
        self.headless = headless

    @abstractmethod
    async def query(self, query_key: str, ref_type: str = "AUTO") -> QueryResult:
        """执行单次查询，返回 QueryResult"""
        ...

    async def query_batch(self, items: list[Dict[str, Any]]) -> list[QueryResult]:
        """批量查询 (默认逐条执行，可覆盖为并发)"""
        results = []
        for item in items:
            query_key = str(item.get("bl_no") or item.get("batch_no") or "")
            result = await self.query(query_key)
            result._row_data = item  # 保留原始行引用
            results.append(result)
        return results

    @abstractmethod
    def check_login_status(self) -> bool:
        """检查登录状态是否有效"""
        ...

    @abstractmethod
    def login(self, credentials: Optional[Dict[str, str]] = None) -> bool:
        """执行登录，返回是否成功"""
        ...

    def get_profile_dir(self) -> Path:
        """获取浏览器 Profile 目录"""
        from .config import EVIDENCE_DIR
        return EVIDENCE_DIR / "profiles" / self.carrier_code.lower()
