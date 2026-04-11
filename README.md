# Finance Reconciliation

本项目是一个面向财务人员使用的本地网页对账工具。

当前状态：已完成核心对账引擎、网页上传流程、主结果展示、双向订单差异检查和 Excel 导出。

## 项目架构说明

当前代码采用“分层 + 平台适配器”结构，核心目标是：
- 对账业务逻辑与 Web/Excel 技术细节解耦；
- 便于后续继续接入飞猪、美团等平台；
- 保持流程清晰，方便维护与测试。

### 1) 目录与分层职责

`app/` 目录的主要结构如下：

- `main.py`
  - FastAPI 应用入口。
  - 挂载静态资源目录（`/static`）并注册网页路由。

- `web/`
  - `routes.py`：Web 层控制器，负责接收表单、保存上传文件、调用应用服务、渲染页面、处理导出。
  - `templates/index.html`：前端页面模板。
  - `static/styles.css`：页面样式。

- `application/`
  - `reconciliation_service.py`：应用服务层，编排完整对账流程（读内部单、选平台适配器、解析平台数据、调用领域算法、组装结果）。

- `domain/`
  - `reconcile.py`：纯业务核心，对内部订单与外部订单做匹配，并按产品汇总指标与利润。

- `models/`
  - `reconciliation.py`：领域数据模型（如 `InternalOrder`、`ExternalOrderAggregate`、`ReconciliationResult` 等）。

- `platforms/`
  - `base.py`：平台适配器抽象接口。
  - `ctrip_adapter.py`：携程实现，负责字段校验、按月过滤、按订单号聚合。
  - `registry.py`：平台名到适配器的注册与分发。

- `infrastructure/`
  - `excel_reader.py`：Excel 读取。
  - `excel_writer.py`：Excel 导出构建。
  - `date_parser.py`：月份日期区间工具（用于“按月过滤”）。

### 2) 运行链路（从页面到结果）

1. 用户在首页选择对账月份、平台并上传两个 Excel。  
2. `web/routes.py` 接收请求并将文件写入临时目录。  
3. `application/reconciliation_service.py` 启动对账流程：
   - 读取聚天下内部订单；
   - 按平台名获取适配器（当前为携程）；
   - 解析平台 Excel 为统一外部订单结构；
   - 调用 `domain/reconcile.py` 做匹配与汇总。  
4. Web 层将结果渲染为页面摘要 + 明细表。  
5. 页面同时展示主结果表与双向订单差异检查结果。
6. 点击“导出 Excel”后，`infrastructure/excel_writer.py` 生成文件并下载。

### 3) 架构边界（为什么这样分）

- Web 层只负责“收发请求与页面渲染”，不直接写业务算法。
- Domain 层只负责业务规则，不依赖 FastAPI、模板或具体平台文件格式。
- 平台差异放在 `platforms/` 适配器中，新增平台时不需要改核心算法。
- Excel 读写放在 `infrastructure/`，避免技术细节污染业务逻辑。

### 4) 扩展指引（新增一个平台）

1. 在 `app/platforms/` 新增适配器类并实现 `parse`。  
2. 在 `registry.py` 注册新平台名与适配器。  
3. 在 `web/templates/index.html` 中增加平台选项。  
4. 为新适配器补充测试用例（建议放在 `tests/platforms/`）。

## 当前已支持

- 启动本地 FastAPI 服务
- 打开首页
- 手动选择 `对账月份`
- 选择平台 `携程`
- 上传 `聚天下` Excel 文件
- 上传 `携程` Excel 文件
- 执行 `聚天下 + 携程` 对账
- 页面展示摘要信息、主结果表和双向订单差异检查结果
- 差异明细在网页中提供序号，便于财务定位查看进度
- 导出 Excel 结果文件

## 当前尚未支持

- 飞猪、美团等其他平台适配
- 历史记录持久化
- 登录权限
- 桌面程序打包

## 运行环境

- Python 3.10+

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 启动项目

```powershell
uvicorn app.main:app --reload
```

启动后在浏览器访问：

```text
http://127.0.0.1:8000
```

## 当前测试状态

已验证通过：

- 首页渲染测试
- 纯业务汇总测试
- 携程适配器过滤与聚合测试
- 样例 Excel 集成测试
- 网页提交流程测试
- Excel 导出测试

自动化测试命令：

```powershell
pytest -q
```

## 手工验收

建议结合 [手工验收清单.md](D:/DaMoXing/ZZY/finance/手工验收清单.md) 一起使用。

## 下一步可继续扩展

- 把当前结果页继续优化为更适合财务阅读的样式
- 增加更友好的异常提示
- 接入飞猪、美团等平台适配器
