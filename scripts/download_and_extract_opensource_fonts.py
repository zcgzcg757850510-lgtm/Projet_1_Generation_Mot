#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载开源字体并提取英文字母和数字
使用Google Noto Sans等开源字体
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np


# 开源字体下载链接
OPENSOURCE_FONTS = {
    'Roboto-Regular': {
        'url': 'https://github.com/google/roboto/raw/main/src/hinted/Roboto-Regular.ttf',
        'description': 'Google Roboto字体（开源，Apache License 2.0）'
    },
    'NotoSans-Regular': {
        'url': 'https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf',
        'description': 'Google Noto Sans字体（开源，OFL）'
    },
    'SourceSansPro-Regular': {
        'url': 'https://github.com/adobe-fonts/source-sans/raw/release/TTF/SourceSans3-Regular.ttf',
        'description': 'Adobe Source Sans Pro字体（开源，OFL）'
    },
    'DejaVuSans': {
        'url': 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf',
        'description': 'DejaVu Sans字体（开源，自由许可证）'
    }
}


def download_font(font_name, font_info, fonts_dir='fonts'):
    """下载开源字体"""
    os.makedirs(fonts_dir, exist_ok=True)
    
    font_path = os.path.join(fonts_dir, f'{font_name}.ttf')
    
    # 如果已存在，跳过
    if os.path.exists(font_path):
        print(f"  ✅ {font_name} - 已存在")
        return font_path
    
    try:
        print(f"  ⬇️  {font_name} - 下载中...")
        print(f"     {font_info['description']}")
        print(f"     URL: {font_info['url']}")
        
        # 下载字体
        urllib.request.urlretrieve(font_info['url'], font_path)
        
        file_size = os.path.getsize(font_path)
        print(f"  ✅ {font_name} - 下载成功 ({file_size/1024:.1f} KB)")
        return font_path
        
    except Exception as e:
        print(f"  ❌ {font_name} - 下载失败: {e}")
        return None


def render_char_to_image(char, font_path, size=256):
    """渲染字符到图像"""
    try:
        # 创建图像
        img = Image.new('L', (size, size), color=255)  # 白色背景
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        font = ImageFont.truetype(font_path, int(size * 0.7))
        
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
    """从图像提取骨架线"""
    # 二值化
    binary = (img_array < 128).astype(np.uint8)
    
    if not binary.any():
        return []
    
    # 提取轮廓点
    points = []
    
    # 垂直扫描
    for y in range(binary.shape[0]):
        row = binary[y, :]
        if row.any():
            black_pixels = np.where(row > 0)[0]
            if len(black_pixels) > 0:
                center_x = int(np.mean(black_pixels))
                points.append([center_x, y])
    
    # 简化点
    if len(points) > 20:
        step = max(1, len(points) // 15)
        points = [points[i] for i in range(0, len(points), step)]
    
    return points if len(points) >= 2 else []


def convert_to_mmh_coordinates(points, original_size=256):
    """将0-256坐标转换为MMH坐标系"""
    scale = 1024.0 / original_size
    y_top = 900.0
    
    mmh_points = []
    for x, y in points:
        x_mmh = x * scale
        y_mmh = y_top - (y * scale)
        mmh_points.append([int(x_mmh), int(y_mmh)])
    
    return mmh_points


def center_character(points):
    """将字符居中"""
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
    """提取单个字符的median"""
    img = render_char_to_image(char, font_path)
    if img is None:
        return None
    
    img_array = np.array(img)
    skeleton = extract_skeleton(img_array)
    
    if not skeleton:
        return None
    
    mmh_points = convert_to_mmh_coordinates(skeleton)
    centered = center_character(mmh_points)
    
    if len(centered) < 2:
        return None
    
    return [centered]


def extract_all_alphanumeric(font_path, font_name):
    """提取所有字母和数字"""
    
    chars = []
    chars.extend([str(i) for i in range(10)])  # 0-9
    chars.extend([chr(i) for i in range(ord('A'), ord('Z') + 1)])  # A-Z
    chars.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])  # a-z
    
    results = {}
    
    print(f"\n🎨 从 {font_name} 提取字符...")
    print("=" * 70)
    
    for i, char in enumerate(chars):
        medians = extract_char_median(char, font_path)
        
        if medians is None:
            print(f"  ❌ {char}")
            continue
        
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
            "source": f"opensource_{font_name}",
            "license": "Open Source",
            "coordinate_system": "MMH"
        }
        
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
                print()
    
    print("\n" + "=" * 70)
    print(f"✅ 成功提取: {len(results)}/{len(chars)} 个字符")
    
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
    print("使用开源字体提取英文字母和数字")
    print("=" * 70)
    print("\n📜 使用开源字体（遵循开源许可证）:")
    for name, info in OPENSOURCE_FONTS.items():
        print(f"  • {info['description']}")
    
    print("\n" + "=" * 70)
    print("下载开源字体...")
    print("=" * 70)
    
    # 下载字体
    downloaded_fonts = {}
    for font_name, font_info in OPENSOURCE_FONTS.items():
        font_path = download_font(font_name, font_info)
        if font_path:
            downloaded_fonts[font_name] = font_path
    
    if not downloaded_fonts:
        print("\n❌ 没有成功下载任何字体")
        return 1
    
    print(f"\n✅ 成功下载 {len(downloaded_fonts)} 个字体")
    
    # 选择第一个可用字体进行提取
    selected_name = list(downloaded_fonts.keys())[0]
    selected_path = downloaded_fonts[selected_name]
    
    print(f"\n📝 使用字体: {selected_name}")
    
    # 提取字符
    results = extract_all_alphanumeric(selected_path, selected_name)
    
    if not results:
        print("\n❌ 没有成功提取任何字符")
        return 1
    
    # 保存结果
    output_file = 'data/alphanumeric_medians.json'
    
    # 备份旧文件
    if os.path.exists(output_file):
        backup_file = output_file + '.old_manual'
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"\n💾 已备份旧文件到: {backup_file}")
    
    # 保存新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 添加许可证信息
    license_file = 'fonts/LICENSE.txt'
    with open(license_file, 'w', encoding='utf-8') as f:
        f.write("开源字体许可证信息\n")
        f.write("=" * 70 + "\n\n")
        for name, info in OPENSOURCE_FONTS.items():
            if name in downloaded_fonts:
                f.write(f"{name}:\n")
                f.write(f"  描述: {info['description']}\n")
                f.write(f"  来源: {info['url']}\n")
                f.write(f"  许可证: 开源（详见字体项目）\n\n")
    
    print(f"📜 许可证信息已保存到: {license_file}")
    
    # 验证坐标
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
    print("✅ 提取完成！使用开源字体")
    print("\n📝 下一步:")
    print("  1. 查看 fonts/ 目录中的下载字体")
    print("  2. 查看 fonts/LICENSE.txt 了解许可证信息")
    print("  3. 重启服务器: python start_server.py")
    print("  4. 测试输入: 123, ABC, Hello")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

