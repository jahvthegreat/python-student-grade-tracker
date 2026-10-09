"""SQLite integration tests on temporary databases."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import GradebookStore
from tracker import calculate_course


class GradebookDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = GradebookStore(Path(self.tmp.name) / "nested" / "gradebook.sqlite3")

    def test_add_edit_delete_course(self):
        cid = self.store.create_course("py101", "Python", "Fall 2026", 3)
        self.assertEqual(self.store.list_courses()[0]["code"], "PY101")
        self.store.update_course(cid, "py201", "Advanced Python", "Winter 2027", 4)
        row = self.store.list_courses("Winter 2027")[0]
        self.assertEqual(row["name"], "Advanced Python")
        self.assertEqual(row["credits"], 4)
        self.store.delete_course(cid)
        self.assertEqual(self.store.list_courses(), [])

    def test_duplicate_course_code_same_term_rejected(self):
        self.store.create_course("PY101", "Python", "Fall 2026", 3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.create_course("py101", "Another Python", "Fall 2026", 3)
        self.store.create_course("PY101", "Python", "Winter 2027", 3)
        self.assertEqual(len(self.store.list_courses()), 2)

    def test_assessment_crud_and_weight_cap(self):
        cid = self.store.create_course("DB101", "Databases", "Fall 2026", 3)
        aid = self.store.create_assessment(cid, "Midterm", 82.5, 40)
        self.store.create_assessment(cid, "Project", 92, 30)
        with self.assertRaises(ValueError):
            self.store.create_assessment(cid, "Final", 85, 31)
        self.store.update_assessment(aid, "Midterm exam", 90, 50)
        result = calculate_course(self.store.list_assessments(cid))
        self.assertAlmostEqual(result.current_average, (90 * 50 + 92 * 30) / 80)
        self.assertAlmostEqual(result.graded_weight, 80)
        self.store.delete_assessment(aid)
        self.assertEqual(len(self.store.list_assessments(cid)), 1)

    def test_delete_course_cascades_assessments(self):
        cid = self.store.create_course("WEB100", "Web", "Fall 2026", 3)
        self.store.create_assessment(cid, "Quiz", 99, 20)
        self.store.delete_course(cid)
        self.assertEqual(self.store.all_assessments(), [])

    def test_export_data_join_and_demo(self):
        self.store.load_demo()
        self.assertEqual(len(self.store.list_courses()), 4)
        self.assertEqual(len(self.store.all_assessments()), 10)
        self.assertEqual(len(self.store.list_terms()), 1)
        with self.assertRaises(ValueError):
            self.store.load_demo()
        self.store.clear()
        self.assertEqual(len(self.store.list_courses()), 0)
        self.store.load_demo()
        self.assertEqual(len(self.store.list_courses()), 4)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            self.store.create_course("", "Name", "Fall 2026", 3)
        with self.assertRaises(ValueError):
            self.store.create_course("PY101", "Name", "Fall 2026", -1)
        cid = self.store.create_course("PY101", "Name", "Fall 2026", 3)
        with self.assertRaises(ValueError):
            self.store.create_assessment(cid, "Bad score", -2, 10)
        with self.assertRaises(ValueError):
            self.store.create_assessment(cid, "", 80, 10)


if __name__ == "__main__":
    unittest.main()
