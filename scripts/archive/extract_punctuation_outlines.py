#!/usr/bin/env python3
"""
从系统字体提取标点符号的完整轮廓路径
不进行骨架化，直接使用轮廓数据
"""

import os
import json
import platform
from typing import List, Tuple


def find_chinese_font():
    """查找系统中的中文字体"""
    system = platform.system()
    
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
        ]
    elif system == 'Darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"[OK] 找到字体: {path}")
            return path
    
    print("[ERROR] 未找到合适的中文字体")
    return None


def extract_glyph_outline(font_path: str, char: str):
    """
    提取字符的完整轮廓
    """
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        
        # 加载字体
        font = TTFont(font_path, fontNumber=0)
        
        # 获取字符映射
        cmap = font.getBestCmap()
        if not cmap:
            return None, None
        
        char_code = ord(char)
        glyph_name = cmap.get(char_code)
        
        if not glyph_name:
            return None, None
        
        # 获取glyph set
        glyph_set = font.getGlyphSet()
        glyph = glyph_set[glyph_name]
        
        # 使用SVGPathPen获取SVG路径
        pen = SVGPathPen(glyph_set)
        glyph.draw(pen)
        
        svg_path = pen.getCommands()
        
        # 获取字体单位
        units_per_em = font['head'].unitsPerEm
        
        font.close()
        
        return svg_path, units_per_em
        
    except Exception as e:
        print(f"  [ERROR] 提取 {char} 失败: {e}")
        return None, None


def parse_svg_path_to_points(svg_path: str, units_per_em: int):
    """
    将SVG路径解析为点列表
    """
    import re
    
    # 缩放到256x256空间
    scale = 256.0 / units_per_em
    
    # 解析SVG路径命令
    points = []
    commands = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?[0-9]*\.?[0-9]+', svg_path)
    
    current_x, current_y = 0, 0
    i = 0
    
    while i < len(commands):
        cmd = commands[i]
        
        if cmd in ['M', 'm']:  # MoveTo
            i += 1
            x = float(commands[i])
            i += 1
            y = float(commands[i])
            
            if cmd == 'm':  # relative
                current_x += x
                current_y += y
            else:  # absolute
                current_x = x
                current_y = y
            
            # 翻转Y轴并缩放
            scaled_x = int(current_x * scale)
            scaled_y = int((units_per_em - current_y) * scale)
            points.append([scaled_x, scaled_y])
        
        elif cmd in ['L', 'l']:  # LineTo
            i += 1
            x = float(commands[i])
            i += 1
            y = float(commands[i])
            
            if cmd == 'l':
                current_x += x
                current_y += y
            else:
                current_x = x
                current_y = y
            
            scaled_x = int(current_x * scale)
            scaled_y = int((units_per_em - current_y) * scale)
            points.append([scaled_x, scaled_y])
        
        elif cmd in ['C', 'c']:  # CurveTo (cubic bezier)
            # 三次贝塞尔：取控制点和终点
            for _ in range(3):  # 3对坐标
                i += 1
                x = float(commands[i])
                i += 1
                y = float(commands[i])
                
                if cmd == 'c':
                    x += current_x
                    y += current_y
                
                current_x = x
                current_y = y
                
                scaled_x = int(x * scale)
                scaled_y = int((units_per_em - y) * scale)
                points.append([scaled_x, scaled_y])
        
        elif cmd in ['Q', 'q']:  # QuadraticCurveTo
            for _ in range(2):
                i += 1
                x = float(commands[i])
                i += 1
                y = float(commands[i])
                
                if cmd == 'q':
                    x += current_x
                    y += current_y
                
                current_x = x
                current_y = y
                
                scaled_x = int(x * scale)
                scaled_y = int((units_per_em - y) * scale)
                points.append([scaled_x, scaled_y])
        
        elif cmd in ['Z', 'z']:  # ClosePath
            pass
        
        i += 1
    
    return points


def adjust_punctuation_position(points: List, char: str):
    """调整标点符号到标准位置"""
    if not points or len(points) < 2:
        return points
    
    # 计算边界
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return points
    
    # 根据标点类型确定目标位置
    if char in ['，', '。', '、']:
        target_x, target_y, target_size = 220, 220, 25
    elif char in ['！', '？']:
        target_x, target_y, target_size = 128, 140, 90
    elif char in ['；', '：']:
        target_x, target_y, target_size = 220, 150, 50
    elif char in ['"', '"', ''', ''']:
        target_x, target_y, target_size = 110, 90, 35
    elif char in ['（', '）', '《', '》', '【', '】']:
        target_x, target_y, target_size = 128, 128, 90
    else:
        target_x, target_y, target_size = 128, 128, 70
    
    # 当前中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 缩放
    scale = target_size / max(width, height)
    
    # 变换
    adjusted_points = []
    for x, y in points:
        x = (x - center_x) * scale + target_x
        y = (y - center_y) * scale + target_y
        adjusted_points.append([int(x), int(y)])
    
    return adjusted_points


def main():
    print("=" * 60)
    print("从系统字体提取标点符号完整轮廓")
    print("=" * 60)
    
    font_path = find_chinese_font()
    if not font_path:
        return 1
    
    punctuation_list = [
        '，', '。', '、', '；', '：',
        '！', '？',
        '"', '"', ''', ''',
        '（', '）', '《', '》', '【', '】',
        '…', '——',
    ]
    
    results = {}
    print("\n开始提取...")
    print("-" * 60)
    
    for char in punctuation_list:
        try:
            svg_path, units_per_em = extract_glyph_outline(font_path, char)
            
            if not svg_path or not units_per_em:
                print(f"  [X] {char:2s} - 未找到轮廓")
                continue
            
            # 解析路径为点
            points = parse_svg_path_to_points(svg_path, units_per_em)
            
            if not points or len(points) < 2:
                print(f"  [X] {char:2s} - 点数不足")
                continue
            
            # 调整位置
            adjusted = adjust_punctuation_position(points, char)
            
            results[char] = {
                "character": char,
                "medians": [adjusted],  # 作为单个stroke
                "strokes": 1,
                "source": "font_outline"
            }
            
            print(f"  [OK] {char:2s} - {len(adjusted)} points")
            
        except Exception as e:
            print(f"  [X] {char:2s} - ERROR: {e}")
    
    print("-" * 60)
    print(f"\n[RESULT] 成功提取 {len(results)}/{len(punctuation_list)} 个标点")
    
    if results:
        output_path = 'data/punctuation_medians.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        print(f"[FILE] {output_path}")
        print(f"[SIZE] {file_size / 1024:.1f} KB")
        print("\n" + "=" * 60)
        print("请重启服务器以加载新数据")
        print("=" * 60)
        return 0
    else:
        print("\n[ERROR] 没有成功提取任何标点")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

