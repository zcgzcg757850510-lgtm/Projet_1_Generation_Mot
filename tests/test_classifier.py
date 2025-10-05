import unittest

from src.classifier import classify_glyph


class TestClassifier(unittest.TestCase):
    def test_basic_directions(self):
        # heng: horizontal left->right
        med_h = [[(0.1, 0.5), (0.9, 0.5)]]
        # shu: vertical top->bottom
        med_s = [[(0.5, 0.1), (0.5, 0.9)]]
        # pie: upper-right to lower-left
        med_p = [[(0.8, 0.2), (0.2, 0.8)]]
        # na: upper-left to lower-right
        med_n = [[(0.2, 0.2), (0.8, 0.8)]]
        labs_h = classify_glyph(med_h)
        labs_s = classify_glyph(med_s)
        labs_p = classify_glyph(med_p)
        labs_n = classify_glyph(med_n)
        self.assertEqual(labs_h[0], "heng")
        self.assertEqual(labs_s[0], "shu")
        self.assertEqual(labs_p[0], "pie")
        self.assertEqual(labs_n[0], "na")


if __name__ == "__main__":
    unittest.main()
