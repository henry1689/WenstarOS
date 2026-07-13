"""D23 职场厂区·工作环境 — 客观工作负荷 + 通勤疲劳叠加"""
from .base_objective_channel import BaseObjectiveChannel, ObjDimConfig, ObjectiveResult, ObjCategory

D23_CONFIG = ObjDimConfig(dim_id=23, dim_key="workplace", category=ObjCategory.SPATIOTEMPORAL,
    label_cn="D23 职场厂区·工作环境", medical_metric_name="工作皮质醇", medical_baseline=14.0,
    medical_unit="μg/dL", standard_range=(8, 22), sibling_dims=[21,22,24,25,26])

class D23WorkplaceObjective(BaseObjectiveChannel):
    def __init__(self): super().__init__(D23_CONFIG)
    def compute_objective(self, env, temporal, duration, interpersonal) -> ObjectiveResult:
        work_h = duration.get("work_duration_hours", 0)
        # 基础工作皮质醇
        cortisol = 14.0 + max(0, work_h - 6) * 0.8
        # 驾驶疲劳叠加: 如果有通勤，每10%驾驶疲劳→+0.5μg/dL
        drive_fatigue = duration.get("drive_fatigue", 0.0)
        cortisol += drive_fatigue * 5.0
        # 物理疲劳叠加
        phys_fatigue = duration.get("physical_fatigue", 0.0)
        cortisol += phys_fatigue * 3.0
        return self.make_result(round(min(cortisol, 28), 1),
            work_hours=work_h,
            drive_fatigue=round(drive_fatigue, 2),
            physical_fatigue=round(phys_fatigue, 2))
