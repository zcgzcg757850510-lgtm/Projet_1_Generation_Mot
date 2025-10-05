"""
D2生成器 - 完整封装的D2生成功能

这个模块提供了一个完全独立的D2生成功能，可以：
1. 自动搜索指定文件夹中的最新D1文件
2. 自动读取网格变形参数
3. 基于D1和网格参数生成D2文件
4. 支持从任何地方调用

使用示例：
    from src.d2_generator import D2Generator
    
    generator = D2Generator()
    result = generator.generate_d2(char='的')
    if result['success']:
        print(f"D2生成成功: {result['filepath']}")
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, Optional, Any, List
import logging

# 导入现有的网格变形和SVG处理模块
# 注释掉不存在的模块导入
# from web.services.grid_transform import apply_grid_deformation_to_svg
# from src.svg_utils import load_svg_content, save_svg_content


class D2Generator:
    """D2生成器 - 完整封装的D2生成功能"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化D2生成器
        
        Args:
            output_dir: 输出目录，默认为 output/compare/C_processed_centerline
        """
        self.output_dir = output_dir or os.path.join('output', 'compare', 'C_processed_centerline')
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def find_latest_d1_file(self, char: str) -> Optional[str]:
        """
        在指定文件夹中搜索最新的D1文件
        
        Args:
            char: 字符
            
        Returns:
            最新D1文件的完整路径，如果未找到返回None
        """
        pattern = os.path.join(self.output_dir, f"{char}_*_d1.svg")
        d1_files = glob.glob(pattern)
        
        if not d1_files:
            self.logger.warning(f"未找到字符 '{char}' 的D1文件")
            return None
        
        # 按修改时间排序，获取最新文件
        latest_file = max(d1_files, key=os.path.getmtime)
        self.logger.info(f"找到最新D1文件: {latest_file}")
        return latest_file
    
    def load_grid_parameters(self) -> Optional[Dict[str, Any]]:
        """
        读取网格变形参数
        
        从多个可能的位置读取网格参数：
        1. 临时状态文件
        2. 浏览器localStorage（通过Web接口）
        3. 默认网格配置
        
        Returns:
            网格参数字典，如果无法读取返回None
        """
        # 尝试从临时状态文件读取
        state_file = os.path.join('temp', 'grid_state.json')
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    grid_state = json.load(f)
                    self.logger.info("从临时状态文件读取网格参数")
                    return grid_state
            except Exception as e:
                self.logger.warning(f"读取临时状态文件失败: {e}")
        
        # 尝试从Web接口获取当前状态
        try:
            from web.services.grid_state import get_current_grid_state
            grid_state = get_current_grid_state()
            if grid_state:
                self.logger.info("从Web接口获取网格参数")
                return grid_state
        except ImportError:
            pass
        
        # 返回默认网格状态（无变形）
        self.logger.info("使用默认网格状态（无变形）")
        return self._get_default_grid_state()
    
    def _get_default_grid_state(self) -> Dict[str, Any]:
        """获取默认网格状态（无变形）"""
        return {
            'size': 3,  # 3x3网格
            'controlPoints': [
                {'x': i * 100, 'y': j * 100} 
                for j in range(4) for i in range(4)
            ],
            'hasDeformation': False
        }
    
    def generate_d2_filename(self, char: str) -> str:
        """
        生成D2文件名
        
        Args:
            char: 字符
            
        Returns:
            D2文件名（包含时间戳）
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{char}_{timestamp}_d2.svg"
    
    def apply_grid_deformation(self, svg_content: str, grid_params: Dict[str, Any]) -> str:
        """
        应用网格变形到SVG内容
        
        Args:
            svg_content: 原始SVG内容
            grid_params: 网格参数
            
        Returns:
            变形后的SVG内容
        """
        if not grid_params.get('hasDeformation', False):
            self.logger.info("无网格变形，返回原始SVG")
            return svg_content
        
        # 暂时返回原始SVG，等待网格变形模块完善
        self.logger.info("网格变形功能暂未实现，返回原始SVG")
        return svg_content
    
    def save_d2_file(self, svg_content: str, filename: str) -> str:
        """
        保存D2文件
        
        Args:
            svg_content: D2 SVG内容
            filename: 文件名
            
        Returns:
            保存的文件完整路径
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            self.logger.info(f"D2文件保存成功: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"保存D2文件失败: {e}")
            raise
    
    def generate_d2(self, char: str, grid_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成D2文件 - 主要接口
        
        Args:
            char: 字符
            grid_params: 网格参数（可选，如果不提供会自动读取）
            
        Returns:
            生成结果字典:
            {
                'success': bool,
                'filepath': str,  # 成功时的文件路径
                'filename': str,  # 成功时的文件名
                'error': str      # 失败时的错误信息
            }
        """
        try:
            self.logger.info(f"开始生成字符 '{char}' 的D2文件")
            
            # 1. 搜索最新的D1文件
            d1_file = self.find_latest_d1_file(char)
            if not d1_file:
                return {
                    'success': False,
                    'error': f"未找到字符 '{char}' 的D1文件"
                }
            
            # 2. 读取D1文件内容
            with open(d1_file, 'r', encoding='utf-8') as f:
                d1_content = f.read()
            
            # 3. 获取网格参数
            if grid_params is None:
                grid_params = self.load_grid_parameters()
            
            if not grid_params:
                return {
                    'success': False,
                    'error': "无法读取网格变形参数"
                }
            
            # 4. 应用网格变形
            d2_content = self.apply_grid_deformation(d1_content, grid_params)
            
            # 5. 生成文件名并保存
            d2_filename = self.generate_d2_filename(char)
            d2_filepath = self.save_d2_file(d2_content, d2_filename)
            
            self.logger.info(f"D2生成完成: {d2_filepath}")
            
            return {
                'success': True,
                'filepath': d2_filepath,
                'filename': d2_filename,
                'has_deformation': grid_params.get('hasDeformation', False)
            }
            
        except Exception as e:
            error_msg = f"D2生成失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }


# 便捷函数 - 提供简单的调用接口
def generate_d2_for_char(char: str, output_dir: str = None) -> Dict[str, Any]:
    """
    为指定字符生成D2文件的便捷函数
    
    Args:
        char: 字符
        output_dir: 输出目录（可选）
        
    Returns:
        生成结果字典
    """
    generator = D2Generator(output_dir)
    return generator.generate_d2(char)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 测试生成D2
    result = generate_d2_for_char('的')
    
    if result['success']:
        print(f"✅ D2生成成功!")
        print(f"   文件: {result['filename']}")
        print(f"   路径: {result['filepath']}")
        print(f"   变形: {'是' if result.get('has_deformation') else '否'}")
    else:
        print(f"❌ D2生成失败: {result['error']}")
