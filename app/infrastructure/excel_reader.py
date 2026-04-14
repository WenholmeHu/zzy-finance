"""Excel 读取基础设施。

该模块只负责“按工作表读取 DataFrame”，不承载业务规则。
这样做可以让上层（应用服务/适配器）专注业务处理，底层专注 I/O。
"""

from pathlib import Path

import pandas as pd


def read_excel_sheet(file_path: Path, sheet_name: str) -> pd.DataFrame:
    """读取指定工作表并返回 DataFrame。

    参数:
    - file_path: Excel 文件路径；
    - sheet_name: 要读取的工作表名（必须和业务约定一致）。
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)
