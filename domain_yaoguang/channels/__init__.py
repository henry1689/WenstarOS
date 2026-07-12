"""
channels/ — 瑶光 32 维客观参数通道
===================================
每个维度一条独立通道，继承 BaseObjectiveChannel。
输出: 纯客观标准基线值（无主观情绪/体感）
用途: wf_perception_filter 工作流调用全部 32 通道生成 YaoguangUpstream 快照
"""
from .base_objective_channel import (
    BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory,
)

from .obj_d1_muscle import D1MuscleObjective
from .obj_d2_pain import D2PainObjective
from .obj_d3_touch import D3TouchObjective
from .obj_d4_endocrine import D4EndocrineObjective
from .obj_d5_pheromone import D5PheromoneObjective
from .obj_d6_metabolism import D6MetabolismObjective
from .obj_d7_recovery import D7RecoveryObjective
from .obj_d8_senses import D8SensesObjective
from .obj_d9_self_identity import D9SelfIdentityObjective
from .obj_d10_desire import D10DesireObjective
from .obj_d11_fear import D11FearObjective
from .obj_d12_enjoyment import D12EnjoymentObjective
from .obj_d13_empathy import D13EmpathyObjective
from .obj_d14_self_protection import D14SelfProtectionObjective
from .obj_d15_partner_attachment import D15PartnerAttachmentObjective
from .obj_d16_partner_protection import D16PartnerProtectionObjective
from .obj_d17_family_belonging import D17FamilyBelongingObjective
from .obj_d18_family_protection import D18FamilyProtectionObjective
from .obj_d19_social import D19SocialObjective
from .obj_d20_team import D20TeamObjective
from .obj_d21_private_space import D21PrivateSpaceObjective
from .obj_d22_home_environment import D22HomeEnvironmentObjective
from .obj_d23_workplace import D23WorkplaceObjective
from .obj_d24_public_space import D24PublicSpaceObjective
from .obj_d25_spatiotemporal import D25SpatiotemporalObjective
from .obj_d26_seasonal import D26SeasonalObjective
from .obj_d27_micro_physiology import D27MicroPhysiologyObjective
from .obj_d28_nature_expansion import D28NatureExpansionObjective
from .obj_d29_social_refinement import D29SocialRefinementObjective
from .obj_d30_spiritual_growth import D30SpiritualGrowthObjective
from .obj_d31_quantum_coupling import D31QuantumCouplingObjective
from .obj_d32_holistic import D32HolisticObjective

_CHANNEL_CLASSES = {
    1: D1MuscleObjective, 2: D2PainObjective, 3: D3TouchObjective, 4: D4EndocrineObjective,
    5: D5PheromoneObjective, 6: D6MetabolismObjective, 7: D7RecoveryObjective, 8: D8SensesObjective,
    9: D9SelfIdentityObjective, 10: D10DesireObjective, 11: D11FearObjective,
    12: D12EnjoymentObjective, 13: D13EmpathyObjective, 14: D14SelfProtectionObjective,
    15: D15PartnerAttachmentObjective, 16: D16PartnerProtectionObjective,
    17: D17FamilyBelongingObjective, 18: D18FamilyProtectionObjective,
    19: D19SocialObjective, 20: D20TeamObjective,
    21: D21PrivateSpaceObjective, 22: D22HomeEnvironmentObjective,
    23: D23WorkplaceObjective, 24: D24PublicSpaceObjective,
    25: D25SpatiotemporalObjective, 26: D26SeasonalObjective,
    27: D27MicroPhysiologyObjective, 28: D28NatureExpansionObjective,
    29: D29SocialRefinementObjective, 30: D30SpiritualGrowthObjective,
    31: D31QuantumCouplingObjective, 32: D32HolisticObjective,
}

def get_objective_channel(dim_id: int) -> BaseObjectiveChannel:
    cls = _CHANNEL_CLASSES.get(dim_id)
    if cls is None:
        raise KeyError(f"维度 {dim_id} 不在瑶光客观通道注册表中")
    return cls()

def create_all_objective_channels() -> dict:
    return {dim_id: cls() for dim_id, cls in _CHANNEL_CLASSES.items()}

__all__ = [
    "BaseObjectiveChannel", "ObjDimConfig", "ObjectiveResult", "ObjCategory",
    "get_objective_channel", "create_all_objective_channels",
]
