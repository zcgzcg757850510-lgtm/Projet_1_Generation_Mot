#!/usr/bin/env python3
"""
从系统字体提取标点符号数据

使用 fonttools 从真实字体文件中提取标点符号的轮廓
转换为与汉字兼容的 medians 格式
"""

import os
import sys
import json
import platform
from typing import List, Tuple, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_chinese_font():
    """查找系统中的中文字体"""
    system = platform.system()
    
    candidates = []
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/simsun.ttc',   # 宋体
            'C:/Windows/Fonts/simhei.ttf',   # 黑体
            'C:/Windows/Fonts/msyh.ttc',     # 微软雅黑
        ]
    elif system == 'Darwin':  # macOS
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Songti.ttc',
        ]
    else:  # Linux
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"[OK] 找到字体: {path}")
            return path
    
    print("[ERROR] 未找到合适的中文字体")
    return None


def extract_glyph_contours(font_path: str, char: str):
    """
    从字体提取字符的轮廓点
    
    Returns:
        List of strokes, each stroke is a list of points [[x, y], ...]
    """
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        
        font = TTFont(font_path)
        glyph_set = font.getGlyphSet()
        
        # 获取字符的 glyph
        cmap = font.getBestCmap()
        if not cmap:
            return None
        
        char_code = ord(char)
        glyph_name = cmap.get(char_code)
        
        if not glyph_name:
            return None
        
        # 使用 RecordingPen 记录绘制命令
        pen = RecordingPen()
        glyph = glyph_set[glyph_name]
        glyph.draw(pen)
        
        # 获取字体单位
        units_per_em = font['head'].unitsPerEm
        
        return pen.value, units_per_em
        
    except Exception as e:
        import traceback
        print(f"  [ERROR] 提取失败: {e}")
        # traceback.print_exc()  # 取消注释以查看详细错误
        return None, None


def contour_to_strokes(contour_data, units_per_em: int):
    """
    将字体轮廓转换为笔画（stroke）列表
    
    策略：
    1. 提取每个子路径作为一个笔画
    2. 简化曲线为关键点
    3. 归一化到 0-256 空间
    """
    strokes = []
    current_stroke = []
    
    # 缩放因子：从字体单位转换到 256x256 空间
    scale = 256.0 / units_per_em
    
    for command, args in contour_data:
        if command == 'moveTo':
            # 开始新的笔画
            if current_stroke:
                strokes.append(current_stroke)
            x, y = args[0]
            current_stroke = [[int(x * scale), int(y * scale)]]
        
        elif command == 'lineTo':
            # 直线
            x, y = args[0]
            current_stroke.append([int(x * scale), int(y * scale)])
        
        elif command == 'qCurveTo':
            # 二次贝塞尔曲线 - 提取控制点和终点
            for point in args:
                x, y = point
                current_stroke.append([int(x * scale), int(y * scale)])
        
        elif command == 'curveTo':
            # 三次贝塞尔曲线 - 提取所有点
            for point in args:
                x, y = point
                current_stroke.append([int(x * scale), int(y * scale)])
        
        elif command == 'closePath':
            # 闭合路径
            if current_stroke:
                # 对于闭合路径，只保留外轮廓的中心线
                # 简化：取每个点作为笔画的一部分
                strokes.append(current_stroke)
            current_stroke = []
    
    # 添加最后一笔
    if current_stroke:
        strokes.append(current_stroke)
    
    return strokes


def simplify_stroke(stroke: List[List[int]], tolerance: int = 5):
    """
    简化笔画，使用 Douglas-Peucker 算法
    """
    if len(stroke) <= 2:
        return stroke
    
    def point_line_distance(point, line_start, line_end):
        """计算点到线段的距离"""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return ((x0 - x1)**2 + (y0 - y1)**2)**0.5
        
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)))
        
        projection_x = x1 + t * dx
        projection_y = y1 + t * dy
        
        return ((x0 - projection_x)**2 + (y0 - projection_y)**2)**0.5
    
    def douglas_peucker(points, tolerance):
        """Douglas-Peucker 算法"""
        if len(points) <= 2:
            return points
        
        # 找到距离首尾连线最远的点
        max_distance = 0
        max_index = 0
        
        for i in range(1, len(points) - 1):
            distance = point_line_distance(points[i], points[0], points[-1])
            if distance > max_distance:
                max_distance = distance
                max_index = i
        
        # 如果最大距离大于容差，递归简化
        if max_distance > tolerance:
            left = douglas_peucker(points[:max_index + 1], tolerance)
            right = douglas_peucker(points[max_index:], tolerance)
            return left[:-1] + right
        else:
            return [points[0], points[-1]]
    
    return douglas_peucker(stroke, tolerance)


