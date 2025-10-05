#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版标点符号扩展工具
补充缺失的常用标点符号
"""

import json
import os
import math

def load_existing(filepath='data/punctuation_medians.json'):
    """加载现有数据"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def create_circle(cx, cy, r, n=24):
    """创建圆形"""
    pts = []
    for i in range(n):
        a = (i / n) * 2 * math.pi
        pts.append([int(cx + r * math.cos(a)), int(cy + r * math.sin(a))])
    pts.append(pts[0])
    return pts

def create_dot(x, y, r=4):
    """创建点"""
    return create_circle(x, y, r, 12)

def add_new_punctuation(data):
    """添加新标点符号"""
    added = []
    
    # 中文单引号
    if '\u2018' not in data:  # '
        data['\u2018'] = {
            "character": "\u2018",
            "medians": [[[107, 88], [104, 93], [103, 98], [103, 102]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "top_left"
        }
        added.append('左单引号')
    
    if '\u2019' not in data:  # '
        data['\u2019'] = {
            "character": "\u2019",
            "medians": [[[107, 107], [104, 102], [103, 97], [103, 93]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "top_left"
        }
        added.append('右单引号')
    
    # 直角引号
    corners = {
        '\u300c': ([[168, 75], [138, 75], [138, 181]], '左直角引号'),  # 「
        '\u300d': ([[88, 75], [118, 75], [118, 181]], '右直角引号'),  # 」
        '\u300e': ([[[175, 70], [145, 70], [145, 186]], [[160, 80], [135, 80], [135, 176]]], '左双直角引号'),  # 『
        '\u300f': ([[[81, 70], [111, 70], [111, 186]], [[96, 80], [121, 80], [121, 176]]], '右双直角引号')  # 』
    }
    
    for char_code, (medians, name) in corners.items():
        if char_code not in data:
            if isinstance(medians[0][0], list):  # 多笔画
                median_data = medians
                stroke_count = len(medians)
            else:  # 单笔画
                median_data = [medians]
                stroke_count = 1
            
            data[char_code] = {
                "character": char_code,
                "medians": median_data,
                "strokes": stroke_count,
                "source": "manual_design_expanded",
                "position": "center"
            }
            added.append(name)
    
    # 英文标点
    english = {
        '.': ([[create_dot(128, 218, 4)], 'bottom_center', '英文句号']),
        '!': ([[[128, 90], [128, 100], [128, 110], [128, 120], [128, 130], [128, 140], [128, 150], [128, 160]], create_dot(128, 178, 5)], 'center', '英文感叹号'),
        '?': ([[[100, 118], [108, 106], [118, 100], [128, 98], [138, 100], [146, 106], [150, 115], [150, 125], [147, 133], [140, 140], [132, 145], [128, 150], [128, 160]], create_dot(128, 178, 5)], 'center', '英文问号'),
        ':': ([create_dot(128, 135, 4), create_dot(128, 165, 4)], 'center', '英文冒号'),
        ';': ([create_dot(128, 145, 4), [[128, 180], [130, 185], [131, 190], [130, 195], [128, 198]]], 'center', '英文分号'),
    }
    
    for char, (medians, pos, name) in english.items():
        if char not in data:
            if not isinstance(medians, list) or not medians:
                continue
            # 确定笔画数
            stroke_count = len(medians)
            data[char] = {
                "character": char,
                "medians": medians,
                "strokes": stroke_count,
                "source": "manual_design_expanded",
                "position": pos
            }
            added.append(name)
    
    # 英文括号
    left_paren = []
    right_paren = []
    for angle in range(-85, 86, 8):
        rad = math.radians(angle)
        left_paren.append([int(145 - 18 * math.cos(rad)), int(128 + 60 * math.sin(rad))])
        right_paren.append([int(111 + 18 * math.cos(rad)), int(128 + 60 * math.sin(rad))])
    
    if '(' not in data:
        data['('] = {
            "character": "(",
            "medians": [left_paren],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('左圆括号')
    
    if ')' not in data:
        data[')'] = {
            "character": ")",
            "medians": [right_paren],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('右圆括号')
    
    # 方括号
    if '[' not in data:
        data['['] = {
            "character": "[",
            "medians": [[[148, 75], [128, 75], [128, 181], [148, 181]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('左方括号')
    
    if ']' not in data:
        data[']'] = {
            "character": "]",
            "medians": [[[108, 75], [128, 75], [128, 181], [108, 181]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('右方括号')
    
    # 连字符和下划线
    if '-' not in data:
        data['-'] = {
            "character": "-",
            "medians": [[[95, 128], [115, 128], [135, 128], [161, 128]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('连字符')
    
    if '_' not in data:
        data['_'] = {
            "character": "_",
            "medians": [[[70, 220], [100, 220], [130, 220], [160, 220], [186, 220]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "bottom"
        }
        added.append('下划线')
    
    # 斜杠
    if '/' not in data:
        data['/'] = {
            "character": "/",
            "medians": [[[105, 180], [115, 160], [125, 140], [135, 120], [145, 100], [151, 85]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('斜杠')
    
    if '\\' not in data:
        data['\\'] = {
            "character": "\\",
            "medians": [[[105, 85], [115, 100], [125, 120], [135, 140], [145, 160], [151, 180]]],
            "strokes": 1,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('反斜杠')
    
    # 百分号
    if '%' not in data:
        top_circle = create_circle(105, 100, 8, 16)
        bottom_circle = create_circle(151, 156, 8, 16)
        slash = [[100, 165], [110, 145], [120, 125], [130, 105], [140, 85], [156, 91]]
        data['%'] = {
            "character": "%",
            "medians": [top_circle, slash, bottom_circle],
            "strokes": 3,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('百分号')
    
    # 加号和等号
    if '+' not in data:
        data['+'] = {
            "character": "+",
            "medians": [
                [[128, 108], [128, 118], [128, 128], [128, 138], [128, 148]],
                [[108, 128], [118, 128], [128, 128], [138, 128], [148, 128]]
            ],
            "strokes": 2,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('加号')
    
    if '=' not in data:
        data['='] = {
            "character": "=",
            "medians": [
                [[95, 118], [115, 118], [135, 118], [155, 118]],
                [[95, 138], [115, 138], [135, 138], [155, 138]]
            ],
            "strokes": 2,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('等号')
    
    # 星号
    if '*' not in data:
        lines = []
        for angle in [0, 60, 120, 180, 240, 300]:
            rad = math.radians(angle)
            x1 = int(128 + 8 * math.cos(rad))
            y1 = int(128 + 8 * math.sin(rad))
            x2 = int(128 + 20 * math.cos(rad))
            y2 = int(128 + 20 * math.sin(rad))
            lines.append([[128, 128], [x1, y1], [x2, y2]])
        data['*'] = {
            "character": "*",
            "medians": lines,
            "strokes": 6,
            "source": "manual_design_expanded",
            "position": "center"
        }
        added.append('星号')
    
    return added

def main():
    print("=" * 70)
    print("标点符号扩展工具")
    print("=" * 70)
    
    # 加载现有数据
    data = load_existing()
    print(f"\n✅ 已加载 {len(data)} 个现有标点符号")
    print(f"   现有: {''.join(sorted(data.keys()))}")
    
    # 添加新标点
    print("\n🎨 开始添加缺失的标点符号...")
    print("-" * 70)
    added = add_new_punctuation(data)
    
    if added:
        print(f"\n✅ 新增 {len(added)} 个标点符号:")
        for name in added:
            print(f"  - {name}")
        
        # 保存
        output_path = 'data/punctuation_medians.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        print(f"\n💾 已保存到: {output_path}")
        print(f"📦 文件大小: {file_size / 1024:.2f} KB")
        print(f"📊 总计: {len(data)} 个标点符号")
        
        print("\n" + "=" * 70)
        print("📝 下一步:")
        print("  1. 测试: python scripts/test_punctuation_quick.py")
        print("  2. 重启服务器: python start_server.py")
        print("=" * 70)
    else:
        print("\n✅ 所有标点符号已存在，无需添加")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

