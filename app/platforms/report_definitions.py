"""平台主结果表定义。

该模块负责描述每个平台主结果表有哪些列、列顺序是什么，
供 Web 页面和 Excel 导出统一复用。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportColumn:
    """主结果表的一列定义。"""

    key: str
    label: str
    is_numeric: bool = True


@dataclass(frozen=True)
class PlatformReportDefinition:
    """平台对应的主结果表定义。"""

    platform_name: str
    platform_label: str
    columns: list[ReportColumn]


_PLATFORM_REPORT_DEFINITIONS = {
    "ctrip": PlatformReportDefinition(
        platform_name="ctrip",
        platform_label="携程",
        columns=[
            ReportColumn(key="product_name", label="产品名称", is_numeric=False),
            ReportColumn(key="actual_people", label="核销人次"),
            ReportColumn(key="sales_amount", label="销售额"),
            ReportColumn(key="settlement_paid", label="结算实付"),
            ReportColumn(key="purchase_amount", label="采购金额"),
            ReportColumn(key="profit", label="利润"),
        ],
    ),
    "meituan": PlatformReportDefinition(
        platform_name="meituan",
        platform_label="美团",
        columns=[
            ReportColumn(key="product_name", label="产品名称", is_numeric=False),
            ReportColumn(key="actual_people", label="核销人次"),
            ReportColumn(key="sales_amount", label="销售额"),
            ReportColumn(key="technical_service_fee", label="技术服务费"),
            ReportColumn(key="merchant_coupon", label="优惠券（商家承担）"),
            ReportColumn(key="settlement_paid", label="结算实付"),
            ReportColumn(key="purchase_amount", label="采购金额"),
            ReportColumn(key="profit", label="利润"),
        ],
    ),
    "douyin": PlatformReportDefinition(
        platform_name="douyin",
        platform_label="抖音",
        columns=[
            ReportColumn(key="product_name", label="产品名称", is_numeric=False),
            ReportColumn(key="actual_people", label="核销人次"),
            ReportColumn(key="sales_amount", label="销售额"),
            ReportColumn(key="technical_service_fee", label="技术服务费"),
            ReportColumn(key="commission", label="佣金"),
            ReportColumn(key="service_provider_commission", label="服务商佣金"),
            ReportColumn(key="settlement_paid", label="结算实付"),
            ReportColumn(key="purchase_amount", label="采购金额"),
            ReportColumn(key="profit", label="利润"),
        ],
    ),
}


def get_platform_report_definition(platform_name: str) -> PlatformReportDefinition:
    """根据平台名返回主结果表定义。"""
    try:
        return _PLATFORM_REPORT_DEFINITIONS[platform_name]
    except KeyError as exc:
        raise ValueError(f"暂不支持的平台报表定义: {platform_name}") from exc


def get_platform_label(platform_name: str) -> str:
    """返回平台中文显示名。"""
    return get_platform_report_definition(platform_name).platform_label


def list_platform_report_definitions() -> list[PlatformReportDefinition]:
    """返回所有已注册的平台报表定义。"""
    return list(_PLATFORM_REPORT_DEFINITIONS.values())
