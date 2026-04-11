# Results Page Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Optimize the reconciliation results page for finance users by emphasizing summary cards, improving result hierarchy, and making order-difference details collapsible.

**Architecture:** Keep all business logic unchanged. Limit this round to web presentation structure, template markup, and CSS styling. Use native HTML collapsible elements so the page stays stable and low-maintenance.

**Tech Stack:** FastAPI, Jinja2, HTML, CSS, pytest

---

### Task 1: Lock the new page structure with failing tests

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_reconcile_route.py`

**Step 1: Write the failing test**

Assert that the rendered results page contains:

- `结果总览`
- `主结果表`
- `订单差异检查`
- two `details` blocks for the difference sections

**Step 2: Run the test to verify it fails**

Run:

```powershell
pytest tests/web/test_reconcile_route.py -q
```

Expected: fail because the current template does not yet expose the new structural headings and collapsible markup.

### Task 2: Implement the new template structure

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`

**Step 1: Write minimal implementation**

- add section titles for overview, main table, and difference area;
- restructure summary cards into clearer groups;
- replace always-open difference blocks with native `details/summary`.

**Step 2: Run the test**

Run:

```powershell
pytest tests/web/test_reconcile_route.py -q
```

Expected: markup-related assertions pass or only style-driven expectations remain.

### Task 3: Apply visual refinement in CSS

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\app\web\static\styles.css`

**Step 1: Write minimal implementation**

- widen the main content area for report reading;
- improve spacing between form and results;
- emphasize priority summary cards;
- improve section framing and table readability;
- style the collapsible difference panels and zero states.

**Step 2: Run relevant tests**

Run:

```powershell
pytest tests/web/test_reconcile_route.py -q
```

Expected: test still passes.

### Task 4: Run full verification and update records

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

**Step 2: Update records**

- record the results-page optimization completion;
- note the verification result.
