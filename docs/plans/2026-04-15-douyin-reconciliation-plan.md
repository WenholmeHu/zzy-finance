# Douyin Reconciliation Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Douyin reconciliation support with two-sheet input, a platform-specific internal match key, Douyin-specific report columns, and platform-specific difference headers without regressing existing Ctrip and Meituan flows.

**Architecture:** Extend the platform contract so the application layer can load multiple worksheets and choose the correct Jutianxia match column per platform. Keep Douyin-specific parsing and metric mapping inside a dedicated adapter, reuse the existing metric-driven domain aggregation, and thread platform-specific difference labels through the web and export layers.

**Tech Stack:** Python, FastAPI, Jinja2, pandas, openpyxl, pytest

---

### Task 1: Introduce platform metadata for worksheet lists and internal match keys

**Files:**
- Modify: `app/platforms/base.py`
- Modify: `app/platforms/registry.py`
- Modify: `app/application/reconciliation_service.py`
- Test: `tests/integration/test_sample_reconciliation.py`

**Step 1: Write the failing test**

Add a small application/integration-focused test that asserts platform metadata exposes:

- Ctrip worksheet list
- Meituan worksheet list
- Douyin worksheet list
- the internal Jutianxia match column for each platform

Example assertions:

```python
spec = get_platform_spec("douyin")
assert spec.worksheet_names == ["分账明细-正向-团购", "分账明细-退款-团购"]
assert spec.internal_order_column == "渠道订单号"
assert spec.internal_difference_label == "渠道订单号"
assert spec.external_difference_label == "订单编号"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`
Expected: FAIL because the current registry only returns adapter instances and has no worksheet-list or match-key metadata.

**Step 3: Write minimal implementation**

Add a platform-spec concept that the application layer can consume.

Suggested shape:

```python
@dataclass(frozen=True)
class PlatformSpec:
    platform_name: str
    platform_label: str
    worksheet_names: list[str]
    internal_order_column: str
    internal_difference_label: str
    external_difference_label: str
    adapter_factory: type[PlatformAdapter]
```

Update `reconciliation_service.py` so `_load_internal_orders()` accepts the platform-selected Jutianxia match column instead of hard-coding `订单号`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`
Expected: PASS for the metadata assertions, while Douyin end-to-end behavior is still unimplemented.

**Step 5: Commit**

```bash
git add app/platforms/base.py app/platforms/registry.py app/application/reconciliation_service.py tests/integration/test_sample_reconciliation.py
git commit -m "refactor: add platform metadata for reconciliation inputs"
```

### Task 2: Add a workbook-loading contract that supports multiple platform sheets

**Files:**
- Modify: `app/platforms/base.py`
- Modify: `app/application/reconciliation_service.py`
- Modify: `app/platforms/ctrip_adapter.py`
- Modify: `app/platforms/meituan_adapter.py`
- Test: `tests/platforms/test_ctrip_adapter.py`
- Test: `tests/platforms/test_meituan_adapter.py`

**Step 1: Write the failing test**

Add or update adapter tests so they cover the new parse input shape and prove existing platforms still work when their workbook data is loaded through the new contract.

Example assertion:

```python
result = adapter.parse_workbook(
    {"流水": dataframe},
    reconciliation_month="2026-03",
)
assert result.orders[0].external_order_no == "12345"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py -q`
Expected: FAIL because adapters currently accept only a single DataFrame via `parse(...)`.

**Step 3: Write minimal implementation**

Evolve the adapter contract to accept a workbook-data mapping.

Suggested shape:

```python
class PlatformAdapter(ABC):
    platform_name: str

    @abstractmethod
    def parse_workbook(
        self,
        workbook_data: dict[str, pd.DataFrame],
        reconciliation_month: str,
    ) -> PlatformParseResult:
        raise NotImplementedError
