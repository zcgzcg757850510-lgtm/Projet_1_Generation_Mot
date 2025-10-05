"""
移动变换模块

实现笔画的平移变换，支持水平和垂直方向的移动。
"""

from typing import List, Dict, Any
from .base_transform import BaseTransform
from ..centerline import Point


class MoveTransform(BaseTransform):
    """移动变换实现"""
    
    def __init__(self):
        super().__init__("move")
    
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """
        应用移动变换
        
        Args:
            points: 输入点序列
            params: 移动参数 {"dx": 水平偏移, "dy": 垂直偏移}
            
        Returns:
            移动后的点序列
        """
        if not self.is_enabled(params):
            return points
            
        dx = float(params.get("dx", 0.0))
        dy = float(params.get("dy", 0.0))
        
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return points
            
        result = []
        for x, y in points:
            result.append((x + dx, y + dy))
        return result
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认移动参数"""
        return {
            "dx": 0.0,
            "dy": 0.0,
            "enabled": False
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证移动参数"""
        try:
            dx = float(params.get("dx", 0.0))
            dy = float(params.get("dy", 0.0))
            # 合理的移动范围检查
            return -100.0 <= dx <= 100.0 and -100.0 <= dy <= 100.0
        except (ValueError, TypeError):
            return False
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """检查移动变换是否启用"""
        if not params.get("enabled", False):
            return False
        dx = float(params.get("dx", 0.0))
        dy = float(params.get("dy", 0.0))
        return abs(dx) > 1e-6 or abs(dy) > 1e-6
