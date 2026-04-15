# Finance Reconciliation

本项目是一个面向财务人员使用的本地网页对账工具，当前已经支持：

- `聚天下 + 携程`
- `聚天下 + 美团`
- `聚天下 + 抖音`
- `聚天下 + 同程`

系统提供：

- 网页上传双 Excel
- 按月过滤外部平台数据
- 订单匹配后按产品汇总
- 主结果表展示
- 双向订单差异检查
- 主结果 Excel 导出
- 差异订单 Excel 导出

## 当前版本的真实边界

当前代码已经不是“固定 6 列、单金额字段”的早期版本，而是 3 层扩展机制叠加的结构：

1. `平台元数据`
2. `平台适配器`
3. `平台报表定义`

这意味着系统已经支持：

- 不同平台使用不同工作表
- 单工作表但工作表名动态变化
- 不同平台使用不同聚天下关联字段
- 不同平台使用不同订单级指标集合
- 不同平台使用不同主结果表列结构
- 不同平台使用不同差异表头

但当前系统仍然默认：

- 只有 `1` 个主结果表
- 只有 `2` 个方向的差异结果
- 匹配模型仍然是“内部订单号 = 外部订单号”
- 汇总粒度仍然是 `产品内容`
- 利润公式仍然是 `结算实付 - 采购金额`

如果未来某个平台超出这些边界，不应只改适配器，而要同步升级领域层、页面或导出结构。

## 目录与职责

`app/` 目录的关键结构如下：

- `app/main.py`
  - FastAPI 应用入口

- `app/web/`
  - `routes.py`
    - 接收上传
    - 调用应用服务
    - 渲染页面
    - 处理导出
  - `templates/index.html`
    - 结果页与动态表头展示
  - `static/styles.css`
    - 页面样式

- `app/application/`
  - `reconciliation_service.py`
    - 一次完整对账的流程编排
    - 读取聚天下
    - 读取平台工作簿
    - 调用平台适配器
    - 调用领域汇总

- `app/domain/`
  - `reconcile.py`
    - 通用对账算法
    - 匹配订单
    - 汇总产品
    - 计算利润
    - 生成双向差异结果

- `app/models/`
  - `reconciliation.py`
    - 统一数据模型
    - `InternalOrder`
    - `ExternalOrderAggregate`
    - `PlatformParseResult`
    - `ProductSummaryRow`
    - `ReconciliationResult`

- `app/platforms/`
  - `base.py`
    - `PlatformAdapter`
    - `PlatformSpec`
  - `registry.py`
    - 平台注册表
    - 平台工作表列表
    - 聚天下关联字段
    - 差异表头
  - `report_definitions.py`
    - 平台主结果表列定义
  - `ctrip_adapter.py`
    - 携程解析逻辑
  - `meituan_adapter.py`
    - 美团解析逻辑
  - `douyin_adapter.py`
    - 抖音解析逻辑
  - `tongcheng_adapter.py`
    - 同程解析逻辑

- `app/infrastructure/`
  - `excel_reader.py`
    - Excel 读取
  - `excel_writer.py`
    - 主结果 / 差异表导出
  - `date_parser.py`
    - 月份区间工具

## 四个平台的代码边界

### 平台元数据边界

平台静态元数据集中在 [registry.py](D:/DaMoXing/ZZY/finance/app/platforms/registry.py)。

这里负责：

- 平台内部代号
- 平台中文名
- 需要读取哪些工作表
- 聚天下使用哪个字段参与匹配
- 差异表显示什么表头
- 对应适配器类

当前 4 个平台的核心元数据如下：

| 平台 | 工作表 | 聚天下关联字段 | 差异表头（内部） | 差异表头（外部） |
| --- | --- | --- | --- | --- |
| 携程 | `流水` | `订单号` | `订单号` | `第三方单号` |
| 美团 | `订单详情` | `订单号` | `订单号` | `商家订单号` |
| 抖音 | `分账明细-正向-团购`、`分账明细-退款-团购` | `渠道订单号` | `渠道订单号` | `订单编号` |
| 同程 | `单工作表（名称动态）` | `订单号` | `订单号` | `三方流水号` |

如果某个平台以后要改：

- 聚天下匹配字段
- 工作表名称
- 差异表表头

优先改这里，而不是直接改领域层。

### 平台输入解析边界

平台原始 Excel 的清洗、字段映射、按月过滤、一单多行聚合，统一放在 `app/platforms/*_adapter.py`。

当前每个平台的职责划分如下：

- 携程
  - 文件：[ctrip_adapter.py](D:/DaMoXing/ZZY/finance/app/platforms/ctrip_adapter.py)
  - 负责：
    - 读取 `流水`
    - 使用 `出发时间` 过滤
    - `第三方单号` 聚合
    - 输出：
      - `sales_amount`
      - `settlement_paid`

