"""
倾斜变换模块

实现笔画的旋转倾斜变换，支持围绕指定中心点的旋转。
"""

import math
from typing import List, Dict, Any, Tuple
from .base_transform import BaseTransform
from ..centerline import Point


class TiltTransform(BaseTransform):
    """倾斜变换实现"""
    
    def __init__(self):
        super().__init__("tilt")
    
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """
        应用倾斜变换
        
        Args:
            points: 输入点序列
            params: 倾斜参数 {"angle_deg": 角度, "center_point": 旋转中心}
            
        Returns:
            倾斜后的点序列
        """
        if not self.is_enabled(params):
            return points
            
        angle_deg = params.get('angle_deg', 0.0)
        if abs(angle_deg) < 1e-6:
            return points
        
        # 计算旋转中心
        center_point = params.get('center_point')
        if center_point is not None:
            center = center_point
        else:
            # 回退到计算当前边界框中心
            center = self._calculate_bbox_center(points)
        
        # 执行旋转
        return self._rotate_points(points, angle_deg, center)
    
    def _calculate_bbox_center(self, points: List[Point]) -> Tuple[float, float]:
        """计算点序列的边界框中心"""
        if not points:
            return (0.0, 0.0)
            
        xs = [x for x, y in points]
        ys = [y for x, y in points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
    
    def _rotate_points(self, points: List[Point], angle_deg: float, center: Tuple[float, float]) -> List[Point]:
        """围绕中心点旋转点序列"""
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        cx, cy = center
        
        result = []
        for x, y in points:
            # 平移到原点
            dx = x - cx
            dy = y - cy
            
            # 旋转
            new_x = dx * cos_a - dy * sin_a
            new_y = dx * sin_a + dy * cos_a
            
            # 平移回去
            result.append((new_x + cx, new_y + cy))
        
        return result
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认倾斜参数"""
        return {
            "angle_deg": 0.0,
            "center": None,  # None表示自动计算边界框中心
            "enabled": False
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证倾斜参数"""
        try:
            angle_deg = float(params.get("angle_deg", 0.0))
            # 合理的角度范围检查
            return -90.0 <= angle_deg <= 90.0
        except (ValueError, TypeError):
            return False
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """检查倾斜变换是否启用"""
        if not params.get("enabled", False):
            return False
        angle_deg = float(params.get("angle_deg", 0.0))
        return abs(angle_deg) > 1e-6
