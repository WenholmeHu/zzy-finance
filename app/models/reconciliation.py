from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class InternalOrder:
    order_no: str
    product_name: str
    actual_people: float
    purchase_amount: float


@dataclass(frozen=True)
class ExternalOrderAggregate:
    external_order_no: str
    settlement_amount: float
    platform_name: str
    source_row_count: int
    business_date: date | None = None


@dataclass(frozen=True)
class ProductSummaryRow:
    product_name: str
    actual_people_total: float
    sales_amount_total: float
    settlement_paid_total: float
    purchase_amount_total: float
    profit_total: float


@dataclass(frozen=True)
class ReconciliationResult:
    rows: list[ProductSummaryRow]
    matched_order_count: int
    unmatched_order_count: int
    filtered_out_of_month_row_count: int = 0
    internal_only_order_nos: list[str] = field(default_factory=list)
    external_only_order_nos: list[str] = field(default_factory=list)

    @property
    def product_count(self) -> int:
        return len(self.rows)

    @property
    def internal_only_count(self) -> int:
        return len(self.internal_only_order_nos)

    @property
    def external_only_count(self) -> int:
        return len(self.external_only_order_nos)


@dataclass(frozen=True)
class PlatformParseResult:
    orders: list[ExternalOrderAggregate]
    filtered_out_of_month_row_count: int
