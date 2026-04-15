# Difference Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a separate Excel export for order-difference details while keeping the main reconciliation export unchanged.

**Architecture:** Keep the current `/export` route for the main result workbook. Add a second web-only export action and a dedicated workbook builder that writes two difference sheets, each with month and platform metadata at the top.

**Tech Stack:** FastAPI, Jinja2, openpyxl, pytest

---

### Task 1: Lock expected behavior with failing tests

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_reconcile_route.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_export_route.py`

**Step 1: Write the failing tests**

- Assert the results page shows a second button: `导出差异表`.
- Add a dedicated route test for exporting the difference workbook.
- Assert the difference workbook contains:
  - two sheets,
  - month metadata,
  - platform metadata,
  - indexed difference rows.

**Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: fail because the current page has no difference-export button and no dedicated difference export route.

### Task 2: Implement the new export flow

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`
- Modify: `D:\DaMoXing\ZZY\finance\app\infrastructure\excel_writer.py`

**Step 1: Write minimal implementation**

- Add a second payload for difference export.
- Add `/export-differences`.
- Add a workbook builder for the two difference sheets.
- Render a second export button in the results page.

**Step 2: Run focused tests**

Run:

```powershell
pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: pass.

### Task 3: Full verification and record updates

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\task_plan.md`
- Modify: `D:\DaMoXing\ZZY\finance\findings.md`
- Modify: `D:\DaMoXing\ZZY\finance\progress.md`
- Modify: `D:\DaMoXing\ZZY\finance\README.md`

**Step 1: Run full verification**

Run:

```powershell
pytest -q
```

Expected: all tests pass.

**Step 2: Update project records**

- note that difference export is now a separate file;
- note that each difference sheet includes platform metadata.
