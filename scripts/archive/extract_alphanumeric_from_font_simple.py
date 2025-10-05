#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从系统字体提取英文字母和数字（简化版）
使用PIL渲染字符，然后提取骨架作为median
这个方法更简单，不需要fontTools
"""

import os
import json
import platform
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def find_latin_font():
    """查找系统中的拉丁字母字体"""
    system = platform.system()
    
    candidates = []
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/arial.ttf',      # Arial
            'C:/Windows/Fonts/times.ttf',      # Times New Roman
            'C:/Windows/Fonts/calibri.ttf',    # Calibri
        ]
    elif system == 'Darwin':  # macOS
        candidates = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Times.ttc',
        ]
    else:  # Linux
        candidates = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ 找到字体: {path}")
            return path
    
    print("❌ 未找到合适的拉丁字母字体")
    return None


def render_char_to_image(char, font_path, size=256):
    """渲染字符到图像"""
    try:
        # 创建图像
        img = Image.new('L', (size, size), color=255)  # 白色背景
        draw = ImageDraw.Draw(img)
        
        # 加载字体（使用较大字体以获得更好的质量）
        try:
            font = ImageFont.truetype(font_path, int(size * 0.7))
        except Exception as e:
            print(f"  ⚠️ 字体加载失败: {e}")
            return None
        
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


def extract_skeleton(img_array):
    """
    从图像提取骨架线
    策略：扫描图像，提取轮廓的中心线
    """
    # 二值化
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 提取轮廓点
    points = []
    
    # 垂直扫描 - 从上到下
    for y in range(binary.shape[0]):
        row = binary[y, :]
        if row.any():
            black_pixels = np.where(row > 0)[0]
            if len(black_pixels) > 0:
                # 取中点
                center_x = int(np.mean(black_pixels))
                points.append([center_x, y])
    
    # 简化点：减少密度
    if len(points) > 20:
        step = max(1, len(points) // 15)
        points = [points[i] for i in range(0, len(points), step)]
    
    return points if len(points) >= 2 else []


def convert_to_mmh_coordinates(points, original_size=256):
    """
    将0-256坐标转换为MMH坐标系
    MMH: X(0-1024), Y(900到-124，Y轴翻转)
    """
    scale = 1024.0 / original_size  # 4.0
    y_top = 900.0
    
    mmh_points = []
    for x, y in points:
        x_mmh = x * scale
        y_mmh = y_top - (y * scale)  # 翻转Y轴
        mmh_points.append([int(x_mmh), int(y_mmh)])
    
    return mmh_points


def center_character(points):
    """将字符居中到画布中心"""
    if not points:
        return []
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    # 当前中心
    center_x = (min(xs) + max(xs)) / 2
    center_y = (min(ys) + max(ys)) / 2
    
    # 目标中心（MMH坐标系）
    target_x = 512
    target_y = 388
    
    # 偏移
    offset_x = target_x - center_x
    offset_y = target_y - center_y
    
    # 应用偏移
    centered = [[int(p[0] + offset_x), int(p[1] + offset_y)] for p in points]
    
    return centered


def extract_char_median(char, font_path):
    """提取单个字符的median"""
    # 1. 渲染字符
    img = render_char_to_image(char, font_path)
    if img is None:
        return None
    
    # 2. 提取骨架
    img_array = np.array(img)
    skeleton = extract_skeleton(img_array)
    
    if not skeleton:
        return None
    
    # 3. 转换坐标系
    mmh_points = convert_to_mmh_coordinates(skeleton)
    
    # 4. 居中
    centered = center_character(mmh_points)
    
    if len(centered) < 2:
        return None
    
    return [centered]  # 返回为单笔画


def extract_all_alphanumeric(font_path):
    """提取所有字母和数字"""
    
    # 要提取的字符
    chars = []
    # 数字 0-9
    chars.extend([str(i) for i in range(10)])
    # 大写字母 A-Z
    chars.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])
    # 小写字母 a-z
    chars.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
    
    results = {}
    
    print("\n🎨 提取字符...")
    print("=" * 70)
    
    for i, char in enumerate(chars):
        medians = extract_char_median(char, font_path)
        
        if medians is None:
            print(f"  ❌ {char}")
            continue
        
        # 确定类型
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
            "source": "system_font_pil",
            "coordinate_system": "MMH"
        }
        
        # 显示进度
        if char in '0AZaz' or (i + 1) % 10 == 0:
            pts = [p for s in medians for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x_center = (min(xs) + max(xs)) // 2
            y_center = (min(ys) + max(ys)) // 2
            print(f"  ✅ {char}: X中心={x_center}, Y中心={y_center}")
        else:
            print(f"  ✅ {char}", end='')
            if (i + 1) % 20 == 0:
                print()  # 每20个字符换行
    
    print("\n" + "=" * 70)
    print(f"✅ 成功提取: {len(results)}/{len(chars)} 个字符")
    
    # 统计
    types = {}
    for char, data in results.items():
        t = data.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    print("\n📊 统计:")
    for t, count in sorted(types.items()):
        print(f"  {t:12s}: {count} 个")
    
    return results


def main():
    print("=" * 70)
    print("从系统字体提取英文字母和数字（PIL版本）")
    print("=" * 70)
    
    # 查找字体
    font_path = find_latin_font()
    if not font_path:
        print("\n❌ 错误: 未找到合适的字体")
        print("\n💡 建议:")
        print("  1. 确保系统安装了Arial或Times New Roman字体")
        print("  2. Windows系统通常在 C:/Windows/Fonts/")
        return 1
    
    # 提取字符
    results = extract_all_alphanumeric(font_path)
    
    if not results:
        print("\n❌ 没有成功提取任何字符")
        return 1
    
    # 保存结果
    output_file = 'data/alphanumeric_medians.json'
    
    # 备份旧文件
    if os.path.exists(output_file):
        backup_file = output_file + '.manual_backup'
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"\n💾 已备份旧文件到: {backup_file}")
    
    # 保存新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 验证几个字符
    print("\n🔍 验证坐标范围:")
    print("-" * 70)
    test_chars = ['1', '5', 'A', 'Z', 'a', 'z']
    for char in test_chars:
        if char in results:
            medians = results[char]['medians']
            pts = [p for s in medians for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x_center = (min(xs) + max(xs)) // 2
            y_center = (min(ys) + max(ys)) // 2
            print(f"  {char}: X({min(xs):3d}-{max(xs):3d}) 中心{x_center:3d}  |  "
                  f"Y({min(ys):3d}-{max(ys):3d}) 中心{y_center:3d}")
    print("-" * 70)
    print("  预期: X中心≈512, Y中心≈388")
    
    print("\n" + "=" * 70)
    print("✅ 提取完成！")
    print("\n📝 下一步:")
    print("  1. 重启服务器: python start_server.py")
    print("  2. 测试输入: 123, ABC, Hello")
    print("  3. 检查字符是否正确显示和居中")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

