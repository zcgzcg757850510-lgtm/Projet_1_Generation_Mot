"""
变换管理器

统一管理和协调各种变换模块的执行，提供变换流水线功能。
"""

from typing import List, Dict, Any, Optional
from .base_transform import BaseTransform
from .move_transform import MoveTransform
from .tilt_transform import TiltTransform
from .scale_transform import ScaleTransform
from .smooth_transform import SmoothTransform
from ..centerline import Point


class TransformManager:
    """变换管理器，负责协调各种变换的执行"""
    
    def __init__(self):
        # 注册所有变换模块
        self.transforms = {
            "move": MoveTransform(),
            "tilt": TiltTransform(),
            "scale": ScaleTransform(),
            "chaikin_smooth": SmoothTransform(),
            "moving_average_smooth": SmoothTransform()
        }
        
        # 默认变换执行顺序（将平滑放到最后，避免影响其他属性）
        self.default_order = [
            "move",
            "tilt",
            "scale",
            "chaikin_smooth",
            "moving_average_smooth"
        ]
    
    def apply_transforms(self, points: List[Point], config: Dict[str, Any], 
                        order: Optional[List[str]] = None) -> List[Point]:
        """
        按指定顺序应用变换
        
        Args:
            points: 输入点序列
            config: 变换配置字典
            order: 变换执行顺序，None使用默认顺序
            
        Returns:
            变换后的点序列
        """
        if not points:
            return points
            
        result = list(points)
        execution_order = order or self.default_order
        
        for transform_name in execution_order:
            if transform_name in self.transforms and transform_name in config:
                transform = self.transforms[transform_name]
                params = config[transform_name]
                
                if transform.is_enabled(params):
                    result = transform.apply(result, params)
        
        return result
    
    def apply_single_transform(self, points: List[Point], transform_name: str, 
                              params: Dict[str, Any]) -> List[Point]:
        """
        应用单个变换
        
        Args:
            points: 输入点序列
            transform_name: 变换名称
            params: 变换参数
            
        Returns:
            变换后的点序列
        """
        if transform_name not in self.transforms:
            return points
            
        transform = self.transforms[transform_name]
        return transform.apply(points, params)
    
    def get_transform_defaults(self, transform_name: str) -> Dict[str, Any]:
        """获取指定变换的默认参数"""
        if transform_name in self.transforms:
            return self.transforms[transform_name].get_default_params()
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证变换配置的有效性"""
        for transform_name, params in config.items():
            if transform_name in self.transforms:
                transform = self.transforms[transform_name]
                if not transform.validate_params(params):
                    return False
        return True
    
    def register_transform(self, name: str, transform: BaseTransform):
        """注册新的变换模块"""
        self.transforms[name] = transform
    
    def get_available_transforms(self) -> List[str]:
        """获取所有可用的变换名称"""
        return list(self.transforms.keys())