```

Update Ctrip and Meituan adapters to pull their single expected sheet from `workbook_data` and keep their existing behavior unchanged.

**Step 4: Run test to verify it passes**

Run: `pytest tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/platforms/base.py app/application/reconciliation_service.py app/platforms/ctrip_adapter.py app/platforms/meituan_adapter.py tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py
git commit -m "refactor: support workbook-based platform parsing"
```

### Task 3: Add the Douyin adapter and adapter-level tests

**Files:**
- Create: `app/platforms/douyin_adapter.py`
- Modify: `app/platforms/registry.py`
- Test: `tests/platforms/test_douyin_adapter.py`

**Step 1: Write the failing test**

Create `tests/platforms/test_douyin_adapter.py` covering:

- missing worksheet errors
- required-column validation per worksheet
- month filtering by `核销时间`
- aggregation across positive and refund sheets
- duplicate `订单编号` consolidation
- direct-addition handling for refund rows

Example assertions:

```python
order = result.orders[0]
assert order.external_order_no == "1092863204608662040"
assert order.metrics["sales_amount"] == -68.35
assert order.metrics["technical_service_fee"] == 3.42
assert order.metrics["commission"] == 12.44
assert order.metrics["service_provider_commission"] == 0.0
assert order.metrics["settlement_paid"] == -52.49
```

For an order spanning both sheets, assert the adapter sums the raw values exactly once per row:

```python
assert order.metrics["sales_amount"] == positive_sales + refund_sales
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_douyin_adapter.py -q`
Expected: FAIL because the adapter does not exist yet.

**Step 3: Write minimal implementation**

Create `app/platforms/douyin_adapter.py` with:

- required worksheets:
  - `分账明细-正向-团购`
  - `分账明细-退款-团购`
- required columns:
  - `核销时间`
  - `订单编号`
  - `订单实收金额`
  - `增量宝`
  - `软件服务费`
  - `平台撮合佣金`
  - `达人佣金`
  - `撮合经纪服务费`
  - `保险费用`
  - `服务商佣金`
  - `商家应得`

Map each in-month row to:

```python
metrics = {
    "sales_amount": row["订单实收金额"],
    "technical_service_fee": row["增量宝"] + row["软件服务费"],
    "commission": (
        row["平台撮合佣金"]
        + row["达人佣金"]
        + row["撮合经纪服务费"]
        + row["保险费用"]
    ),
    "service_provider_commission": row["服务商佣金"],
    "settlement_paid": row["商家应得"],
}
```

Then concatenate positive and refund rows and aggregate by `订单编号`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/platforms/test_douyin_adapter.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/platforms/douyin_adapter.py app/platforms/registry.py tests/platforms/test_douyin_adapter.py
git commit -m "feat: add douyin reconciliation adapter"
```

### Task 4: Add Douyin report definitions and platform-specific difference headers

**Files:**
- Modify: `app/platforms/report_definitions.py`
- Modify: `app/web/routes.py`
- Modify: `app/web/templates/index.html`
- Modify: `app/infrastructure/excel_writer.py`
- Test: `tests/web/test_reconcile_route.py`
- Test: `tests/web/test_export_route.py`

**Step 1: Write the failing test**

Update web tests to assert:

- Douyin appears in the platform dropdown
- the Douyin main report renders these headers:
  - `产品名称`
  - `核销人次`
  - `销售额`
  - `技术服务费`
  - `佣金`
  - `服务商佣金`
  - `结算实付`
  - `采购金额`
  - `利润`
- the difference section uses `渠道订单号` and `订单编号`
- the difference export workbook uses the same headers

Example assertions:

