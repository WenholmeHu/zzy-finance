"""平台适配器抽象定义。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from app.models.reconciliation import PlatformParseResult


class PlatformAdapter(ABC):
    """所有平台适配器必须遵守的统一协议。

    新平台接入时，实习生只要实现这个抽象类并在 registry 注册，
    就能接入整条对账链路，无需改动领域算法。
    """

    # 平台唯一标识（如 ctrip、meituan）。
    platform_name: str

    @abstractmethod
    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        """把平台工作簿数据解析成统一结构。

        期望完成三件事：
        1) 字段校验（缺字段要抛清晰异常）；
        2) 数据清洗与按月过滤；
        3) 按订单号聚合后返回 PlatformParseResult。
        """
        raise NotImplementedError


@dataclass(frozen=True)
class PlatformSpec:
    """平台在应用层使用的静态元数据。"""

    platform_name: str
    platform_label: str
    worksheet_names: tuple[str, ...]
    internal_order_column: str
    internal_difference_label: str
    external_difference_label: str
    adapter_factory: type[PlatformAdapter] | None
