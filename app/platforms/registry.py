"""平台适配器注册表。"""

from app.platforms.ctrip_adapter import CtripAdapter


def get_platform_adapter(platform_name: str):
    """根据平台名返回对应适配器实例。"""
    adapters = {
        "ctrip": CtripAdapter,
    }
    try:
        return adapters[platform_name]()
    except KeyError as exc:
        raise ValueError(f"暂不支持的平台: {platform_name}") from exc
