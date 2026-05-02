# MOD-004 M4: PIL 连接器 (Mock)
# 上线前需替换为 Playwright 实现

import logging
import asyncio
from .base import BaseConnector, QueryResult

log = logging.getLogger(__name__)


class PILConnector(BaseConnector):
    """PIL (Pacific International Lines) 官网查询连接器"""

    carrier_code = "PIL"
    carrier_name = "PIL"

    async def query(self, query_key: str, ref_type: str = "AUTO") -> QueryResult:
        """查询 PIL 官网 — 当前为 Mock 实现"""
        log.info(f"[PIL] 查询: {query_key}")

        # TODO: 替换为 Playwright 实现
        # 1. 打开 https://www.pilship.com/track-by-booking
        # 2. 输入 Booking/BL/Container 号
        # 3. 点击查询
        # 4. 解析结果页面
        # 5. 截图保存到 EVIDENCE_DIR

        result = QueryResult(
            carrier="PIL",
            query_key=query_key,
            ref_type=ref_type,
            success=True,
            status="ok",
            # Mock 数据 — 上线后删除
            vessel="KOTA NILAM",
            voyage="0215E",
            etd="2024-12-29",
            eta="2025-02-09",
            current_location="新加坡中转",
            next_step="预计02.09到达目的港",
            page_url="https://www.pilship.com/track-by-booking",
        )
        return result

    def check_login_status(self) -> bool:
        """检查 PIL 网站登录状态"""
        # TODO: Playwright 实现
        return True

    def login(self, credentials=None) -> bool:
        """PIL 登录"""
        # PIL 官网查询通常不需要登录
        return True


class MockPILConnector(PILConnector):
    """带模拟延迟的测试连接器"""
    async def query(self, query_key: str, ref_type: str = "AUTO") -> QueryResult:
        await asyncio.sleep(0.3)
        return await super().query(query_key, ref_type)
