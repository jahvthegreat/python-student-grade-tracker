"""Pure grade-calculation functions for GradeFlow.

The GPA conversion is an ILLUSTRATIVE US-style 4.0 scale, not an official
conversion for Seneca Polytechnic or any other institution.
"""

from dataclasses import dataclass
from typing import Iterable


# Each entry is (minimum percentage, letter grade, grade point).
# Edit this table to match your institution's published policy.
GPA_SCALE = (
    (93, "A", 4.0),
    (90, "A-", 3.7),
    (87, "B+", 3.3),
    (83, "B", 3.0),
    (80, "B-", 2.7),
    (77, "C+", 2.3),
    (73, "C", 2.0),
    (70, "C-", 1.7),
    (67, "D+", 1.3),
    (63, "D", 1.0),
    (60, "D-", 0.7),
    (0, "F", 0.0),
)


@dataclass(frozen=True)
class CourseResult:
    """Progress and grade metrics for one course."""

    graded_weight: float
    remaining_weight: float
    current_average: float | None
    final_percentage: float | None
    is_complete: bool


def validate_percentage(value: float, name: str = "Percentage") -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if not 0 <= number <= 100:
        raise ValueError(f"{name} must be between 0 and 100.")
    return number


def grade_to_gpa(percentage: float) -> tuple[str, float]:
    """Return (letter, points) under the app's illustrative 4.0 scale."""
    number = validate_percentage(percentage, "Grade")
    for minimum, letter, points in GPA_SCALE:
        if number + 1e-9 >= minimum:
            return letter, points
    raise AssertionError("GPA_SCALE must include a zero threshold")


def calculate_course(assessments: Iterable[dict]) -> CourseResult:
    """Return the *current* average over graded weights; do not treat it as final.

    Assessments should supply score (0-100%) and weight (0-100%).
    """
    weighted_sum = 0.0
    total_weight = 0.0
    for assessment in assessments:
        score = validate_percentage(assessment["score"], "Assessment score")
        weight = float(assessment["weight"])
        if not 0 < weight <= 100:
            raise ValueError("Assessment weight must be greater than 0 and at most 100.")
        total_weight += weight
        weighted_sum += score * weight

    if total_weight > 100 + 1e-7:
        raise ValueError("Assessment weights cannot exceed 100% for one course.")

    if abs(total_weight - 100) <= 1e-7:
        total_weight = 100.0
    is_complete = total_weight == 100.0
    average = weighted_sum / total_weight if total_weight else None
    final_grade = weighted_sum / 100.0 if is_complete else None
    return CourseResult(
        graded_weight=round(total_weight, 6),
        remaining_weight=round(max(0, 100 - total_weight), 6),
        current_average=average,
        final_percentage=final_grade,
        is_complete=is_complete,
    )


def calculate_gpa(completed_courses: Iterable[tuple[float, float]]) -> float | None:
    """Credit-weighted GPA of courses with ALL their assessment weight graded."""
    total_points = 0.0
    total_credits = 0.0
    for grade_percent, credits in completed_courses:
        credits = float(credits)
        if credits <= 0:
            raise ValueError("Course credits must be positive.")
        _, points = grade_to_gpa(grade_percent)
        total_points += points * credits
        total_credits += credits
    return total_points / total_credits if total_credits else None
