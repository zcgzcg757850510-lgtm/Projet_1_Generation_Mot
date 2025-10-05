"""
基础变换接口

定义所有变换模块的统一接口，确保一致的API和行为。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..centerline import Point


class BaseTransform(ABC):
    """变换基类，定义所有变换的统一接口"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """
        应用变换到点序列
        
        Args:
            points: 输入点序列
            params: 变换参数字典
            
        Returns:
            变换后的点序列
        """
        pass
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """
        获取默认参数
        
        Returns:
            默认参数字典
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证参数有效性
        
        Args:
            params: 待验证的参数字典
            
        Returns:
            参数是否有效
        """
        return True
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """
        检查变换是否启用
        
        Args:
            params: 参数字典
            
        Returns:
            变换是否应该执行
        """
        return True
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
