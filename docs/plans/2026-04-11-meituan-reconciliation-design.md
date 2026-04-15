# 美团对账扩展设计

文档日期：2026-04-11
当前状态：设计已确认，待进入实施计划
适用范围：在保留携程现有行为的前提下，新增美团平台对账能力，并支持按平台动态展示主结果列

## 1. 背景与目标

当前系统已支持：

- 聚天下 + 携程 对账
- 固定 6 列主结果表
- 双向订单差异检查
- 页面展示与 Excel 导出

本次新增的美团需求与携程相比，存在两个关键差异：

1. 关联规则变化
- `聚天下[订单号] == 美团[订单详情].[商家订单号]`

2. 主结果表结构变化
- 美团主结果表不是当前固定 6 列，而是 8 列：
  - 产品名称
  - 核销人次
  - 销售额
  - 技术服务费
  - 优惠券（商家承担）
  - 结算实付
  - 采购金额
  - 利润

因此，本次扩展不能被视为“仅新增适配器”的 A 类扩展，而应视为“结果结构变化”的 C 类扩展。

本次设计目标：

- 保持携程现有页面、导出和测试行为尽量不变
- 新增美团平台接入能力
- 将主结果表升级为“按平台动态列结构”
- 继续复用现有双向差异检查规则
- 为后续接入飞猪等平台预留可复用扩展点

## 2. 已确认输入与业务口径

### 2.1 文件与工作表

- 聚天下文件：`test_data/jutianxia.xlsx`
- 工作表：`订单列表`

- 美团文件：`test_data/meituan.xlsx`
- 工作表：`订单详情`

### 2.2 已核对的美团关键字段

`订单详情` 工作表中已确认存在以下列：

- `商家订单号`
- `销售时间`
- `应付金额`
- `技术服务费`
- `技术服务费退款`
- `商家承担优惠`
- `结算金额`

### 2.3 月份过滤规则

- 前端选择 `reconciliation_month`
- 美团适配器按 `订单详情.销售时间` 做月份过滤
- 非目标月份记录不参与主结果计算
- 差异表也必须基于“过滤后的美团订单号集合”生成

### 2.4 差异表规则

差异表继续沿用携程现有规则：

- `聚天下有、第三方当月无`
- `第三方有、聚天下当月无`

展示字段不变：

- 前者只展示 `订单号`
- 后者只展示 `第三方单号`

## 3. 设计结论

推荐采用“平台适配器 + 平台报表定义”双扩展点方案。

### 3.1 平台适配器负责什么

平台适配器继续负责：

- 校验平台原始字段
- 清洗订单号
- 解析日期
- 按月份过滤
- 按订单号聚合原始明细
- 输出标准化的订单级指标

### 3.2 平台报表定义负责什么

新增“平台报表定义”概念，用于声明：

- 主结果表列顺序
- 每列显示名称
- 每列对应的指标键
- 导出 Excel 的列顺序
- 页面表头的动态渲染方式

这样可以做到：

- 携程继续使用 6 列定义
- 美团使用 8 列定义
- Web 层与导出层不再写死表头

## 4. 数据模型调整

当前模型存在两个明显限制：

1. `ExternalOrderAggregate` 只有 `settlement_amount`
2. `ProductSummaryRow` 固定为 6 个业务字段

这两个限制都无法满足美团新需求。

### 4.1 外部订单模型升级方向

将外部平台订单从“单金额字段模型”升级为“订单级指标集合模型”。

建议保留以下稳定字段：

- `external_order_no`
- `platform_name`
- `source_row_count`
- `business_date`

并新增一个指标容器，例如：

- `metrics: dict[str, float]`

其中：

- 携程订单可写入：
  - `sales_amount`
  - `settlement_paid`

- 美团订单可写入：
  - `sales_amount`
  - `technical_service_fee`
  - `merchant_coupon`
  - `settlement_paid`

这样领域层不必再假设“所有平台都只有一个金额字段”。

### 4.2 主结果行模型升级方向

将固定结构的 `ProductSummaryRow` 升级为“产品名 + 动态指标值”结构。

建议形态：

- `product_name`
- `metrics: dict[str, float]`

其中平台公共指标可包括：

- `actual_people`
- `purchase_amount`
- `profit`

平台可选指标包括：

- `sales_amount`
- `technical_service_fee`
- `merchant_coupon`
- `settlement_paid`

### 4.3 平台报表列定义

新增列定义模型，例如：

- `ReportColumn(key, label, number_format)`

新增平台报表定义模型，例如：

- `PlatformReportDefinition(platform_name, platform_label, columns)`

其中：

- 携程列定义：
  - 产品名称
  - 核销人次
  - 销售额
  - 结算实付
  - 采购金额
  - 利润

- 美团列定义：
  - 产品名称
  - 核销人次
  - 销售额
  - 技术服务费
  - 优惠券（商家承担）
  - 结算实付
  - 采购金额
  - 利润

## 5. 领域层改造思路

领域层继续承担：

- 内外部订单按订单号匹配
- 差异订单集合计算
- 按聚天下产品名汇总
- 利润计算

但需要去掉当前“销售额 = 结算实付 = settlement_amount”的硬编码。

### 5.1 新的汇总方式

对于每个匹配成功的订单：

1. 汇总内部指标
- `actual_people += internal.actual_people`
- `purchase_amount += internal.purchase_amount`

