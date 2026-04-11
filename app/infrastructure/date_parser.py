from datetime import date


def month_date_range(reconciliation_month: str) -> tuple[date, date]:
    year_str, month_str = reconciliation_month.split("-")
    year = int(year_str)
    month = int(month_str)
    start = date(year, month, 1)
    if month == 12:
        return start, date(year + 1, 1, 1)
    return start, date(year, month + 1, 1)