# Tongcheng Reconciliation Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Tongcheng reconciliation support with month filtering by `旅游日期`, matching on `聚天下[订单号] == 同程[三方流水号]`, dynamic single-sheet workbook loading, Tongcheng report definitions, and stable regression coverage.

**Architecture:** Keep Tongcheng-specific parsing inside a dedicated adapter and register the platform through the existing metadata/report-definition pipeline. Add a small shared workbook-loading capability for platforms whose files must contain exactly one worksheet even when the worksheet name is dynamic, and keep the current domain aggregation, page structure, and export structure unchanged.

**Tech Stack:** Python, FastAPI, Jinja2, pandas, openpyxl, pytest

---

### Task 1: Add a dynamic single-sheet loading contract to platform metadata

**Files:**
- Modify: `app/platforms/base.py`
- Modify: `app/platforms/registry.py`
- Modify: `app/application/reconciliation_service.py`
- Modify: `app/infrastructure/excel_reader.py`
- Test: `tests/integration/test_sample_reconciliation.py`

**Step 1: Write the failing test**

Add an application-layer test that proves a platform can declare “dynamic single worksheet” input and that the service layer loads the only sheet from the workbook into `workbook_data`.

Example structure:

```python
fake_spec = PlatformSpec(
    platform_name="tongcheng",
    platform_label="同程",
    worksheet_names=(),
    worksheet_mode="single_dynamic",
    internal_order_column="订单号",
    internal_difference_label="订单号",
    external_difference_label="三方流水号",
    adapter_factory=None,
)
```

Assert that:

- a workbook with one sheet succeeds
- a workbook with more than one sheet raises a clear error

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`
Expected: FAIL because the current platform metadata only supports fixed worksheet names.

**Step 3: Write minimal implementation**

Add a small platform worksheet-selection contract, for example:

```python
@dataclass(frozen=True)
class PlatformSpec:
    platform_name: str
    platform_label: str
    worksheet_names: tuple[str, ...]
    worksheet_mode: str = "fixed"
    internal_order_column: str = "订单号"
    internal_difference_label: str = "订单号"
    external_difference_label: str = "第三方单号"
    adapter_factory: type[PlatformAdapter] | None = None
```

Add workbook utilities to:

- list sheet names
- load the only sheet when `worksheet_mode == "single_dynamic"`
- raise a business-friendly error if the workbook does not contain exactly one sheet

Keep current Ctrip, Meituan, and Douyin fixed-sheet behavior unchanged.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`
Expected: PASS for the new loading assertions.

**Step 5: Commit**

```bash
git add app/platforms/base.py app/platforms/registry.py app/application/reconciliation_service.py app/infrastructure/excel_reader.py tests/integration/test_sample_reconciliation.py
git commit -m "refactor: support dynamic single-sheet platform inputs"
```

### Task 2: Add Tongcheng adapter tests first

**Files:**
- Create: `tests/platforms/test_tongcheng_adapter.py`

**Step 1: Write the failing test**

Create adapter-level tests covering:

- missing required columns
- month filtering by `旅游日期`
- cleaning `14869628.0` into `14869628`
- mapping `应结(元)` to both `sales_amount` and `settlement_paid`
- aggregating multiple rows with the same `三方流水号`

Example assertions:

```python
order = result.orders[0]
assert order.external_order_no == "14869628"
assert order.metrics["sales_amount"] == pytest.approx(200.0)
assert order.metrics["settlement_paid"] == pytest.approx(200.0)
assert order.source_row_count == 2
```

Also add a failure case:

```python
with pytest.raises(ValueError, match="同程文件缺少必要字段"):
    adapter.parse_workbook({"订单2026-04-01": dataframe}, "2026-03")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_tongcheng_adapter.py -q`
Expected: FAIL because the adapter does not exist yet.

**Step 3: Write minimal implementation**

Do not implement the adapter yet. Only keep the failing test file in place and confirm it accurately expresses the intended Tongcheng behavior.

**Step 4: Run test again to confirm failure is meaningful**

Run: `pytest tests/platforms/test_tongcheng_adapter.py -q`
Expected: FAIL with import or missing implementation errors, not with malformed tests.

**Step 5: Commit**

```bash
git add tests/platforms/test_tongcheng_adapter.py
git commit -m "test: add tongcheng adapter coverage"
```

### Task 3: Implement the Tongcheng adapter and register the platform

**Files:**
- Create: `app/platforms/tongcheng_adapter.py`
- Modify: `app/platforms/registry.py`
- Test: `tests/platforms/test_tongcheng_adapter.py`

