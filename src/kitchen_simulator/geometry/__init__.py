"""기하학 유틸리티"""
from .polygon import (
    create_polygon, create_rectangle, get_area, get_bounds,
    get_centroid, get_vertices, buffer_polygon,
    split_rectangle_horizontal, split_rectangle_vertical,
    rotate_polygon, translate_polygon,
    create_l_shape, create_u_shape,
)
from .collision import (
    check_overlap, check_contains, get_overlap_area,
    check_minimum_distance, get_distance,
    find_placement_candidates, check_aisle_width,
)
from .partitioner import (
    partition_rectangle_for_zones,
    partition_l_shape_for_zones,
    adjust_zone_ratios_for_restaurant_type,
)

__all__ = [
    "create_polygon", "create_rectangle", "get_area", "get_bounds",
    "get_centroid", "get_vertices", "buffer_polygon",
    "split_rectangle_horizontal", "split_rectangle_vertical",
    "rotate_polygon", "translate_polygon",
    "create_l_shape", "create_u_shape",
    "check_overlap", "check_contains", "get_overlap_area",
    "check_minimum_distance", "get_distance",
    "find_placement_candidates", "check_aisle_width",
    "partition_rectangle_for_zones", "partition_l_shape_for_zones",
    "adjust_zone_ratios_for_restaurant_type",
]
