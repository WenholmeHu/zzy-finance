"""平台适配器抽象定义。"""

from abc import ABC, abstractmethod

import pandas as pd

from app.models.reconciliation import PlatformParseResult


class PlatformAdapter(ABC):
    """所有平台适配器必须遵守的统一协议。

    新平台接入时，实习生只要实现这个抽象类并在 registry 注册，
    就能接入整条对账链路，无需改动领域算法。
    """

    # 平台唯一标识（如 ctrip、meituan）。
    platform_name: str
    # 平台 Excel 中需要读取的工作表名。
    worksheet_name: str

    @abstractmethod
    def parse(self, dataframe: pd.DataFrame, reconciliation_month: str) -> PlatformParseResult:
        """把平台原始 DataFrame 解析成统一结构。

        期望完成三件事：
        1) 字段校验（缺字段要抛清晰异常）；
        2) 数据清洗与按月过滤；
        3) 按订单号聚合后返回 PlatformParseResult。
        """
        raise NotImplementedError
