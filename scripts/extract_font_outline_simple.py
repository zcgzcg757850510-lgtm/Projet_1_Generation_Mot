#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的字体提取 - 使用轮廓而不是单一中轴线
不依赖scipy，使用简单但有效的方法
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np


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
    """渲染字符到图像"""
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


def extract_outline_trace(img_array):
    """
    提取轮廓跟踪 - 沿着字符边缘走
    这比单一中心线更准确
    """
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 找到所有黑色像素
    y_coords, x_coords = np.where(binary > 0)
    
    if len(x_coords) == 0:
        return []
    
    # 对每一行，找到最左和最右的点
    # 这样可以捕捉字母的实际宽度
    outline_points = []
    
    y_min, y_max = y_coords.min(), y_coords.max()
    
    for y in range(y_min, y_max + 1):
        # 找到这一行的所有X坐标
        row_mask = (y_coords == y)
        if not row_mask.any():
            continue
        
        xs_in_row = x_coords[row_mask]
        
        if len(xs_in_row) > 0:
            x_left = xs_in_row.min()
            x_right = xs_in_row.max()
            x_center = (x_left + x_right) // 2
            
            # 添加左、中、右三个点来表示这一行
            # 这样可以保留字母的宽度信息
            outline_points.append([x_left, y])
            if x_right - x_left > 5:  # 如果宽度足够，添加中心点
                outline_points.append([x_center, y])
            if x_right != x_left:  # 避免重复
                outline_points.append([x_right, y])
    
    # 简化点数（保留关键点）- 修改为更智能的方法
    if len(outline_points) > 40:
        # 不要简单地按步长采样，而是保留极值点（左右边界）
        simplified = []
        prev_x = None
        
        for i, point in enumerate(outline_points):
            x, y = point
            # 保留每行的第一个和最后一个点（左右边界）
            is_boundary = (i == 0 or i == len(outline_points) - 1)
            # 或者X坐标发生明显变化的点
            is_change = (prev_x is None or abs(x - prev_x) > 3)
            # 或者每隔几个点采样一次
            is_sample = (i % max(1, len(outline_points) // 30) == 0)
            
            if is_boundary or is_change or is_sample:
                simplified.append(point)
                prev_x = x
        
        outline_points = simplified
    
    return outline_points if len(outline_points) >= 2 else []


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
    outline = extract_outline_trace(img_array)
    
    if not outline:
        return None
    
    mmh_points = convert_to_mmh_coordinates(outline)
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
    
    print(f"\n🎨 使用轮廓跟踪方法提取字符...")
    print("=" * 70)
    
    for i, char in enumerate(chars):
        medians = extract_char_median(char, font_path)
        
        if medians is None:
            print(f"  ❌ {char}")
            continue
        
        # 质量检查
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
            "source": "opensource_Roboto_outline_trace",
            "license": "Open Source",
            "coordinate_system": "MMH"
        }
        
        # 显示关键字符的质量信息
        if char in ['A', 'B', 'M', 'W', 'a', 'm', 'w', '1']:
            ratio = height / width if width > 0 else 0
            print(f"  ✅ {char}: 宽{width:3d}, 高{height:3d}, 比例{ratio:.1f}, {len(pts):2d}点")
        elif (i + 1) % 15 == 0:
            print(f"  ... 已完成: {len(results)}/62")
    
    print("\n" + "=" * 70)
    print(f"✅ 成功提取: {len(results)}/62 个字符")
    
    return results


def main():
    print("=" * 70)
    print("使用轮廓跟踪方法提取字体")
    print("=" * 70)
    print("✨ 改进：提取字符的完整轮廓而不是单一中心线")
    print()
    
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
        backup_file = output_file + '.before_outline_fix'
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"\n💾 已备份旧文件到: {backup_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    print("\n🔍 质量对比检查:")
    print("-" * 70)
    print("  字符 | 宽度 | 高度 | 宽高比 | 点数")
    print("-" * 70)
    
    for char in ['A', 'B', 'M', 'W', 'a', 'b', 'm', 'w', '1', '8']:
        if char in results:
            data = results[char]
            pts = [p for s in data['medians'] for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            ratio = height / width if width > 0 else 0
            print(f"    {char}  | {width:4d} | {height:4d} | {ratio:5.2f} | {len(pts):3d}")
    
    print("-" * 70)
    print("预期：宽度应该>50，宽高比应该在0.5-3之间")
    
    print("\n" + "=" * 70)
    print("✅ 提取完成！")
    print("\n📝 建议:")
    print("  1. 运行 python check_letter_quality.py 验证质量")
    print("  2. 重启服务器测试: python start_server.py")
    print("  3. 测试输入: ABC, abc, 123")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