- 美团
  - 文件：[meituan_adapter.py](D:/DaMoXing/ZZY/finance/app/platforms/meituan_adapter.py)
  - 负责：
    - 读取 `订单详情`
    - 使用 `销售时间` 过滤
    - `商家订单号` 聚合
    - 输出：
      - `sales_amount`
      - `technical_service_fee`
      - `merchant_coupon`
      - `settlement_paid`

- 抖音
  - 文件：[douyin_adapter.py](D:/DaMoXing/ZZY/finance/app/platforms/douyin_adapter.py)
  - 负责：
    - 同时读取 `分账明细-正向-团购`、`分账明细-退款-团购`
    - 使用 `核销时间` 过滤
    - 两张表合并后按 `订单编号` 聚合
    - 退款口径按“原值直接相加”
    - 输出：
      - `sales_amount`
      - `technical_service_fee`
      - `commission`
      - `service_provider_commission`
      - `settlement_paid`

- 同程
  - 文件：[tongcheng_adapter.py](D:/DaMoXing/ZZY/finance/app/platforms/tongcheng_adapter.py)
  - 负责：
    - 读取平台文件中的唯一工作表（工作表名动态）
    - 使用 `旅游日期` 过滤
    - `三方流水号` 聚合
    - 输出：
      - `sales_amount`
      - `settlement_paid`

如果某个平台以后只是：

- 字段名变化
- 日期列变化
- 工作表变化
- 多一个输入工作表
- 金额映射变化

优先改该平台适配器。

### 主结果表边界

主结果表的列定义集中在 [report_definitions.py](D:/DaMoXing/ZZY/finance/app/platforms/report_definitions.py)。

这里负责：

- 每个平台主结果表有哪些列
- 列顺序
- 列标题
- 哪些列按数值右对齐

当前 4 个平台的主结果表：

- 携程：
  - `产品名称 / 核销人次 / 销售额 / 结算实付 / 采购金额 / 利润`

- 美团：
  - `产品名称 / 核销人次 / 销售额 / 技术服务费 / 优惠券（商家承担） / 结算实付 / 采购金额 / 利润`

- 抖音：
  - `产品名称 / 核销人次 / 销售额 / 技术服务费 / 佣金 / 服务商佣金 / 结算实付 / 采购金额 / 利润`

- 同程：
  - `产品名称 / 核销人次 / 销售额 / 结算实付 / 采购金额 / 利润`

如果某个平台以后只是“结果列不同”，优先改这里。

### 应用编排边界

[reconciliation_service.py](D:/DaMoXing/ZZY/finance/app/application/reconciliation_service.py) 负责串联所有平台共享流程：

1. 根据 `PlatformSpec` 选择聚天下匹配字段
2. 读取聚天下 `订单列表`
3. 读取平台工作簿中指定工作表
4. 调用平台适配器
5. 把统一结果交给领域层

如果以后要改：

- 聚天下读取规则
- 平台工作簿加载规则
- 订单号保真 / `.0` 清洗
- 平台共用的流程编排

优先改这里。

### 领域规则边界

[reconcile.py](D:/DaMoXing/ZZY/finance/app/domain/reconcile.py) 是全平台共享的统一业务算法。

这里负责：

- `internal.order_no == external.external_order_no`
- 按 `product_name` 汇总
- 汇总内部指标：
  - `actual_people`
  - `purchase_amount`
- 汇总外部 `metrics`
- 计算：
  - `profit = settlement_paid - purchase_amount`
- 生成：
  - `internal_only_order_nos`
  - `external_only_order_nos`

如果以后要改：

- 利润公式
- 汇总维度
- 匹配模型
- 差异结果生成规则

不要只改平台适配器，而要评估这里是否要升级。

## 改某一个平台时，先看哪里

| 需求类型 | 优先修改文件 |
| --- | --- |
| 只改某平台输入字段/日期/聚合逻辑 | `app/platforms/<platform>_adapter.py` |
| 改某平台工作表名 | `app/platforms/registry.py` |
| 改某平台聚天下匹配字段 | `app/platforms/registry.py` |
| 改某平台差异表头 | `app/platforms/registry.py` |
| 改某平台主结果表列 | `app/platforms/report_definitions.py` |
| 改所有平台共享读取流程 | `app/application/reconciliation_service.py` / `app/infrastructure/excel_reader.py` |
| 改页面展示结构 | `app/web/routes.py` / `app/web/templates/index.html` |
| 改导出结构 | `app/infrastructure/excel_writer.py` |
| 改利润/汇总/差异核心算法 | `app/domain/reconcile.py` |

