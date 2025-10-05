#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充完整的小写字母 f-z
"""

import json
import os
import math


def create_line(x1, y1, x2, y2, points=5):
    """创建直线"""
    pts = []
    for i in range(points):
        t = i / (points - 1)
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        pts.append([x, y])
    return pts


def create_curve(x1, y1, cx, cy, x2, y2, points=10):
    """创建二次贝塞尔曲线"""
    pts = []
    for i in range(points):
        t = i / (points - 1)
        x = int((1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2)
        y = int((1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2)
        pts.append([x, y])
    return pts


def create_arc(cx, cy, r, start_angle, end_angle, points=15):
    """创建圆弧"""
    pts = []
    angle_range = end_angle - start_angle
    for i in range(points):
        t = i / (points - 1)
        angle = start_angle + angle_range * t
        rad = math.radians(angle)
        x = int(cx + r * math.cos(rad))
        y = int(cy + r * math.sin(rad))
        pts.append([x, y])
    return pts


def create_circle(cx, cy, r, points=20):
    """创建完整圆"""
    pts = []
    for i in range(points):
        angle = (i / points) * 2 * math.pi
        x = int(cx + r * math.cos(angle))
        y = int(cy + r * math.sin(angle))
        pts.append([x, y])
    pts.append(pts[0])
    return pts


def create_lowercase_f_to_z():
    """创建小写字母 f-z"""
    lowercase = {}
    
    # f - 曲线+横线
    lowercase['f'] = {
        "character": "f",
        "medians": [
            create_curve(135, 85, 125, 85, 115, 95, 5) + 
            create_line(115, 95, 115, 155, 6),
            create_line(100, 115, 130, 115, 4)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # g - 圆+下尾
    lowercase['g'] = {
        "character": "g",
        "medians": [
            create_circle(126, 135, 20, 16)[:-1] + 
            create_line(146, 135, 146, 165, 4) +
            create_curve(146, 165, 140, 175, 120, 175, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # h - 竖线+弧
    lowercase['h'] = {
        "character": "h",
        "medians": [
            create_line(110, 85, 110, 155, 8),
            create_curve(110, 125, 115, 115, 130, 115, 5) +
            create_line(130, 115, 130, 155, 5)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # i - 点+竖线
    lowercase['i'] = {
        "character": "i",
        "medians": [
            [[128, 95], [130, 95], [130, 97], [128, 97], [128, 95]],  # 点
            create_line(128, 110, 128, 155, 5)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # j - 点+钩
    lowercase['j'] = {
        "character": "j",
        "medians": [
            [[135, 95], [137, 95], [137, 97], [135, 97], [135, 95]],  # 点
            create_line(135, 110, 135, 160, 6) +
            create_curve(135, 160, 130, 175, 115, 172, 5)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # k - 竖线+两斜线
    lowercase['k'] = {
        "character": "k",
        "medians": [
            create_line(110, 85, 110, 155, 8),
            create_line(140, 115, 110, 132, 4),
            create_line(110, 132, 140, 155, 4)
        ],
        "strokes": 3,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # l - 简单竖线
    lowercase['l'] = {
        "character": "l",
        "medians": [create_line(128, 85, 128, 155, 8)],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # m - 三个弧
    lowercase['m'] = {
        "character": "m",
        "medians": [
            create_line(100, 115, 100, 155, 5) +
            create_curve(100, 115, 105, 110, 115, 110, 4) +
            create_line(115, 110, 115, 155, 5) +
            create_curve(115, 115, 120, 110, 130, 110, 4) +
            create_line(130, 110, 130, 155, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # n - 竖线+弧
    lowercase['n'] = {
        "character": "n",
        "medians": [
            create_line(110, 115, 110, 155, 5) +
            create_curve(110, 125, 115, 115, 130, 115, 5) +
            create_line(130, 115, 130, 155, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # o - 小圆
    lowercase['o'] = {
        "character": "o",
        "medians": [create_circle(128, 135, 22, 18)],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # p - 竖线+圆
    lowercase['p'] = {
        "character": "p",
        "medians": [
            create_line(110, 115, 110, 175, 7),
            create_circle(130, 135, 20, 16)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # q - 圆+竖线
    lowercase['q'] = {
        "character": "q",
        "medians": [
            create_circle(126, 135, 20, 16),
            create_line(146, 115, 146, 175, 7)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # r - 竖线+小弧
    lowercase['r'] = {
        "character": "r",
        "medians": [
            create_line(110, 115, 110, 155, 5) +
            create_curve(110, 120, 115, 115, 130, 115, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # s - 小S曲线
    lowercase['s'] = {
        "character": "s",
        "medians": [
            create_curve(140, 120, 115, 115, 115, 128, 6) +
            create_curve(115, 128, 115, 135, 125, 140, 5) +
            create_curve(125, 140, 140, 145, 140, 150, 5) +
            create_curve(140, 150, 135, 155, 115, 150, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # t - 竖线+横线
    lowercase['t'] = {
        "character": "t",
        "medians": [
            create_line(120, 95, 120, 150, 6) +
            create_curve(120, 150, 120, 155, 128, 155, 4),
            create_line(105, 115, 135, 115, 4)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # u - 弧+竖线
    lowercase['u'] = {
        "character": "u",
        "medians": [
            create_line(110, 115, 110, 145, 4) +
            create_curve(110, 145, 110, 155, 128, 155, 5) +
            create_curve(128, 155, 146, 155, 146, 145, 5) +
            create_line(146, 145, 146, 115, 4)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # v - V形
    lowercase['v'] = {
        "character": "v",
        "medians": [
            create_line(105, 115, 128, 155, 6),
            create_line(128, 155, 151, 115, 6)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # w - W形
    lowercase['w'] = {
        "character": "w",
        "medians": [
            create_line(100, 115, 110, 155, 5),
            create_line(110, 155, 128, 130, 4),
            create_line(128, 130, 146, 155, 4),
            create_line(146, 155, 156, 115, 5)
        ],
        "strokes": 4,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # x - X形
    lowercase['x'] = {
        "character": "x",
        "medians": [
            create_line(105, 115, 151, 155, 8),
            create_line(151, 115, 105, 155, 8)
        ],
        "strokes": 2,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # y - 弧+下尾
    lowercase['y'] = {
        "character": "y",
        "medians": [
            create_line(110, 115, 110, 145, 4) +
            create_curve(110, 145, 110, 155, 128, 155, 5) +
            create_curve(128, 155, 146, 155, 146, 145, 5) +
            create_line(146, 145, 146, 165, 3) +
            create_curve(146, 165, 140, 175, 120, 175, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    # z - Z形
    lowercase['z'] = {
        "character": "z",
        "medians": [
            create_line(105, 115, 151, 115, 5) +
            create_line(151, 115, 105, 155, 8) +
            create_line(105, 155, 151, 155, 5)
        ],
        "strokes": 1,
        "type": "lowercase",
        "source": "manual_alphanumeric"
    }
    
    return lowercase


def main():
    print("=" * 70)
    print("补充小写字母 f-z")
    print("=" * 70)
    
    # 加载现有数据
    input_file = 'data/alphanumeric_medians.json'
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✅ 已加载 {len(data)} 个字符")
    
    # 创建小写字母
    print("\n🎨 创建小写字母 f-z...")
    lowercase = create_lowercase_f_to_z()
    
    # 合并数据
    data.update(lowercase)
    
    print(f"✅ 新增 {len(lowercase)} 个小写字母")
    print(f"📦 总计: {len(data)} 个字符")
    
    # 保存
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(input_file)
    print(f"\n💾 已保存到: {input_file}")
    print(f"📦 文件大小: {file_size / 1024:.2f} KB")
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 完整统计:")
    print("-" * 70)
    
    types = {}
    for char, char_data in data.items():
        char_type = char_data.get('type', 'unknown')
        types[char_type] = types.get(char_type, 0) + 1
    
    for char_type, count in sorted(types.items()):
        chars = [c for c, d in data.items() if d.get('type') == char_type]
        print(f"  {char_type:12s}: {count:3d} 个  - {''.join(sorted(chars)[:30])}")
    
    print("-" * 70)
    print(f"  总计: {len(data)} 个字符")
    print("=" * 70)
    
    print("\n✅ 完整的字母和数字数据已创建！")
    print("   - 数字: 0-9 (10个)")
    print("   - 大写字母: A-Z (26个)")
    print("   - 小写字母: a-z (26个)")
    print("   - 总计: 62个字符")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

