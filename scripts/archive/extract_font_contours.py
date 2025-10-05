#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用字体轮廓提取 - 更准确的方法
保留完整的轮廓路径，而不是简化为不准确的中轴线
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage


def download_font_if_needed():
    """确保Roboto字体存在"""
    font_path = 'fonts/Roboto-Regular.ttf'
    if os.path.exists(font_path):
        return font_path
    
    print("⚠️ Roboto字体不存在，正在下载...")
    url = 'https://github.com/google/roboto/raw/main/src/hinted/Roboto-Regular.ttf'
    
    try:
        os.makedirs('fonts', exist_ok=True)
        urllib.request.urlretrieve(url, font_path)
        print(f"✅ 下载成功: {font_path}")
        return font_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None


def render_char_to_image(char, font_path, size=256):
    """渲染字符到高分辨率图像"""
    try:
        img = Image.new('L', (size, size), color=255)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, int(size * 0.7))
        
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        
        draw.text((x, y), char, fill=0, font=font)
        return img
    except Exception as e:
        print(f"  ❌ 渲染失败 {char}: {e}")
        return None


def extract_contours_better(img_array):
    """
    更好的轮廓提取方法
    不使用单一中心线，而是提取实际轮廓
    """
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 获取骨架（使用形态学细化）
    # 这会给出字符的实际骨架而不是简单的中心线
    skeleton = ndimage.morphology.binary_erosion(binary, iterations=3)
    skeleton = skeleton.astype(np.uint8)
    
    # 找到所有非零点
    y_coords, x_coords = np.where(skeleton > 0)
    
    if len(x_coords) == 0:
        # 如果腐蚀过度，使用原始轮廓
        y_coords, x_coords = np.where(binary > 0)
    
    if len(x_coords) == 0:
        return []
    
    # 组合坐标
    points = list(zip(x_coords.tolist(), y_coords.tolist()))
    
    # 按Y坐标排序
    points.sort(key=lambda p: p[1])
    
    # 对于每个Y值，保留所有X值（不取平均）
    # 这样可以保留字母的多个部分
    y_groups = {}
    for x, y in points:
        if y not in y_groups:
            y_groups[y] = []
        y_groups[y].append(x)
    
    # 为每个Y值取X的范围（左右边界的中点们）
    contour_points = []
    for y in sorted(y_groups.keys()):
        xs = y_groups[y]
        if len(xs) > 1:
            # 有多个X值，取左右边界
            x_min, x_max = min(xs), max(xs)
            # 添加左边界、中心、右边界的点
            contour_points.append([x_min, y])
            if x_max - x_min > 10:  # 如果宽度足够，添加中心点
                contour_points.append([(x_min + x_max) // 2, y])
            contour_points.append([x_max, y])
        else:
            contour_points.append([xs[0], y])
    
    # 简化点数
    if len(contour_points) > 30:
        step = len(contour_points) // 20
        contour_points = [contour_points[i] for i in range(0, len(contour_points), step)]
    
    return contour_points if len(contour_points) >= 2 else []


def convert_to_mmh_coordinates(points, original_size=256):
    """转换到MMH坐标系"""
    if not points:
        return []
    
    scale = 1024.0 / original_size
    y_top = 900.0
    
    mmh_points = []
    for x, y in points:
        x_mmh = x * scale
        y_mmh = y_top - (y * scale)
        mmh_points.append([int(x_mmh), int(y_mmh)])
    
    return mmh_points


def center_character(points):
    """居中字符"""
    if not points:
        return []
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    target_x = 512
    target_y = 388
    
    offset_x = target_x - center_x
    offset_y = target_y - center_y
    
    centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in points]
    return centered


def extract_char_median(char, font_path):
    """提取字符数据"""
    img = render_char_to_image(char, font_path)
    if img is None:
        return None
    
    img_array = np.array(img)
    contours = extract_contours_better(img_array)
    
    if not contours:
        return None
    
    mmh_points = convert_to_mmh_coordinates(contours)
    centered = center_character(mmh_points)
    
    if len(centered) < 2:
        return None
    
    return [centered]


def extract_all_alphanumeric(font_path):
    """提取所有字母和数字"""
    chars = []
    chars.extend([str(i) for i in range(10)])
    chars.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])
    chars.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
    
    results = {}
    
    print(f"\n🎨 使用改进的轮廓提取方法...")
    print("=" * 70)
    
    for char in chars:
        medians = extract_char_median(char, font_path)
        
        if medians is None:
            print(f"  ❌ {char}")
            continue
        
        # 检查质量
        pts = [p for s in medians for p in s]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        
        if char.isdigit():
            char_type = 'digit'
        elif char.isupper():
            char_type = 'uppercase'
        else:
            char_type = 'lowercase'
        
        results[char] = {
            "character": char,
            "medians": medians,
            "strokes": len(medians),
            "type": char_type,
            "source": "opensource_Roboto_contour_method",
            "license": "Open Source",
            "coordinate_system": "MMH"
        }
        
        if char in ['A', 'M', 'W', 'a', 'm', 'w', '1', '8']:
            print(f"  ✅ {char}: 宽{width}, 高{height}, {len(pts)}点")
        elif len(results) % 10 == 0:
            print(f"  ✅ 已完成: {len(results)}/62")
    
    print("\n" + "=" * 70)
    print(f"✅ 成功提取: {len(results)}/62 个字符")
    
    return results


def main():
    print("=" * 70)
    print("使用改进的轮廓提取方法")
    print("=" * 70)
    print("⚠️ 需要安装: pip install scipy")
    print()
    
    try:
        import scipy
        print(f"✅ scipy已安装 (version {scipy.__version__})")
    except ImportError:
        print("❌ scipy未安装，请运行: pip install scipy")
        return 1
    
    font_path = download_font_if_needed()
    if not font_path:
        return 1
    
    results = extract_all_alphanumeric(font_path)
    
    if not results:
        print("\n❌ 没有成功提取任何字符")
        return 1
    
    # 保存
    output_file = 'data/alphanumeric_medians.json'
    
    if os.path.exists(output_file):
        backup_file = output_file + '.before_contour_fix'
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"\n💾 已备份旧文件到: {backup_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    print("\n🔍 质量检查...")
    print("-" * 70)
    for char in ['A', 'M', 'W']:
        data = results[char]
        pts = [p for s in data['medians'] for p in s]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        ratio = height / width if width > 0 else 0
        print(f"  {char}: 宽{width:3d}, 高{height:3d}, 比例{ratio:.2f}, {len(pts):2d}点")
    
    print("\n" + "=" * 70)
    print("✅ 提取完成！使用改进的轮廓方法")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

