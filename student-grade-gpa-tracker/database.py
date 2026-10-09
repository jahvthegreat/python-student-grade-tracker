"""SQLite persistence for GradeFlow. No external database required."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from tracker import validate_percentage


class GradebookStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL COLLATE NOCASE,
                    name TEXT NOT NULL,
                    term TEXT NOT NULL,
                    credits REAL NOT NULL CHECK (credits > 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (code, term)
                );
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY,
                    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    score REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
                    weight REAL NOT NULL CHECK (weight > 0 AND weight <= 100)
                );
                CREATE INDEX IF NOT EXISTS idx_assessments_course ON assessments(course_id);
            """)

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _required(value: str, field: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{field} cannot be blank.")
        if len(value) > 90:
            raise ValueError(f"{field} must be at most 90 characters.")
        return value

    @staticmethod
    def _credits(value: float) -> float:
        try:
            credits = float(value)
        except (ValueError, TypeError) as exc:
            raise ValueError("Credits must be a number.") from exc
        if not 0 < credits <= 24:
            raise ValueError("Credits must be greater than 0 and at most 24.")
        return credits

    def list_courses(self, term: str | None = None) -> list[dict]:
        query = "SELECT * FROM courses"
        params: tuple = ()
        if term is not None:
            query += " WHERE term = ?"
            params = (term,)
        query += " ORDER BY term DESC, code COLLATE NOCASE"
        with self._connection() as db:
            return [dict(row) for row in db.execute(query, params).fetchall()]

    def list_terms(self) -> list[str]:
        with self._connection() as db:
            return [row[0] for row in db.execute(
                "SELECT DISTINCT term FROM courses ORDER BY term DESC"
            ).fetchall()]

    def create_course(self, code: str, name: str, term: str, credits: float) -> int:
        code = self._required(code, "Course code").upper()
        name = self._required(name, "Course name")
        term = self._required(term, "Term")
        credits = self._credits(credits)
        with self._connection() as db:
            cursor = db.execute(
                "INSERT INTO courses (code, name, term, credits) VALUES (?, ?, ?, ?)",
                (code, name, term, credits),
            )
            db.commit()
            return cursor.lastrowid

    def update_course(self, course_id: int, code: str, name: str, term: str, credits: float):
        code = self._required(code, "Course code").upper()
        name = self._required(name, "Course name")
        term = self._required(term, "Term")
        credits = self._credits(credits)
        with self._connection() as db:
            db.execute(
                "UPDATE courses SET code=?, name=?, term=?, credits=? WHERE id=?",
                (code, name, term, credits, course_id),
            )
            db.commit()

    def delete_course(self, course_id: int):
        with self._connection() as db:
            db.execute("DELETE FROM courses WHERE id=?", (course_id,))
            db.commit()

    def list_assessments(self, course_id: int) -> list[dict]:
        with self._connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM assessments WHERE course_id=? ORDER BY id", (course_id,)
            ).fetchall()]

    def all_assessments(self) -> list[dict]:
        with self._connection() as db:
            return [dict(row) for row in db.execute("""
                SELECT a.*, c.code AS course_code, c.name AS course_name,
                       c.term, c.credits
                FROM assessments a JOIN courses c ON c.id=a.course_id
                ORDER BY c.term DESC, c.code, a.id
            """).fetchall()]

    def _check_weight(self, course_id: int, weight: float, excluding_id: int | None = None):
        try:
            weight = float(weight)
        except (TypeError, ValueError) as exc:
            raise ValueError("Weight must be a number.") from exc
        if not 0 < weight <= 100:
            raise ValueError("Assessment weight must be greater than 0 and at most 100.")
        existing = [a for a in self.list_assessments(course_id) if a["id"] != excluding_id]
        current_weight = sum(a["weight"] for a in existing)
        if current_weight + weight > 100 + 1e-7:
            raise ValueError(f"Total weight would exceed 100% (currently {current_weight:g}%).")
        return weight

    def create_assessment(self, course_id: int, name: str, score: float, weight: float) -> int:
        name = self._required(name, "Assessment name")
        score = validate_percentage(score, "Score")
        weight = self._check_weight(course_id, weight)
        with self._connection() as db:
            cursor = db.execute(
                "INSERT INTO assessments (course_id, name, score, weight) VALUES (?, ?, ?, ?)",
                (course_id, name, score, weight),
            )
            db.commit()
            return cursor.lastrowid

    def update_assessment(self, assessment_id: int, name: str, score: float, weight: float):
        name = self._required(name, "Assessment name")
        score = validate_percentage(score, "Score")
        with self._connection() as db:
            row = db.execute("SELECT course_id FROM assessments WHERE id=?", (assessment_id,)).fetchone()
            if row is None:
                raise ValueError("Assessment not found.")
            weight = self._check_weight(row["course_id"], weight, excluding_id=assessment_id)
            db.execute(
                "UPDATE assessments SET name=?, score=?, weight=? WHERE id=?",
                (name, score, weight, assessment_id),
            )
            db.commit()

    def delete_assessment(self, assessment_id: int):
        with self._connection() as db:
            db.execute("DELETE FROM assessments WHERE id=?", (assessment_id,))
            db.commit()

    def clear(self):
        with self._connection() as db:
            db.execute("DELETE FROM courses")
            db.commit()

    def load_demo(self):
        if self.list_courses():
            raise ValueError("Sample data can only be loaded into an empty gradebook.")
        example = [
            ("PY101", "Python Programming", "Fall 2026", 3.0,
             [("Labs", 91, 30), ("Midterm", 86, 30), ("Final", 94, 40)]),
            ("DB201", "Database Fundamentals", "Fall 2026", 3.0,
             [("Assignments", 88, 35), ("Project", 93, 25), ("Final", 84, 40)]),
            ("WEB220", "Web Development", "Fall 2026", 4.0,
             [("Assignments", 95, 25), ("Quiz", 89, 15)]),
            ("MAT150", "Statistics for Developers", "Fall 2026", 3.0,
             [("Quizzes", 82, 20), ("Midterm", 78, 30)]),
        ]
        for code, name, term, credits, items in example:
            cid = self.create_course(code, name, term, credits)
            for title, score, weight in items:
                self.create_assessment(cid, title, score, weight)
