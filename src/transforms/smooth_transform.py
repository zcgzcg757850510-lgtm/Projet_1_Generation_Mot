"""
平滑变换模块

实现笔画的平滑变换，包括Chaikin平滑和移动平均平滑。
"""

from typing import List, Dict, Any
from .base_transform import BaseTransform
from ..centerline import Point, length_preserving_chaikin
from ..centerline import _length as _poly_length  # type: ignore
from ..centerline import _length_preserving_adjust  # type: ignore


class SmoothTransform(BaseTransform):
    """平滑变换实现"""
    
    def __init__(self):
        super().__init__("smooth")
    
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """
        应用平滑变换
        
        Args:
            points: 输入点序列
            params: 平滑参数 {"method": "chaikin"|"moving_average", "iterations": 次数, "window": 窗口大小}
            
        Returns:
            平滑后的点序列
        """
        if not self.is_enabled(params):
            return points
            
        method = params.get("method", "chaikin")
        
        if method == "chaikin":
            return self._apply_chaikin_smooth(points, params)
        elif method == "moving_average":
            return self._apply_moving_average_smooth(points, params)
        else:
            return points
    
    def _apply_chaikin_smooth(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """应用Chaikin平滑算法（长度与端点保持）"""
        iterations = int(params.get("iterations", 1))
        if iterations <= 0:
            return points
        # 使用中心线模块的长度保持实现
        return length_preserving_chaikin(points, iterations)
    
    def _apply_moving_average_smooth(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """应用移动平均平滑算法（端点固定+长度保持）"""
        window = int(params.get("window", 3))
        if window <= 1 or len(points) < window:
            return points
            
        result = []
        half_window = window // 2
        
        for i in range(len(points)):
            # 计算窗口范围
            start = max(0, i - half_window)
            end = min(len(points), i + half_window + 1)
            
            # 计算平均值
            sum_x = sum(x for x, y in points[start:end])
            sum_y = sum(y for x, y in points[start:end])
            count = end - start
            
            avg_x = sum_x / count
            avg_y = sum_y / count
            
            result.append((avg_x, avg_y))
        # 固定端点
        if result:
            result[0] = points[0]
            result[-1] = points[-1]
        # 长度保持调整
        L0 = _poly_length(points)
        return _length_preserving_adjust(result, points[0], points[-1], L0)
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认平滑参数"""
        return {
            "method": "chaikin",
            "iterations": 1,
            "window": 3,
            "enabled": False
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证平滑参数"""
        try:
            method = params.get("method", "chaikin")
            if method not in ["chaikin", "moving_average"]:
                return False
                
            if method == "chaikin":
                iterations = int(params.get("iterations", 1))
                return 0 <= iterations <= 10
            elif method == "moving_average":
                window = int(params.get("window", 3))
                return 1 <= window <= 21 and window % 2 == 1  # 奇数窗口
                
        except (ValueError, TypeError):
            return False
        
        return True
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """检查平滑变换是否启用"""
        if not params.get("enabled", False):
            return False
            
        method = params.get("method", "chaikin")
        if method == "chaikin":
            iterations = int(params.get("iterations", 1))
            return iterations > 0
        elif method == "moving_average":
            window = int(params.get("window", 3))
            return window > 1
            
        return False
