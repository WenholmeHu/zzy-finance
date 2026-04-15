"""平台适配器注册表。"""

from app.platforms.ctrip_adapter import CtripAdapter
from app.platforms.douyin_adapter import DouyinAdapter
from app.platforms.meituan_adapter import MeituanAdapter
from app.platforms.base import PlatformSpec
from app.platforms.tongcheng_adapter import TongchengAdapter


_PLATFORM_SPECS = {
    "ctrip": PlatformSpec(
        platform_name="ctrip",
        platform_label="携程",
        worksheet_names=("流水",),
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="第三方单号",
        adapter_factory=CtripAdapter,
    ),
    "meituan": PlatformSpec(
        platform_name="meituan",
        platform_label="美团",
        worksheet_names=("订单详情",),
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="商家订单号",
        adapter_factory=MeituanAdapter,
    ),
    "douyin": PlatformSpec(
        platform_name="douyin",
        platform_label="抖音",
        worksheet_names=("分账明细-正向-团购", "分账明细-退款-团购"),
        internal_order_column="渠道订单号",
        internal_difference_label="渠道订单号",
        external_difference_label="订单编号",
        adapter_factory=DouyinAdapter,
    ),
    "tongcheng": PlatformSpec(
        platform_name="tongcheng",
        platform_label="同程",
        worksheet_names=(),
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="三方流水号",
        adapter_factory=TongchengAdapter,
        worksheet_mode="single_dynamic",
    ),
}


def get_platform_spec(platform_name: str) -> PlatformSpec:
    """根据平台名返回对应平台规格。"""
    try:
        return _PLATFORM_SPECS[platform_name]
    except KeyError as exc:
        raise ValueError(f"暂不支持的平台: {platform_name}") from exc


def get_platform_adapter(platform_name: str):
    """根据平台名返回对应适配器实例。

    这是平台扩展的唯一入口之一：
    - 新增平台时，把 `平台代号: 规格` 注册到规格表；
    - 上层流程无需感知具体实现，按平台名获取即可。
    """
    spec = get_platform_spec(platform_name)
    if spec.adapter_factory is None:
        raise ValueError(f"暂不支持的平台适配器: {platform_name}")
    return spec.adapter_factory()
