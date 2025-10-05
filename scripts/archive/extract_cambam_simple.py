#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从CamBam单线字体提取英文字母和数字（简化版，无需额外依赖）
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("=" * 70)
print("从CamBam单线字体提取数据（简化版）")
print("=" * 70)

# CamBam字体信息
CAMBAM_URL = 'https://github.com/Springwald/CamBamStickFont/raw/master/Fonts/CamBamStickFont1.ttf'
CAMBAM_FILENAME = 'CamBamStickFont1.ttf'


def download_font():
    """下载CamBam字体"""
    fonts_dir = 'fonts'
    os.makedirs(fonts_dir, exist_ok=True)
    
    font_path = os.path.join(fonts_dir, CAMBAM_FILENAME)
    
    if os.path.exists(font_path):
        print(f"✅ 字体已存在: {font_path}")
        return font_path
    
    try:
        print(f"⬇️  下载CamBam字体...")
        print(f"   URL: {CAMBAM_URL}")
        urllib.request.urlretrieve(CAMBAM_URL, font_path)
        print(f"✅ 下载成功: {os.path.getsize(font_path)/1024:.1f} KB")
        return font_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print(f"\n💡 请手动下载:")
        print(f"   1. 访问: {CAMBAM_URL}")
        print(f"   2. 保存到: {font_path}")
        return None


def render_char(char, font_path, size=256):
    """渲染字符"""
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, int(size * 0.6))
    
    bbox = draw.textbbox((0, 0), char, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]
    
    draw.text((x, y), char, fill=0, font=font)
    return img


def extract_centerline_simple(img_array):
    """
    简单的中心线提取（针对单线字体）
    对于每一行，找到黑色像素的中心
    """
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    points = []
    
    # 方法1: 垂直扫描（适合竖线）
    for y in range(binary.shape[0]):
        row = binary[y, :]
        if row.any():
            black_pixels = np.where(row > 0)[0]
            if len(black_pixels) > 0:
                center_x = int(np.mean(black_pixels))
                points.append([center_x, y])
    
    # 如果点太少，尝试水平扫描
    if len(points) < 5:
        points = []
        for x in range(binary.shape[1]):
            col = binary[:, x]
            if col.any():
                black_pixels = np.where(col > 0)[0]
                if len(black_pixels) > 0:
                    center_y = int(np.mean(black_pixels))
                    points.append([x, center_y])
    
    # 简化点数
    if len(points) > 30:
        step = max(1, len(points) // 20)
        points = [points[i] for i in range(0, len(points), step)]
    
    return points


def to_mmh_coords(points):
    """转换为MMH坐标系"""
    if not points:
        return []
    
    scale = 1024.0 / 256.0
    mmh = []
    for x, y in points:
        mmh_x = int(x * scale)
        mmh_y = int(900 - y * scale)
        mmh.append([mmh_x, mmh_y])
    
    # 居中
    xs = [p[0] for p in mmh]
    ys = [p[1] for p in mmh]
    
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    offset_x = 512 - center_x
    offset_y = 388 - center_y
    
    centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in mmh]
    
    return centered


def main():
    # 下载字体
    print("\n📦 步骤1: 下载字体")
    print("-" * 70)
    font_path = download_font()
    
    if not font_path:
        return 1
    
    # 提取字符
    print("\n🎨 步骤2: 提取字符")
    print("-" * 70)
    
    characters = []
    characters.extend([str(i) for i in range(10)])
    characters.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])
    characters.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
    
    print(f"需要提取: {len(characters)} 个字符")
    
    data = {}
    success = 0
    
    for char in characters:
        try:
            img = render_char(char, font_path)
            img_array = np.array(img)
            points = extract_centerline_simple(img_array)
            
            if points and len(points) >= 2:
                mmh_points = to_mmh_coords(points)
                
                char_type = 'digit' if char.isdigit() else ('uppercase' if char.isupper() else 'lowercase')
                
                data[char] = {
                    "character": char,
                    "medians": [mmh_points],
                    "strokes": 1,
                    "type": char_type,
                    "source": "cambam_stick_font_1",
                    "license": "Open Source",
                    "coordinate_system": "MMH"
                }
                
                success += 1
                print(f"  ✅ {char}: {len(mmh_points)}个点")
            else:
                print(f"  ⚠️  {char}: 点数不足")
                
        except Exception as e:
            print(f"  ❌ {char}: {e}")
    
    print(f"\n✅ 成功: {success}/{len(characters)}")
    
    # 统计
    stats = {
        'digit': sum(1 for v in data.values() if v['type'] == 'digit'),
        'uppercase': sum(1 for v in data.values() if v['type'] == 'uppercase'),
        'lowercase': sum(1 for v in data.values() if v['type'] == 'lowercase')
    }
    
    print(f"\n📊 统计:")
    for t, c in stats.items():
        print(f"  {t}: {c}个")
    
    # 保存
    print("\n💾 步骤3: 保存数据")
    print("-" * 70)
    
    output = 'data/alphanumeric_medians_cambam.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize(output)
    print(f"✅ 已保存: {output}")
    print(f"📦 大小: {size/1024:.2f} KB")
    
    if 'A' in data:
        print(f"\n📝 示例 - 字母A:")
        print(f"  点数: {len(data['A']['medians'][0])}")
        print(f"  来源: {data['A']['source']}")
    
    print("\n" + "=" * 70)
    print("✅ 完成！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 对比效果: python test_cambam_render.py")
    print("  2. 如果满意，替换数据:")
    print("     copy data\\alphanumeric_medians_cambam.json data\\alphanumeric_medians.json")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

