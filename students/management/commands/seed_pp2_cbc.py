from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import (
    CurriculumVersion,
    CurriculumGrade,
    CurriculumLearningArea,
    CurriculumStrand,
    CurriculumSubStrand,
    CurriculumAssessmentItem,
)


class Command(BaseCommand):
    help = "Seed PP2 CBC assessment-book curriculum for Terms 1-3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2026",
            help="Academic year for the curriculum version.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        academic_year = str(options["academic_year"])

        # ==============================================================
        # CURRICULUM VERSION
        # ==============================================================

        version, _ = CurriculumVersion.objects.get_or_create(
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": (
                    f"CBC curriculum for the {academic_year} "
                    "academic year."
                ),
            },
        )

        version.name = f"CBC {academic_year}"
        version.academic_year = academic_year
        version.description = (
            f"CBC curriculum for the {academic_year} academic year."
        )
        version.save()

        # ==============================================================
        # PP2 GRADE
        # ==============================================================

        grade, _ = CurriculumGrade.objects.get_or_create(
            curriculum_version=version,
            grade="PP2",
            defaults={
                "display_name": "PP2",
            },
        )

        grade.display_name = "PP2"
        grade.save()

        # ==============================================================
        # PP2 CBC CURRICULUM
        #
        # Term grouping is provided specifically for the
        # SchoolManagerPro assessment-book workflow.
        #
        # E.E / M.E / A.E / B.E are NOT curriculum items.
        # They remain part of the assessment/performance system.
        # ==============================================================

        curriculum = [

            # ==========================================================
            # LANGUAGE ACTIVITIES
            # ==========================================================

            (
                "Language Activities",
                "1.0",
                "Greetings and Farewell",
                "1",
                [
                    (
                        "1.1.1",
                        "Listening and Speaking - Greetings and farewell",
                    ),
                    (
                        "1.1.2",
                        "Listening and Speaking - Time-related greetings and farewell",
                    ),
                    (
                        "1.2.1",
                        "Reading - Reading readiness",
                    ),
                    (
                        "1.3.1",
                        "Writing - Writing readiness",
                    ),
                ],
            ),

            (
                "Language Activities",
                "2.0",
                "Our Neighbourhood",
                "1",
                [
                    (
                        "2.1.1",
                        "Listening and Speaking - Listening for comprehension",
                    ),
                    (
                        "2.1.2",
                        "Listening and Speaking - News telling",
                    ),
                    (
                        "2.2.1",
                        "Reading - Book handling",
                    ),
                    (
                        "2.2.2",
                        "Reading - Reading readiness",
                    ),
                    (
                        "2.2.3",
                        "Reading - Letter recognition",
                    ),
                    (
                        "2.3.1",
                        "Writing - Letter writing",
                    ),
                    (
                        "2.3.2",
                        "Writing - Writing practice",
                    ),
                ],
            ),

            (
                "Language Activities",
                "3.0",
                "Our School",
                "1",
                [
                    (
                        "3.1.1",
                        "Listening and Speaking - Active listening",
                    ),
                    (
                        "3.1.2",
                        "Listening and Speaking - Self-expression",
                    ),
                    (
                        "3.2.1",
                        "Reading - Print awareness",
                    ),
                    (
                        "3.2.2",
                        "Reading - Reading syllables (ba-bu, da-du)",
                    ),
                    (
                        "3.3.1",
                        "Writing - Drawing and colouring pictures",
                    ),
                    (
                        "3.3.2",
                        "Writing - Writing syllables (ba-bu, da-du)",
                    ),
                ],
            ),

            (
                "Language Activities",
                "4.0",
                "Our Market",
                "2",
                [
                    (
                        "4.1.1",
                        "Listening and Speaking - Polite language",
                    ),
                    (
                        "4.1.2",
                        "Listening and Speaking - Passing information",
                    ),
                    (
                        "4.2.1",
                        "Reading - Visual discrimination",
                    ),
                    (
                        "4.2.2",
                        "Reading - Letter-sound correspondence",
                    ),
                    (
                        "4.2.3",
                        "Reading - Reading syllables (fa-fu, ha-hu)",
                    ),
                    (
                        "4.3.1",
                        "Writing - Eye-hand coordination",
                    ),
                    (
                        "4.3.2",
                        "Writing - Writing letters of the alphabet",
                    ),
                    (
                        "4.3.3",
                        "Writing - Writing syllables (fa-fu, ha-hu)",
                    ),
                ],
            ),

            (
                "Language Activities",
                "5.0",
                "Animals",
                "2",
                [
                    (
                        "5.1.1",
                        "Listening and Speaking - Auditory discrimination",
                    ),
                    (
                        "5.1.2",
                        "Listening and Speaking - Audience awareness",
                    ),
                    (
                        "5.2.1",
                        "Reading - Visual memory",
                    ),
                    (
                        "5.2.2",
                        "Reading - Reading syllables (ja-ju, la-lu)",
                    ),
                    (
                        "5.3.1",
                        "Writing - Pattern writing",
                    ),
                    (
                        "5.3.2",
                        "Writing - Writing syllables (ja-ju, la-lu)",
                    ),
                ],
            ),

            (
                "Language Activities",
                "6.0",
                "Weather Conditions",
                "2",
                [
                    (
                        "6.1.1",
                        "Listening and Speaking - Auditory memory",
                    ),
                    (
                        "6.1.2",
                        "Listening and Speaking - Reporting skills",
                    ),
                    (
                        "6.2.1",
                        "Reading - Visual discrimination",
                    ),
                    (
                        "6.2.2",
                        "Reading - Reading syllables (ma-mu, pa-pu)",
                    ),
                    (
                        "6.3.1",
                        "Writing - Recording skills",
                    ),
                    (
                        "6.3.2",
                        "Writing - Writing syllables (ma-mu, pa-pu)",
                    ),
                ],
            ),

            (
                "Language Activities",
                "7.0",
                "Water",
                "3",
                [
                    (
                        "7.1.1",
                        "Listening and Speaking - Naming",
                    ),
                    (
                        "7.1.2",
                        "Listening and Speaking - Articulation of letter sounds",
                    ),
                    (
                        "7.2.1",
                        "Reading - Picture reading",
                    ),
                    (
                        "7.2.2",
                        "Reading - Reading syllables (ra-ru, ta-tu)",
                    ),
                    (
                        "7.2.3",
                        "Reading - Word formation",
                    ),
                    (
                        "7.3.1",
                        "Writing - Hand writing",
                    ),
                    (
                        "7.3.2",
                        "Writing - Writing syllables (ra-ru, ta-tu)",
                    ),
                ],
            ),

            (
                "Language Activities",
                "8.0",
                "Time",
                "3",
                [
                    (
                        "8.1.1",
                        "Listening and Speaking - News telling",
                    ),
                    (
                        "8.1.2",
                        "Listening and Speaking - Passing information",
                    ),
                    (
                        "8.1.3",
                        "Listening and Speaking - Story telling",
                    ),
                    (
                        "8.2.1",
                        "Reading - Reading syllables (va-vu, za-zu)",
                    ),
                    (
                        "8.2.2",
                        "Reading - Reading three-letter words",
                    ),
                    (
                        "8.3.1",
                        "Writing - Writing syllables",
                    ),
                    (
                        "8.3.2",
                        "Writing - Writing three-letter words",
                    ),
                ],
            ),

            (
                "Language Activities",
                "9.0",
                "Transport",
                "3",
                [
                    (
                        "9.1.1",
                        "Listening and Speaking - Naming",
                    ),
                    (
                        "9.1.2",
                        "Listening and Speaking - News telling",
                    ),
                    (
                        "9.2.1",
                        "Reading - Picture reading",
                    ),
                    (
                        "9.3.1",
                        "Writing - Drawing and colouring pictures",
                    ),
                    (
                        "9.3.2",
                        "Writing - Writing practice",
                    ),
                ],
            ),

            # ==========================================================
            # MATHEMATICAL ACTIVITIES
            # ==========================================================

            (
                "Mathematical Activities",
                "1.0",
                "Pre-Number Activities",
                "1",
                [
                    ("1.1", "Sorting and Grouping"),
                    ("1.2", "Matching and Pairing"),
                    ("1.3", "Ordering"),
                    ("1.4", "Patterns"),
                ],
            ),

            (
                "Mathematical Activities",
                "2.0",
                "Numbers",
                "1",
                [
                    ("2.1", "Rote Counting (1-30)"),
                    ("2.2", "Number Recognition (1-20)"),
                    ("2.3", "Counting Concrete Objects (1-20)"),
                    ("2.4", "Number Sequencing (1-20)"),
                    ("2.5", "Number Value (up to 20)"),
                    ("2.6", "Number Writing (1-20)"),
                    (
                        "2.7",
                        "Putting Together (sums not exceeding 9)",
                    ),
                    ("2.8", "Taking Away"),
                ],
            ),

            (
                "Mathematical Activities",
                "3.0",
                "Measurement",
                "2",
                [
                    (
                        "3.1",
                        "Sides of Objects - Long and Short",
                    ),
                    (
                        "3.2",
                        "Mass - Heavy and Light",
                    ),
                    (
                        "3.3",
                        "Capacity - How much a container can hold",
                    ),
                    (
                        "3.4",
                        "Time - Daily routines, days and months",
                    ),
                    (
                        "3.5",
                        "Money - Kenyan currency coins (KSh.1, KSh.5, KSh.10, KSh.20)",
                    ),
                    (
                        "3.6",
                        "Area - Surfaces of Objects",
                    ),
                ],
            ),

            (
                "Mathematical Activities",
                "4.0",
                "Geometry",
                "3",
                [
                    (
                        "4.1",
                        "Lines - Straight, wavy and zigzag",
                    ),
                    (
                        "4.2",
                        "Shapes - Rectangle, circle, triangle, oval and square",
                    ),
                ],
            ),

            # ==========================================================
            # CREATIVE ACTIVITIES
            # ==========================================================

            (
                "Creative Activities",
                "1.0",
                "Our Neighbourhood",
                "1",
                [
                    ("1.1", "Doodling"),
                    ("1.2", "Painting"),
                ],
            ),

            (
                "Creative Activities",
                "2.0",
                "Our School",
                "1",
                [
                    ("2.1", "Mosaic"),
                    ("2.2", "Swinging and Stretching"),
                    ("2.3", "Body Percussions"),
                ],
            ),

            (
                "Creative Activities",
                "3.0",
                "Our Market",
                "2",
                [
                    ("3.1", "Colouring"),
                    ("3.2", "Musical Rhymes"),
                ],
            ),

            (
                "Creative Activities",
                "4.0",
                "Animals",
                "2",
                [
                    ("4.1", "Modelling"),
                    ("4.2", "Walking and Hopping"),
                ],
            ),

            (
                "Creative Activities",
                "5.0",
                "Weather",
                "3",
                [
                    ("5.1", "Paper Pleating"),
                ],
            ),

            (
                "Creative Activities",
                "6.0",
                "Water",
                "3",
                [
                    ("6.1", "Water Play"),
                ],
            ),

            # ==========================================================
            # ENVIRONMENTAL ACTIVITIES
            # ==========================================================

            (
                "Environmental Activities",
                "1.0",
                "Myself",
                "1",
                [
                    ("1.1", "External Body Parts"),
                    ("1.2", "Uses of Body Parts"),
                    ("1.3", "Cleaning Nose"),
                    ("1.4", "Dressing"),
                ],
            ),

            (
                "Environmental Activities",
                "2.0",
                "My Family",
                "1",
                [
                    ("2.1", "Foods"),
                    ("2.2", "Importance of Eating Food"),
                ],
            ),

            (
                "Environmental Activities",
                "3.0",
                "My Home",
                "2",
                [
                    ("3.1", "Houses at Home"),
                    ("3.2", "Work Done at Home"),
                    ("3.3", "Domestic Animals"),
                ],
            ),

            (
                "Environmental Activities",
                "4.0",
                "My Neighbourhood",
                "2",
                [
                    (
                        "4.1",
                        "Families in Our Neighbourhood",
                    ),
                    (
                        "4.2",
                        "Buildings in Our Neighbourhood",
                    ),
                    ("4.3", "Plants"),
                ],
            ),

            (
                "Environmental Activities",
                "5.0",
                "My School",
                "3",
                [
                    ("5.1", "People in Our School"),
                    ("5.2", "Things in Our School"),
                    ("5.3", "Care for Our School"),
                    (
                        "5.4",
                        "Safety in the Environment",
                    ),
                    (
                        "5.5",
                        "Weather Condition",
                    ),
                ],
            ),

            # ==========================================================
            # CHRISTIAN RELIGIOUS EDUCATION ACTIVITIES
            # ==========================================================

            (
                "Christian Religious Education Activities",
                "1.0",
                "Creation",
                "1",
                [
                    ("1.1", "God the Creator"),
                    (
                        "1.2",
                        "Caring for God's Creation",
                    ),
                ],
            ),

            (
                "Christian Religious Education Activities",
                "2.0",
                "The Holy Bible",
                "1",
                [
                    (
                        "2.1",
                        "Handling the Holy Bible",
                    ),
                    (
                        "2.2",
                        "Noah and the Ark",
                    ),
                ],
            ),

            (
                "Christian Religious Education Activities",
                "3.0",
                "The Life of Jesus Christ",
                "2",
                [
                    (
                        "3.1",
                        "The Birth of Jesus Christ",
                    ),
                    (
                        "3.2",
                        "Celebrating the Birth of Jesus",
                    ),
                ],
            ),

            (
                "Christian Religious Education Activities",
                "4.0",
                "Christian Values",
                "2",
                [
                    (
                        "4.1",
                        "Respect for Parents",
                    ),
                    (
                        "4.2",
                        "Responsibility",
                    ),
                ],
            ),

            (
                "Christian Religious Education Activities",
                "5.0",
                "The Church",
                "3",
                [
                    (
                        "5.1",
                        "A House of God",
                    ),
                    (
                        "5.2",
                        "Church Activities",
                    ),
                ],
            ),
        ]

        # ==============================================================
        # CREATE / UPDATE CURRICULUM
        # ==============================================================

        learning_area_cache = {}

        for (
            learning_area_name,
            strand_code,
            strand_name,
            term,
            sub_strands,
        ) in curriculum:

            # ----------------------------------------------------------
            # LEARNING AREA
            # ----------------------------------------------------------

            if learning_area_name not in learning_area_cache:

                learning_area, _ = (
                    CurriculumLearningArea.objects.get_or_create(
                        curriculum_grade=grade,
                        pathway=None,
                        name=learning_area_name,
                        defaults={
                            "code": self.make_code(
                                learning_area_name
                            ),
                            "description": (
                                "PP2 CBC assessment "
                                "learning area."
                            ),
                            "assessment_enabled": True,
                        },
                    )
                )

                learning_area.code = self.make_code(
                    learning_area_name
                )
                learning_area.description = (
                    "PP2 CBC assessment learning area."
                )
                learning_area.assessment_enabled = True
                learning_area.save()

                learning_area_cache[
                    learning_area_name
                ] = learning_area

            else:
                learning_area = learning_area_cache[
                    learning_area_name
                ]

            # ----------------------------------------------------------
            # STRAND
            # ----------------------------------------------------------

            strand, _ = CurriculumStrand.objects.get_or_create(
                learning_area=learning_area,
                code=strand_code,
                defaults={
                    "name": strand_name,
                    "order": self.order_from_code(
                        strand_code
                    ),
                    "description": "",
                },
            )

            strand.name = strand_name
            strand.order = self.order_from_code(
                strand_code
            )
            strand.description = ""
            strand.save()

            # ----------------------------------------------------------
            # SUB-STRANDS
            # ----------------------------------------------------------

            for index, (
                sub_code,
                sub_name,
            ) in enumerate(sub_strands, start=1):

                sub_strand, _ = (
                    CurriculumSubStrand.objects.get_or_create(
                        strand=strand,
                        code=sub_code,
                        defaults={
                            "name": sub_name,
                            "order": index,
                            "description": "",
                        },
                    )
                )

                sub_strand.name = sub_name
                sub_strand.order = index
                sub_strand.description = ""
                sub_strand.save()

                # ------------------------------------------------------
                # ASSESSMENT ITEM
                # ------------------------------------------------------

                assessment_item, _ = (
                    CurriculumAssessmentItem.objects.get_or_create(
                        sub_strand=sub_strand,
                        term=term,
                        name=sub_name,
                        defaults={
                            "description": "",
                            "order": index,
                            "active": True,
                        },
                    )
                )

                assessment_item.description = ""
                assessment_item.order = index
                assessment_item.active = True
                assessment_item.save()

        # ==============================================================
        # COUNTS
        # ==============================================================

        learning_area_count = (
            CurriculumLearningArea.objects.filter(
                curriculum_grade=grade,
                pathway=None,
            ).count()
        )

        strand_count = (
            CurriculumStrand.objects.filter(
                learning_area__curriculum_grade=grade,
            ).count()
        )

        sub_strand_count = (
            CurriculumSubStrand.objects.filter(
                strand__learning_area__curriculum_grade=grade,
            ).count()
        )

        assessment_item_count = (
            CurriculumAssessmentItem.objects.filter(
                sub_strand__strand__learning_area__curriculum_grade=grade,
            ).count()
        )

        # ==============================================================
        # SUCCESS OUTPUT
        # ==============================================================

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"PP2 CBC curriculum seeded successfully "
                f"for {academic_year}."
            )
        )
        self.stdout.write("")

        self.stdout.write(
            f"Curriculum Version : {version.name}"
        )

        self.stdout.write(
            f"Grade              : {grade.display_name}"
        )

        self.stdout.write(
            f"Learning Areas     : {learning_area_count}"
        )

        self.stdout.write(
            f"Strands            : {strand_count}"
        )

        self.stdout.write(
            f"Sub-Strands        : {sub_strand_count}"
        )

        self.stdout.write(
            f"Assessment Items   : {assessment_item_count}"
        )

        self.stdout.write("")

    # ==============================================================
    # HELPERS
    # ==============================================================

    @staticmethod
    def make_code(name):
        return (
            name.upper()
            .replace("&", "AND")
            .replace(" ", "_")
            .replace("-", "_")
        )[:50]

    @staticmethod
    def order_from_code(code):
        try:
            if "-" in str(code):
                return int(
                    str(code).split("-")[-1]
                )

            return int(
                float(code)
            )

        except (TypeError, ValueError):
            return 0