2. 汇总外部指标
- 遍历 `external.metrics`
- 把各项指标累加到对应产品分组桶

3. 计算派生指标
- `profit = settlement_paid - purchase_amount`

### 5.2 携程兼容口径

为了保持携程原行为不变，携程适配器可输出：

- `sales_amount = 结算价金额`
- `settlement_paid = 结算价金额`

这样在新结构下仍然能得到与当前一致的结果。

## 6. 美团平台适配设计

### 6.1 工作表与字段

- 工作表：`订单详情`
- 订单关联字段：`商家订单号`
- 月份过滤字段：`销售时间`

### 6.2 订单级指标映射

美团单笔订单聚合后输出如下指标：

- `sales_amount = 应付金额`
- `technical_service_fee = 技术服务费 + 技术服务费退款`
- `merchant_coupon = 商家承担优惠`
- `settlement_paid = 结算金额`

### 6.3 订单清洗与过滤规则

- 丢弃 `商家订单号` 为空的行
- 清洗 `12345.0` 形式订单号
- `销售时间` 使用 `pd.to_datetime(..., errors="coerce")`
- 使用 `[month_start, next_month_start)` 方式过滤
- 过滤统计基于原始明细行数

### 6.4 聚合规则

按 `商家订单号` 聚合，并对以下字段求和：

- `应付金额`
- `技术服务费`
- `技术服务费退款`
- `商家承担优惠`
- `结算金额`

同时保留：

- 最早 `销售时间` 作为 `business_date`
- 原始行数作为 `source_row_count`

## 7. Web 与导出改造

### 7.1 页面渲染

当前页面把表头和行字段写死在模板中，需要改成：

- 后端传入 `report_columns`
- 后端传入 `result_rows`
- 模板根据列定义循环渲染表头和每行数据

这样同一页面可以支持不同平台不同列数。

### 7.2 导出 Excel

当前 `build_reconciliation_workbook()` 写死了 6 列，需要改成：

- 接收 `report_columns`
- 按列定义写入表头
- 按列 key 写入每行值

差异表导出保持不变。

### 7.3 平台名称与平台选项

需要统一平台元数据来源，避免散落在多个文件里。

建议由同一平台定义模块提供：

- 平台内部代号
- 中文名称
- 主结果表列定义

## 8. 错误处理

美团适配器需要至少覆盖以下错误场景：

- 缺少 `商家订单号`
- 缺少 `销售时间`
- 缺少 `应付金额`
- 缺少 `技术服务费`
- 缺少 `技术服务费退款`
- 缺少 `商家承担优惠`
- 缺少 `结算金额`

错误信息风格应延续当前项目做法，直接面向业务使用者，例如：

- `美团文件缺少必要字段: 商家订单号`
- `美团文件中的“销售时间”存在无法识别的日期，请检查原始数据格式`

## 9. 测试设计

本次扩展至少需要补齐四类测试。

### 9.1 领域层测试

验证新动态指标模型下：

- 仍能正确匹配订单
- 能按产品汇总多个指标
- `profit = settlement_paid - purchase_amount`
- 携程兼容口径不回归

### 9.2 平台适配器测试

新增 `tests/platforms/test_meituan_adapter.py`，覆盖：

- 必填字段缺失报错
- 按 `销售时间` 过滤月份
- 同一 `商家订单号` 多行聚合
- 技术服务费计算为 `技术服务费 + 技术服务费退款`
- 订单号清洗与唯一订单集合输出

### 9.3 集成测试

新增美团样例集成测试，覆盖：

- 使用 `jutianxia.xlsx + meituan.xlsx` 跑完整流程
- 断言匹配数、差异数、产品数
- 断言至少 1 到 3 个关键产品的指标结果
- 断言差异表关键订单号

### 9.4 Web / 导出测试

需要覆盖：

- 页面平台下拉框新增 `美团`
- 选择美团后能成功提交
- 主结果表头按美团 8 列展示
- 导出 Excel 列顺序与页面一致
- 差异导出仍然正确
- 携程页面和导出行为不回归

## 10. 实施范围

预计涉及以下模块：

- `app/models/reconciliation.py`
- `app/domain/reconcile.py`
- `app/platforms/base.py`
- `app/platforms/registry.py`
- `app/platforms/ctrip_adapter.py`
- `app/platforms/meituan_adapter.py`
- `app/application/reconciliation_service.py`
- `app/infrastructure/excel_writer.py`
- `app/web/routes.py`
- `app/web/templates/index.html`
- `tests/domain/test_reconcile.py`
- `tests/platforms/test_ctrip_adapter.py`
- `tests/platforms/test_meituan_adapter.py`
- `tests/integration/test_sample_reconciliation.py`
- `tests/integration/test_meituan_reconciliation.py`
- `tests/web/test_reconcile_route.py`
- `tests/web/test_export_route.py`

## 11. 本次设计结论

本次美团扩展应采用“统一订单级指标 + 平台动态报表列”的改造方案。

原因如下：

- 能满足美团新增指标与动态列需求
- 不会把平台专属逻辑硬编码进当前携程模型
- 携程可通过兼容映射保持现有结果
- 差异表规则可继续复用
- 后续再接入飞猪等平台时，扩展成本更低

设计确认后，下一步应进入实施计划编写，不直接开始编码。