## 平台扩展的标准入口

后续新增平台，优先看这几份代码：

- [base.py](D:/DaMoXing/ZZY/finance/app/platforms/base.py)
- [registry.py](D:/DaMoXing/ZZY/finance/app/platforms/registry.py)
- [report_definitions.py](D:/DaMoXing/ZZY/finance/app/platforms/report_definitions.py)
- [reconciliation_service.py](D:/DaMoXing/ZZY/finance/app/application/reconciliation_service.py)
- [reconcile.py](D:/DaMoXing/ZZY/finance/app/domain/reconcile.py)

最常见的新增平台改动是：

1. 新增 `app/platforms/<platform>_adapter.py`
2. 在 `registry.py` 注册 `PlatformSpec`
3. 在 `report_definitions.py` 补主结果表列
4. 增加适配器测试
5. 增加集成测试
6. 视情况增加 Web / 导出测试

## 当前支持的平台规则摘要

### 聚天下

固定工作表：

- `订单列表`

当前实际使用的字段：

- `订单号`
- `渠道订单号`
- `产品内容`
- `实到人数`
- `采购金额`

说明：

- 携程、美团使用 `订单号`
- 抖音使用 `渠道订单号`

### 携程

- 工作表：`流水`
- 关联规则：`聚天下[订单号] == 携程[第三方单号]`
- 月份过滤字段：`出发时间`
- 指标：
  - `销售额 = 结算价金额`
  - `结算实付 = 结算价金额`

### 美团

- 工作表：`订单详情`
- 关联规则：`聚天下[订单号] == 美团[商家订单号]`
- 月份过滤字段：`销售时间`
- 指标：
  - `销售额 = 应付金额`
  - `技术服务费 = 技术服务费 + 技术服务费退款`
  - `优惠券（商家承担） = 商家承担优惠`
  - `结算实付 = 结算金额`

### 抖音

- 工作表：
  - `分账明细-正向-团购`
  - `分账明细-退款-团购`
- 关联规则：`聚天下[渠道订单号] == 抖音[订单编号]`
- 月份过滤字段：`核销时间`
- 指标：
  - `销售额 = 订单实收金额`
  - `技术服务费 = 增量宝 + 软件服务费`
  - `佣金 = 平台撮合佣金 + 达人佣金 + 撮合经纪服务费 + 保险费用`
  - `服务商佣金 = 服务商佣金`
  - `结算实付 = 商家应得`

### 同程

- 工作表：平台文件中的唯一工作表（名称动态）
- 关联规则：`聚天下[订单号] == 同程[三方流水号]`
- 月份过滤字段：`旅游日期`
- 指标：
  - `销售额 = 应结(元)`
  - `结算实付 = 应结(元)`

## 推荐阅读顺序

如果后续要继续扩平台，建议按下面顺序阅读：

1. [平台拓展开发说明.md](D:/DaMoXing/ZZY/finance/docs/dev/平台拓展开发说明.md)
2. [平台接入检查清单.md](D:/DaMoXing/ZZY/finance/docs/dev/平台接入检查清单.md)
3. [项目设计文档.md](D:/DaMoXing/ZZY/finance/docs/dev/项目设计文档.md)
4. 目标平台真实样例 Excel
5. 现有最接近的平台适配器实现

## 当前样例文件

当前仓库中默认提供的真实样例文件位于 [test_data](D:/DaMoXing/ZZY/finance/test_data)：

- `jutianxia_tc.xlsx`
- `tongcheng.xlsx`

说明：

- 当前 `test_data` 已切换为同程样例
- 抖音 / 美团真实样例集成测试在样例文件缺失时会自动跳过

## 本地运行

运行环境：`Python 3.10+`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

浏览器访问：

```text
http://127.0.0.1:8000
```

## 测试

当前可稳定执行的验证命令：

```powershell
pytest tests -q
```

说明：

- 当前仓库已包含携程 / 美团 / 抖音 / 同程的适配器与相关测试代码
- 若 `test_data` 中未包含某个平台的真实样例文件，该平台的真实样例集成测试会自动跳过

## 相关文档

- [平台拓展开发说明.md](D:/DaMoXing/ZZY/finance/docs/dev/平台拓展开发说明.md)
- [平台接入检查清单.md](D:/DaMoXing/ZZY/finance/docs/dev/平台接入检查清单.md)
- [项目设计文档.md](D:/DaMoXing/ZZY/finance/docs/dev/项目设计文档.md)
- [reconciliation_requirements_draft.md](D:/DaMoXing/ZZY/finance/docs/dev/reconciliation_requirements_draft.md)
- [人工验收.md](D:/DaMoXing/ZZY/finance/docs/dev/人工验收.md)
