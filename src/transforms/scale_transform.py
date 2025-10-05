"""
缩放变换模块

实现笔画的缩放变换，支持围绕指定中心点的等比或非等比缩放。
"""

from typing import List, Dict, Any, Tuple
from .base_transform import BaseTransform
from ..centerline import Point


class ScaleTransform(BaseTransform):
    """缩放变换实现"""
    
    def __init__(self):
        super().__init__("scale")
    
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """
        应用缩放变换
        
        Args:
            points: 输入点序列
            params: 缩放参数 {"factor_x": X缩放, "factor_y": Y缩放, "center": 缩放中心}
            
        Returns:
            缩放后的点序列
        """
        if not self.is_enabled(params):
            return points
            
        factor_x = float(params.get("factor_x", 1.0))
        factor_y = float(params.get("factor_y", factor_x))  # 默认等比缩放
        
        if abs(factor_x - 1.0) < 1e-6 and abs(factor_y - 1.0) < 1e-6:
            return points
            
        # 计算缩放中心
        center = params.get("center")
        if center is None:
            center = self._calculate_bbox_center(points)
        
        # 执行缩放
        return self._scale_points(points, factor_x, factor_y, center)
    
    def _calculate_bbox_center(self, points: List[Point]) -> Tuple[float, float]:
        """计算点序列的边界框中心"""
        if not points:
            return (0.0, 0.0)
            
        xs = [x for x, y in points]
        ys = [y for x, y in points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
    
    def _scale_points(self, points: List[Point], factor_x: float, factor_y: float, center: Tuple[float, float]) -> List[Point]:
        """围绕中心点缩放点序列"""
        cx, cy = center
        
        result = []
        for x, y in points:
            # 平移到原点
            dx = x - cx
            dy = y - cy
            
            # 缩放
            new_x = dx * factor_x
            new_y = dy * factor_y
            
            # 平移回去
            result.append((new_x + cx, new_y + cy))
        
        return result
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认缩放参数"""
        return {
            "factor_x": 1.0,
            "factor_y": 1.0,
            "center": None,  # None表示自动计算边界框中心
            "enabled": False
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证缩放参数"""
        try:
            factor_x = float(params.get("factor_x", 1.0))
            factor_y = float(params.get("factor_y", 1.0))
            # 合理的缩放范围检查
            return 0.1 <= factor_x <= 10.0 and 0.1 <= factor_y <= 10.0
        except (ValueError, TypeError):
            return False
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """检查缩放变换是否启用"""
        if not params.get("enabled", False):
            return False
        factor_x = float(params.get("factor_x", 1.0))
        factor_y = float(params.get("factor_y", 1.0))
        return abs(factor_x - 1.0) > 1e-6 or abs(factor_y - 1.0) > 1e-6
