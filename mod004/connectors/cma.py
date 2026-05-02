# MOD-004 M4: CMA 连接器 (Mock)
# 上线前需替换为 Playwright 实现

import logging
from .base import BaseConnector, QueryResult

log = logging.getLogger(__name__)


class CMAConnector(BaseConnector):
    """CMA CGM 官网查询连接器"""

    carrier_code = "CMA"
    carrier_name = "CMA CGM"

    async def query(self, query_key: str, ref_type: str = "AUTO") -> QueryResult:
        log.info(f"[CMA] 查询: {query_key}")

        # TODO: 替换为 Playwright 实现
        # 1. 打开 https://www.cma-cgm.com/ebusiness/tracking
        # 2. 输入提单号/Booking号
        # 3. 解析跟踪结果页面
        # 4. 截图保存

        return QueryResult(
            carrier="CMA",
            query_key=query_key,
            ref_type=ref_type,
            success=True,
            status="ok",
            vessel="CMA CGM LISBON",
            voyage="",
            etd="2024-03-23",
            eta="2024-05-12",
            current_location="海上航行",
            next_step="预计05.12到达",
            page_url="https://www.cma-cgm.com/ebusiness/tracking",
        )

    def check_login_status(self) -> bool:
        return True

    def login(self, credentials=None) -> bool:
        # CMA 基础查询通常不需要登录
        return True
