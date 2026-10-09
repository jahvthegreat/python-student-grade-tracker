"""Pure domain-layer tests, runnable with Python's built-in unittest."""

import unittest

from tracker import calculate_course, calculate_gpa, grade_to_gpa


class GradeCalculationTests(unittest.TestCase):
    def test_empty_course_has_no_grade(self):
        result = calculate_course([])
        self.assertIsNone(result.current_average)
        self.assertIsNone(result.final_percentage)
        self.assertEqual(result.remaining_weight, 100)
        self.assertFalse(result.is_complete)

    def test_partial_course_normalizes_only_graded_weight(self):
        result = calculate_course([
            {"score": 80, "weight": 20},
            {"score": 90, "weight": 30},
        ])
        self.assertAlmostEqual(result.current_average, 86.0)
        self.assertEqual(result.graded_weight, 50)
        self.assertIsNone(result.final_percentage)
        self.assertFalse(result.is_complete)

    def test_complete_course_calculates_final_grade(self):
        result = calculate_course([
            {"score": 80, "weight": 40},
            {"score": 95, "weight": 60},
        ])
        self.assertTrue(result.is_complete)
        self.assertAlmostEqual(result.final_percentage, 89)
        self.assertAlmostEqual(result.current_average, 89)
        self.assertEqual(result.remaining_weight, 0)

    def test_grade_scale_boundaries(self):
        self.assertEqual(grade_to_gpa(93), ("A", 4.0))
        self.assertEqual(grade_to_gpa(90), ("A-", 3.7))
        self.assertEqual(grade_to_gpa(0), ("F", 0.0))
        self.assertEqual(grade_to_gpa(89.99), ("B+", 3.3))

    def test_reject_invalid_scores_and_weights(self):
        with self.assertRaises(ValueError):
            calculate_course([{"score": 110, "weight": 50}])
        with self.assertRaises(ValueError):
            calculate_course([{"score": 90, "weight": 0}])
        with self.assertRaises(ValueError):
            calculate_course([{"score": 90, "weight": 60}, {"score": 70, "weight": 50}])
        with self.assertRaises(ValueError):
            grade_to_gpa(-1)

    def test_gpa_uses_credit_weights(self):
        # 93% -> 4.0 pts, 70% -> 1.7 pts
        self.assertAlmostEqual(calculate_gpa([(93, 3), (70, 1)]), (4 * 3 + 1.7) / 4)
        self.assertIsNone(calculate_gpa([]))

    def test_gpa_rejects_invalid_credits(self):
        with self.assertRaises(ValueError):
            calculate_gpa([(90, 0)])


if __name__ == "__main__":
    unittest.main()
