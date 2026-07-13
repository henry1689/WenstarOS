"""D25 空间距离·时差流逝 — 客观通勤时间/紧迫度/距离"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D25_CONFIG = ObjDimConfig(dim_id=25, dim_key="spatiotemporal", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D25 空间距离·时差流逝", medical_metric_name="时间紧迫应激皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(8, 22), sibling_dims=[21,22,23,24,26])

class D25SpatiotemporalObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D25_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        # 通勤数据
        commute_km = duration.get("commute_distance_km", 0.0)
        commute_min = duration.get("commute_time_min", 0.0)
        buffer_min = duration.get("buffer_min", 60)

        # 紧迫度: 通勤时间相对于缓冲时间
        if buffer_min > 0 and commute_min > 0:
            urgency = max(0, min(1, commute_min / (commute_min + buffer_min) * 1.5))
        else:
            urgency = 0.0

        # 如果是公寓模式（步行2分钟），紧迫度≈0
        if commute_km < 1.0:
            urgency = 0.0

        cortisol = 14.0 + urgency * 8 + commute_km * 0.15  # 每10km → +1.5
        return self.make_result(round(min(cortisol, 25), 1),
            urgency=round(urgency, 2),
            commute_km=commute_km,
            commute_min=commute_min,
            buffer_min=buffer_min)
