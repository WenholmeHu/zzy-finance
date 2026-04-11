"""项目 Web 应用入口。

这个文件负责三件事：
1. 创建 FastAPI 实例；
2. 挂载前端静态资源目录；
3. 注册页面与接口路由。

可以把它理解为“总装配点”。
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.web.routes import router as web_router


app = FastAPI(title="Finance Reconciliation")

# 将 /static 路径映射到 app/web/static 目录。
# 模板中的 CSS、图片等资源都会通过这个挂载点访问。
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "web" / "static"),
    name="static",
)

# 注册网页相关路由：包含首页、执行对账、导出 Excel。
app.include_router(web_router)
