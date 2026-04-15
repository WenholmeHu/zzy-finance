"""同程平台适配器：把同程原始 Excel 解析成统一对账结构。"""

import pandas as pd

from app.infrastructure.date_parser import month_date_range
from app.models.reconciliation import ExternalOrderAggregate, PlatformParseResult
from app.platforms.base import PlatformAdapter


class TongchengAdapter(PlatformAdapter):
    """同程适配器实现。"""

    platform_name = "tongcheng"

    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        """解析同程数据并按对账月份过滤。"""
        if len(workbook_data) != 1:
            raise ValueError("同程文件必须且只能包含 1 个工作表")

        dataframe = next(iter(workbook_data.values()))

        order_column = "三方流水号"
        travel_date_column = "旅游日期"
        settlement_column = "应结(元)"
        required_columns = [order_column, travel_date_column, settlement_column]

        missing_columns = [column for column in required_columns if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"同程文件缺少必要字段: {', '.join(missing_columns)}")

        working = dataframe[dataframe[order_column].notna()].copy()
        working[order_column] = working[order_column].astype(str).str.replace(".0", "", regex=False)
        working[settlement_column] = pd.to_numeric(working[settlement_column], errors="coerce").fillna(0)
        working["_travel_date"] = pd.to_datetime(working[travel_date_column], errors="coerce")

        start_date, next_month_start = month_date_range(reconciliation_month)
        in_month_mask = (
            working["_travel_date"].notna()
            & (working["_travel_date"] >= pd.Timestamp(start_date))
            & (working["_travel_date"] < pd.Timestamp(next_month_start))
        )
        filtered_out_count = int((~in_month_mask).sum())
        filtered = working.loc[in_month_mask].copy()

        grouped = (
            filtered.groupby(order_column, as_index=False)
            .agg(
                {
                    settlement_column: "sum",
                    "_travel_date": "min",
                }
            )
            .rename(columns={order_column: "external_order_no"})
        )
        row_counts = filtered.groupby(order_column).size().to_dict()

        orders = []
        for _, row in grouped.iterrows():
            travel_date = row["_travel_date"]
            business_date = travel_date.date() if isinstance(travel_date, pd.Timestamp) else None
            order_no = str(row["external_order_no"])
            settlement_amount = float(row[settlement_column])
            orders.append(
                ExternalOrderAggregate(
                    external_order_no=order_no,
                    metrics={
                        "sales_amount": settlement_amount,
                        "settlement_paid": settlement_amount,
                    },
                    platform_name=self.platform_name,
                    source_row_count=int(row_counts[order_no]),
                    business_date=business_date,
                )
            )

        return PlatformParseResult(
            orders=orders,
            filtered_out_of_month_row_count=filtered_out_count,
        )
