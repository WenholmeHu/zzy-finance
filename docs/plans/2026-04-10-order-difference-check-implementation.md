# Order Difference Check Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add bidirectional monthly order difference checks to the existing reconciliation flow, while keeping the main product summary result intact.

**Architecture:** Extend the reconciliation result model so one request returns both the main summary table and two order-difference lists. Keep the platform adapter responsible for monthly filtering and normalized external order keys, and keep the domain flow responsible for set comparison and summary aggregation.

**Tech Stack:** Python, FastAPI, Jinja2, pandas, openpyxl, pytest

---

### Task 1: Lock expected behavior with tests

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\tests\domain\test_reconcile.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\integration\test_sample_reconciliation.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_reconcile_route.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_export_route.py`

**Step 1: Write failing tests**

- Add domain assertions for:
  - `internal_only_order_nos`
  - `external_only_order_nos`
  - corresponding counts
- Add integration assertions for the real sample files.
- Add route assertions for summary counts and the two difference sections.
- Add export assertions for difference output in the workbook.

**Step 2: Run focused tests to verify they fail**

Run:

```powershell
pytest tests/domain/test_reconcile.py tests/integration/test_sample_reconciliation.py tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: failures due to missing result fields and missing rendered/exported difference content.

### Task 2: Implement the new result model and domain behavior

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\models\reconciliation.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\domain\reconcile.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\application\reconciliation_service.py`

**Step 1: Write minimal implementation**

- Extend `ReconciliationResult` with:
  - `internal_only_order_nos`
  - `external_only_order_nos`
  - convenience count properties
- Compute bidirectional unique order differences in `reconcile_orders`.
- Preserve existing matched summary behavior.

**Step 2: Run focused tests**

Run:

```powershell
pytest tests/domain/test_reconcile.py tests/integration/test_sample_reconciliation.py -q
```

Expected: pass for domain/integration scope or fail only on web/export expectations.

### Task 3: Surface difference results in the web UI and export

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`
- Modify: `D:\DaMoXing\ZZY\finance\app\infrastructure\excel_writer.py`

**Step 1: Write minimal implementation**

- Add difference counts to the summary context.
- Add two rendered result sections in the template.
- Include difference payload in export.
- Export the difference result in additional worksheets or clear sections.

**Step 2: Run focused tests**

Run:

```powershell
pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: pass.

### Task 4: Full verification and project record updates

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\task_plan.md`
- Modify: `D:\DaMoXing\ZZY\finance\findings.md`
- Modify: `D:\DaMoXing\ZZY\finance\progress.md`

**Step 1: Run full test suite**

Run:

```powershell
pytest -q
```

Expected: all tests pass.

**Step 2: Update project records**

- Note the new bidirectional order difference capability.
- Record the latest verification result.
