#!/usr/bin/env python3
"""
合并圆润数字到现有字母数据
只替换0-9，保留A-Z和a-z
"""
import json
import sys

def merge_digits(digit_file, target_file='data/alphanumeric_medians.json'):
    """合并数字数据"""
    print("=" * 60)
    print("合并圆润数字到字母数据")
    print("=" * 60)
    
    # 读取数字数据
    print(f"\n📖 读取数字数据: {digit_file}")
    with open(digit_file, 'r', encoding='utf-8') as f:
        digits_data = json.load(f)
    
    digit_count = len(digits_data)
    print(f"✅ 加载了 {digit_count} 个数字")
    
    # 读取现有字母数据
    print(f"\n📖 读取现有字母数据: {target_file}")
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"✅ 现有数据: {len(existing_data)} 个字符")
    except FileNotFoundError:
        print("⚠️  目标文件不存在，将创建新文件")
        existing_data = {}
    
    # 备份
    if existing_data:
        backup_file = f"{target_file}.backup_before_digits"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        print(f"💾 已备份到: {backup_file}")
    
    # 合并：用新数字替换旧数字，保留所有字母
    merged_data = existing_data.copy()
    
    replaced_count = 0
    for digit, data in digits_data.items():
        if digit in merged_data:
            replaced_count += 1
        merged_data[digit] = data
    
    print(f"\n🔄 替换了 {replaced_count} 个现有数字")
    print(f"➕ 添加了 {digit_count - replaced_count} 个新数字")
    
    # 统计
    stats = {}
    for char, data in merged_data.items():
        char_type = data.get('type', 'unknown')
        stats[char_type] = stats.get(char_type, 0) + 1
    
    print(f"\n📊 合并后统计:")
    for t, c in sorted(stats.items()):
        print(f"  {t}: {c}个")
    
    # 保存
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到: {target_file}")
    print(f"📦 总字符数: {len(merged_data)}")
    
    print("\n" + "=" * 60)
    print("✅ 合并完成！")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python merge_rounded_digits.py <数字文件>")
        print("\n例如:")
        print("  python merge_rounded_digits.py data/digits_comfortaa.json")
        print("  python merge_rounded_digits.py data/digits_varelaround.json")
        sys.exit(1)
    
    digit_file = sys.argv[1]
    sys.exit(merge_digits(digit_file))

