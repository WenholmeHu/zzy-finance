"""抖音平台适配器：把抖音原始 Excel 解析成统一对账结构。"""

import pandas as pd

from app.infrastructure.date_parser import month_date_range
from app.models.reconciliation import ExternalOrderAggregate, PlatformParseResult
from app.platforms.base import PlatformAdapter


class DouyinAdapter(PlatformAdapter):
    """抖音适配器实现。"""

    platform_name = "douyin"
    positive_worksheet_name = "分账明细-正向-团购"
    refund_worksheet_name = "分账明细-退款-团购"
    required_columns = (
        "核销时间",
        "订单编号",
        "订单实收金额",
        "增量宝",
        "软件服务费",
        "平台撮合佣金",
        "达人佣金",
        "撮合经纪服务费",
        "保险费用",
        "服务商佣金",
        "商家应得",
    )

    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        positive_rows = self._parse_worksheet(
            workbook_data,
            self.positive_worksheet_name,
            reconciliation_month,
        )
        refund_rows = self._parse_worksheet(
            workbook_data,
            self.refund_worksheet_name,
            reconciliation_month,
        )
        filtered_out_of_month_row_count = (
            positive_rows.attrs["filtered_out_of_month_row_count"]
            + refund_rows.attrs["filtered_out_of_month_row_count"]
        )

        combined = pd.concat([positive_rows, refund_rows], ignore_index=True)
        if combined.empty:
            return PlatformParseResult(
                orders=[],
                filtered_out_of_month_row_count=filtered_out_of_month_row_count,
            )

        grouped = (
            combined.groupby("订单编号", as_index=False)
            .agg(
                {
                    "sales_amount": "sum",
                    "technical_service_fee": "sum",
                    "commission": "sum",
                    "service_provider_commission": "sum",
                    "settlement_paid": "sum",
                }
            )
            .rename(columns={"订单编号": "external_order_no"})
        )
        row_counts = combined.groupby("订单编号").size().to_dict()

        orders = []
        for _, row in grouped.iterrows():
            order_no = str(row["external_order_no"])
            orders.append(
                ExternalOrderAggregate(
                    external_order_no=order_no,
                    metrics={
                        "sales_amount": round(float(row["sales_amount"]), 2),
                        "technical_service_fee": round(
                            float(row["technical_service_fee"]), 2
                        ),
                        "commission": round(float(row["commission"]), 2),
                        "service_provider_commission": round(
                            float(row["service_provider_commission"]), 2
                        ),
                        "settlement_paid": round(float(row["settlement_paid"]), 2),
                    },
                    platform_name=self.platform_name,
                    source_row_count=int(row_counts[order_no]),
                )
            )

        return PlatformParseResult(
            orders=orders,
            filtered_out_of_month_row_count=filtered_out_of_month_row_count,
        )

    def _parse_worksheet(
        self,
        workbook_data: dict[str, pd.DataFrame],
        worksheet_name: str,
        reconciliation_month: str,
    ) -> pd.DataFrame:
        try:
            dataframe = workbook_data[worksheet_name]
        except KeyError as exc:
            raise ValueError(f"抖音文件缺少工作表: {worksheet_name}") from exc

        missing_columns = [column for column in self.required_columns if column not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"抖音文件工作表 {worksheet_name} 缺少必要字段: {', '.join(missing_columns)}")

        working = dataframe[dataframe["订单编号"].notna()].copy()
        working["订单编号"] = working["订单编号"].astype(str).str.replace(".0", "", regex=False)
        for column in self.required_columns[2:]:
            working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)
        working["_writeoff_time"] = pd.to_datetime(working["核销时间"], errors="coerce")

        start_date, next_month_start = month_date_range(reconciliation_month)
        in_month_mask = (
            working["_writeoff_time"].notna()
            & (working["_writeoff_time"] >= pd.Timestamp(start_date))
            & (working["_writeoff_time"] < pd.Timestamp(next_month_start))
        )
        filtered = working.loc[in_month_mask].copy()
        filtered.attrs["filtered_out_of_month_row_count"] = int((~in_month_mask).sum())

        filtered["sales_amount"] = filtered["订单实收金额"]
        filtered["technical_service_fee"] = filtered["增量宝"] + filtered["软件服务费"]
        filtered["commission"] = (
            filtered["平台撮合佣金"]
            + filtered["达人佣金"]
            + filtered["撮合经纪服务费"]
            + filtered["保险费用"]
        )
        filtered["service_provider_commission"] = filtered["服务商佣金"]
        filtered["settlement_paid"] = filtered["商家应得"]

        return filtered[
            [
                "订单编号",
                "sales_amount",
                "technical_service_fee",
                "commission",
                "service_provider_commission",
                "settlement_paid",
            ]
        ]
