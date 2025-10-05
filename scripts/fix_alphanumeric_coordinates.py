#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复字母数字坐标系
将 0-256 坐标系转换为 MMH 的 0-1024 翻转Y坐标系
"""

import json
import os


def convert_to_mmh_coordinates(medians, original_size=256):
    """
    将字母数字坐标从 0-256 转换为 MMH 坐标系
    
    MMH坐标系：
    - X: 0-1024
    - Y: -124 到 900（Y轴翻转，900在上，-124在下）
    
    我们的设计：
    - X: 0-256
    - Y: 0-256（0在上，256在下）
    
    转换公式：
    - X_mmh = X_ours * (1024 / 256) = X_ours * 4
    - Y_mmh = 900 - Y_ours * ((900 - (-124)) / 256) = 900 - Y_ours * 4
    """
    scale = 1024.0 / original_size  # 4.0
    
    # MMH的Y范围
    y_top = 900.0
    y_bottom = -124.0
    y_range = y_top - y_bottom  # 1024
    
    converted_medians = []
    
    for stroke in medians:
        converted_stroke = []
        for x, y in stroke:
            # X: 直接缩放
            x_mmh = x * scale
            
            # Y: 翻转并缩放
            # 我们的Y: 0(上) -> 256(下)
            # MMH的Y: 900(上) -> -124(下)
            y_mmh = y_top - (y * scale)
            
            converted_stroke.append([int(x_mmh), int(y_mmh)])
        
        converted_medians.append(converted_stroke)
    
    return converted_medians


def center_character_in_canvas(medians, canvas_size=1024):
    """
    将字符居中到画布中
    """
    # 找到边界框
    all_points = [pt for stroke in medians for pt in stroke]
    if not all_points:
        return medians
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # 当前中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 目标中心（画布中心）
    target_x = canvas_size / 2  # 512
    target_y = 900 / 2  # MMH的中心Y大约是 388
    
    # 偏移量
    offset_x = target_x - center_x
    offset_y = target_y - center_y
    
    # 应用偏移
    centered_medians = []
    for stroke in medians:
        centered_stroke = [[int(x + offset_x), int(y + offset_y)] for x, y in stroke]
        centered_medians.append(centered_stroke)
    
    return centered_medians


def fix_coordinates(input_file, output_file):
    """修复所有字符的坐标"""
    
    print("=" * 70)
    print("修复字母数字坐标系")
    print("=" * 70)
    
    # 加载数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✅ 加载了 {len(data)} 个字符")
    
    # 转换每个字符
    print("\n🔧 转换坐标系...")
    
    fixed_data = {}
    for char, char_data in data.items():
        medians = char_data.get('medians', [])
        
        # 1. 转换为MMH坐标系
        mmh_medians = convert_to_mmh_coordinates(medians)
        
        # 2. 居中
        centered_medians = center_character_in_canvas(mmh_medians)
        
        # 3. 更新数据
        fixed_char_data = dict(char_data)
        fixed_char_data['medians'] = centered_medians
        fixed_char_data['coordinate_system'] = 'MMH'
        
        fixed_data[char] = fixed_char_data
        
        # 显示进度
        if char in '0AaZ':  # 显示几个关键字符的信息
            orig_pts = [pt for stroke in medians for pt in stroke]
            new_pts = [pt for stroke in centered_medians for pt in stroke]
            if orig_pts and new_pts:
                print(f"  {char}: X({min([p[0] for p in orig_pts])}-{max([p[0] for p in orig_pts])}) "
                      f"→ X({min([p[0] for p in new_pts])}-{max([p[0] for p in new_pts])}), "
                      f"Y({min([p[1] for p in orig_pts])}-{max([p[1] for p in orig_pts])}) "
                      f"→ Y({min([p[1] for p in new_pts])}-{max([p[1] for p in new_pts])})")
    
    print(f"\n✅ 转换完成: {len(fixed_data)} 个字符")
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 验证
    print("\n" + "=" * 70)
    print("验证修复结果")
    print("-" * 70)
    
    # 检查几个字符的坐标范围
    test_chars = ['1', 'A', 'a']
    for char in test_chars:
        if char in fixed_data:
            medians = fixed_data[char]['medians']
            all_pts = [pt for stroke in medians for pt in stroke]
            if all_pts:
                xs = [p[0] for p in all_pts]
                ys = [p[1] for p in all_pts]
                print(f"  {char}: X({min(xs):4d} - {max(xs):4d}), Y({min(ys):4d} - {max(ys):4d})")
    
    print("-" * 70)
    print("✅ 坐标系修复完成！")
    print("=" * 70)
    
    return len(fixed_data)


def main():
    input_file = 'data/alphanumeric_medians.json'
    output_file = 'data/alphanumeric_medians.json'
    
    # 备份原文件
    backup_file = 'data/alphanumeric_medians.json.backup'
    if os.path.exists(input_file):
        import shutil
        shutil.copy(input_file, backup_file)
        print(f"✅ 已备份到: {backup_file}\n")
    
    # 修复
    count = fix_coordinates(input_file, output_file)
    
    print("\n📝 提示:")
    print("  1. 原文件已备份")
    print("  2. 坐标系已转换为MMH格式")
    print("  3. 所有字符已居中")
    print("  4. 请重启服务器测试")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

