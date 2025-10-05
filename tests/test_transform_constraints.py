import unittest
import math

from src.transformer import transform_medians
from src.constraints import apply_collision_avoidance


class TestTransformConstraints(unittest.TestCase):
    def test_length_scale(self):
        med = [[(0.1, 0.5), (0.9, 0.5)]]
        style = {"geometry": {"length_scale": 2.0, "tilt_deg": 0.0, "shear": 0.0}}
        out = transform_medians(med, style)
        dx_in = med[0][-1][0] - med[0][0][0]
        dx_out = out[0][-1][0] - out[0][0][0]
        self.assertTrue(dx_out > dx_in)

    def test_tilt_rotation(self):
        med = [[(0.1, 0.0), (0.1, 1.0)]]  # vertical
        style = {"geometry": {"length_scale": 1.0, "tilt_deg": 90.0, "shear": 0.0}}
        out = transform_medians(med, style)
        # after 90 deg, x-span should be larger than y-span roughly
        xs = [p[0] for p in out[0]]
        ys = [p[1] for p in out[0]]
        self.assertTrue((max(xs) - min(xs)) > (max(ys) - min(ys)))

    def test_collision_distance_increase(self):
        # two identical overlapping horizontal strokes
        med = [
            [(0.1, 0.5), (0.9, 0.5)],
            [(0.1, 0.5), (0.9, 0.5)],
        ]
        out = apply_collision_avoidance(med, min_distance=0.05, strength=1.0, iterations=2)
        # endpoints should move apart in y
        y0 = out[0][0][1]
        y1 = out[1][0][1]
        self.assertNotEqual(y0, y1)
        self.assertGreater(abs(y0 - y1), 0.0)


if __name__ == "__main__":
    unittest.main()
