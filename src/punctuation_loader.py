"""
标点符号数据加载器

功能：
1. 加载标点符号的 medians 数据
2. 将标点符号数据与汉字数据合并
3. 提供独立的开关控制是否启用标点符号

设计原则：
- 模块化：不修改现有代码
- 可选性：可以通过配置开关启用/禁用
- 兼容性：与现有汉字数据格式完全兼容
"""

import os
import json
from typing import Dict, Any, Optional


class PunctuationLoader:
    """标点符号数据加载器"""
    
    def __init__(self, data_path: str = None):
        """
        初始化加载器
        
        Args:
            data_path: 标点符号数据文件路径，默认为 data/punctuation_medians.json
        """
        if data_path is None:
            data_path = os.path.join('data', 'punctuation_medians.json')
        
        self.data_path = data_path
        self._cache = None
        self._enabled = True  # 默认启用
    
    def is_enabled(self) -> bool:
        """检查标点符号系统是否启用"""
        return self._enabled
    
    def set_enabled(self, enabled: bool):
        """设置标点符号系统的启用状态"""
        self._enabled = enabled
        print(f"[PUNCTUATION] 标点符号系统: {'启用' if enabled else '禁用'}")
    
    def load(self) -> Dict[str, Any]:
        """
        加载标点符号数据
        
        Returns:
            标点符号数据字典 {char: {character, medians, strokes, source}}
        """
        if not self._enabled:
            return {}
        
        # 使用缓存
        if self._cache is not None:
            return self._cache
        
        try:
            if not os.path.exists(self.data_path):
                print(f"[PUNCTUATION] ⚠️ 未找到标点符号数据: {self.data_path}")
                self._cache = {}
                return {}
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache = data
            print(f"[PUNCTUATION] ✅ 加载了 {len(data)} 个标点符号")
            
            return data
            
        except Exception as e:
            print(f"[PUNCTUATION] ❌ 加载失败: {e}")
            self._cache = {}
            return {}
    
    def is_punctuation(self, char: str) -> bool:
        """
        判断字符是否为标点符号
        
        Args:
            char: 要判断的字符
        
        Returns:
            是否为标点符号
        """
        if not self._enabled:
            return False
        
        data = self.load()
        return char in data
    
    def get(self, char: str) -> Optional[Dict[str, Any]]:
        """
        获取标点符号的数据
        
        Args:
            char: 标点符号字符
        
        Returns:
            标点符号数据，如果不存在返回 None
        """
        if not self._enabled:
            return None
        
        data = self.load()
        return data.get(char)
    
    def merge_with_hanzi(self, hanzi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将标点符号数据与汉字数据合并
        
        Args:
            hanzi_data: 汉字数据字典
        
        Returns:
            合并后的数据字典（汉字 + 标点）
        """
        if not self._enabled:
            return hanzi_data
        
        punctuation_data = self.load()
        
        # 合并数据，汉字优先（如果有冲突，保留汉字）
        merged = dict(hanzi_data)
        
        for char, data in punctuation_data.items():
            if char not in merged:
                merged[char] = data
        
        added_count = len(merged) - len(hanzi_data)
        if added_count > 0:
            print(f"[PUNCTUATION] ✅ 添加了 {added_count} 个标点符号到字符库")
        
        return merged


# 全局实例
_punctuation_loader = PunctuationLoader()


def get_punctuation_loader() -> PunctuationLoader:
    """获取全局标点符号加载器实例"""
    return _punctuation_loader


def is_punctuation_enabled() -> bool:
    """检查标点符号系统是否启用"""
    return _punctuation_loader.is_enabled()


def set_punctuation_enabled(enabled: bool):
    """设置标点符号系统的启用状态"""
    _punctuation_loader.set_enabled(enabled)


def load_punctuation_data() -> Dict[str, Any]:
    """加载标点符号数据（便捷函数）"""
    return _punctuation_loader.load()


def merge_punctuation_with_hanzi(hanzi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将标点符号数据与汉字数据合并（便捷函数）
    
    这是主要的集成点！在现有代码中调用这个函数即可
    """
    return _punctuation_loader.merge_with_hanzi(hanzi_data)


# 配置项（可以通过环境变量或配置文件控制）
PUNCTUATION_ENABLED = os.getenv('PUNCTUATION_ENABLED', 'true').lower() == 'true'

# 应用配置
if not PUNCTUATION_ENABLED:
    set_punctuation_enabled(False)

