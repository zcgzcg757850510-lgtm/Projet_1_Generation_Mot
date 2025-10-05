import unittest
import json
from pathlib import Path

from src.styler import load_style, build_rng, sample_style_for_stroke, style_layers, interpolate_styles


class TestStyler(unittest.TestCase):
    def setUp(self):
        self.style_path = Path("data/style_profiles.json")
        self.assertTrue(self.style_path.exists(), "style_profiles.json not found")
        self.style_json = load_style(str(self.style_path))
        self.global_layer, self.stroke_types = style_layers(self.style_json)

    def test_deterministic_with_seed(self):
        import random
        rng1 = build_rng(123)
        rng2 = build_rng(123)
        st1 = sample_style_for_stroke(self.global_layer, self.stroke_types.get("heng", {}), rng1)
        st2 = sample_style_for_stroke(self.global_layer, self.stroke_types.get("heng", {}), rng2)
        self.assertEqual(json.dumps(st1, sort_keys=True), json.dumps(st2, sort_keys=True))

    def test_value_ranges(self):
        rng = build_rng(1)
        st = sample_style_for_stroke(self.global_layer, self.stroke_types.get("heng", {}), rng)
        # check a few fields within reasonable ranges
        th = st.get("thickness", {})
        self.assertGreaterEqual(float(th.get("width_base", 0.0)), 0.0)
        geom = st.get("geometry", {})
        self.assertGreaterEqual(float(geom.get("length_scale", 0.0)), 0.0)

    def test_interpolation(self):
        rng = build_rng(7)
        a = sample_style_for_stroke(self.global_layer, self.stroke_types.get("heng", {}), rng)
        b = sample_style_for_stroke(self.global_layer, self.stroke_types.get("heng", {}), rng)
        mid = interpolate_styles(a, b, 0.5)
        # simple numeric sanity: width_base should lie between a and b
        aw = float(a.get("thickness", {}).get("width_base", 0.0))
        bw = float(b.get("thickness", {}).get("width_base", 0.0))
        mw = float(mid.get("thickness", {}).get("width_base", 0.0))
        lo, hi = (aw, bw) if aw <= bw else (bw, aw)
        self.assertGreaterEqual(mw, lo)
        self.assertLessEqual(mw, hi)


if __name__ == "__main__":
    unittest.main()
