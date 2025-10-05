#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从CamBam单线字体提取英文字母和数字
CamBam是专门为CNC加工设计的单线字体，天然就是中轴线格式
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from skimage.morphology import skeletonize

print("=" * 70)
print("从CamBam单线字体提取数据")
print("=" * 70)

# CamBam字体下载信息
CAMBAM_FONTS = {
    'CamBam Stick 1': {
        'url': 'https://github.com/Springwald/CamBamStickFont/raw/master/Fonts/CamBamStickFont1.ttf',
        'filename': 'CamBamStickFont1.ttf',
        'description': 'CamBam单线字体1号（基础款）'
    },
    'CamBam Stick 2': {
        'url': 'https://github.com/Springwald/CamBamStickFont/raw/master/Fonts/CamBamStickFont2.ttf',
        'filename': 'CamBamStickFont2.ttf',
        'description': 'CamBam单线字体2号（带衬线）'
    },
    'CamBam Stick 9': {
        'url': 'https://github.com/Springwald/CamBamStickFont/raw/master/Fonts/CamBamStickFont9.ttf',
        'filename': 'CamBamStickFont9.ttf',
        'description': 'CamBam单线字体9号（现代款）'
    }
}


def download_cambam_font(font_info, fonts_dir='fonts'):
    """下载CamBam字体"""
    os.makedirs(fonts_dir, exist_ok=True)
    
    font_path = os.path.join(fonts_dir, font_info['filename'])
    
    # 如果已存在，跳过
    if os.path.exists(font_path):
        print(f"  ✅ 字体已存在: {font_info['filename']}")
        return font_path
    
    try:
        print(f"  ⬇️  下载中: {font_info['description']}")
        print(f"     URL: {font_info['url']}")
        
        # 下载字体
        urllib.request.urlretrieve(font_info['url'], font_path)
        
        file_size = os.path.getsize(font_path)
        print(f"  ✅ 下载成功: {file_size/1024:.1f} KB")
        return font_path
        
    except Exception as e:
        print(f"  ❌ 下载失败: {e}")
        print(f"  💡 请手动下载: {font_info['url']}")
        print(f"     并保存到: {font_path}")
        return None


def render_char_to_image(char, font_path, size=256):
    """渲染字符到图像"""
    try:
        # 创建图像
        img = Image.new('L', (size, size), color=255)  # 白色背景
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        font = ImageFont.truetype(font_path, int(size * 0.6))
        
        # 获取文字边界
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 居中绘制
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        
        draw.text((x, y), char, fill=0, font=font)  # 黑色文字
        
        return img
    except Exception as e:
        print(f"  ❌ 渲染失败 {char}: {e}")
        return None


