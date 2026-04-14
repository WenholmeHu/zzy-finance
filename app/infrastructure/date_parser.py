"""月份区间解析工具。

用于把前端提交的 `YYYY-MM` 文本转换成 [当月起始, 次月起始) 区间。
采用“左闭右开”区间可以简化日期过滤条件，避免月底边界判断错误。
"""

from datetime import date


def month_date_range(reconciliation_month: str) -> tuple[date, date]:
    """返回对账月份的日期区间: (当月1号, 次月1号)。"""
    year_str, month_str = reconciliation_month.split("-")
    year = int(year_str)
    month = int(month_str)
    start = date(year, month, 1)
    # 12 月需要进位到下一年 1 月。
    if month == 12:
        return start, date(year + 1, 1, 1)
    return start, date(year, month + 1, 1)
