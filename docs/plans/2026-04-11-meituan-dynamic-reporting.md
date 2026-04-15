# Meituan Dynamic Reporting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Meituan reconciliation support while upgrading the main report to use platform-specific dynamic columns without regressing existing Ctrip behavior.

**Architecture:** Refactor the reconciliation pipeline from a fixed six-column result model into a metric-driven result model. Keep platform-specific file parsing inside adapters, introduce a shared platform report-definition layer for table/export columns, and continue using the existing difference-report flow.

**Tech Stack:** Python, FastAPI, Jinja2, pandas, openpyxl, pytest

---

### Task 1: Introduce dynamic report models

**Files:**
- Modify: `app/models/reconciliation.py`
- Test: `tests/domain/test_reconcile.py`

**Step 1: Write the failing test**

Add a new domain test that constructs:

- one internal order list
- one external order list with `metrics={"sales_amount": 150.0, "settlement_paid": 150.0}`
- one external order list with Meituan-style metrics such as `technical_service_fee`

Example assertions:

```python
row = result.rows[0]
assert row.product_name == "产品A"
assert row.metrics["actual_people"] == 3
assert row.metrics["sales_amount"] == 150.0
assert row.metrics["settlement_paid"] == 150.0
assert row.metrics["purchase_amount"] == 120.0
assert row.metrics["profit"] == 30.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/domain/test_reconcile.py -q`
Expected: FAIL because the current models still expose fixed fields like `settlement_amount` and `sales_amount_total`

**Step 3: Write minimal implementation**

Update `app/models/reconciliation.py` so that:

- `ExternalOrderAggregate` contains `metrics: dict[str, float]`
- `ProductSummaryRow` contains `metrics: dict[str, float]`
- existing result container types stay intact for match counts and difference lists

Suggested shape:

```python
@dataclass(frozen=True)
class ExternalOrderAggregate:
    external_order_no: str
    metrics: dict[str, float]
    platform_name: str
    source_row_count: int
    business_date: date | None = None


@dataclass(frozen=True)
class ProductSummaryRow:
    product_name: str
    metrics: dict[str, float]
```

**Step 4: Run test to verify it still fails for the right reason**

Run: `pytest tests/domain/test_reconcile.py -q`
Expected: FAIL inside `reconcile_orders()` because domain logic still assumes fixed metric fields

**Step 5: Commit**

```bash
git add app/models/reconciliation.py tests/domain/test_reconcile.py
git commit -m "refactor: introduce metric-driven reconciliation models"
```

### Task 2: Refactor domain reconciliation to aggregate dynamic metrics

**Files:**
- Modify: `app/domain/reconcile.py`
- Test: `tests/domain/test_reconcile.py`

**Step 1: Write the failing test**

Extend the domain test to assert both:

- Ctrip compatibility metrics
- Meituan-specific metrics

Example:

```python
assert row.metrics["technical_service_fee"] == 12.0
assert row.metrics["merchant_coupon"] == 3.0
assert row.metrics["profit"] == 27.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/domain/test_reconcile.py -q`
Expected: FAIL because the grouping bucket does not yet aggregate arbitrary external metrics

**Step 3: Write minimal implementation**

Refactor `reconcile_orders()` to:

- keep order matching and difference-list logic
- initialize a per-product bucket as `defaultdict(float)`
- always add internal metrics:
  - `actual_people`
  - `purchase_amount`
- iterate through `external_order.metrics.items()` and accumulate each key
- derive `profit` after grouping using:

```python
profit = bucket.get("settlement_paid", 0.0) - bucket.get("purchase_amount", 0.0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/domain/test_reconcile.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/domain/reconcile.py tests/domain/test_reconcile.py
git commit -m "refactor: aggregate reconciliation metrics dynamically"
```

### Task 3: Add platform report definitions and migrate Ctrip

**Files:**
- Create: `app/platforms/report_definitions.py`
- Modify: `app/platforms/base.py`
- Modify: `app/platforms/registry.py`
- Modify: `app/platforms/ctrip_adapter.py`
- Test: `tests/platforms/test_ctrip_adapter.py`

**Step 1: Write the failing test**

Update Ctrip adapter tests to assert metric-based output:

```python
order = result.orders[0]
assert order.metrics["sales_amount"] == 150.0
assert order.metrics["settlement_paid"] == 150.0
```

Add a registry-level assertion for a report definition helper, for example:

```python
definition = get_platform_report_definition("ctrip")
assert [column.label for column in definition.columns] == [
    "产品名称",
    "核销人次",
    "销售额",
    "结算实付",
    "采购金额",
    "利润",
]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_ctrip_adapter.py -q`
Expected: FAIL because Ctrip still writes `settlement_amount` and no report-definition registry exists

**Step 3: Write minimal implementation**

Create `app/platforms/report_definitions.py` with:

- `ReportColumn`
- `PlatformReportDefinition`
- `get_platform_report_definition(platform_name)`

Define Ctrip columns using keys:

- `product_name`
- `actual_people`
- `sales_amount`
- `settlement_paid`
- `purchase_amount`
- `profit`

Update `CtripAdapter.parse()` so each order writes:

```python
metrics={
    "sales_amount": float(row[settlement_column]),
    "settlement_paid": float(row[settlement_column]),
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/platforms/test_ctrip_adapter.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/platforms/base.py app/platforms/registry.py app/platforms/report_definitions.py app/platforms/ctrip_adapter.py tests/platforms/test_ctrip_adapter.py
git commit -m "refactor: add platform report definitions"
```

### Task 4: Add Meituan adapter and adapter tests

**Files:**
- Create: `app/platforms/meituan_adapter.py`
- Modify: `app/platforms/registry.py`
- Test: `tests/platforms/test_meituan_adapter.py`

**Step 1: Write the failing test**

