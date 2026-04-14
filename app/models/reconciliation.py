"""对账领域模型定义。

这个文件是全项目的数据契约中心，主要职责是：
1) 统一“内部订单 / 外部订单 / 汇总结果”的结构；
2) 明确各层之间传参字段，避免字典散落导致字段名不一致；
3) 通过不可变 dataclass（frozen=True）降低误修改风险。
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class InternalOrder:
    """内部订单（来自聚天下文件）的标准结构。"""

    order_no: str
    product_name: str
    actual_people: float
    purchase_amount: float


@dataclass(frozen=True)
class ExternalOrderAggregate:
    """外部平台订单聚合后的标准结构。

    注意：一个外部订单号在原始文件中可能出现多行，适配器会先聚合再产出该模型。
    """

    external_order_no: str
    metrics: dict[str, float]
    platform_name: str
    source_row_count: int
    business_date: date | None = None


@dataclass(frozen=True)
class ProductSummaryRow:
    """主结果表中的一行（按产品维度汇总）。"""

    product_name: str
    metrics: dict[str, float]


@dataclass(frozen=True)
class ReconciliationResult:
    """一次对账流程的最终结果对象。

    Web 层和导出层都以它作为统一输入，不直接依赖底层计算细节。
    """

    rows: list[ProductSummaryRow]
    matched_order_count: int
    unmatched_order_count: int
    filtered_out_of_month_row_count: int = 0
    internal_only_order_nos: list[str] = field(default_factory=list)
    external_only_order_nos: list[str] = field(default_factory=list)

    @property
    def product_count(self) -> int:
        """主结果表中的产品行数。"""
        return len(self.rows)

    @property
    def internal_only_count(self) -> int:
        """仅内部存在的订单数。"""
        return len(self.internal_only_order_nos)

    @property
    def external_only_count(self) -> int:
        """仅外部平台存在的订单数。"""
        return len(self.external_only_order_nos)


@dataclass(frozen=True)
class PlatformParseResult:
    """平台适配器解析结果。

    orders: 可参与对账的外部订单聚合列表。
    filtered_out_of_month_row_count: 因非目标月份被过滤掉的原始行数。
    """

    orders: list[ExternalOrderAggregate]
    filtered_out_of_month_row_count: int
