import os
from typing import Dict, Any
from web.config import OUTPUT_COMPARE


def latest_filenames_for_char(ch: str) -> Dict[str, Any]:
    mapping = {
        'A': os.path.join(OUTPUT_COMPARE, 'A_outlines'),        # A窗口: 轮廓
        'B': os.path.join(OUTPUT_COMPARE, 'B_raw_centerline'),   # B窗口: 原始中轴
        'C': os.path.join(OUTPUT_COMPARE, 'C_processed_centerline'), # C窗口: 处理中轴
        'D1': os.path.join(OUTPUT_COMPARE, 'D1_grid_transform'), # D1窗口: 网格变形
        'D2': os.path.join(OUTPUT_COMPARE, 'D2_median_fill'),    # D2窗口: 中轴填充
    }
    result: Dict[str, Any] = {k: None for k in mapping.keys()}
    
    # 添加调试信息
    print(f"[DEBUG] latest_filenames_for_char 查找字符: {ch}")
    
    for key, base in mapping.items():
        if not os.path.exists(base):
            print(f"[DEBUG] {key} 目录不存在: {base}")
            continue
            
        best_name = None
        best_mtime = -1.0
        suffix = f"_{ch}_{key}.svg"  # Maintenant on cherche _{ch}_A.svg, _{ch}_B.svg, etc.
        
        print(f"[DEBUG] {key} 目录: {base}, 查找模式: *{suffix}")
        
        files_in_dir = os.listdir(base)
        svg_files = [f for f in files_in_dir if f.lower().endswith('.svg')]
        print(f"[DEBUG] {key} 目录中SVG文件数: {len(svg_files)}")
        
        matching_files = []
        for fn in svg_files:
            if fn.endswith(suffix):
                matching_files.append(fn)
                fp = os.path.join(base, fn)
                try:
                    mt = os.path.getmtime(fp)
                    if mt > best_mtime:
                        best_mtime = mt
                        best_name = fn
                except OSError:
                    pass
        
        print(f"[DEBUG] {key} 匹配文件数: {len(matching_files)}")
        if matching_files:
            print(f"[DEBUG] {key} 匹配的文件: {matching_files}")
        if best_name:
            print(f"[DEBUG] {key} 最新文件: {best_name}")
        else:
            print(f"[DEBUG] {key} 未找到匹配文件")
            
        result[key] = best_name
    
    print(f"[DEBUG] latest_filenames_for_char 最终结果: {result}")
    return result


def clean_compare_ab_only() -> None:
    for sub in ('A_outlines', 'D2_median_fill'):  # Changé B_median_fill -> D2_median_fill
        base = os.path.join(OUTPUT_COMPARE, sub)
        if not os.path.exists(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if fn.lower().endswith('.svg') and fn[:3].isdigit() and fn[3] == '_':
                    try:
                        os.remove(os.path.join(root, fn))
                    except OSError:
                        pass


def clean_compare_all() -> None:
    for sub in ('A_outlines', 'B_raw_centerline', 'C_processed_centerline', 'D1_grid_transform', 'D2_median_fill'):
        base = os.path.join(OUTPUT_COMPARE, sub)
        if not os.path.exists(base):
            continue
        # 只删除以时间戳开头的 svg，避免误删历史样例
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if fn.lower().endswith('.svg') and (fn[:8].isdigit() or fn[:4].isdigit()):
                    try:
                        os.remove(os.path.join(root, fn))
                    except OSError:
                        pass