def normalize_to_standard_position(strokes: List[List[List[int]]], char: str):
    """
    将笔画归一化到标准位置
    
    标点符号的标准位置：
    - 逗号、句号：右下角 (200-230, 200-240)
    - 感叹号、问号：垂直居中 (100-150, 80-180)
    - 顿号：右下角斜线 (190-230, 180-230)
    - 分号、冒号：垂直居中 (210-230, 100-200)
    """
    if not strokes:
        return strokes
    
    # 计算当前边界
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke)
    
    if not all_points:
        return strokes
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return strokes
    
    # 根据标点类型确定目标位置
    # 注意：字体坐标系Y轴向上，需要翻转
    if char in ['，', '。', '、']:
        # 右下角，较小
        target_center_x = 220
        target_center_y = 220
        target_size = 20
    elif char in ['！', '？']:
        # 居中，较大
        target_center_x = 128
        target_center_y = 140
        target_size = 80
    elif char in ['；', '：']:
        # 居中偏右，中等
        target_center_x = 220
        target_center_y = 150
        target_size = 40
    elif char in ['"', '"', ''', ''']:
        # 左上或右上
        target_center_x = 110
        target_center_y = 90
        target_size = 30
    elif char in ['（', '）', '《', '》', '【', '】']:
        # 居中，较大
        target_center_x = 128
        target_center_y = 128
        target_size = 80
    else:
        # 默认：居中
        target_center_x = 128
        target_center_y = 128
        target_size = 60
    
    # 计算缩放和平移
    current_center_x = (min_x + max_x) / 2
    current_center_y = (min_y + max_y) / 2
    
    scale = target_size / max(width, height)
    
    # 应用变换
    normalized_strokes = []
    for stroke in strokes:
        normalized_stroke = []
        for x, y in stroke:
            # 翻转Y轴（字体坐标系Y向上，SVG坐标系Y向下）
            y_flipped = 256 - y
            
            # 平移到原点
            x_centered = x - current_center_x
            y_centered = y_flipped - (256 - current_center_y)
            
            # 缩放
            x_scaled = x_centered * scale
            y_scaled = y_centered * scale
            
            # 平移到目标位置
            x_final = int(x_scaled + target_center_x)
            y_final = int(y_scaled + target_center_y)
            
            normalized_stroke.append([x_final, y_final])
        
        normalized_strokes.append(normalized_stroke)
    
    return normalized_strokes


def extract_punctuation_data(font_path: str, punctuation_list: List[str]):
    """
    从字体文件批量提取标点符号数据
    """
    results = {}
    
    print(f"\n开始提取标点符号...")
    print("-" * 60)
    
    for char in punctuation_list:
        try:
            # 提取轮廓
            contour_data, units_per_em = extract_glyph_contours(font_path, char)
            
            if contour_data is None:
                print(f"  [X] {char:2s} - 未找到字形")
                continue
            
            # 转换为笔画
            strokes = contour_to_strokes(contour_data, units_per_em)
            
            if not strokes:
                print(f"  [X] {char:2s} - 无有效笔画")
                continue
            
            # 简化笔画
            simplified_strokes = [simplify_stroke(s, tolerance=3) for s in strokes]
            
            # 归一化位置
            normalized_strokes = normalize_to_standard_position(simplified_strokes, char)
            
            # 过滤太短的笔画
            valid_strokes = [s for s in normalized_strokes if len(s) >= 2]
            
            if not valid_strokes:
                print(f"  [X] {char:2s} - 笔画太短")
                continue
            
            results[char] = {
                "character": char,
                "medians": valid_strokes,
                "strokes": len(valid_strokes),
                "source": "system_font"
            }
            
            points_count = sum(len(s) for s in valid_strokes)
            print(f"  [OK] {char:2s} - {len(valid_strokes)} bi hua, {points_count} dian")
            
        except Exception as e:
            print(f"  [X] {char:2s} - cuowu: {e}")
    
    return results


def main():
    print("=" * 60)
    print("从系统字体提取标点符号数据")
    print("=" * 60)
    
    # 查找字体
    font_path = find_chinese_font()
    if not font_path:
        print("\n❌ 错误：未找到合适的字体文件")
        return 1
    
    # 定义要提取的标点符号
    punctuation_list = [
        # 中文标点（常用）
        '，', '。', '、', '；', '：',
        '！', '？',
        '"', '"', ''', ''',
        '（', '）', '《', '》', '【', '】',
        '…', '——',
        
        # 英文标点
        ',', '.', '!', '?', ';', ':',
        '"', "'", '(', ')', '[', ']',
        '-', '—',
    ]
    
    # 提取数据
    results = extract_punctuation_data(font_path, punctuation_list)
    
    print("-" * 60)
    print(f"\n[OK] 成功提取 {len(results)}/{len(punctuation_list)} 个标点符号")
    
    if results:
        # 保存结果
        output_path = 'data/punctuation_medians.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_path)
        print(f"[FILE] 保存到: {output_path}")
        print(f"[SIZE] 文件大小: {file_size / 1024:.1f} KB")
        print(f"[CHARS] 标点符号数量: {len(results)}")
        
        print("\n" + "=" * 60)
        print("下一步：重启服务器以加载新的标点符号数据")
        print("  python start_server.py")
        print("=" * 60)
        
        return 0
    else:
        print("\n[ERROR] 失败：没有成功提取任何标点符号")
        return 1


if __name__ == "__main__":
    sys.exit(main())

