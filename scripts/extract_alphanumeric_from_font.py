#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从系统字体提取英文字母和数字
使用fontTools从TrueType字体提取真实的字形轮廓
"""

import os
import json
import platform


def find_latin_font():
    """查找系统中的拉丁字母字体"""
    system = platform.system()
    
    candidates = []
    if system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/arial.ttf',      # Arial
            'C:/Windows/Fonts/times.ttf',      # Times New Roman
            'C:/Windows/Fonts/calibri.ttf',    # Calibri
            'C:/Windows/Fonts/consola.ttf',    # Consolas
        ]
    elif system == 'Darwin':  # macOS
        candidates = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Times.ttc',
        ]
    else:  # Linux
        candidates = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
    
    for path in candidates:
        if os.path.exists(path):
            print(f"✅ 找到字体: {path}")
            return path
    
    print("❌ 未找到合适的拉丁字母字体")
    return None


def extract_glyph_contours(font, char):
    """从字体提取字符的轮廓"""
    try:
        # 获取字符编码
        cmap = font.getBestCmap()
        if not cmap:
            return None
        
        char_code = ord(char)
        glyph_name = cmap.get(char_code)
        
        if not glyph_name:
            return None
        
        # 获取glyf表（TrueType轮廓）
        if 'glyf' not in font:
            return None
        
        glyf_table = font['glyf']
        glyph = glyf_table[glyph_name]
        
        # 获取坐标
        if not hasattr(glyph, 'coordinates') or glyph.coordinates is None:
            return None
        
        coords = glyph.coordinates
        end_pts = glyph.endPtsOfContours
        
        if not coords or not end_pts:
            return None
        
        # 分离不同的轮廓
        contours = []
        start = 0
        for end in end_pts:
            contour = list(coords[start:end+1])
            if contour:
                contours.append(contour)
            start = end + 1
        
        # 获取字体单位
        units_per_em = font['head'].unitsPerEm
        
        return contours, units_per_em
        
    except Exception as e:
        print(f"  ⚠️ 提取 '{char}' 失败: {e}")
        return None


def normalize_to_mmh(contours, units_per_em):
    """
    归一化轮廓到MMH坐标系
    MMH: X(0-1024), Y(900到-124, Y轴翻转)
    """
    if not contours:
        return []
    
    # 1. 先转换到0-1024范围
    scale = 1024.0 / units_per_em
    
    scaled_contours = []
    for contour in contours:
        scaled_contour = []
        for x, y in contour:
            # 缩放并翻转Y轴
            x_scaled = x * scale
            y_scaled = (units_per_em - y) * scale  # 翻转Y
            scaled_contour.append([x_scaled, y_scaled])
        scaled_contours.append(scaled_contour)
    
    return scaled_contours


def center_and_scale_glyph(contours, target_size=340):
    """
    居中并缩放字形到合适大小
    target_size: 字符的目标高度（约1/3画布）
    """
    if not contours:
        return []
    
    # 找到边界框
    all_points = []
    for contour in contours:
        all_points.extend(contour)
    
    if not all_points:
        return []
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return []
    
    # 当前中心
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 目标中心（MMH坐标系）
    target_x = 512  # 画布中心X
    target_y = 388  # MMH中心Y (介于900和-124之间)
    
    # 缩放比例：让字符高度约为target_size
    scale = target_size / max(width, height)
    
    # 应用变换
    centered_contours = []
    for contour in contours:
        centered_contour = []
        for x, y in contour:
            # 1. 移到原点
            x = x - center_x
            y = y - center_y
            # 2. 缩放
            x = x * scale
            y = y * scale
            # 3. 移到目标中心
            x = x + target_x
            y = y + target_y
            centered_contour.append([int(x), int(y)])
        
        centered_contours.append(centered_contour)
    
    return centered_contours


def simplify_contour(contour, max_points=20):
    """简化轮廓，减少点的数量"""
    if len(contour) <= max_points:
        return contour
    
    # 均匀采样
    step = len(contour) / max_points
    simplified = []
    for i in range(max_points):
        idx = int(i * step)
        simplified.append(contour[idx])
    
    return simplified


def contour_to_median(contour):
    """
    将轮廓转换为中线（median）
    简化策略：将轮廓近似为中心线
    """
    if len(contour) < 2:
        return []
    
    # 简化轮廓
    simplified = simplify_contour(contour, max_points=15)
    
    return simplified


def extract_alphanumeric(font):
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
    
    for char in chars:
        result = extract_glyph_contours(font, char)
        
        if result is None:
            print(f"  ❌ {char} - 未找到或无轮廓")
            continue
        
        contours, units_per_em = result
        
        # 1. 归一化到MMH坐标系
        normalized = normalize_to_mmh(contours, units_per_em)
        
        if not normalized:
            print(f"  ❌ {char} - 归一化失败")
            continue
        
        # 2. 居中并缩放
        centered = center_and_scale_glyph(normalized)
        
        if not centered:
            print(f"  ❌ {char} - 居中失败")
            continue
        
        # 3. 转换为median格式（简化轮廓为中线）
        medians = []
        for contour in centered:
            median = contour_to_median(contour)
            if median:
                medians.append(median)
        
        if not medians:
            print(f"  ❌ {char} - 转换median失败")
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
            "source": "system_font_extracted",
            "coordinate_system": "MMH"
        }
        
        # 显示进度
        if char in '05AZaz':
            pts = [p for s in medians for p in s]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x_center = (min(xs) + max(xs)) // 2
            y_center = (min(ys) + max(ys)) // 2
            print(f"  ✅ {char}: {len(medians)}笔画, X中心:{x_center}, Y中心:{y_center}")
        else:
            print(f"  ✅ {char}", end='')
            if char in '9Zz':
                print()  # 换行
    
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
    from fontTools.ttLib import TTFont
    
    print("=" * 70)
    print("从系统字体提取英文字母和数字")
    print("=" * 70)
    
    # 查找字体
    font_path = find_latin_font()
    if not font_path:
        print("\n❌ 错误: 未找到合适的字体")
        print("\n💡 建议:")
        print("  1. 确保系统安装了Arial或Times New Roman字体")
        print("  2. 或手动指定字体路径")
        return 1
    
    # 打开字体
    try:
        font = TTFont(font_path)
        print(f"✅ 成功打开字体")
    except Exception as e:
        print(f"❌ 打开字体失败: {e}")
        return 1
    
    # 提取字符
    results = extract_alphanumeric(font)
    
    font.close()
    
    if not results:
        print("\n❌ 没有成功提取任何字符")
        return 1
    
    # 保存结果
    output_file = 'data/alphanumeric_medians.json'
    
    # 备份旧文件
    if os.path.exists(output_file):
        backup_file = output_file + '.old'
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"\n💾 已备份旧文件到: {backup_file}")
    
    # 保存新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file)
    
    print(f"\n💾 已保存到: {output_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    print("\n" + "=" * 70)
    print("✅ 提取完成！")
    print("\n📝 下一步:")
    print("  1. 检查输出文件")
    print("  2. 重启服务器: python start_server.py")
    print("  3. 测试字母和数字是否正确显示")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

