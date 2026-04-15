"""携程平台适配器：把携程原始 Excel 解析成统一对账结构。"""

from datetime import date

import pandas as pd

from app.infrastructure.date_parser import month_date_range
from app.models.reconciliation import ExternalOrderAggregate, PlatformParseResult
from app.platforms.base import PlatformAdapter


class CtripAdapter(PlatformAdapter):
    """携程适配器实现。

    主要完成两件事：
    - 把携程特有字段映射到统一模型；
    - 将原始明细按订单号聚合成可对账数据。
    """

    platform_name = "ctrip"
    worksheet_name = "流水"

    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        """解析携程数据并按对账月份过滤。"""
        try:
            dataframe = workbook_data[self.worksheet_name]
        except KeyError as exc:
            raise ValueError(f"携程文件缺少工作表: {self.worksheet_name}") from exc

        # 这里定义的是“携程原始字段名”，改模板时优先修改此处。
        third_order_column = "第三方单号"
        settlement_column = "结算价金额"
        departure_column = "出发时间"
        required_columns = [third_order_column, settlement_column, departure_column]

        # 先做字段校验，避免后续处理时报难定位的 KeyError。
        missing_columns = [column for column in required_columns if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"携程文件缺少必要字段: {', '.join(missing_columns)}")

        # 过滤无订单号数据，并清洗“12345.0”这类 Excel 浮点订单号。
        working = dataframe[dataframe[third_order_column].notna()].copy()
        working[third_order_column] = (
            working[third_order_column].astype(str).str.replace(".0", "", regex=False)
        )
        working["_departure_date"] = pd.to_datetime(working[departure_column], errors="coerce")

        # 只保留对账月份内的出发记录。
        # 条件采用 [start, next_month_start) 避免月底 23:59:59 边界问题。
        start_date, next_month_start = month_date_range(reconciliation_month)
        in_month_mask = (
            working["_departure_date"].notna()
            & (working["_departure_date"] >= pd.Timestamp(start_date))
            & (working["_departure_date"] < pd.Timestamp(next_month_start))
        )
        filtered_out_count = int((~in_month_mask).sum())
        filtered = working.loc[in_month_mask].copy()

        # 一个订单号可能对应多行，按订单号聚合结算金额。
        grouped = (
            filtered.groupby(third_order_column, as_index=False)
            .agg(
                {
                    settlement_column: "sum",
                    "_departure_date": "min",
                }
            )
            .rename(columns={third_order_column: "external_order_no"})
        )
        row_counts = filtered.groupby(third_order_column).size().to_dict()

        orders = []
        for _, row in grouped.iterrows():
            departure_value = row["_departure_date"]
            business_date = (
                departure_value.date() if isinstance(departure_value, pd.Timestamp) else None
            )
            order_no = row["external_order_no"]
            # order_no 在 grouped 中可能仍是数值类型，这里统一转字符串以对齐内部订单号。
            settlement_amount = float(row[settlement_column])
            orders.append(
                ExternalOrderAggregate(
                    external_order_no=str(order_no),
                    metrics={
                        "sales_amount": settlement_amount,
                        "settlement_paid": settlement_amount,
                    },
                    platform_name=self.platform_name,
                    source_row_count=int(row_counts[str(order_no)]),
                    business_date=business_date,
                )
            )

        return PlatformParseResult(
            orders=orders,
            filtered_out_of_month_row_count=filtered_out_count,
        )
