# Phase 3 Web Integration And Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the stage-2 reconciliation engine to the web form, render finance-friendly result summaries, and support Excel export without introducing persistence.

**Architecture:** Keep the web layer thin. The POST reconcile route should save uploads to temporary files, call the existing reconciliation service, and render a result view. The export route should receive serialized result rows from the current page and generate an Excel workbook on demand, avoiding any database or session storage.

**Tech Stack:** Python 3.10, FastAPI, Jinja2, openpyxl, pytest

---

### Task 1: Reconcile Web Route

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\web\test_reconcile_route.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\static\styles.css`

**Step 1: Write the failing test**

Use `TestClient` and the real sample Excel files to assert that POSTing:

- `reconciliation_month=2026-03`
- `platform=ctrip`
- `jutianxia_file`
- `platform_file`

returns HTML that includes:

- success summary counts
- at least one expected product row
- an export button

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_reconcile_route.py -q`  
Expected: FAIL because the route does not yet exist.

**Step 3: Write minimal implementation**

Implement:

- multipart form handling
- temporary file persistence for the current request
- service invocation
- result rendering in the template

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_reconcile_route.py -q`  
Expected: PASS

### Task 2: Excel Export Route

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\web\test_export_route.py`
- Create: `D:\DaMoXing\ZZY\finance\app\infrastructure\excel_writer.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`

**Step 1: Write the failing test**

POST a serialized result payload to the export route and assert:

- status code `200`
- Excel content type
- workbook contains expected headers and at least one row value

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_export_route.py -q`  
Expected: FAIL because export writer/route does not exist.

**Step 3: Write minimal implementation**

Implement:

- workbook generation from result rows
- export response with a finance-readable filename
- hidden payload wiring in the result page

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_export_route.py -q`  
Expected: PASS

### Task 3: Full Phase Verification

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\README.md`
- Modify: `D:\DaMoXing\ZZY\finance\progress.md`
- Modify: `D:\DaMoXing\ZZY\finance\findings.md`

**Step 1: Run full test suite**

Run: `pytest -q`

**Step 2: Run app import check**

Run: `python -c "from app.main import app; print(app.title)"`

**Step 3: Update docs**

Record what the web layer now supports and what remains for the final polish stage.

**Step 4: Commit**

If Git is available, commit the verified phase-3 slice. Otherwise skip commit.
