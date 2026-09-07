from django.db import transaction

from students.models import (
    Student,
    StudentAcademicEnrollment,
)


VALID_TERMS = {"1", "2", "3"}


def _year_number(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid academic year: {value}"
        )


def get_next_academic_period(
    academic_year,
    term,
):
    """
    Return the only valid academic period immediately
    following the supplied period.

    2026 T1 -> 2026 T2
    2026 T2 -> 2026 T3
    2026 T3 -> 2027 T1
    """

    academic_year = str(academic_year).strip()
    term = str(term).strip()

    if not academic_year:
        raise ValueError(
            "Academic year is required."
        )

    if term not in VALID_TERMS:
        raise ValueError(
            f"Invalid academic term: {term}"
        )

    year = _year_number(academic_year)

    if term == "1":
        return str(year), "2"

    if term == "2":
        return str(year), "3"

    return str(year + 1), "1"


@transaction.atomic
def create_next_period_enrollments(
    school,
    old_academic_year,
    old_term,
    new_academic_year,
    new_term,
):
    """
    Create historical StudentAcademicEnrollment records
    when a school advances to the next valid academic period.

    Only the immediate next period is accepted.
    """

    old_year, old_term = (
        str(old_academic_year).strip(),
        str(old_term).strip(),
    )

    new_year, new_term = (
        str(new_academic_year).strip(),
        str(new_term).strip(),
    )

    expected_year, expected_term = get_next_academic_period(
        old_year,
        old_term,
    )

    if (
        new_year != expected_year
        or new_term != expected_term
    ):
        raise ValueError(
            f"Invalid academic period transition: "
            f"{old_year} T{old_term} -> "
            f"{new_year} T{new_term}. "
            f"The next valid period is "
            f"{expected_year} T{expected_term}."
        )

    students = Student.objects.filter(
        school=school,
        academic_enrollments__academic_year=old_year,
        academic_enrollments__term=old_term,
    ).select_related(
        "school_class",
    ).distinct()

    created_count = 0

    for student in students:

        if not student.school_class_id:
            continue

        _, created = StudentAcademicEnrollment.objects.get_or_create(
            student=student,
            academic_year=new_year,
            term=new_term,
            defaults={
                "school_class": student.school_class,
            },
        )

        if created:
            created_count += 1

    return created_count

