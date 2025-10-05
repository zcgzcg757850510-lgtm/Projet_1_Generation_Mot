from __future__ import annotations
from typing import Any, Dict, List
import numpy as np


def _eval_profile(profile: Dict[str, Any], t: float) -> float:
    pts = profile.get("points") or []
    if not pts:
        return 1.0
    if t <= pts[0][0]:
        return float(pts[0][1])
    for i in range(len(pts) - 1):
        t0, y0 = float(pts[i][0]), float(pts[i][1])
        t1, y1 = float(pts[i + 1][0]), float(pts[i + 1][1])
        if t0 <= t <= t1:
            if t1 - t0 < 1e-9:
                return y1
            r = (t - t0) / (t1 - t0)
            return y0 * (1 - r) + y1 * r
    return float(pts[-1][1])


def _easing(easing: str, x: np.ndarray, power: float = 2.0) -> np.ndarray:
    if easing == "cosine":
        # smoothstep (cosine)
        return 0.5 - 0.5 * np.cos(np.clip(x, 0.0, 1.0) * np.pi)
    if easing == "power":
        return np.power(np.clip(x, 0.0, 1.0), max(0.1, power))
    # linear
    return np.clip(x, 0.0, 1.0)


def _to_float(v: Any, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return default


def compute_pressure_scale(ts: np.ndarray, style: Dict[str, Any]) -> np.ndarray:
    """Compute pressure scale along stroke parameter ts in [0,1].
    Sources: pressure.base, pressure.profile, rhythm.speed_profile, pressure.from_speed,
    and cap_taper to guarantee pleasant taper at the ends.
    """
    # Defaults
    pressure = style.get("pressure", {}) if isinstance(style, dict) else {}
    base = _to_float(pressure.get("pressure_base", 1.0), 1.0)
    prof = pressure.get("pressure_profile", {}) if isinstance(pressure, dict) else {}

    # speed -> pressure mapping
    rhythm = style.get("rhythm", {}) if isinstance(style, dict) else {}
    prof_speed = rhythm.get("speed_profile", {}) if isinstance(rhythm, dict) else {}
    alpha = _to_float(pressure.get("from_speed", {}).get("alpha", -0.3), -0.3)
    gamma = _to_float(pressure.get("from_speed", {}).get("gamma", 1.0), 1.0)

    p_prof = np.array([_eval_profile(prof, float(t)) for t in ts], dtype=float)
    s = np.array([_eval_profile(prof_speed, float(t)) for t in ts], dtype=float)
    s_factor = 1.0 + alpha * (np.power(s, gamma) - 1.0)

    # cap taper
    taper = pressure.get("cap_taper", {}) if isinstance(pressure, dict) else {}
    start_len = _to_float(taper.get("start_len", 0.08), 0.08)
    end_len = _to_float(taper.get("end_len", 0.12), 0.12)
    start_min = _to_float(taper.get("start_min", 0.05), 0.05)
    end_min = _to_float(taper.get("end_min", 0.05), 0.05)
    easing_name = (taper.get("easing", "cosine") or "cosine").lower()
    easing_pow = _to_float(taper.get("power", 2.0), 2.0)

    taper_w = np.ones_like(ts, dtype=float)
    # start
    if start_len > 1e-6:
        x = np.clip(ts / max(1e-6, start_len), 0.0, 1.0)
        e = _easing(easing_name, x, easing_pow)
        taper_w *= (start_min + (1.0 - start_min) * e)
    # end
    if end_len > 1e-6:
        x = np.clip((1.0 - ts) / max(1e-6, end_len), 0.0, 1.0)
        e = _easing(easing_name, x, easing_pow)
        taper_w *= (end_min + (1.0 - end_min) * e)

    scale = base * p_prof * s_factor * taper_w

    # smoothing (optional)
    smooth = pressure.get("smooth", {}) if isinstance(pressure, dict) else {}
    win = int(_to_float(smooth.get("window", 0), 0))
    if win and win > 1:
        k = np.ones(win, dtype=float) / float(win)
        # pad reflect to keep vector length
        pad = win // 2
        pad_left = scale[:pad][::-1]
        pad_right = scale[-pad:][::-1] if pad > 0 else scale[:0]
        tmp = np.concatenate([pad_left, scale, pad_right])
        scale = np.convolve(tmp, k, mode="same")[pad:-pad or None]

    return np.clip(scale, 0.01, 5.0)
