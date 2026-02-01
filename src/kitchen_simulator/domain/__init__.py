"""도메인 모델"""
from .kitchen import Kitchen, KitchenShape, RestaurantType
from .zone import Zone, ZoneType, ZONE_RATIOS, WORKFLOW_ORDER, ADJACENCY_RULES
from .equipment import EquipmentSpec, EquipmentPlacement, EquipmentCategory
from .constraint import ConstraintType, ConstraintViolation, CONSTRAINTS

__all__ = [
    "Kitchen", "KitchenShape", "RestaurantType",
    "Zone", "ZoneType", "ZONE_RATIOS", "WORKFLOW_ORDER", "ADJACENCY_RULES",
    "EquipmentSpec", "EquipmentPlacement", "EquipmentCategory",
    "ConstraintType", "ConstraintViolation", "CONSTRAINTS",
]