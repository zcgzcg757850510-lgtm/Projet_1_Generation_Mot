import unittest

from src import parser


class TestParser(unittest.TestCase):
    def test_demo_glyph_strokes(self):
        g = parser.demo_glyph_shi()
        self.assertIn("medians", g)
        self.assertEqual(len(g["medians"]), 2)
        # each stroke has at least 2 points
        self.assertTrue(all(len(st) >= 2 for st in g["medians"]))

    def test_normalize_bounds(self):
        g = parser.demo_glyph_shi()
        meds = parser.normalize_medians(g["medians"])
        for st in meds:
            for x, y in st:
                self.assertGreaterEqual(x, 0.0)
                self.assertLessEqual(x, 1.0)
                self.assertGreaterEqual(y, 0.0)
                self.assertLessEqual(y, 1.0)


if __name__ == "__main__":
    unittest.main()
