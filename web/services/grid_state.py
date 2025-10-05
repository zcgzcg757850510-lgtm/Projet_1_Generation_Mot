"""
网格状态管理模块

提供网格变形状态的保存、读取和管理功能，
支持与前端JavaScript的GridStateManager同步。
"""

import os
import json
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime


class GridStateManager:
    """网格状态管理器"""
    
    def __init__(self, state_file: str = None):
        """
        初始化网格状态管理器
        
        Args:
            state_file: 状态文件路径，默认使用项目output/temp目录
        """
        if state_file is None:
            # 修改：使用项目的output/temp目录，与前端保存位置一致
            temp_dir = os.path.join('output', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            state_file = os.path.join(temp_dir, 'grid_state.json')
        
        self.state_file = state_file
    
    def save_state(self, grid_state: Dict[str, Any]) -> bool:
        """
        保存网格状态到文件
        
        Args:
            grid_state: 网格状态字典
            
        Returns:
            保存是否成功
        """
        try:
            # 添加时间戳
            grid_state['timestamp'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(grid_state, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存网格状态失败: {e}")
            return False
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        从文件加载网格状态
        
        Returns:
            网格状态字典，如果加载失败返回None
        """
        try:
            if not os.path.exists(self.state_file):
                return None
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载网格状态失败: {e}")
            return None
    
    def has_deformation(self) -> bool:
        """
        检查是否存在网格变形
        
        Returns:
            是否存在变形
        """
        state = self.load_state()
        if not state:
            return False
        
        return state.get('hasDeformation', False)
    
    def get_grid_size(self) -> int:
        """
        获取网格大小
        
        Returns:
            网格大小（默认3表示3x3网格）
        """
        state = self.load_state()
        if not state:
            return 3
        
        return state.get('size', 3)
    
    def clear_state(self) -> bool:
        """
        清除网格状态
        
        Returns:
            清除是否成功
        """
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            return True
        except Exception as e:
            print(f"清除网格状态失败: {e}")
            return False


# 全局实例
_global_state_manager = GridStateManager()


def save_grid_state(grid_state: Dict[str, Any]) -> bool:
    """保存网格状态的便捷函数"""
    return _global_state_manager.save_state(grid_state)


def load_grid_state() -> Optional[Dict[str, Any]]:
    """加载并拆解保存的网格状态"""
    raw = _global_state_manager.load_state()
    if not raw:
        return None
    # 兼容旧格式：可能顶层直接就是grid_state
    if 'grid_state' in raw:
        state = dict(raw['grid_state'] or {})
        # 合并辅助信息
        for key in ('canvas_dimensions', 'char', 'deformStrength', 'hasDeformation'):
            if key in raw and key not in state:
                state[key] = raw[key]
        return state
    return dict(raw)


def has_grid_deformation() -> bool:
    """检查是否存在网格变形的便捷函数"""
    state = load_grid_state()
    if not state:
        return False
    if state.get('hasDeformation'):
        return True
    cps = state.get('controlPoints') or []
    for p in cps:
        dx = abs(p.get('x', 0) - p.get('originalX', p.get('x', 0)))
        dy = abs(p.get('y', 0) - p.get('originalY', p.get('y', 0)))
        if dx > 0.1 or dy > 0.1:
            return True
    return False


def get_current_grid_state() -> Optional[Dict[str, Any]]:
    """获取当前网格状态的便捷函数"""
    return load_grid_state()


def clear_grid_state() -> bool:
    """清除网格状态的便捷函数"""
    return _global_state_manager.clear_state()
