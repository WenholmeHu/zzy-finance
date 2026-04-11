# Phase 1 Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a runnable FastAPI project skeleton with a finance-friendly home page that exposes the first-step reconciliation form.

**Architecture:** Keep the first slice deliberately thin: one FastAPI entrypoint, one web route, one Jinja template, and one static stylesheet. Do not implement real reconciliation logic yet; only prove the application can start and render the expected form structure.

**Tech Stack:** Python 3.10, FastAPI, Jinja2, pytest

---

### Task 1: Bootstrap FastAPI App And Red Test

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\web\test_index.py`
- Create: `D:\DaMoXing\ZZY\finance\app\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\main.py`
- Create: `D:\DaMoXing\ZZY\finance\app\web\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\web\routes.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


def test_home_page_renders_successfully():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "聚天下文件" in response.text
    assert "外部平台文件" in response.text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_index.py -q`  
Expected: FAIL because `app.main` or route/template is missing.

**Step 3: Write minimal implementation**

Create a FastAPI app, register a root route, and return an HTML response from `/`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_index.py -q`  
Expected: PASS

**Step 5: Commit**

If the workspace is a Git repository, commit the phase-1 bootstrap files. If not, skip commit and continue.

### Task 2: Replace Inline HTML With Jinja Template And Form Structure

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\app\web\templates\index.html`
- Create: `D:\DaMoXing\ZZY\finance\app\web\static\styles.css`
- Modify: `D:\DaMoXing\ZZY\finance\app\web\routes.py`
- Modify: `D:\DaMoXing\ZZY\finance\tests\web\test_index.py`

**Step 1: Write the failing test**

Extend the page test to assert the presence of:

- `对账月份`
- `平台选择`
- `开始对账`

**Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_index.py -q`  
Expected: FAIL because the template does not yet expose the full form.

**Step 3: Write minimal implementation**

Render a Jinja template containing:

- month input
- platform select
- 聚天下 file input
- 外部平台 file input
- submit button

Link a simple stylesheet so the page is readable.

**Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_index.py -q`  
Expected: PASS

**Step 5: Commit**

If Git exists, commit the template slice. Otherwise skip commit.

### Task 3: Add Startup Documentation And Smoke Verification

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\requirements.txt`
- Create or Modify: `D:\DaMoXing\ZZY\finance\README.md`

**Step 1: Write the failing check**

Define the expected run command and dependency list in documentation:

- `uvicorn app.main:app --reload`
- required packages for phase 1

**Step 2: Run smoke command**

Run: `python -c "from app.main import app; print(app.title)"`  
Expected: FAIL before dependencies/files are fully wired or PASS once app exists.

**Step 3: Write minimal implementation**

Document:

- how to install dependencies
- how to start the service
- what phase 1 currently supports

**Step 4: Run verification**

Run:

- `pytest tests/web/test_index.py -q`
- `python -c "from app.main import app; print(app.title)"`

Expected:

- tests PASS
- app imports successfully

**Step 5: Commit**

If Git exists, commit the phase-1 completion slice. Otherwise skip commit.
