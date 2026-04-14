from app.domain.reconcile import reconcile_orders
from app.models.reconciliation import ExternalOrderAggregate, InternalOrder


def test_reconcile_orders_groups_metrics_by_product_and_ignores_unmatched_orders() -> None:
    internal_orders = [
        InternalOrder(
            order_no="A-001",
            product_name="产品A",
            actual_people=2,
            purchase_amount=80.0,
        ),
        InternalOrder(
            order_no="A-002",
            product_name="产品A",
            actual_people=1,
            purchase_amount=40.0,
        ),
        InternalOrder(
            order_no="B-001",
            product_name="产品B",
            actual_people=1,
            purchase_amount=20.0,
        ),
    ]
    external_orders = [
        ExternalOrderAggregate(
            external_order_no="A-001",
            metrics={
                "sales_amount": 100.0,
                "settlement_paid": 100.0,
                "technical_service_fee": 10.0,
                "merchant_coupon": 2.0,
            },
            platform_name="ctrip",
            source_row_count=2,
        ),
        ExternalOrderAggregate(
            external_order_no="A-002",
            metrics={
                "sales_amount": 50.0,
                "settlement_paid": 50.0,
                "technical_service_fee": 2.0,
                "merchant_coupon": 1.0,
            },
            platform_name="ctrip",
            source_row_count=1,
        ),
        ExternalOrderAggregate(
            external_order_no="X-999",
            metrics={
                "sales_amount": 999.0,
                "settlement_paid": 999.0,
            },
            platform_name="ctrip",
            source_row_count=1,
        ),
    ]

    result = reconcile_orders(internal_orders=internal_orders, external_orders=external_orders)

    assert result.matched_order_count == 2
    assert result.unmatched_order_count == 1
    assert result.product_count == 1
    assert result.internal_only_count == 1
    assert result.external_only_count == 1
    assert result.internal_only_order_nos == ["B-001"]
    assert result.external_only_order_nos == ["X-999"]

    row = result.rows[0]
    assert row.product_name == "产品A"
    assert row.metrics["actual_people"] == 3
    assert row.metrics["sales_amount"] == 150.0
    assert row.metrics["settlement_paid"] == 150.0
    assert row.metrics["technical_service_fee"] == 12.0
    assert row.metrics["merchant_coupon"] == 3.0
    assert row.metrics["purchase_amount"] == 120.0
    assert row.metrics["profit"] == 30.0
