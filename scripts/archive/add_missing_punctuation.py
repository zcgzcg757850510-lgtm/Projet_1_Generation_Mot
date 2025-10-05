#!/usr/bin/env python3
"""
补充缺失的常用标点符号
在现有基础上添加更多中英文标点符号
"""

import json
import os
import math
from typing import List


class PunctuationExpander:
    """标点符号扩展器"""
    
    def __init__(self, existing_file: str = 'data/punctuation_medians.json'):
        self.existing_file = existing_file
        self.data = {}
        self.load_existing()
    
    def load_existing(self):
        """加载现有标点符号"""
        if os.path.exists(self.existing_file):
            with open(self.existing_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 已加载 {len(self.data)} 个现有标点符号")
            print(f"   现有: {''.join(sorted(self.data.keys()))}")
        else:
            print("⚠️ 未找到现有文件，将创建新文件")
    
    def create_circle(self, center_x: int, center_y: int, radius: int, points: int = 24) -> List[List[int]]:
        """创建圆形路径"""
        circle = []
        for i in range(points):
            angle = (i / points) * 2 * math.pi
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            circle.append([x, y])
        circle.append(circle[0])
        return circle
    
    def create_dot(self, x: int, y: int, radius: int = 4) -> List[List[int]]:
        """创建圆点"""
        return self.create_circle(x, y, radius, points=12)
    
    # ==================== 中文标点符号 ====================
    
    def add_single_quotes(self):
        """添加中文单引号"""
        left_single = '''  # U+2018 左单引号
        right_single = '''  # U+2019 右单引号
        
        if left_single not in self.data:
            # 左单引号 '
            self.data[left_single] = {
                "character": left_single,
                "medians": [[[107, 88], [104, 93], [103, 98], [103, 102]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "top_left"
            }
            print(f"  ✅ 添加: {left_single} (左单引号)")
        
        if right_single not in self.data:
            # 右单引号 '
            self.data[right_single] = {
                "character": right_single,
                "medians": [[[107, 107], [104, 102], [103, 97], [103, 93]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "top_left"
            }
            print(f"  ✅ 添加: {right_single} (右单引号)")
    
    def add_corner_quotes(self):
        """添加直角引号 「」『』"""
        if '「' not in self.data:
            # 左直角引号
            self.data['「'] = {
                "character": "「",
                "medians": [
                    [[168, 75], [138, 75], [138, 181]]
                ],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "left_center"
            }
            print("  ✅ 添加: 「 (左直角引号)")
        
        if '」' not in self.data:
            # 右直角引号
            self.data['」'] = {
                "character": "」",
                "medians": [
                    [[88, 75], [118, 75], [118, 181]]
                ],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "right_center"
            }
            print("  ✅ 添加: 」 (右直角引号)")
        
        if '『' not in self.data:
            # 左双直角引号
            self.data['『'] = {
                "character": "『",
                "medians": [
                    [[175, 70], [145, 70], [145, 186]],  # 外层
                    [[160, 80], [135, 80], [135, 176]]   # 内层
                ],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "left_center"
            }
            print("  ✅ 添加: 『 (左双直角引号)")
        
        if '』' not in self.data:
            # 右双直角引号
            self.data['』'] = {
                "character": "』",
                "medians": [
                    [[81, 70], [111, 70], [111, 186]],   # 外层
                    [[96, 80], [121, 80], [121, 176]]    # 内层
                ],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "right_center"
            }
            print("  ✅ 添加: 』 (右双直角引号)")
    
    # ==================== 英文标点符号 ====================
    
    def add_english_period(self):
        """添加英文句号 ."""
        if '.' not in self.data:
            self.data['.'] = {
                "character": ".",
                "medians": [self.create_circle(128, 218, 4, points=12)],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "bottom_center"
            }
            print("  ✅ 添加: . (英文句号)")
    
    def add_english_exclamation(self):
        """添加英文感叹号 !"""
        if '!' not in self.data:
            line = [[128, 90], [128, 100], [128, 110], [128, 120], 
                    [128, 130], [128, 140], [128, 150], [128, 160]]
            dot = self.create_dot(128, 178, radius=5)
            
            self.data['!'] = {
                "character": "!",
                "medians": [line, dot],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ! (英文感叹号)")
    
    def add_english_question(self):
        """添加英文问号 ?"""
        if '?' not in self.data:
            curve = [
                [100, 118], [108, 106], [118, 100], [128, 98],
                [138, 100], [146, 106], [150, 115], [150, 125],
                [147, 133], [140, 140], [132, 145], [128, 150], [128, 160]
            ]
            dot = self.create_dot(128, 178, radius=5)
            
            self.data['?'] = {
                "character": "?",
                "medians": [curve, dot],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ? (英文问号)")
    
    def add_english_semicolon(self):
        """添加英文分号 ;"""
        if ';' not in self.data:
            top_dot = self.create_dot(128, 145, radius=4)
            bottom_comma = [[128, 180], [130, 185], [131, 190], [130, 195], [128, 198]]
            
            self.data[';'] = {
                "character": ";",
                "medians": [top_dot, bottom_comma],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ; (英文分号)")
    
    def add_english_colon(self):
        """添加英文冒号 :"""
        if ':' not in self.data:
            top_dot = self.create_dot(128, 135, radius=4)
            bottom_dot = self.create_dot(128, 165, radius=4)
            
            self.data[':'] = {
                "character": ":",
                "medians": [top_dot, bottom_dot],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: : (英文冒号)")
    
    def add_english_quotes(self):
        """添加英文引号 ' " """
        if "'" not in self.data:
            # 英文单引号
            self.data["'"] = {
                "character": "'",
                "medians": [[[128, 95], [126, 100], [125, 105]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "top_center"
            }
            print("  ✅ 添加: ' (英文单引号)")
        
        if '"' not in self.data:
            # 英文双引号
            self.data['"'] = {
                "character": '"',
                "medians": [
                    [[115, 95], [113, 100], [112, 105]],  # 左撇
                    [[141, 95], [139, 100], [138, 105]]   # 右撇
                ],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "top_center"
            }
            print("  ✅ 添加: \" (英文双引号)")
    
    def add_english_parentheses(self):
        """添加英文括号 ( )"""
        if '(' not in self.data:
            left_paren = []
            center_x, center_y = 145, 128
            radius_x, radius_y = 18, 60
            for angle in range(-85, 86, 8):
                rad = math.radians(angle)
                x = int(center_x - radius_x * math.cos(rad))
                y = int(center_y + radius_y * math.sin(rad))
                left_paren.append([x, y])
            
            self.data['('] = {
                "character": "(",
                "medians": [left_paren],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ( (左括号)")
        
        if ')' not in self.data:
            right_paren = []
            center_x = 111
            for angle in range(-85, 86, 8):
                rad = math.radians(angle)
                x = int(center_x + radius_x * math.cos(rad))
                y = int(center_y + radius_y * math.sin(rad))
                right_paren.append([x, y])
            
            self.data[')'] = {
                "character": ")",
                "medians": [right_paren],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ) (右括号)")
    
    def add_square_brackets(self):
        """添加方括号 [ ]"""
        if '[' not in self.data:
            self.data['['] = {
                "character": "[",
                "medians": [[[148, 75], [128, 75], [128, 181], [148, 181]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: [ (左方括号)")
        
        if ']' not in self.data:
            self.data[']'] = {
                "character": "]",
                "medians": [[[108, 75], [128, 75], [128, 181], [108, 181]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: ] (右方括号)")
    
    def add_curly_braces(self):
        """添加花括号 { }"""
        if '{' not in self.data:
            # 左花括号 - 手工设计复杂曲线
            self.data['{'] = {
                "character": "{",
                "medians": [[
                    [155, 75], [145, 78], [140, 85],     # 上弧
                    [138, 95], [137, 110], [136, 120],   # 上直
                    [135, 128],                          # 中点
                    [130, 128], [125, 128],              # 向左突出
                    [130, 128], [135, 128],              # 返回
                    [136, 136], [137, 146], [138, 161],  # 下直
                    [140, 171], [145, 178], [155, 181]   # 下弧
                ]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: { (左花括号)")
        
        if '}' not in self.data:
            # 右花括号 - 镜像
            self.data['}'] = {
                "character": "}",
                "medians": [[
                    [101, 75], [111, 78], [116, 85],     # 上弧
                    [118, 95], [119, 110], [120, 120],   # 上直
                    [121, 128],                          # 中点
                    [126, 128], [131, 128],              # 向右突出
                    [126, 128], [121, 128],              # 返回
                    [120, 136], [119, 146], [118, 161],  # 下直
                    [116, 171], [111, 178], [101, 181]   # 下弧
                ]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: } (右花括号)")
    
    # ==================== 常用符号 ====================
    
    def add_hyphen_dash(self):
        """添加连字符和短横线 - """
        if '-' not in self.data:
            self.data['-'] = {
                "character": "-",
                "medians": [[[95, 128], [115, 128], [135, 128], [161, 128]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: - (连字符)")
    
    def add_underscore(self):
        """添加下划线 _"""
        if '_' not in self.data:
            self.data['_'] = {
                "character": "_",
                "medians": [[[70, 220], [100, 220], [130, 220], [160, 220], [186, 220]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "bottom"
            }
            print("  ✅ 添加: _ (下划线)")
    
    def add_slashes(self):
        """添加斜杠 / \"""
        if '/' not in self.data:
            self.data['/'] = {
                "character": "/",
                "medians": [[[105, 180], [115, 160], [125, 140], [135, 120], [145, 100], [151, 85]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: / (斜杠)")
        
        if '\\' not in self.data:
            self.data['\\'] = {
                "character": "\\",
                "medians": [[[105, 85], [115, 100], [125, 120], [135, 140], [145, 160], [151, 180]]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: \\ (反斜杠)")
    
    def add_percent(self):
        """添加百分号 %"""
        if '%' not in self.data:
            # 上圆圈
            top_circle = self.create_circle(105, 100, 8, points=16)
            # 下圆圈
            bottom_circle = self.create_circle(151, 156, 8, points=16)
            # 斜线
            slash = [[100, 165], [110, 145], [120, 125], [130, 105], [140, 85], [156, 91]]
            
            self.data['%'] = {
                "character": "%",
                "medians": [top_circle, slash, bottom_circle],
                "strokes": 3,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: % (百分号)")
    
    def add_ampersand(self):
        """添加和号 &"""
        if '&' not in self.data:
            # 简化的&符号
            self.data['&'] = {
                "character": "&",
                "medians": [[
                    [150, 100], [140, 95], [130, 95], [120, 100],  # 上部圆弧
                    [115, 108], [115, 118], [120, 126],            # 左下
                    [125, 130], [130, 135], [135, 140],            # 中部
                    [125, 150], [115, 158], [110, 168],            # 左下圆
                    [110, 178], [115, 185], [125, 188],            # 底部
                    [135, 185], [145, 178], [150, 168]             # 右下
                ]],
                "strokes": 1,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: & (和号)")
    
    def add_at_symbol(self):
        """添加@符号"""
        if '@' not in self.data:
            # 外圆
            outer = []
            for angle in range(-30, 331, 15):
                rad = math.radians(angle)
                x = int(128 + 50 * math.cos(rad))
                y = int(128 + 50 * math.sin(rad))
                outer.append([x, y])
            
            # 内圈 + a
            inner = [[148, 118], [148, 138], [140, 145], [130, 145], 
                     [122, 140], [122, 128], [130, 120], [140, 120], [148, 125]]
            
            self.data['@'] = {
                "character": "@",
                "medians": [outer, inner],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: @ (at符号)")
    
    def add_asterisk(self):
        """添加星号 *"""
        if '*' not in self.data:
            # 6条射线
            lines = []
            for angle in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(angle)
                x1 = int(128 + 8 * math.cos(rad))
                y1 = int(128 + 8 * math.sin(rad))
                x2 = int(128 + 20 * math.cos(rad))
                y2 = int(128 + 20 * math.sin(rad))
                lines.append([[128, 128], [x1, y1], [x2, y2]])
            
            self.data['*'] = {
                "character": "*",
                "medians": lines,
                "strokes": 6,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: * (星号)")
    
    def add_plus_minus(self):
        """添加加号减号 + -"""
        if '+' not in self.data:
            self.data['+'] = {
                "character": "+",
                "medians": [
                    [[128, 108], [128, 118], [128, 128], [128, 138], [128, 148]],  # 竖线
                    [[108, 128], [118, 128], [128, 128], [138, 128], [148, 128]]   # 横线
                ],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: + (加号)")
        
        # 减号（-）已在 hyphen 中添加
    
    def add_equals(self):
        """添加等号 ="""
        if '=' not in self.data:
            self.data['='] = {
                "character": "=",
                "medians": [
                    [[95, 118], [115, 118], [135, 118], [155, 118]],  # 上横线
                    [[95, 138], [115, 138], [135, 138], [155, 138]]   # 下横线
                ],
                "strokes": 2,
                "source": "manual_design_expanded",
                "position": "center"
            }
            print("  ✅ 添加: = (等号)")
    
    def add_all_missing(self):
        """添加所有缺失的标点符号"""
        initial_count = len(self.data)
        
        print("\n🎨 开始添加缺失的标点符号...")
        print("-" * 70)
        
        print("\n[1] 中文标点符号")
        self.add_single_quotes()
        self.add_corner_quotes()
        
        print("\n[2] 英文标点符号")
        self.add_english_period()
        self.add_english_exclamation()
        self.add_english_question()
        self.add_english_semicolon()
        self.add_english_colon()
        self.add_english_quotes()
        self.add_english_parentheses()
        
        print("\n[3] 括号类符号")
        self.add_square_brackets()
        self.add_curly_braces()
        
        print("\n[4] 连接符号")
        self.add_hyphen_dash()
        self.add_underscore()
        self.add_slashes()
        
        print("\n[5] 特殊符号")
        self.add_percent()
        self.add_ampersand()
        self.add_at_symbol()
        self.add_asterisk()
        self.add_plus_minus()
        self.add_equals()
        
        added_count = len(self.data) - initial_count
        print("\n" + "-" * 70)
        print(f"✅ 新增 {added_count} 个标点符号")
        print(f"📦 总计 {len(self.data)} 个标点符号")
        
        return added_count
    
    def save(self, output_path: str = None):
        """保存数据"""
        if output_path is None:
            output_path = self.existing_file
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        return output_path, file_size


def main():
    print("=" * 70)
    print("标点符号扩展工具")
    print("=" * 70)
    
    expander = PunctuationExpander()
    
    # 添加所有缺失的标点
    added_count = expander.add_all_missing()
    
    if added_count > 0:
        # 保存
        print("\n💾 保存扩展后的标点符号...")
        output_path, file_size = expander.save()
        
        print(f"✅ 已保存到: {output_path}")
        print(f"📦 文件大小: {file_size / 1024:.2f} KB")
        
        # 显示完整列表
        print("\n" + "=" * 70)
        print("📊 完整标点符号列表:")
        print("-" * 70)
        
        categories = {
            '中文句读': ['，', '。', '、', '；', '：'],
            '中文语气': ['！', '？'],
            '中文引号': ['"', '"', ''', ''', '「', '」', '『', '』'],
            '中文括号': ['（', '）', '《', '》', '【', '】'],
            '中文特殊': ['…', '——'],
            '英文标点': ['.', ',', '!', '?', ';', ':', "'", '"'],
            '英文括号': ['(', ')', '[', ']', '{', '}'],
            '符号': ['-', '_', '/', '\\', '%', '&', '@', '*', '+', '=']
        }
        
        for category, chars in categories.items():
            found = [c for c in chars if c in expander.data]
            if found:
                print(f"{category:12s}: {''.join(found)}")
        
        print("-" * 70)
        print(f"总计: {len(expander.data)} 个")
        print("=" * 70)
        
        print("\n📝 下一步:")
        print("  1. 运行测试: python scripts/test_punctuation_quick.py")
        print("  2. 重启服务器: python start_server.py")
        print("  3. 在文章中测试新标点符号")
        print("=" * 70)
        
        return 0
    else:
        print("\n✅ 所有标点符号已存在，无需添加")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