def extract_centerline_from_image(img_array):
    """
    从图像提取中心线
    CamBam是单线字体，所以提取会很干净
    """
    # 二值化
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 骨架化
    skeleton = skeletonize(binary)
    
    # 提取骨架点
    points = []
    y_coords, x_coords = np.where(skeleton > 0)
    
    if len(y_coords) == 0:
        return []
    
    # 按照连续性排序点
    # 简单方法：按Y坐标排序（适合竖线）或X坐标排序（适合横线）
    
    # 判断主方向
    y_range = y_coords.max() - y_coords.min()
    x_range = x_coords.max() - x_coords.min()
    
    if y_range > x_range:
        # 竖向为主，按Y排序
        sorted_indices = np.argsort(y_coords)
    else:
        # 横向为主，按X排序
        sorted_indices = np.argsort(x_coords)
    
    for idx in sorted_indices:
        points.append([int(x_coords[idx]), int(y_coords[idx])])
    
    # 简化点（Douglas-Peucker算法的简化版）
    if len(points) > 30:
        step = max(1, len(points) // 20)
        points = [points[i] for i in range(0, len(points), step)]
    
    return points


def convert_to_mmh_coordinates(points, original_size=256):
    """将0-256坐标转换为MMH坐标系"""
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
    """将字符居中到标准位置"""
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


def extract_character(char, font_path):
    """提取单个字符的数据"""
    # 渲染
    img = render_char_to_image(char, font_path, size=256)
    if img is None:
        return None
    
    # 转为numpy数组
    img_array = np.array(img)
    
    # 提取中心线
    points = extract_centerline_from_image(img_array)
    if not points or len(points) < 2:
        return None
    
    # 转换坐标
    mmh_points = convert_to_mmh_coordinates(points)
    
    # 居中
    centered_points = center_character(mmh_points)
    
    return centered_points


def main():
    print("\n📦 步骤1: 下载CamBam字体")
    print("-" * 70)
    
    # 选择字体（推荐使用1号基础款）
    selected_font = 'CamBam Stick 1'
    font_info = CAMBAM_FONTS[selected_font]
    
    font_path = download_cambam_font(font_info)
    
    if not font_path or not os.path.exists(font_path):
        print("\n❌ 字体下载失败！")
        print("\n💡 解决方案:")
        print("  1. 手动下载字体:")
        print(f"     {font_info['url']}")
        print(f"  2. 保存到: fonts/{font_info['filename']}")
        print("  3. 重新运行此脚本")
        return 1
    
    print("\n🎨 步骤2: 提取字符")
    print("-" * 70)
    
    # 要提取的字符
    characters = []
    
    # 数字 0-9
    characters.extend([str(i) for i in range(10)])
    
    # 大写字母 A-Z
    characters.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])
    
    # 小写字母 a-z
    characters.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
    
    print(f"总共需要提取: {len(characters)} 个字符")
    
    # 提取数据
    alphanum_data = {}
    success_count = 0
    
    for char in characters:
        try:
            points = extract_character(char, font_path)
            
            if points and len(points) >= 2:
                # 判断类型
                if char.isdigit():
                    char_type = 'digit'
                elif char.isupper():
                    char_type = 'uppercase'
                else:
                    char_type = 'lowercase'
                
                alphanum_data[char] = {
                    "character": char,
                    "medians": [points],  # CamBam通常是单笔画
                    "strokes": 1,
                    "type": char_type,
                    "source": "cambam_stick_font_1",
                    "license": "Open Source",
                    "coordinate_system": "MMH"
                }
                
                success_count += 1
                print(f"  ✅ {char}: {len(points)}个点")
            else:
                print(f"  ⚠️  {char}: 提取失败（点数不足）")
                
        except Exception as e:
            print(f"  ❌ {char}: 提取失败 - {e}")
    
    print(f"\n✅ 成功提取: {success_count}/{len(characters)} 个字符")
    
    # 统计
    digit_count = sum(1 for v in alphanum_data.values() if v['type'] == 'digit')
    upper_count = sum(1 for v in alphanum_data.values() if v['type'] == 'uppercase')
    lower_count = sum(1 for v in alphanum_data.values() if v['type'] == 'lowercase')
    
    print(f"\n📊 统计:")
    print(f"  digit       : {digit_count} 个")
    print(f"  uppercase   : {upper_count} 个")
    print(f"  lowercase   : {lower_count} 个")
    
    # 保存数据
    print("\n💾 步骤3: 保存数据")
    print("-" * 70)
    
    output_file = 'data/alphanumeric_medians_cambam.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(alphanum_data, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    print(f"✅ 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 显示示例
    if 'A' in alphanum_data:
        print("\n📝 示例数据 - 字母A:")
        print(f"  来源: {alphanum_data['A']['source']}")
        print(f"  笔画数: {alphanum_data['A']['strokes']}")
        print(f"  点数: {len(alphanum_data['A']['medians'][0])}")
    
    print("\n" + "=" * 70)
    print("✅ 提取完成！")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 查看生成的数据: data/alphanumeric_medians_cambam.json")
    print("  2. 测试效果: python test_cambam_render.py")
    print("  3. 如果满意，替换当前数据:")
    print("     copy data\\alphanumeric_medians_cambam.json data\\alphanumeric_medians.json")
    print("  4. 重启服务器: python start_server.py")
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)

