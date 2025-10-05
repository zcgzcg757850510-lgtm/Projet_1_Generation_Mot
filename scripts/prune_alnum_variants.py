#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归档多余的 alphanumeric_medians_* 版本，仅保留指定集合。

默认保留：
  - alphanumeric_medians.json (当前)
  - alphanumeric_medians_cambam.json (候选：CamBam)
  - alphanumeric_medians_fonttools.json (候选：FontTools子集)

其余以 alphanumeric_medians_*.json 命名的文件会被移动到 data/archive/ 下。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Set

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

DEFAULT_KEEP: Set[str] = {
    'alphanumeric_medians.json',
    'alphanumeric_medians_cambam.json',
    'alphanumeric_medians_fonttools.json',
}


def main() -> int:
    archive = DATA / 'archive'
    archive.mkdir(parents=True, exist_ok=True)
    moved = 0
    for p in DATA.glob('alphanumeric_medians_*.json'):
        if p.name in DEFAULT_KEEP:
            continue
        # 也跳过明确的备份文件
        if p.name.startswith('alphanumeric_medians.json'):
            continue
        target = archive / p.name
        try:
            shutil.move(str(p), str(target))
            moved += 1
            print(f"➡️  归档: {p.name} → archive/{p.name}")
        except Exception as e:
            print(f"⚠️  无法归档 {p.name}: {e}")
    print(f"\n✅ 完成，归档 {moved} 个文件。保留集合: {sorted(DEFAULT_KEEP)}")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())


