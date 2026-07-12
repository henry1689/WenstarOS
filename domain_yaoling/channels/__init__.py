"""
channels/ — 瑶灵 32 维通道处理器
=================================
每个维度一条独立通道，继承 BaseChannel。
提供 channel_registry 便捷获取全部通道实例。
"""

from .base_channel import BaseChannel, DimConfig, SignalInput, OrganState, SensationResult, Intensity, HealthLevel, ChannelCategory
from .d1_muscle import D1MuscleChannel
from .d2_pain import D2PainChannel
from .d3_touch import D3TouchChannel
from .d4_endocrine import D4EndocrineChannel
from .d5_pheromone import D5PheromoneChannel
from .d6_metabolism import D6MetabolismChannel
from .d7_recovery import D7RecoveryChannel
from .d8_senses import D8SensesChannel
from .d9_self_identity import D9SelfIdentityChannel
from .d10_desire_drive import D10DesireDriveChannel
from .d11_fear_fatigue import D11FearFatigueChannel
from .d12_enjoyment import D12EnjoymentChannel
from .d13_empathy import D13EmpathyChannel
from .d14_self_protection import D14SelfProtectionChannel
from .d15_partner_attachment import D15PartnerAttachmentChannel
from .d16_partner_protection import D16PartnerProtectionChannel
from .d17_family_belonging import D17FamilyBelongingChannel
from .d18_family_protection import D18FamilyProtectionChannel
from .d19_social import D19SocialChannel
from .d20_team import D20TeamChannel
from .d21_private_space import D21PrivateSpaceChannel
from .d22_home_environment import D22HomeEnvironmentChannel
from .d23_workplace import D23WorkplaceChannel
from .d24_public_space import D24PublicSpaceChannel
from .d25_spatiotemporal import D25SpatiotemporalChannel
from .d26_seasonal import D26SeasonalChannel
from .d27_micro_physiology import D27MicroPhysiologyChannel
from .d28_nature_expansion import D28NatureExpansionChannel
from .d29_social_refinement import D29SocialRefinementChannel
from .d30_spiritual_growth import D30SpiritualGrowthChannel
from .d31_quantum_coupling import D31QuantumCouplingChannel
from .d32_holistic import D32HolisticChannel

_CHANNEL_CLASSES = {
    1: D1MuscleChannel, 2: D2PainChannel, 3: D3TouchChannel, 4: D4EndocrineChannel,
    5: D5PheromoneChannel, 6: D6MetabolismChannel, 7: D7RecoveryChannel, 8: D8SensesChannel,
    9: D9SelfIdentityChannel, 10: D10DesireDriveChannel, 11: D11FearFatigueChannel,
    12: D12EnjoymentChannel, 13: D13EmpathyChannel, 14: D14SelfProtectionChannel,
    15: D15PartnerAttachmentChannel, 16: D16PartnerProtectionChannel,
    17: D17FamilyBelongingChannel, 18: D18FamilyProtectionChannel,
    19: D19SocialChannel, 20: D20TeamChannel,
    21: D21PrivateSpaceChannel, 22: D22HomeEnvironmentChannel,
    23: D23WorkplaceChannel, 24: D24PublicSpaceChannel,
    25: D25SpatiotemporalChannel, 26: D26SeasonalChannel,
    27: D27MicroPhysiologyChannel, 28: D28NatureExpansionChannel,
    29: D29SocialRefinementChannel, 30: D30SpiritualGrowthChannel,
    31: D31QuantumCouplingChannel, 32: D32HolisticChannel,
}

def get_channel(dim_id: int) -> BaseChannel:
    """获取指定维度的通道实例。"""
    cls = _CHANNEL_CLASSES.get(dim_id)
    if cls is None:
        raise KeyError(f"维度 {dim_id} 不在通道注册表中")
    return cls()

def create_all_channels() -> dict:
    """创建全部 32 通道的实例字典 {dim_id: channel}。"""
    return {dim_id: cls() for dim_id, cls in _CHANNEL_CLASSES.items()}

__all__ = [
    "BaseChannel", "DimConfig", "SignalInput", "OrganState", "SensationResult",
    "Intensity", "HealthLevel", "ChannelCategory",
    "get_channel", "create_all_channels",
]
