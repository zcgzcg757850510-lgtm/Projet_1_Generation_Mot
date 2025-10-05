#!/usr/bin/env python3
"""
改进的手动标点符号生成器
特点：
1. 手工精确设计每个标点符号
2. 可视化预览功能
3. 质量验证
4. 支持批量生成和单个修改
"""

import json
import os
import math
from typing import List, Tuple, Dict

class PunctuationDesigner:
    """标点符号设计器"""
    
    def __init__(self):
        self.punctuation_data = {}
        self.canvas_size = 256
        
    def create_circle(self, center_x: int, center_y: int, radius: int, points: int = 24) -> List[List[int]]:
        """创建圆形路径"""
        circle = []
        for i in range(points):
            angle = (i / points) * 2 * math.pi
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            circle.append([x, y])
        circle.append(circle[0])  # 闭合圆形
        return circle
    
    def create_dot(self, x: int, y: int, radius: int = 4) -> List[List[int]]:
        """创建圆点"""
        return self.create_circle(x, y, radius, points=12)
    
    def create_curve(self, points: List[List[int]]) -> List[List[int]]:
        """创建平滑曲线"""
        # 如果点数太少，使用贝塞尔曲线插值
        if len(points) < 5:
            return points
        
        # 简单的插值，让曲线更平滑
        smooth_points = []
        for i in range(len(points) - 1):
            smooth_points.append(points[i])
            # 在两点之间添加中间点
            mid_x = (points[i][0] + points[i+1][0]) // 2
            mid_y = (points[i][1] + points[i+1][1]) // 2
            smooth_points.append([mid_x, mid_y])
        smooth_points.append(points[-1])
        return smooth_points
    
    def design_comma(self):
        """设计逗号 "，" """
        # 逗号位置：右下角
        # 形状：短曲线，从上向下右弯
        points = [
            [220, 208],  # 起点
            [222, 212],
            [224, 216],
            [225, 220],
            [225, 224],
            [224, 228],
            [222, 231],
            [220, 233],
            [217, 235],
            [214, 236]   # 终点
        ]
        self.punctuation_data["，"] = {
            "character": "，",
            "medians": [points],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "bottom_right"
        }
    
    def design_period(self):
        """设计句号 "。" """
        # 句号位置：右下角
        # 形状：小圆点
        self.punctuation_data["。"] = {
            "character": "。",
            "medians": [self.create_circle(220, 220, 6, points=20)],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "bottom_right"
        }
    
    def design_pause_mark(self):
        """设计顿号 "、" """
        # 顿号：短斜线
        points = [
            [205, 215],
            [210, 220],
            [215, 225],
            [220, 230],
            [224, 234]
        ]
        self.punctuation_data["、"] = {
            "character": "、",
            "medians": [points],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "bottom_right"
        }
    
    def design_semicolon(self):
        """设计分号 "；" """
        # 上面的点
        top_dot = self.create_dot(220, 150, radius=4)
        
        # 下面的逗号
        bottom_comma = [
            [220, 185],
            [222, 189],
            [223, 193],
            [223, 197],
            [222, 201],
            [220, 204],
            [218, 206],
            [215, 207]
        ]
        
        self.punctuation_data["；"] = {
            "character": "；",
            "medians": [top_dot, bottom_comma],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "right_center"
        }
    
    def design_colon(self):
        """设计冒号 "：" """
        # 上点和下点
        top_dot = self.create_dot(220, 140, radius=4)
        bottom_dot = self.create_dot(220, 170, radius=4)
        
        self.punctuation_data["："] = {
            "character": "：",
            "medians": [top_dot, bottom_dot],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "right_center"
        }
    
    def design_exclamation(self):
        """设计感叹号 "！" """
        # 竖线
        line = [
            [128, 85],
            [128, 95],
            [128, 105],
            [128, 115],
            [128, 125],
            [128, 135],
            [128, 145],
            [128, 155]
        ]
        
        # 下面的点
        dot = self.create_dot(128, 173, radius=5)
        
        self.punctuation_data["！"] = {
            "character": "！",
            "medians": [line, dot],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_question(self):
        """设计问号 "？" """
        # 问号主体 - 手工设计的优美曲线
        curve = [
            [98, 115],   # 左上起点
            [105, 103],  # 向右上
            [115, 97],
            [125, 95],
            [135, 97],
            [143, 103],  # 到右上
            [147, 112],
            [148, 122],  # 开始向下
            [145, 130],
            [138, 137],
            [130, 142],
            [128, 147],
            [128, 155]   # 结束
        ]
        
        # 下面的点
        dot = self.create_dot(128, 173, radius=5)
        
        self.punctuation_data["？"] = {
            "character": "？",
            "medians": [curve, dot],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_quotation_marks(self):
        """设计引号"""
        # 左双引号 "
        left_outer = [[92, 88], [89, 93], [88, 98], [88, 102]]
        left_inner = [[107, 88], [104, 93], [103, 98], [103, 102]]
        
        char_left = '"'  # U+201C 左双引号
        self.punctuation_data[char_left] = {
            "character": char_left,
            "medians": [left_outer, left_inner],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "top_left"
        }
        
        # 右双引号 "
        right_outer = [[92, 107], [89, 102], [88, 97], [88, 93]]
        right_inner = [[107, 107], [104, 102], [103, 97], [103, 93]]
        
        char_right = '"'  # U+201D 右双引号
        self.punctuation_data[char_right] = {
            "character": char_right,
            "medians": [right_outer, right_inner],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "top_left"
        }
    
    def design_parentheses(self):
        """设计括号 （）"""
        # 左括号 - 平滑弧线
        left_paren = []
        center_x, center_y = 148, 128
        radius_x, radius_y = 22, 65
        for angle in range(-85, 86, 8):
            rad = math.radians(angle)
            x = int(center_x - radius_x * math.cos(rad))
            y = int(center_y + radius_y * math.sin(rad))
            left_paren.append([x, y])
        
        self.punctuation_data["（"] = {
            "character": "（",
            "medians": [left_paren],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "center"
        }
        
        # 右括号 - 镜像
        right_paren = []
        center_x = 108
        for angle in range(-85, 86, 8):
            rad = math.radians(angle)
            x = int(center_x + radius_x * math.cos(rad))
            y = int(center_y + radius_y * math.sin(rad))
            right_paren.append([x, y])
        
        self.punctuation_data["）"] = {
            "character": "）",
            "medians": [right_paren],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_angle_brackets(self):
        """设计书名号 《》"""
        # 《 - 两个尖括号向左
        self.punctuation_data["《"] = {
            "character": "《",
            "medians": [
                [[175, 88], [138, 128], [175, 168]],  # 外层
                [[138, 88], [101, 128], [138, 168]]   # 内层
            ],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
        
        # 》 - 两个尖括号向右
        self.punctuation_data["》"] = {
            "character": "》",
            "medians": [
                [[81, 88], [118, 128], [81, 168]],    # 外层
                [[118, 88], [155, 128], [118, 168]]   # 内层
            ],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_square_brackets(self):
        """设计方括号 【】"""
        # 【 - 左方括号
        self.punctuation_data["【"] = {
            "character": "【",
            "medians": [
                [[168, 68], [168, 188]],  # 右竖线
                [[168, 68], [138, 68], [138, 188], [168, 188]]  # 左边框
            ],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
        
        # 】 - 右方括号
        self.punctuation_data["】"] = {
            "character": "】",
            "medians": [
                [[88, 68], [88, 188]],  # 左竖线
                [[88, 68], [118, 68], [118, 188], [88, 188]]  # 右边框
            ],
            "strokes": 2,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_ellipsis(self):
        """设计省略号 …"""
        # 6个圆点，均匀分布
        dots = []
        y = 218
        radius = 3
        x_positions = [75, 103, 131, 159, 187, 215]
        
        for x_center in x_positions:
            dot = self.create_circle(x_center, y, radius, points=10)
            dots.append(dot)
        
        self.punctuation_data["…"] = {
            "character": "…",
            "medians": dots,
            "strokes": 6,
            "source": "manual_design_improved",
            "position": "bottom_center"
        }
    
    def design_dash(self):
        """设计破折号 ——"""
        # 长横线，占据大部分宽度
        # 添加轻微的厚度以提高渲染质量
        self.punctuation_data["——"] = {
            "character": "——",
            "medians": [
                [[55, 126], [75, 127], [100, 128], [125, 128], 
                 [150, 128], [175, 129], [201, 130]]
            ],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "center"
        }
    
    def design_english_comma(self):
        """设计英文逗号 ,"""
        # 扩大宽度，使其更明显
        points = [
            [124, 190],
            [126, 193],
            [128, 196],
            [130, 199],
            [131, 202],
            [131, 205],
            [130, 208],
            [128, 210],
            [125, 212]
        ]
        self.punctuation_data[","] = {
            "character": ",",
            "medians": [points],
            "strokes": 1,
            "source": "manual_design_improved",
            "position": "bottom_center"
        }
    
    def design_all(self):
        """设计所有标点符号"""
        print("正在手工设计标点符号...")
        
        self.design_comma()           # ，
        self.design_period()          # 。
        self.design_pause_mark()      # 、
        self.design_semicolon()       # ；
        self.design_colon()           # ：
        self.design_exclamation()     # ！
        self.design_question()        # ？
        self.design_quotation_marks() # ""
        self.design_parentheses()     # （）
        self.design_angle_brackets()  # 《》
        self.design_square_brackets() # 【】
        self.design_ellipsis()        # …
        self.design_dash()            # ——
        self.design_english_comma()   # ,
        
        print(f"✅ 完成设计 {len(self.punctuation_data)} 个标点符号")
    
    def validate(self) -> List[str]:
        """验证数据质量"""
        issues = []
        
        for char, data in self.punctuation_data.items():
            # 检查必需字段
            if 'medians' not in data:
                issues.append(f"{char}: 缺少 medians 字段")
                continue
            
            # 检查坐标范围
            for stroke_idx, stroke in enumerate(data['medians']):
                for point_idx, point in enumerate(stroke):
                    if len(point) != 2:
                        issues.append(f"{char}: 笔画 {stroke_idx} 点 {point_idx} 格式错误")
                        continue
                    
                    x, y = point
                    if not (0 <= x <= self.canvas_size):
                        issues.append(f"{char}: 笔画 {stroke_idx} 点 {point_idx} X坐标越界 ({x})")
                    if not (0 <= y <= self.canvas_size):
                        issues.append(f"{char}: 笔画 {stroke_idx} 点 {point_idx} Y坐标越界 ({y})")
            
            # 检查笔画数
            if len(data['medians']) != data.get('strokes', 0):
                issues.append(f"{char}: 笔画数不匹配 (实际 {len(data['medians'])} vs 声明 {data.get('strokes', 0)})")
        
        return issues
    
    def save(self, output_path: str = 'data/punctuation_medians.json'):
        """保存数据"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.punctuation_data, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        return output_path, file_size
    
    def generate_preview_svg(self, char: str) -> str:
        """生成单个标点符号的预览SVG"""
        if char not in self.punctuation_data:
            return ""
        
        data = self.punctuation_data[char]
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">',
            '<rect width="256" height="256" fill="white"/>',
            '<rect width="256" height="256" fill="none" stroke="#e0e0e0" stroke-width="1"/>'
        ]
        
        # 绘制网格（辅助）
        for i in range(0, 257, 32):
            svg_parts.append(f'<line x1="{i}" y1="0" x2="{i}" y2="256" stroke="#f0f0f0" stroke-width="0.5"/>')
            svg_parts.append(f'<line x1="0" y1="{i}" x2="256" y2="{i}" stroke="#f0f0f0" stroke-width="0.5"/>')
        
        # 绘制标点符号
        colors = ['#ff0000', '#0000ff', '#00aa00', '#ff8800', '#aa00aa', '#00aaaa']
        for stroke_idx, stroke in enumerate(data['medians']):
            if not stroke:
                continue
            
            color = colors[stroke_idx % len(colors)]
            path_d = f"M {stroke[0][0]},{stroke[0][1]}"
            for point in stroke[1:]:
                path_d += f" L {point[0]},{point[1]}"
            
            svg_parts.append(
                f'<path d="{path_d}" stroke="{color}" stroke-width="2" fill="none" '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
            )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def save_preview_svgs(self, output_dir: str = 'output/punctuation_preview'):
        """保存所有预览SVG"""
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, char in enumerate(self.punctuation_data.keys()):
            svg_content = self.generate_preview_svg(char)
            # 使用索引作为文件名（避免特殊字符问题）
            # 对于多字符标点，使用第一个字符的编码
            try:
                char_code = ord(char[0]) if len(char) > 0 else idx
            except:
                char_code = idx
            
            filename = f"punct_{char_code:04x}_{idx:02d}.svg"
            filepath = os.path.join(output_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
            except (OSError, TypeError) as e:
                print(f"  ⚠️ 无法保存预览 {repr(char)}: {e}")
        
        return output_dir


def main():
    print("=" * 70)
    print("手动标点符号生成器 - 改进版")
    print("=" * 70)
    
    designer = PunctuationDesigner()
    
    # 1. 设计所有标点
    designer.design_all()
    
    # 2. 验证数据
    print("\n📋 验证数据质量...")
    issues = designer.validate()
    
    if issues:
        print(f"⚠️ 发现 {len(issues)} 个问题:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个问题")
        
        response = input("\n是否继续保存? (y/n): ")
        if response.lower() != 'y':
            print("取消保存")
            return 1
    else:
        print("✅ 数据验证通过!")
    
    # 3. 保存数据
    print("\n💾 保存标点符号数据...")
    output_path, file_size = designer.save()
    print(f"✅ 已保存到: {output_path}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 4. 生成预览
    print("\n🎨 生成预览SVG...")
    preview_dir = designer.save_preview_svgs()
    print(f"✅ 预览已保存到: {preview_dir}")
    
    # 5. 统计信息
    print("\n" + "=" * 70)
    print("📊 统计信息:")
    print("-" * 70)
    print(f"{'标点':<8} {'笔画数':<10} {'总点数':<10} {'位置':<15}")
    print("-" * 70)
    
    for char, data in sorted(designer.punctuation_data.items()):
        strokes = data['strokes']
        total_points = sum(len(stroke) for stroke in data['medians'])
        position = data.get('position', 'unknown')
        print(f"{char:<8} {strokes:<10} {total_points:<10} {position:<15}")
    
    print("-" * 70)
    print(f"总计: {len(designer.punctuation_data)} 个标点符号")
    print("=" * 70)
    
    # 6. 下一步提示
    print("\n📝 下一步:")
    print("  1. 查看预览: 打开 output/punctuation_preview/ 目录")
    print("  2. 重启服务器: python start_server.py")
    print("  3. 测试标点: 在文章生成中使用标点符号")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

