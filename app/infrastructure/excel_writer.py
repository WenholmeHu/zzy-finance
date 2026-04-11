from io import BytesIO

from openpyxl import Workbook


def build_reconciliation_workbook(
    reconciliation_month: str,
    platform_label: str,
    rows: list[dict],
) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "对账结果"

    worksheet["A1"] = "对账月份"
    worksheet["B1"] = reconciliation_month
    worksheet["A2"] = "平台"
    worksheet["B2"] = platform_label

    headers = ["产品名称", "核销人次", "销售额", "结算实付", "采购金额", "利润"]
    for column_index, header in enumerate(headers, start=1):
        worksheet.cell(row=4, column=column_index, value=header)

    for row_index, row in enumerate(rows, start=5):
        worksheet.cell(row=row_index, column=1, value=row["product_name"])
        worksheet.cell(row=row_index, column=2, value=row["actual_people_total"])
        worksheet.cell(row=row_index, column=3, value=row["sales_amount_total"])
        worksheet.cell(row=row_index, column=4, value=row["settlement_paid_total"])
        worksheet.cell(row=row_index, column=5, value=row["purchase_amount_total"])
        worksheet.cell(row=row_index, column=6, value=row["profit_total"])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
