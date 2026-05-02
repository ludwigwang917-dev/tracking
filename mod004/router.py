# MOD-004 M2: 船司路由模块
# 职责: 标准化船司代码，按船司分组，路由到对应连接器

import logging
from typing import List, Dict, Any

from .config import CARRIER_NORMALIZE, SUPPORTED_CARRIERS

log = logging.getLogger(__name__)


def normalize_carrier(raw) -> str:
    """标准化船公司名称 -> 统一代码"""
    if not raw or raw is None:
        return ""
    cleaned = raw.strip().upper()
    return CARRIER_NORMALIZE.get(cleaned, cleaned)


def group_by_carrier(candidates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """将待查询记录按船司分组"""
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for row in candidates:
        carrier = row.get("_carrier_norm") or normalize_carrier(row.get("carrier", ""))
        if not carrier:
            continue
        groups.setdefault(carrier, []).append(row)

    log.info(f"船司分组: { {k: len(v) for k, v in groups.items()} }")
    return groups


def get_connector_class(carrier: str):
    """根据船司代码返回对应的连接器类"""
    from .connectors.base import BaseConnector
    from .connectors.pil import PILConnector
    from .connectors.cma import CMAConnector
    from .connectors.msc import MSCConnector

    connector_map = {
        "PIL": PILConnector,
        "CMA": CMAConnector,
        "MSC": MSCConnector,
    }
    return connector_map.get(carrier, BaseConnector)
