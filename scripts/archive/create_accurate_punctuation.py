#!/usr/bin/env python3
"""
创建高质量的标点符号数据
基于真实字体的视觉特征，手工精确定义关键路径
"""

import json
import os


def create_punctuation_data():
    """
    创建标点符号数据
    每个标点都精确设计，确保形状正确
    """
    
    punctuation = {}
    
    # ========== 句号 "。" - 完整的圆形 ==========
    # 生成圆形的点
    import math
    circle_points = []
    center_x, center_y = 222, 222
    radius = 6
    for angle in range(0, 360, 15):  # 每15度一个点
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        circle_points.append([x, y])
    circle_points.append(circle_points[0])  # 闭合圆形
    
    punctuation["。"] = {
        "character": "。",
        "medians": [circle_points],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # ========== 逗号 "，" - 曲线 ==========
    punctuation["，"] = {
        "character": "，",
        "medians": [[
            [222, 210],
            [224, 213],
            [225, 216],
            [225, 219],
            [224, 222],
            [222, 225],
            [220, 227],
            [218, 229],
            [216, 230]
        ]],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # ========== 顿号 "、" - 短斜线 ==========
    punctuation["、"] = {
        "character": "、",
        "medians": [[
            [208, 215],
            [212, 219],
            [216, 223],
            [220, 227],
            [224, 230]
        ]],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # ========== 分号 "；" - 上点+下逗号 ==========
    # 生成上面的小圆点
    semicolon_top = []
    center_x, center_y = 222, 155
    radius = 4
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        semicolon_top.append([x, y])
    semicolon_top.append(semicolon_top[0])
    
    punctuation["；"] = {
        "character": "；",
        "medians": [
            semicolon_top,  # 上面的点
            [  # 下面的逗号
                [222, 185],
                [224, 188],
                [225, 191],
                [225, 194],
                [224, 197],
                [222, 200],
                [220, 202],
                [218, 204],
                [216, 205]
            ]
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 冒号 "：" - 两个圆点 ==========
    # 上点
    colon_top = []
    center_x, center_y = 222, 145
    radius = 4
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        colon_top.append([x, y])
    colon_top.append(colon_top[0])
    
    # 下点
    colon_bottom = []
    center_y = 175
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        colon_bottom.append([x, y])
    colon_bottom.append(colon_bottom[0])
    
    punctuation["："] = {
        "character": "：",
        "medians": [colon_top, colon_bottom],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 感叹号 "！" - 竖线+圆点 ==========
    # 竖线
    exclaim_line = [[128, 90], [128, 95], [128, 100], [128, 110], [128, 120], [128, 130], [128, 140], [128, 150], [128, 160]]
    
    # 下面的圆点
    exclaim_dot = []
    center_x, center_y = 128, 175
    radius = 5
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        exclaim_dot.append([x, y])
    exclaim_dot.append(exclaim_dot[0])
    
    punctuation["！"] = {
        "character": "！",
        "medians": [exclaim_line, exclaim_dot],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 问号 "？" - 曲线问号+圆点 ==========
    punctuation["？"] = {
        "character": "？",
        "medians": [
            [  # 问号主体
                [100, 110],
                [110, 100],
                [120, 95],
                [130, 95],
                [140, 100],
                [145, 110],
                [145, 120],
                [140, 130],
                [130, 138],
                [128, 145],
                [128, 155]
            ],
            [  # 下面的点（圆形）
                [123, 172], [126, 170], [129, 170], [132, 172],
                [133, 175], [132, 178], [129, 180], [126, 180],
                [123, 178], [122, 175], [123, 172]
            ]
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 左右引号 ==========
    punctuation["""] = {
        "character": """,
        "medians": [
            [[95, 90], [92, 95], [91, 100]],   # 左撇
            [[110, 90], [107, 95], [106, 100]]  # 右撇
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    punctuation["""] = {
        "character": """,
        "medians": [
            [[95, 105], [92, 100], [91, 95]],   # 左撇（向上）
            [[110, 105], [107, 100], [106, 95]]  # 右撇（向上）
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    punctuation["'"] = {
        "character": "'",
        "medians": [[[110, 90], [107, 95], [106, 100]]],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    punctuation["'"] = {
        "character": "'",
        "medians": [[[110, 105], [107, 100], [106, 95]]],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # ========== 括号 ==========
    # 左括号 "（" - 圆弧
    left_paren = []
    center_x, center_y = 145, 128
    radius_x, radius_y = 20, 60
    for angle in range(-90, 91, 10):  # 从-90到90度
        rad = math.radians(angle)
        x = center_x - int(radius_x * math.cos(rad))
        y = center_y + int(radius_y * math.sin(rad))
        left_paren.append([x, y])
    
    punctuation["（"] = {
        "character": "（",
        "medians": [left_paren],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # 右括号 "）" - 圆弧（镜像）
    right_paren = []
    center_x = 111
    for angle in range(-90, 91, 10):
        rad = math.radians(angle)
        x = center_x + int(radius_x * math.cos(rad))
        y = center_y + int(radius_y * math.sin(rad))
        right_paren.append([x, y])
    
    punctuation["）"] = {
        "character": "）",
        "medians": [right_paren],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    # ========== 书名号 ==========
    punctuation["《"] = {
        "character": "《",
        "medians": [
            [[180, 90], [140, 128], [180, 166]],  # 右尖括号
            [[140, 90], [100, 128], [140, 166]]   # 左尖括号
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    punctuation["》"] = {
        "character": "》",
        "medians": [
            [[76, 90], [116, 128], [76, 166]],    # 左尖括号
            [[116, 90], [156, 128], [116, 166]]   # 右尖括号
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 方括号 【】 ==========
    punctuation["【"] = {
        "character": "【",
        "medians": [
            [[170, 70], [170, 186]],  # 右竖线
            [[170, 70], [140, 70], [140, 186], [170, 186]]  # 左边的方框
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    punctuation["】"] = {
        "character": "】",
        "medians": [
            [[86, 70], [86, 186]],  # 左竖线
            [[86, 70], [116, 70], [116, 186], [86, 186]]  # 右边的方框
        ],
        "strokes": 2,
        "source": "accurate_design"
    }
    
    # ========== 省略号 "…" - 6个点 ==========
    dots = []
    y = 220
    radius = 3
    for x_center in [80, 108, 136, 164, 192, 220]:
        dot = []
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = x_center + int(radius * math.cos(rad))
            y_pos = y + int(radius * math.sin(rad))
            dot.append([x, y_pos])
        dot.append(dot[0])
        dots.append(dot)
    
    punctuation["…"] = {
        "character": "…",
        "medians": dots,
        "strokes": 6,
        "source": "accurate_design"
    }
    
    # ========== 破折号 "——" - 长横线 ==========
    punctuation["——"] = {
        "character": "——",
        "medians": [[[60, 128], [196, 128]]],
        "strokes": 1,
        "source": "accurate_design"
    }
    
    return punctuation


def main():
    print("=" * 60)
    print("创建高质量标点符号数据")
    print("=" * 60)
    
    data = create_punctuation_data()
    
    print(f"\n创建了 {len(data)} 个标点符号:")
    for char in data.keys():
        strokes = data[char]['strokes']
        points = sum(len(stroke) for stroke in data[char]['medians'])
        print(f"  {char}: {strokes} 笔画, {points} 点")
    
    # 保存
    output_path = 'data/punctuation_medians.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_path)
    
    print("\n" + "-" * 60)
    print(f"[OK] 保存到: {output_path}")
    print(f"[OK] 文件大小: {file_size / 1024:.1f} KB")
    print("\n" + "=" * 60)
    print("标点符号特点:")
    print("  - 。: 完整圆形（24个点形成平滑圆）")
    print("  - ；: 上圆点 + 下逗号")
    print("  - ：: 两个圆点")
    print("  - ！: 竖线 + 圆点")
    print("  - ？: 曲线问号 + 圆点")
    print("  - 括号: 平滑弧线")
    print("  - 省略号: 6个独立圆点")
    print("=" * 60)
    print("\n请重启服务器以加载新数据！")
    print("  python start_server.py")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

