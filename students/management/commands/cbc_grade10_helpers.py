
from decimal import Decimal

from students.models import CBCPerformanceLevel


GRADE10_PERFORMANCE_LEVELS = [
    {
        "category": "EE",
        "code": "EE1",
        "minimum_mark": Decimal("90"),
        "maximum_mark": Decimal("99"),
        "points": Decimal("8"),
        "order": 1,
    },
    {
        "category": "EE",
        "code": "EE2",
        "minimum_mark": Decimal("75"),
        "maximum_mark": Decimal("89"),
        "points": Decimal("7"),
        "order": 2,
    },
    {
        "category": "ME",
        "code": "ME1",
        "minimum_mark": Decimal("58"),
        "maximum_mark": Decimal("74"),
        "points": Decimal("6"),
        "order": 3,
    },
    {
        "category": "ME",
        "code": "ME2",
        "minimum_mark": Decimal("41"),
        "maximum_mark": Decimal("57"),
        "points": Decimal("5"),
        "order": 4,
    },
    {
        "category": "AE",
        "code": "AE1",
        "minimum_mark": Decimal("31"),
        "maximum_mark": Decimal("40"),
        "points": Decimal("4"),
        "order": 5,
    },
    {
        "category": "AE",
        "code": "AE2",
        "minimum_mark": Decimal("21"),
        "maximum_mark": Decimal("30"),
        "points": Decimal("3"),
        "order": 6,
    },
    {
        "category": "BE",
        "code": "BE1",
        "minimum_mark": Decimal("11"),
        "maximum_mark": Decimal("20"),
        "points": Decimal("2"),
        "order": 7,
    },
    {
        "category": "BE",
        "code": "BE2",
        "minimum_mark": Decimal("1"),
        "maximum_mark": Decimal("10"),
        "points": Decimal("1"),
        "order": 8,
    },
]


def seed_grade10_performance_levels(grade):
    """
    Ensure the standard Grade 10 CBC performance scale exists
    for the supplied CurriculumGrade.

    This is deliberately grade-level, not pathway-level.
    All Grade 10 pathways share the same performance scale.
    """

    for item in GRADE10_PERFORMANCE_LEVELS:

        CBCPerformanceLevel.objects.update_or_create(
            curriculum_grade=grade,
            code=item["code"],
            defaults={
                "category": item["category"],
                "minimum_mark": item["minimum_mark"],
                "maximum_mark": item["maximum_mark"],
                "points": item["points"],
                "order": item["order"],
            },
        )