Create `tests/platforms/test_meituan_adapter.py` covering:

- required-column validation
- month filtering by `销售时间`
- aggregation by `商家订单号`
- `technical_service_fee = 技术服务费 + 技术服务费退款`
- cleaned order number output

Example:

```python
assert order.external_order_no == "14869628"
assert order.metrics["sales_amount"] == 189.0
assert order.metrics["technical_service_fee"] == 21.0
assert order.metrics["merchant_coupon"] == 0.0
assert order.metrics["settlement_paid"] == 189.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_meituan_adapter.py -q`
Expected: FAIL because the adapter does not exist yet

**Step 3: Write minimal implementation**

Create `app/platforms/meituan_adapter.py` modeled after the Ctrip adapter:

- `platform_name = "meituan"`
- `worksheet_name = "订单详情"`
- required columns:
  - `商家订单号`
  - `销售时间`
  - `应付金额`
  - `技术服务费`
  - `技术服务费退款`
  - `商家承担优惠`
  - `结算金额`

Aggregate into metrics:

```python
metrics={
    "sales_amount": float(row[payable_column]),
    "technical_service_fee": float(row[service_fee_column] + row[service_fee_refund_column]),
    "merchant_coupon": float(row[merchant_coupon_column]),
    "settlement_paid": float(row[settlement_column]),
}
```

Register the adapter under `"meituan"`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/platforms/test_meituan_adapter.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/platforms/meituan_adapter.py app/platforms/registry.py tests/platforms/test_meituan_adapter.py
git commit -m "feat: add meituan reconciliation adapter"
```

### Task 5: Refactor application, web, and export layers for dynamic columns

**Files:**
- Modify: `app/application/reconciliation_service.py`
- Modify: `app/infrastructure/excel_writer.py`
- Modify: `app/web/routes.py`
- Modify: `app/web/templates/index.html`
- Test: `tests/web/test_reconcile_route.py`
- Test: `tests/web/test_export_route.py`

**Step 1: Write the failing test**

Update web tests to cover:

- platform dropdown shows `美团`
- Ctrip HTML still renders the original six-column labels
- a Meituan export payload renders eight headers including:
  - `技术服务费`
  - `优惠券（商家承担）`

Example export payload assertion:

```python
assert worksheet["D4"].value == "技术服务费"
assert worksheet["E4"].value == "优惠券（商家承担）"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: FAIL because the template and workbook writer still use hard-coded Ctrip columns

**Step 3: Write minimal implementation**

Refactor as follows:

- `run_reconciliation()` also returns or exposes the platform report definition context needed by Web/export
- `routes.py` loads the platform report definition and serializes:
  - `report_columns`
  - metric-driven `result_rows`
- `build_reconciliation_workbook()` accepts `report_columns`
- `index.html` loops over `report_columns` for both header and cell rendering

Suggested payload shape:

```python
{
    "platform_name": platform,
    "reconciliation_month": reconciliation_month,
    "report_columns": [{"key": "sales_amount", "label": "销售额"}],
    "rows": [{"product_name": "测试产品", "metrics": {"sales_amount": 150.0}}],
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/application/reconciliation_service.py app/infrastructure/excel_writer.py app/web/routes.py app/web/templates/index.html tests/web/test_reconcile_route.py tests/web/test_export_route.py
git commit -m "refactor: render reconciliation reports from dynamic columns"
```

### Task 6: Add Meituan integration coverage with real sample files

**Files:**
- Create: `tests/integration/test_meituan_reconciliation.py`
- Modify: `tests/integration/test_sample_reconciliation.py`

**Step 1: Write the failing test**

Add a new integration test using:

- `test_data/jutianxia.xlsx`
- `test_data/meituan.xlsx`

Assert:

- result completes successfully for `platform_name="meituan"`
- key Meituan headers are available through the report definition
- at least one known product has stable metric totals
- difference lists contain expected values from the filtered order sets

Use the existing helper style that locates workbooks by sheet name where practical.

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py -q`
Expected: FAIL because the new Meituan flow is not yet wired end-to-end

**Step 3: Write minimal implementation**

Fill any missing plumbing so that:

- `run_reconciliation(..., platform_name="meituan")` works end-to-end
- result rows and report definitions stay available to downstream layers
- existing Ctrip integration assertions are updated to the new metric structure if needed

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py
git commit -m "test: add meituan end-to-end reconciliation coverage"
```

### Task 7: Run the full verification suite

**Files:**
- Test: `tests/domain/test_reconcile.py`
- Test: `tests/platforms/test_ctrip_adapter.py`
- Test: `tests/platforms/test_meituan_adapter.py`
- Test: `tests/integration/test_sample_reconciliation.py`
- Test: `tests/integration/test_meituan_reconciliation.py`
- Test: `tests/web/test_index.py`
- Test: `tests/web/test_reconcile_route.py`
- Test: `tests/web/test_export_route.py`

**Step 1: Run targeted test groups**

Run:

```bash
pytest tests/domain/test_reconcile.py tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py -q
pytest tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py -q
pytest tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: PASS

**Step 2: Run the full suite**

Run: `pytest -q`
Expected: PASS

**Step 3: Commit**

```bash
git add app tests
git commit -m "feat: support meituan reconciliation with dynamic report columns"
```

## Notes for Execution

- Keep difference-report behavior unchanged unless a test proves otherwise.
- Preserve Ctrip output compatibility by mapping its settlement amount into both `sales_amount` and `settlement_paid`.
- Do not delete or revert unrelated working-tree changes; this repository is already dirty.
- Prefer adding new helpers over branching inside the Jinja template for each platform.
- If real Meituan sample totals are not yet known, first implement the integration test with a small synthetic workbook fixture, then add assertions against the real sample once the numbers are confirmed.
