"""平台适配器抽象定义。"""

from abc import ABC, abstractmethod

import pandas as pd

from app.models.reconciliation import PlatformParseResult


class PlatformAdapter(ABC):
    """所有平台适配器必须遵守的统一协议。"""

    # 平台唯一标识（如 ctrip、meituan）。
    platform_name: str
    # 平台 Excel 中需要读取的工作表名。
    worksheet_name: str

    @abstractmethod
    def parse(self, dataframe: pd.DataFrame, reconciliation_month: str) -> PlatformParseResult:
        """把平台原始 DataFrame 解析成统一结构。"""
        raise NotImplementedError
