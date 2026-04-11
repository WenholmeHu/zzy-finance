# Difference Index And Export Scope Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add per-table row indices to the two web-only order difference sections, and stop exporting order difference details to Excel.

**Architecture:** Keep business reconciliation logic unchanged. Limit this round to web presentation and export scope. The difference sections will each render a `序号` column starting from `1`, while Excel export returns only the main reconciliation sheet.

**Tech Stack:** FastAPI, Jinja2, openpyxl, pytest

---

### Task 1: Lock the behavior with failing tests

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_reconcile_route.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_export_route.py`

**Step 1: Write the failing tests**

- Assert the difference sections render `序号` plus order number columns.
- Assert the first visible difference row starts at `1`.
- Assert Excel export no longer includes the two difference worksheets.

**Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/web/test_reconcile_route.py tests/web/test_export_route.py -q
```

Expected: fail because the current template has no index column and the current workbook still includes difference sheets.

### Task 2: Implement the minimal code

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`
- Modify: `D:\DaMoXing\ZZY\finance\app\infrastructure\excel_writer.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`

**Step 1: Add web-only index columns**

- Render `序号` in both difference tables.
- Use loop index so each table starts from `1`.

**Step 2: Remove difference export**

- Stop passing difference detail payload to the workbook builder.
- Keep Excel export to the main reconciliation sheet only.

**Step 3: Run focused tests**

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

**Step 1: Run full verification**

Run:

```powershell
pytest -q
```

Expected: all tests pass.

**Step 2: Update records**

- note the web-only numbering behavior;
- note the export scope rollback to main result only.
