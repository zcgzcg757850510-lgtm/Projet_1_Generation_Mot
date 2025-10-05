#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从开源字体提取标点符号
使用开源中文字体（如Noto Sans CJK）和英文字体
"""

import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import numpy as np


# 开源字体下载链接
OPENSOURCE_FONTS = {
    'NotoSansCJK-Regular': {
        'url': 'https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf',
        'description': 'Google Noto Sans CJK 简体中文（开源，OFL）',
        'type': 'cjk'
    },
    'NotoSans-Regular': {
        'url': 'https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf',
        'description': 'Google Noto Sans 拉丁字母（开源，OFL）',
        'type': 'latin'
    },
    'SourceHanSans-Regular': {
        'url': 'https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf',
        'description': 'Adobe 思源黑体（开源，OFL）',
        'type': 'cjk'
    }
}


def download_font(font_name, font_info, fonts_dir='fonts'):
    """下载开源字体"""
    os.makedirs(fonts_dir, exist_ok=True)
    
    # 确定文件扩展名
    ext = '.otf' if font_info['url'].endswith('.otf') else '.ttf'
    font_path = os.path.join(fonts_dir, f'{font_name}{ext}')
    
    # 如果已存在，跳过
    if os.path.exists(font_path):
        print(f"  ✅ {font_name} - 已存在")
        return font_path
    
    try:
        print(f"  ⬇️  {font_name} - 下载中...")
        print(f"     {font_info['description']}")
        
        # 大文件可能需要较长时间
        print(f"     ⚠️  CJK字体较大(~10MB)，请耐心等待...")
        
        # 下载字体
        urllib.request.urlretrieve(font_info['url'], font_path)
        
        file_size = os.path.getsize(font_path)
        print(f"  ✅ {font_name} - 下载成功 ({file_size/1024/1024:.1f} MB)")
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
        
        # 加载字体（标点符号使用较大字体以获得清晰度）
        try:
            font = ImageFont.truetype(font_path, int(size * 0.6))
        except Exception as e:
            print(f"  ⚠️ 字体加载失败 {char}: {e}")
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
    """将字符居中到画布中心"""
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


def extract_all_punctuation(font_paths, font_name):
    """提取所有标点符号"""
    
    # 中文标点符号
    chinese_punctuation = [
        '。', '，', '、', '；', '：',
        '！', '？',
        '"', '"', ''', ''',
        '（', '）', '《', '》', '【', '】', '「', '」', '『', '』',
        '…', '——', '—', '·'
    ]
    
    # 英文标点符号
    english_punctuation = [
        '.', ',', ';', ':',
        '!', '?',
        '"', "'",
        '(', ')', '[', ']', '{', '}',
        '-', '/', '\\', '&', '@', '#', '$', '%', '*', '+', '='
    ]
    
    # 合并所有标点
    all_punctuation = chinese_punctuation + english_punctuation
    
    results = {}
    
    print(f"\n🎨 从 {font_name} 提取标点符号...")
    print("=" * 70)
    
    for i, char in enumerate(all_punctuation):
        # 选择合适的字体
        # 中文标点使用CJK字体，英文标点使用拉丁字体
        if char in chinese_punctuation:
            font_path = font_paths.get('cjk')
        else:
            font_path = font_paths.get('latin', font_paths.get('cjk'))
        
        if not font_path:
            print(f"  ❌ {char} - 没有可用字体")
            continue
        
        medians = extract_char_median(char, font_path)
        
        if medians is None:
            print(f"  ❌ {char} - 提取失败")
            continue
        
        # 确定类型
        if char in chinese_punctuation:
            punct_type = 'chinese_punctuation'
        else:
            punct_type = 'english_punctuation'
        
        results[char] = {
            "character": char,
            "medians": medians,
            "strokes": len(medians),
            "type": punct_type,
            "source": f"opensource_{font_name}",
            "license": "Open Source (OFL)",
            "coordinate_system": "MMH"
        }
        
        # 显示进度
        if char in '。，！？.,' or (i + 1) % 5 == 0:
            pts = [p for s in medians for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x_center = (min(xs) + max(xs)) // 2
            y_center = (min(ys) + max(ys)) // 2
            print(f"  ✅ {char}: X中心={x_center}, Y中心={y_center}")
        else:
            print(f"  ✅ {char}", end='')
            if (i + 1) % 10 == 0:
                print()
    
    print("\n" + "=" * 70)
    print(f"✅ 成功提取: {len(results)}/{len(all_punctuation)} 个标点符号")
    
    # 统计
    types = {}
    for char, data in results.items():
        t = data.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    print("\n📊 统计:")
    for t, count in sorted(types.items()):
        print(f"  {t:25s}: {count} 个")
    
    return results


def main():
    print("=" * 70)
    print("从开源字体提取标点符号")
    print("=" * 70)
    print("\n📜 使用开源字体（遵循开源许可证）:")
    for name, info in OPENSOURCE_FONTS.items():
        print(f"  • {info['description']}")
    
    print("\n" + "=" * 70)
    print("下载开源字体...")
    print("=" * 70)
    
    # 下载字体
    downloaded_fonts = {}
    font_paths_by_type = {}
    
    for font_name, font_info in OPENSOURCE_FONTS.items():
        font_path = download_font(font_name, font_info)
        if font_path:
            downloaded_fonts[font_name] = font_path
            font_type = font_info['type']
            if font_type not in font_paths_by_type:
                font_paths_by_type[font_type] = font_path
    
    if not downloaded_fonts:
        print("\n❌ 没有成功下载任何字体")
        print("\n💡 提示：可能是网络问题或GitHub访问受限")
        print("   建议：")
        print("   1. 检查网络连接")
        print("   2. 使用VPN或镜像站点")
        print("   3. 或手动下载字体到 fonts/ 目录")
        return 1
    
    print(f"\n✅ 成功下载 {len(downloaded_fonts)} 个字体")
    
    # 确保至少有一个CJK字体
    if 'cjk' not in font_paths_by_type:
        print("\n❌ 错误: 没有CJK字体，无法提取中文标点")
        print("💡 请确保至少下载了 Noto Sans CJK 或 Source Han Sans")
        return 1
    
    # 选择字体名称用于标记
    selected_name = list(downloaded_fonts.keys())[0]
    
    print(f"\n📝 使用字体:")
    print(f"  • 中文标点: {font_paths_by_type.get('cjk', 'N/A')}")
    print(f"  • 英文标点: {font_paths_by_type.get('latin', font_paths_by_type.get('cjk', 'N/A'))}")
    
    # 提取标点符号
    results = extract_all_punctuation(font_paths_by_type, selected_name)
    
    if not results:
        print("\n❌ 没有成功提取任何标点符号")
        return 1
    
    # 保存结果
    output_file = 'data/punctuation_medians.json'
    
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
    license_file = 'fonts/PUNCTUATION_LICENSE.txt'
    with open(license_file, 'w', encoding='utf-8') as f:
        f.write("标点符号开源字体许可证信息\n")
        f.write("=" * 70 + "\n\n")
        f.write("本项目的标点符号数据提取自以下开源字体：\n\n")
        for name, info in OPENSOURCE_FONTS.items():
            if name in downloaded_fonts:
                f.write(f"{name}:\n")
                f.write(f"  描述: {info['description']}\n")
                f.write(f"  来源: {info['url']}\n")
                f.write(f"  许可证: SIL Open Font License (OFL)\n")
                f.write(f"  类型: {info['type']}\n\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("SIL Open Font License (OFL) 许可证要点：\n")
        f.write("- ✅ 可以免费使用\n")
        f.write("- ✅ 可以商业使用\n")
        f.write("- ✅ 可以修改\n")
        f.write("- ✅ 可以分发\n")
        f.write("- ⚠️ 需要保留许可证声明\n")
        f.write("\n详细许可证信息请访问：https://scripts.sil.org/OFL\n")
    
    print(f"📜 许可证信息已保存到: {license_file}")
    
    # 验证坐标
    print("\n🔍 验证坐标范围:")
    print("-" * 70)
    test_chars = ['。', '，', '！', '？', '.', ',', '!', '?']
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
    print("✅ 标点符号提取完成！使用开源字体")
    print("\n📝 下一步:")
    print("  1. 查看 fonts/ 目录中的下载字体")
    print("  2. 查看 fonts/PUNCTUATION_LICENSE.txt 了解许可证信息")
    print("  3. 重启服务器: python start_server.py")
    print("  4. 测试输入: 你好，世界！Hello, World!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