**Step 1: Write the minimal adapter implementation**

Create `TongchengAdapter` with:

- `platform_name = "tongcheng"`
- support for exactly one worksheet in `workbook_data`
- required columns:
  - `旅游日期`
  - `应结(元)`
  - `三方流水号`

Normalize rows as:

```python
working["三方流水号"] = working["三方流水号"].astype(str).str.replace(".0", "", regex=False)
working["_business_date"] = pd.to_datetime(working["旅游日期"], errors="coerce")
working["应结(元)"] = pd.to_numeric(working["应结(元)"], errors="coerce").fillna(0)
```

Aggregate by `三方流水号` and map:

```python
metrics = {
    "sales_amount": float(row["应结(元)"]),
    "settlement_paid": float(row["应结(元)"]),
}
```

**Step 2: Register Tongcheng**

Add a `PlatformSpec` entry:

```python
"tongcheng": PlatformSpec(
    platform_name="tongcheng",
    platform_label="同程",
    worksheet_names=(),
    worksheet_mode="single_dynamic",
    internal_order_column="订单号",
    internal_difference_label="订单号",
    external_difference_label="三方流水号",
    adapter_factory=TongchengAdapter,
)
```

**Step 3: Run targeted tests**

Run: `pytest tests/platforms/test_tongcheng_adapter.py -q`
Expected: PASS.

**Step 4: Add a small registry assertion**

Extend the platform tests or add one more assertion:

```python
adapter = get_platform_adapter("tongcheng")
assert isinstance(adapter, TongchengAdapter)
```

Run: `pytest tests/platforms/test_tongcheng_adapter.py tests/integration/test_sample_reconciliation.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/platforms/tongcheng_adapter.py app/platforms/registry.py tests/platforms/test_tongcheng_adapter.py tests/integration/test_sample_reconciliation.py
git commit -m "feat: add tongcheng reconciliation adapter"
```

### Task 4: Add Tongcheng report definitions and web/export coverage

**Files:**
- Modify: `app/platforms/report_definitions.py`
- Modify: `tests/web/test_index.py`
- Modify: `tests/web/test_reconcile_route.py`
- Modify: `tests/web/test_export_route.py`

**Step 1: Write the failing web tests**

Add or update tests to assert:

- homepage platform dropdown includes `同程`
- Tongcheng result page renders:
  - `产品名称`
  - `核销人次`
  - `销售额`
  - `结算实付`
  - `采购金额`
  - `利润`
- Tongcheng difference section shows:
  - internal header `订单号`
  - external header `三方流水号`

For the export route, assert:

```python
assert worksheet["B2"].value == "同程"
assert external_only_sheet["B4"].value == "三方流水号"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: FAIL because Tongcheng is not yet in the report definitions or web-facing platform list.

**Step 3: Write minimal implementation**

Add a Tongcheng report definition that mirrors Ctrip’s six columns:

```python
PlatformReportDefinition(
    platform_name="tongcheng",
    platform_label="同程",
    columns=[
        ReportColumn(key="product_name", label="产品名称", is_numeric=False),
        ReportColumn(key="actual_people", label="核销人次"),
        ReportColumn(key="sales_amount", label="销售额"),
        ReportColumn(key="settlement_paid", label="结算实付"),
        ReportColumn(key="purchase_amount", label="采购金额"),
        ReportColumn(key="profit", label="利润"),
    ],
)
```

Rely on the existing route/template/export plumbing for dynamic labels and columns.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/platforms/report_definitions.py tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py
git commit -m "feat: add tongcheng report and web coverage"
```

### Task 5: Add real-sample Tongcheng integration coverage

**Files:**
- Create: `tests/integration/test_tongcheng_reconciliation.py`

**Step 1: Write the failing integration test**

Create an end-to-end test using:

- `test_data/jutianxia_tc.xlsx`
- `test_data/tongcheng.xlsx`

Assert:

- `matched_order_count == 737`
- `product_count == 23`
- `filtered_out_of_month_row_count == 1`
- `internal_only_count == 8748`
- `external_only_count == 0`
- `external_only_order_nos == []`

Also assert one representative product row:

