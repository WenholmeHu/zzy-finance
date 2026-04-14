"""平台适配器注册表。"""

from app.platforms.ctrip_adapter import CtripAdapter
from app.platforms.meituan_adapter import MeituanAdapter


def get_platform_adapter(platform_name: str):
    """根据平台名返回对应适配器实例。

    这是平台扩展的唯一入口之一：
    - 新增平台时，把 `平台代号: 适配器类` 注册到 adapters 字典；
    - 上层流程无需感知具体实现，按平台名获取即可。
    """
    adapters = {
        "ctrip": CtripAdapter,
        "meituan": MeituanAdapter,
    }
    try:
        return adapters[platform_name]()
    except KeyError as exc:
        raise ValueError(f"暂不支持的平台: {platform_name}") from exc
