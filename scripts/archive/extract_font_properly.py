#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用fontTools直接提取字体轮廓数据
这是更专业的方法，直接读取字体的矢量数据而不是从光栅图像提取
"""

import os
import json
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import numpy as np


def download_font_if_needed():
    """确保字体文件存在"""
    font_path = 'fonts/Roboto-Regular.ttf'
    if os.path.exists(font_path):
        print(f"✅ 字体已存在: {font_path}")
        return font_path
    
    print("⚠️ 字体不存在，请先运行:")
    print("   python scripts\\download_and_extract_opensource_fonts.py")
    return None


def extract_glyph_outlines(font_path, char):
    """从字体中提取字符的轮廓数据"""
    try:
        font = TTFont(font_path)
        
        # 获取字符的glyph名称
        cmap = font.getBestCmap()
        glyph_name = cmap.get(ord(char))
        
        if not glyph_name:
            print(f"  ⚠️ 字符 {char} 在字体中不存在")
            return None
        
        # 获取glyph数据
        glyph_set = font.getGlyphSet()
        glyph = glyph_set[glyph_name]
        
        # 使用RecordingPen记录绘制指令
        pen = RecordingPen()
        glyph.draw(pen)
        
        # 获取边界框
        bbox = glyph._glyph.xMin, glyph._glyph.yMin, glyph._glyph.xMax, glyph._glyph.yMax
        
        return {
            'name': glyph_name,
            'bbox': bbox,
            'commands': pen.value,
            'width': glyph.width
        }
        
    except Exception as e:
        print(f"  ❌ 提取失败 {char}: {e}")
        return None


def outline_to_median(outline_data):
    """将轮廓数据转换为中轴线（简化版）"""
    if not outline_data or not outline_data['commands']:
        return []
    
    commands = outline_data['commands']
    bbox = outline_data['bbox']
    
    # 收集所有点
    points = []
    for cmd_type, cmd_data in commands:
        if cmd_type == 'moveTo':
            points.append(cmd_data[0])
        elif cmd_type == 'lineTo':
            points.append(cmd_data[0])
        elif cmd_type == 'qCurveTo':
            # 二次贝塞尔曲线，取控制点和终点
            for pt in cmd_data:
                points.append(pt)
        elif cmd_type == 'curveTo':
            # 三次贝塞尔曲线，取所有点
            for pt in cmd_data:
                points.append(pt)
    
    if not points:
        return []
    
    # 按Y坐标排序，然后对每个Y值取X的平均值作为中心线
    points_array = np.array(points)
    
    # 归一化到0-1范围
    x_min, y_min = points_array.min(axis=0)
    x_max, y_max = points_array.max(axis=0)
    
    if x_max == x_min or y_max == y_min:
        return []
    
    # 采样中轴线点
    y_samples = np.linspace(y_min, y_max, 20)
    median_points = []
    
    for y_sample in y_samples:
        # 找到接近这个Y值的所有点
        close_points = points_array[np.abs(points_array[:, 1] - y_sample) < (y_max - y_min) / 40]
        if len(close_points) > 0:
            x_center = np.mean(close_points[:, 0])
            median_points.append([x_center, y_sample])
    
    return median_points


def convert_to_mmh_system(points, bbox):
    """转换到MMH坐标系统"""
    if not points:
        return []
    
    points_array = np.array(points)
    
    # 获取范围
    x_min, y_min = points_array.min(axis=0)
    x_max, y_max = points_array.max(axis=0)
    
    width = x_max - x_min
    height = y_max - y_min
    
    if width == 0 or height == 0:
        return []
    
    # 归一化并转换到MMH坐标系
    # MMH: X: 0-1024, Y: -124 to 900 (翻转的)
    mmh_points = []
    
    for x, y in points:
        # 归一化到0-1
        x_norm = (x - x_min) / width
        y_norm = (y - y_min) / height
        
        # 转换到MMH坐标
        # X: 居中在512，范围大约300-700
        char_width = 400  # 字符宽度
        x_mmh = 512 - char_width/2 + x_norm * char_width
        
        # Y: 居中在388，翻转方向
        char_height = 500  # 字符高度
        y_mmh = 388 + char_height/2 - y_norm * char_height
        
        mmh_points.append([int(x_mmh), int(y_mmh)])
    
    return mmh_points


def extract_char_with_fonttools(font_path, char):
    """使用fontTools提取字符"""
    outline = extract_glyph_outlines(font_path, char)
    if not outline:
        return None
    
    median = outline_to_median(outline)
    if not median:
        return None
    
    mmh_coords = convert_to_mmh_system(median, outline['bbox'])
    
    if len(mmh_coords) < 2:
        return None
    
    return [mmh_coords]  # 返回单个笔画


def main():
    print("=" * 70)
    print("使用fontTools专业提取字体数据")
    print("=" * 70)
    
    # 检查字体
    font_path = download_font_if_needed()
    if not font_path:
        return 1
    
    print("\n📝 测试提取几个字符...")
    test_chars = ['A', 'B', 'M', 'a', 'b', 'm', '1', '5']
    
    for char in test_chars:
        medians = extract_char_with_fonttools(font_path, char)
        if medians:
            pts = [p for s in medians for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            print(f"  ✅ {char}: {len(pts)}个点, X({min(xs)}-{max(xs)}), Y({min(ys)}-{max(ys)})")
        else:
            print(f"  ❌ {char}: 提取失败")
    
    print("\n" + "=" * 70)
    print("⚠️ 注意: fontTools方法更专业，但需要更复杂的中轴线提取算法")
    print("当前实现是简化版，可能需要进一步优化")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

