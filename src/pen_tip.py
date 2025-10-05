from __future__ import annotations
from typing import Any, Dict
import numpy as np


def _to_float(v: Any, d: float) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _ease(name: str, x: np.ndarray, power: float = 2.0) -> np.ndarray:
    name = (name or "cosine").lower()
    x = np.clip(x, 0.0, 1.0)
    if name == "power":
        return np.power(x, max(0.1, power))
    if name == "linear":
        return x
    # cosine smooth by default
    return 0.5 - 0.5 * np.cos(x * np.pi)


def compute_nib_taper(ts: np.ndarray, style: Dict[str, Any]) -> np.ndarray:
    """Return multiplicative taper scale for pen tips (start/end), independent from pressure.
    This is used to emphasize 藏锋/露锋/回锋 等效果：
      start.mode in {none,cang,luo}
      end.mode   in {none,hui,ti}
    """
    nib = style.get("nib", {}) if isinstance(style, dict) else {}
    start = nib.get("start", {}) if isinstance(nib, dict) else {}
    end = nib.get("end", {}) if isinstance(nib, dict) else {}

    # Parameters
    s_mode = (start.get("mode") or "cang").lower()
    e_mode = (end.get("mode") or "hui").lower()

    s_len = _to_float(start.get("len", 0.06), 0.06)
    s_min = _to_float(start.get("min", 0.04), 0.04)
    s_ease = (start.get("easing") or "cosine").lower()

    e_len = _to_float(end.get("len", 0.08), 0.08)
    e_min = _to_float(end.get("min", 0.03), 0.03)
    e_ease = (end.get("easing") or "cosine").lower()

    scale = np.ones_like(ts, dtype=float)

    # Start tip
    if s_mode != "none" and s_len > 1e-6:
        x = np.clip(ts / max(1e-6, s_len), 0.0, 1.0)
        e = _ease(s_ease, x)
        if s_mode == "cang":  # 藏锋：起笔较细，快速过渡到主体
            local = s_min + (1.0 - s_min) * e
        elif s_mode == "luo":  # 露锋：起笔较露，过渡更缓
            local = (s_min + 0.1) + (1.0 - (s_min + 0.1)) * e
        else:
            local = s_min + (1.0 - s_min) * e
        scale *= local

    # End tip
    if e_mode != "none" and e_len > 1e-6:
        x = np.clip((1.0 - ts) / max(1e-6, e_len), 0.0, 1.0)
        e = _ease(e_ease, x)
        if e_mode == "hui":  # 回锋：收笔回收，尾部尖细
            local = e_min + (1.0 - e_min) * e
        elif e_mode == "ti":  # 提：更尖更短
            local = max(0.01, e_min * 0.7) + (1.0 - max(0.01, e_min * 0.7)) * e
        else:
            local = e_min + (1.0 - e_min) * e
        scale *= local

    return np.clip(scale, 0.01, 2.0)
