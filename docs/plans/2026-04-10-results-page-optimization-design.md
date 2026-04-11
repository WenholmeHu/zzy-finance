# Results Page Optimization Design

**Date:** 2026-04-10  
**Scope:** Reconciliation results page only  
**Status:** Approved for implementation

## Goal

Optimize the current reconciliation page for finance users so they can:

1. first identify whether the month has obvious anomalies,
2. then read the main product summary comfortably,
3. and only then inspect order-difference details when needed.

This is a usability and presentation optimization. It does not change reconciliation business rules.

## Current Problems

The current page is functionally complete, but it still feels like a developer-first tool:

- summary cards do not clearly separate “important” and “secondary” indicators;
- the main result table and difference areas compete for attention;
- order-difference details are always expanded, which increases scanning pressure;
- overall layout is still closer to a raw tool page than a formal reconciliation workspace.

## Target Experience

The optimized page should follow this reading order:

1. `结果总览`
2. `主结果表`
3. `订单差异检查`

Finance staff should be able to answer these questions within a few seconds:

- 本月匹配情况是否正常？
- 是否存在明显差异订单？
- 如果有差异，数量是多少？
- 需要时，差异明细在哪里查看？

## Information Hierarchy

### 1. Result Overview First

The first visual focus should be a summary dashboard.

Priority order:

- 成功匹配订单数
- 聚天下有、第三方当月无
- 第三方有、聚天下当月无
- 汇总产品数
- 被过滤的非当月平台记录数

The two difference counts should look more noticeable than secondary metrics, because they indicate monthly anomalies.

### 2. Main Result Table Second

The main summary table remains directly visible.

Reasons:

- it is still the primary accounting output;
- finance staff should not need one extra click to see it;
- readability should improve through spacing, section framing, and numeric alignment rather than hiding it.

### 3. Difference Details Third

The difference area should move below the main table and become collapsible.

Two sections:

- `聚天下有、第三方当月无`
- `第三方有、聚天下当月无`

Default state:

- collapsed
- title shows count immediately
- users expand only when they need detailed order numbers

## Interaction Design

Use native HTML collapsible panels to keep the feature stable and low-maintenance.

Recommended element:

- `details`
- `summary`

Reasons:

- no extra JavaScript required;
- works well in a local tool;
- easier to maintain than custom expand/collapse logic.

## Visual Direction

The style should feel like a formal internal finance tool, not a flashy dashboard.

Design direction:

- cleaner section separation;
- stronger hierarchy for the overview cards;
- tighter control of table spacing and numeric scanability;
- more breathing room between form area and results area;
- clear visual distinction between normal information and anomaly information.

## Proposed Structure

### Upload Area

Keep the upload form at the top, but visually separate it from the result area.

### Overview Area

Add a clear section title such as `结果总览`.

Card structure:

- one emphasized primary card for matched orders;
- two anomaly cards for the two difference counts;
- secondary cards for product count and filtered count;
- month and platform shown as supportive labels rather than competing with main metrics.

### Main Table Area

Add a clear section title such as `主结果表`.

Improve:

- table framing;
- spacing;
- numeric alignment;
- readability on desktop and mobile.

### Difference Area

Add a clear section title such as `订单差异检查`.

Each difference block:

- collapsed by default;
- title includes count;
- opens into a simple one-column table or list;
- if count is zero, display a calm zero-state rather than a large empty table.

## Testing Scope

This optimization is mostly presentation-oriented, so automated tests should focus on structural behavior:

- the results page renders the new section headings;
- the summary area includes the two difference counts;
- the difference blocks render as collapsible containers;
- the main result table still renders correctly;
- existing reconciliation behavior remains unchanged.

## Non-Goals

This round does not include:

- changing reconciliation formulas;
- changing export structure;
- adding JavaScript-heavy interaction;
- adding charts or dashboard analytics;
- redesigning the upload workflow.
