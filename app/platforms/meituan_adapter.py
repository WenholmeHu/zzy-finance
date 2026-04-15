"""美团平台适配器：把美团原始 Excel 解析成统一对账结构。"""

import pandas as pd

from app.infrastructure.date_parser import month_date_range
from app.models.reconciliation import ExternalOrderAggregate, PlatformParseResult
from app.platforms.base import PlatformAdapter


class MeituanAdapter(PlatformAdapter):
    """美团适配器实现。"""

    platform_name = "meituan"
    worksheet_name = "订单详情"

    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        """解析美团数据并按对账月份过滤。"""
        try:
            dataframe = workbook_data[self.worksheet_name]
        except KeyError as exc:
            raise ValueError(f"美团文件缺少工作表: {self.worksheet_name}") from exc

        order_column = "商家订单号"
        sales_time_column = "销售时间"
        payable_amount_column = "应付金额"
        service_fee_column = "技术服务费"
        service_fee_refund_column = "技术服务费退款"
        merchant_coupon_column = "商家承担优惠"
        settlement_paid_column = "结算金额"
        required_columns = [
            order_column,
            sales_time_column,
            payable_amount_column,
            service_fee_column,
            service_fee_refund_column,
            merchant_coupon_column,
            settlement_paid_column,
        ]

        missing_columns = [column for column in required_columns if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"美团文件缺少必要字段: {', '.join(missing_columns)}")

        working = dataframe[dataframe[order_column].notna()].copy()
        working[order_column] = (
            working[order_column].astype(str).str.replace(".0", "", regex=False)
        )
        for column in [
            payable_amount_column,
            service_fee_column,
            service_fee_refund_column,
            merchant_coupon_column,
            settlement_paid_column,
        ]:
            working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)
        working["_sales_time"] = pd.to_datetime(working[sales_time_column], errors="coerce")

        start_date, next_month_start = month_date_range(reconciliation_month)
        in_month_mask = (
            working["_sales_time"].notna()
            & (working["_sales_time"] >= pd.Timestamp(start_date))
            & (working["_sales_time"] < pd.Timestamp(next_month_start))
        )
        filtered_out_count = int((~in_month_mask).sum())
        filtered = working.loc[in_month_mask].copy()

        grouped = (
            filtered.groupby(order_column, as_index=False)
            .agg(
                {
                    payable_amount_column: "sum",
                    service_fee_column: "sum",
                    service_fee_refund_column: "sum",
                    merchant_coupon_column: "sum",
                    settlement_paid_column: "sum",
                    "_sales_time": "min",
                }
            )
            .rename(columns={order_column: "external_order_no"})
        )
        row_counts = filtered.groupby(order_column).size().to_dict()

        orders = []
        for _, row in grouped.iterrows():
            sales_time = row["_sales_time"]
            business_date = sales_time.date() if isinstance(sales_time, pd.Timestamp) else None
            order_no = str(row["external_order_no"])
            orders.append(
                ExternalOrderAggregate(
                    external_order_no=order_no,
                    metrics={
                        "sales_amount": float(row[payable_amount_column]),
                        "technical_service_fee": float(
                            row[service_fee_column] + row[service_fee_refund_column]
                        ),
                        "merchant_coupon": float(row[merchant_coupon_column]),
                        "settlement_paid": float(row[settlement_paid_column]),
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
