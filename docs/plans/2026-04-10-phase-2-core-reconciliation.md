# Phase 2 Core Reconciliation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the core reconciliation engine for `聚天下 + 携程`, including month filtering, order aggregation, product summarization, and sample-data verification.

**Architecture:** Keep the business core split into three layers: typed domain models, a Ctrip adapter that converts Excel rows into standardized external orders, and a reconciliation engine that joins `聚天下` orders with external aggregates and produces product-level summary rows. Use real sample-data assertions to protect business correctness before wiring the web form.

**Tech Stack:** Python 3.10, pandas, openpyxl, pytest

---

### Task 1: Reconciliation Domain Models And Pure Summarization

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\domain\test_reconcile.py`
- Create: `D:\DaMoXing\ZZY\finance\app\models\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\models\reconciliation.py`
- Create: `D:\DaMoXing\ZZY\finance\app\domain\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\domain\reconcile.py`

**Step 1: Write the failing test**

Test an in-memory scenario where:

- two `聚天下` orders map to one product
- one unmatched order is ignored
- `sales_amount`, `settlement_paid`, `purchase_amount`, and `profit` are correct

**Step 2: Run test to verify it fails**

Run: `pytest tests/domain/test_reconcile.py -q`  
Expected: FAIL because models and reconciliation engine do not exist.

**Step 3: Write minimal implementation**

Create dataclasses for:

- internal order
- external aggregated order
- summary row
- reconciliation result

Implement a reconcile function that:

- indexes external orders by order number
- keeps only matched internal orders
- groups by product name
- sums actual people, sales, settlement, and purchase
- computes profit

**Step 4: Run test to verify it passes**

Run: `pytest tests/domain/test_reconcile.py -q`  
Expected: PASS

**Step 5: Commit**

If Git is available, commit the pure domain slice. Otherwise skip commit.

### Task 2: Ctrip Adapter Month Filtering And Order Aggregation

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\platforms\test_ctrip_adapter.py`
- Create: `D:\DaMoXing\ZZY\finance\app\platforms\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\platforms\base.py`
- Create: `D:\DaMoXing\ZZY\finance\app\platforms\ctrip_adapter.py`
- Create: `D:\DaMoXing\ZZY\finance\app\platforms\registry.py`
- Create: `D:\DaMoXing\ZZY\finance\app\infrastructure\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\infrastructure\date_parser.py`

**Step 1: Write the failing test**

Use an in-memory DataFrame or small fixture to verify:

- only rows inside the selected month survive
- repeated `第三方单号` values are aggregated by sum
- aggregated orders expose standardized fields

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/test_ctrip_adapter.py -q`  
Expected: FAIL because adapter and parser are missing.

**Step 3: Write minimal implementation**

Implement:

- a month-range helper
- a Ctrip adapter that validates required columns
- month filtering on `出发时间`
- grouping by `第三方单号`
- standardized external order output
- a simple platform registry entry for `ctrip`

**Step 4: Run test to verify it passes**

Run: `pytest tests/platforms/test_ctrip_adapter.py -q`  
Expected: PASS

**Step 5: Commit**

If Git is available, commit the adapter slice. Otherwise skip commit.

### Task 3: Sample Excel Integration Verification

**Files:**
- Create: `D:\DaMoXing\ZZY\finance\tests\integration\test_sample_reconciliation.py`
- Create: `D:\DaMoXing\ZZY\finance\app\infrastructure\excel_reader.py`
- Create: `D:\DaMoXing\ZZY\finance\app\application\__init__.py`
- Create: `D:\DaMoXing\ZZY\finance\app\application\reconciliation_service.py`

**Step 1: Write the failing test**

Use the real sample files under `test_data/` and assert:

- matched order count is `1908`
- product summary count is `29`
- at least these product rows match expected totals:
  - `【即买即用】【线下扫码】东运旅行卢宅景区成人票+卢宅文创产品1份`
  - `良渚古城遗址公园成人票（不含观光车）即买即用`
  - `【提前两小时】黄帝陵景区  成人票`

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`  
Expected: FAIL because the service and Excel reader do not exist.

**Step 3: Write minimal implementation**

Implement:

- a small Excel reader for named sheets
- a service that reads `聚天下` orders and Ctrip rows
- adapter invocation by platform name
- reconcile invocation returning a typed result

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_sample_reconciliation.py -q`  
Expected: PASS

**Step 5: Commit**

If Git is available, commit the integration slice. Otherwise skip commit.

### Task 4: Full Phase Verification

**Files:**
- Modify: `D:\DaMoXing\ZZY\finance\README.md` (if needed to note current capability)
- Modify: `D:\DaMoXing\ZZY\finance\progress.md`
- Modify: `D:\DaMoXing\ZZY\finance\findings.md`

**Step 1: Run full automated verification**

Run: `pytest -q`

**Step 2: Verify clean result**

Expected:

- all tests pass
- no missing import errors
- phase 2 behavior is covered by unit and integration tests

**Step 3: Update docs**

Record:

- what phase 2 now supports
- what remains for phase 3

**Step 4: Commit**

If Git is available, commit the verified phase-2 slice. Otherwise skip commit.