```python
row = next(
    row for row in result.rows
    if row.product_name == "【即买即用】【线下扫码】东运旅行卢宅景区成人票+卢宅文创产品1份"
)
assert row.metrics["actual_people"] == 257
assert row.metrics["sales_amount"] == pytest.approx(16705.0)
assert row.metrics["settlement_paid"] == pytest.approx(16705.0)
assert row.metrics["purchase_amount"] == pytest.approx(13364.0)
assert row.metrics["profit"] == pytest.approx(3341.0)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_tongcheng_reconciliation.py -q`
Expected: FAIL until the Tongcheng platform is fully wired through the application service.

**Step 3: Finish any missing plumbing**

If the integration test still fails, make only the smallest missing changes needed so that:

- the service loads the single dynamic Tongcheng worksheet
- internal orders still come from `订单列表`
- matching uses `订单号`
- Tongcheng adapter output reaches the current domain aggregator unchanged

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_tongcheng_reconciliation.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/integration/test_tongcheng_reconciliation.py app/application/reconciliation_service.py app/infrastructure/excel_reader.py
git commit -m "test: add tongcheng end-to-end reconciliation coverage"
```

### Task 6: Repair the regression baseline after the test_data switch

**Files:**
- Modify or Delete: `tests/integration/test_douyin_reconciliation.py`
- Modify or Delete: `tests/integration/test_meituan_reconciliation.py`
- Possibly Modify: `README.md`

**Step 1: Decide the narrowest safe change**

Current full-suite failures are caused by deleted sample files:

- `test_data/jutianxia.xlsx`
- `test_data/douyin.xlsx`
- `test_data/meituan.xlsx`

Prefer the least risky option:

- mark these real-sample tests as skipped when the required files are absent, or
- move them behind explicit fixture/file-existence guards

Do not delete useful logic-only coverage that still passes without the removed files.

**Step 2: Write the failing expectation**

Add a file-presence guard pattern such as:

```python
if not jutianxia_file.exists() or not douyin_file.exists():
    pytest.skip("real sample files not available in current test_data set")
```

**Step 3: Implement the minimal change**

Apply the same pattern to the Meituan sample integration test and update `README.md` if the recommended regression command needs to change.

**Step 4: Run the affected tests**

Run: `pytest tests/integration/test_meituan_reconciliation.py tests/integration/test_douyin_reconciliation.py -q`
Expected: SKIP or PASS, but no longer FAIL because of missing files.

**Step 5: Commit**

```bash
git add tests/integration/test_meituan_reconciliation.py tests/integration/test_douyin_reconciliation.py README.md
git commit -m "test: guard removed real-sample integration fixtures"
```

### Task 7: Run regression verification across the supported suite

**Files:**
- Test: `tests/platforms/test_ctrip_adapter.py`
- Test: `tests/platforms/test_meituan_adapter.py`
- Test: `tests/platforms/test_douyin_adapter.py`
- Test: `tests/platforms/test_tongcheng_adapter.py`
- Test: `tests/integration/test_sample_reconciliation.py`
- Test: `tests/integration/test_meituan_reconciliation.py`
- Test: `tests/integration/test_douyin_reconciliation.py`
- Test: `tests/integration/test_tongcheng_reconciliation.py`
- Test: `tests/web/test_index.py`
- Test: `tests/web/test_reconcile_route.py`
- Test: `tests/web/test_export_route.py`

**Step 1: Run targeted suites**

Run:

```bash
pytest tests/platforms/test_ctrip_adapter.py tests/platforms/test_meituan_adapter.py tests/platforms/test_douyin_adapter.py tests/platforms/test_tongcheng_adapter.py -q
pytest tests/integration/test_sample_reconciliation.py tests/integration/test_meituan_reconciliation.py tests/integration/test_douyin_reconciliation.py tests/integration/test_tongcheng_reconciliation.py -q
pytest tests/web/test_index.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: PASS or intended SKIP for real-sample tests whose fixtures are unavailable.

**Step 2: Run the full suite**

Run: `pytest tests -q`
Expected: PASS or PASS-with-skip, but no unexpected failures.

**Step 3: Commit**

```bash
git add app tests README.md
git commit -m "feat: support tongcheng reconciliation"
```

## Notes for Execution

- The user explicitly requested working in the main workspace, so do not create a worktree for this plan.
- Keep Tongcheng-specific field names out of the domain layer and page template unless a failing test proves otherwise.
- The adapter should not depend on a hard-coded Tongcheng worksheet name; it should consume the only worksheet provided.
- Preserve the current profit formula and current product-level aggregation strategy.
- Do not revert or overwrite the user’s `test_data` changes; adapt the regression strategy around the new fixture set.

## Execution Handoff

Plan complete and saved to `docs/plans/2026-04-15-tongcheng-reconciliation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