```python
assert "渠道订单号" in response.text
assert "订单编号" in response.text
assert worksheet["B4"].value == "渠道订单号"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: FAIL because difference headers are currently hard-coded and Douyin is not yet registered in report definitions.

**Step 3: Write minimal implementation**

Add a Douyin report definition with columns:

```python
[
    ReportColumn(key="product_name", label="产品名称", is_numeric=False),
    ReportColumn(key="actual_people", label="核销人次"),
    ReportColumn(key="sales_amount", label="销售额"),
    ReportColumn(key="technical_service_fee", label="技术服务费"),
    ReportColumn(key="commission", label="佣金"),
    ReportColumn(key="service_provider_commission", label="服务商佣金"),
    ReportColumn(key="settlement_paid", label="结算实付"),
    ReportColumn(key="purchase_amount", label="采购金额"),
    ReportColumn(key="profit", label="利润"),
]
```

Thread platform-specific difference labels from the registry/spec into:

- route context
- template headings
- difference workbook builder

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/platforms/report_definitions.py app/web/routes.py app/web/templates/index.html app/infrastructure/excel_writer.py tests/web/test_reconcile_route.py tests/web/test_export_route.py
git commit -m "feat: add douyin report definitions and difference headers"
```

### Task 5: Add Douyin end-to-end reconciliation coverage

**Files:**
- Create: `tests/integration/test_douyin_reconciliation.py`
- Modify: `tests/integration/test_sample_reconciliation.py`

**Step 1: Write the failing test**

Create an end-to-end integration test using:

- `test_data/jutianxia.xlsx`
- `test_data/douyin.xlsx`

Assert:

- `run_reconciliation(..., platform_name="douyin")` succeeds
- matched order count is non-zero
- product count is non-zero
- at least one known row exposes:
  - `sales_amount`
  - `technical_service_fee`
  - `commission`
  - `service_provider_commission`
  - `settlement_paid`
- difference lists are produced from `渠道订单号` vs filtered `订单编号`

Example assertions:

```python
assert result.matched_order_count > 0
assert result.product_count > 0
assert any("commission" in row.metrics for row in result.rows)
assert isinstance(result.internal_only_order_nos, list)
assert isinstance(result.external_only_order_nos, list)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_douyin_reconciliation.py -q`
Expected: FAIL because the Douyin flow is not yet fully wired through the service layer.

**Step 3: Write minimal implementation**

Complete any missing plumbing so that:

- the service loads both Douyin worksheets
- Jutianxia internal orders use `渠道订单号` for Douyin
- the adapter output reaches the existing domain aggregator
- result payloads remain compatible with the current UI and export layers

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_douyin_reconciliation.py tests/integration/test_sample_reconciliation.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/integration/test_douyin_reconciliation.py tests/integration/test_sample_reconciliation.py
git commit -m "test: add douyin end-to-end reconciliation coverage"
```

### Task 6: Run regression verification across all supported platforms

**Files:**
- Test: `tests/platforms/test_ctrip_adapter.py`
- Test: `tests/platforms/test_meituan_adapter.py`
- Test: `tests/platforms/test_douyin_adapter.py`
- Test: `tests/integration/test_sample_reconciliation.py`
- Test: `tests/integration/test_meituan_reconciliation.py`
- Test: `tests/integration/test_douyin_reconciliation.py`
- Test: `tests/web/test_index.py`
- Test: `tests/web/test_reconcile_route.py`
- Test: `tests/web/test_export_route.py`

**Step 1: Run targeted suites**

Run:

```bash
pytest tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py tests/platforms/test_douyin_adapter.py -q
pytest tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py tests/integration/test_douyin_reconciliation.py -q
pytest tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: PASS.

**Step 2: Run the full suite**

Run: `pytest -q`
Expected: PASS.

**Step 3: Commit**

```bash
git add app tests
git commit -m "feat: support douyin reconciliation"
```

## Notes for Execution

- Keep the domain aggregation strategy unchanged unless a failing Douyin test proves the current metric-driven model is insufficient.
- Do not infer refund behavior from field signs; always follow the confirmed business rule: positive-sheet raw value + refund-sheet raw value.
- Avoid hard-coding Douyin branches in the application layer beyond selecting platform metadata.
- Keep existing Ctrip and Meituan match behavior unchanged by continuing to use `订单号` for those platforms.
- Do not revert unrelated working-tree changes; this repository is already dirty.
