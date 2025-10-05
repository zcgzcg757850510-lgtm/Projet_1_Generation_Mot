"""
字母数字数据加载器

功能：
1. 加载字母和数字的 medians 数据
2. 将字母数字数据与汉字数据合并
3. 提供独立的开关控制是否启用

设计原则：
- 模块化：不修改现有代码
- 可选性：可以通过配置开关启用/禁用
- 兼容性：与现有汉字数据格式完全兼容
"""

import os
import json
from typing import Dict, Any, Optional


class AlphanumericLoader:
    """字母数字数据加载器"""
    
    def __init__(self, data_path: str = None):
        """
        初始化加载器
        
        Args:
            data_path: 字母数字数据文件路径，默认为 data/alphanumeric_medians.json
        """
        if data_path is None:
            data_path = os.path.join('data', 'alphanumeric_medians.json')
        
        self.data_path = data_path
        self._cache = None
        self._enabled = True  # 默认启用
    
    def is_enabled(self) -> bool:
        """检查字母数字系统是否启用"""
        return self._enabled
    
    def set_enabled(self, enabled: bool):
        """设置字母数字系统的启用状态"""
        self._enabled = enabled
        print(f"[ALPHANUMERIC] 字母数字系统: {'启用' if enabled else '禁用'}")
    
    def load(self) -> Dict[str, Any]:
        """
        加载字母数字数据
        
        Returns:
            字母数字数据字典 {char: {character, medians, strokes, type, source}}
        """
        if not self._enabled:
            return {}
        
        # 使用缓存
        if self._cache is not None:
            return self._cache
        
        try:
            if not os.path.exists(self.data_path):
                print(f"[ALPHANUMERIC] ⚠️ 未找到字母数字数据: {self.data_path}")
                self._cache = {}
                return {}
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache = data
            print(f"[ALPHANUMERIC] ✅ 加载了 {len(data)} 个字母和数字")
            
            # 统计类型
            types = {}
            for char, char_data in data.items():
                char_type = char_data.get('type', 'unknown')
                types[char_type] = types.get(char_type, 0) + 1
            
            type_info = ', '.join([f"{t}:{c}" for t, c in sorted(types.items())])
            print(f"[ALPHANUMERIC] 类型分布: {type_info}")
            
            return data
            
        except Exception as e:
            print(f"[ALPHANUMERIC] ❌ 加载失败: {e}")
            self._cache = {}
            return {}
    
    def is_alphanumeric(self, char: str) -> bool:
        """
        判断字符是否为字母或数字
        
        Args:
            char: 要判断的字符
        
        Returns:
            是否为字母或数字
        """
        if not self._enabled:
            return False
        
        data = self.load()
        return char in data
    
    def get(self, char: str) -> Optional[Dict[str, Any]]:
        """
        获取字母数字的数据
        
        Args:
            char: 字母或数字字符
        
        Returns:
            字母数字数据，如果不存在返回 None
        """
        if not self._enabled:
            return None
        
        data = self.load()
        return data.get(char)
    
    def merge_with_hanzi(self, hanzi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将字母数字数据与汉字数据合并
        
        Args:
            hanzi_data: 汉字数据字典
        
        Returns:
            合并后的数据字典（汉字 + 字母数字）
        """
        if not self._enabled:
            return hanzi_data
        
        alphanumeric_data = self.load()
        
        # 合并数据，汉字优先（如果有冲突，保留汉字）
        merged = dict(hanzi_data)
        
        for char, data in alphanumeric_data.items():
            if char not in merged:
                merged[char] = data
        
        added_count = len(merged) - len(hanzi_data)
        if added_count > 0:
            print(f"[ALPHANUMERIC] ✅ 添加了 {added_count} 个字母数字到字符库")
        
        return merged


# 全局实例
_alphanumeric_loader = AlphanumericLoader()


def get_alphanumeric_loader() -> AlphanumericLoader:
    """获取全局字母数字加载器实例"""
    return _alphanumeric_loader


def is_alphanumeric_enabled() -> bool:
    """检查字母数字系统是否启用"""
    return _alphanumeric_loader.is_enabled()


def set_alphanumeric_enabled(enabled: bool):
    """设置字母数字系统的启用状态"""
    _alphanumeric_loader.set_enabled(enabled)


def load_alphanumeric_data() -> Dict[str, Any]:
    """加载字母数字数据（便捷函数）"""
    return _alphanumeric_loader.load()


def merge_alphanumeric_with_hanzi(hanzi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将字母数字数据与汉字数据合并（便捷函数）
    
    这是主要的集成点！在现有代码中调用这个函数即可
    """
    return _alphanumeric_loader.merge_with_hanzi(hanzi_data)


# 配置项（可以通过环境变量或配置文件控制）
ALPHANUMERIC_ENABLED = os.getenv('ALPHANUMERIC_ENABLED', 'true').lower() == 'true'

# 应用配置
if not ALPHANUMERIC_ENABLED:
    set_alphanumeric_enabled(False)

