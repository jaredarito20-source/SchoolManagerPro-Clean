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
    help = "Seed Grade 1 CBC assessment-book curriculum for Terms 1-3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2026",
            help="Academic year for the curriculum version.",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        academic_year = str(options["academic_year"])

        # --------------------------------------------------------------
        # CURRICULUM VERSION
        # --------------------------------------------------------------

        version, _ = CurriculumVersion.objects.get_or_create(
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC Lower Primary curriculum.",
            },
        )

        version.name = f"CBC {academic_year}"
        version.academic_year = academic_year
        version.description = "CBC Lower Primary curriculum."
        version.save()

        # --------------------------------------------------------------
        # GRADE
        # --------------------------------------------------------------

        grade, _ = CurriculumGrade.objects.get_or_create(
            curriculum_version=version,
            grade="GRADE1",
            defaults={
                "display_name": "Grade 1",
            },
        )

        grade.display_name = "Grade 1"
        grade.save()

        # ==============================================================
        # GRADE 1 CBC CURRICULUM
        # ==============================================================
        #
        # Source basis:
        #   KICD regular Lower Primary Grade 1 designs.
        #
        # Structure:
        #
        # Learning Area
        #     -> Strand
        #         -> Sub-Strand
        #             -> Assessment Item
        #
        # E.E / M.E / A.E / B.E are NOT curriculum items.
        # They remain handled by the assessment engine.
        #
        # KICD provides curriculum sequences rather than imposing
        # SchoolManagerPro's internal assessment-book database structure.
        # Therefore the term allocation below is the application's
        # assessment-book grouping of the KICD Grade 1 sequence.
        # ==============================================================

        curriculum = [

            # ==========================================================
            # ENGLISH LANGUAGE ACTIVITIES
            # ==========================================================

            (
                "English Language Activities",
                "1.0",
                "Listening and Speaking",
                "1",
                [
                    (
                        "1.1",
                        "Pronunciation and vocabulary",
                    ),
                ],
            ),

            (
                "English Language Activities",
                "2.0",
                "Reading",
                "1",
                [
                    (
                        "2.1",
                        "Pre-reading",
                    ),
                    (
                        "2.2",
                        "Word reading",
                    ),
                ],
            ),

            (
                "English Language Activities",
                "3.0",
                "Language Use",
                "2",
                [
                    (
                        "3.1",
                        "Word classes",
                    ),
                    (
                        "3.2",
                        "Tense",
                    ),
                    (
                        "3.3",
                        "Sentences",
                    ),
                ],
            ),

            (
                "English Language Activities",
                "4.0",
                "Writing",
                "2",
                [
                    (
                        "4.1",
                        "Pre-writing",
                    ),
                    (
                        "4.2",
                        "Handwriting",
                    ),
                    (
                        "4.3",
                        "Spelling",
                    ),
                ],
            ),

            (
                "English Language Activities",
                "5.0",
                "Reading Fluency and Comprehension",
                "3",
                [
                    (
                        "5.1",
                        "Fluency",
                    ),
                    (
                        "5.2",
                        "Comprehension",
                    ),
                ],
            ),

            (
                "English Language Activities",
                "6.0",
                "Writing Development",
                "3",
                [
                    (
                        "6.1",
                        "Punctuation",
                    ),
                    (
                        "6.2",
                        "Guided writing",
                    ),
                ],
            ),

            # ==========================================================
            # KISWAHILI LANGUAGE ACTIVITIES
            # ==========================================================

            (
                "Kiswahili Language Activities",
                "1.0",
                "Kusikiliza na Kuzungumza",
                "1",
                [
                    (
                        "1.1",
                        "Maamkuzi na Maagano",
                    ),
                    (
                        "1.2",
                        "Matamshi Bora",
                    ),
                ],
            ),

            (
                "Kiswahili Language Activities",
                "2.0",
                "Kusoma",
                "1",
                [
                    (
                        "2.1",
                        "Kusoma kwa Ufasaha",
                    ),
                    (
                        "2.2",
                        "Kusoma kwa Ufahamu",
                    ),
                ],
            ),

            (
                "Kiswahili Language Activities",
                "3.0",
                "Kuandika",
                "2",
                [
                    (
                        "3.1",
                        "Hati nadhifu - Herufi kubwa",
                    ),
                    (
                        "3.2",
                        "Hati nadhifu - Herufi ndogo",
                    ),
                ],
            ),

            (
                "Kiswahili Language Activities",
                "4.0",
                "Sarufi",
                "2",
                [
                    (
                        "4.1",
                        "Matumizi ya Mimi na Sisi",
                    ),
                    (
                        "4.2",
                        "Matumizi ya maneno katika sentensi",
                    ),
                ],
            ),

            (
                "Kiswahili Language Activities",
                "5.0",
                "Kusikiliza na Kuzungumza",
                "3",
                [
                    (
                        "5.1",
                        "Mazungumzo",
                    ),
                    (
                        "5.2",
                        "Usimulizi",
                    ),
                ],
            ),

            (
                "Kiswahili Language Activities",
                "6.0",
                "Kusoma na Kuandika",
                "3",
                [
                    (
                        "6.1",
                        "Kusoma kwa Ufahamu",
                    ),
                    (
                        "6.2",
                        "Kuandika sentensi",
                    ),
                ],
            ),

            # ==========================================================
            # MATHEMATICAL ACTIVITIES
            # ==============================================================

            (
                "Mathematical Activities",
                "1.0",
                "Numbers",
                "1",
                [
                    (
                        "1.1",
                        "Pre-Number Activities",
                    ),
                    (
                        "1.2",
                        "Whole Numbers",
                    ),
                ],
            ),

            (
                "Mathematical Activities",
                "2.0",
                "Numbers",
                "2",
                [
                    (
                        "2.1",
                        "Addition",
                    ),
                    (
                        "2.2",
                        "Subtraction",
                    ),
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
                        "Length",
                    ),
                    (
                        "3.2",
                        "Mass",
                    ),
                    (
                        "3.3",
                        "Capacity",
                    ),
                ],
            ),

            (
                "Mathematical Activities",
                "4.0",
                "Measurement",
                "3",
                [
                    (
                        "4.1",
                        "Time",
                    ),
                    (
                        "4.2",
                        "Money",
                    ),
                ],
            ),

            (
                "Mathematical Activities",
                "5.0",
                "Geometry",
                "3",
                [
                    (
                        "5.1",
                        "Lines",
                    ),
                    (
                        "5.2",
                        "Shapes",
                    ),
                ],
            ),

            # ==========================================================
            # ENVIRONMENTAL ACTIVITIES
            # ==============================================================

            (
                "Environmental Activities",
                "1.0",
                "SOCIAL ENVIRONMENT",
                "1",
                [
                    (
                        "1.1",
                        "Cleaning My Body",
                    ),
                    (
                        "1.2",
                        "Our Home",
                    ),
                ],
            ),

            (
                "Environmental Activities",
                "2.0",
                "SOCIAL ENVIRONMENT",
                "1",
                [
                    (
                        "2.1",
                        "Family Needs",
                    ),
                    (
                        "2.2",
                        "Our School",
                    ),
                ],
            ),

            (
                "Environmental Activities",
                "3.0",
                "SOCIAL ENVIRONMENT",
                "2",
                [
                    (
                        "3.1",
                        "Our Market",
                    ),
                ],
            ),

            (
                "Environmental Activities",
                "4.0",
                "NATURAL ENVIRONMENT",
                "2",
                [
                    (
                        "4.1",
                        "Weather and the Sky",
                    ),
                    (
                        "4.2",
                        "Soil",
                    ),
                ],
            ),

            (
                "Environmental Activities",
                "5.0",
                "NATURAL ENVIRONMENT",
                "2",
                [
                    (
                        "5.1",
                        "Sound",
                    ),
                ],
            ),

            (
                "Environmental Activities",
                "6.0",
                "RESOURCES IN OUR ENVIRONMENT",
                "3",
                [
                    (
                        "6.1",
                        "Water",
                    ),
                    (
                        "6.2",
                        "Plants",
                    ),
                    (
                        "6.3",
                        "Animals",
                    ),
                ],
            ),

            # ==========================================================
            # CREATIVE ACTIVITIES
            # ==============================================================

            (
                "Creative Activities",
                "1.0",
                "Creating and Executing",
                "1",
                [
                    (
                        "1.1",
                        "Jumping",
                    ),
                    (
                        "1.2",
                        "Rhythm",
                    ),
                    (
                        "1.3",
                        "Drawing",
                    ),
                    (
                        "1.4",
                        "Stretching",
                    ),
                ],
            ),

            (
                "Creative Activities",
                "2.0",
                "Creating and Executing",
                "2",
                [
                    (
                        "2.1",
                        "Painting and Colouring",
                    ),
                    (
                        "2.2",
                        "Melody",
                    ),
                    (
                        "2.3",
                        "Pattern Making",
                    ),
                ],
            ),

            (
                "Creative Activities",
                "3.0",
                "Performing and Display",
                "2",
                [
                    (
                        "3.1",
                        "Singing Games - Kenyan Style",
                    ),
                    (
                        "3.2",
                        "Throwing and Catching",
                    ),
                    (
                        "3.3",
                        "Paper Craft",
                    ),
                ],
            ),

            (
                "Creative Activities",
                "4.0",
                "Performing and Display",
                "3",
                [
                    (
                        "4.1",
                        "Log Roll and T Balances",
                    ),
                    (
                        "4.2",
                        "Songs - Action songs",
                    ),
                    (
                        "4.3",
                        "Modelling",
                    ),
                    (
                        "4.4",
                        "Percussion Musical Instruments",
                    ),
                ],
            ),

            (
                "Creative Activities",
                "5.0",
                "Appreciation",
                "3",
                [
                    (
                        "5.1",
                        "Musical Sounds",
                    ),
                    (
                        "5.2",
                        "Water Safety Awareness",
                    ),
                ],
            ),

            # ==========================================================
            # CHRISTIAN RELIGIOUS EDUCATION ACTIVITIES
            # ==============================================================

            (
                "Christian Religious Education Activities",
                "1.0",
                "Creation",
                "1",
                [
                    (
                        "1.1",
                        "God the Creator",
                    ),
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
                        "Bible stories",
                    ),
                ],
            ),

            (
                "Christian Religious Education Activities",
                "3.0",
                "The Life and Teachings of Jesus Christ",
                "2",
                [
                    (
                        "3.1",
                        "The birth of Jesus Christ",
                    ),
                    (
                        "3.2",
                        "Jesus teaches us to share",
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
                        "Love",
                    ),
                    (
                        "4.2",
                        "Sharing",
                    ),
                    (
                        "4.3",
                        "Respect",
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
                        "The church as a house of God",
                    ),
                    (
                        "5.2",
                        "Church activities",
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

            cache_key = learning_area_name

            if cache_key not in learning_area_cache:

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
                                "Grade 1 CBC assessment "
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
                    "Grade 1 CBC assessment learning area."
                )

                learning_area.assessment_enabled = True
                learning_area.save()

                learning_area_cache[cache_key] = learning_area

            else:
                learning_area = learning_area_cache[cache_key]

            # ----------------------------------------------------------
            # STRAND
            # ----------------------------------------------------------

            strand, _ = CurriculumStrand.objects.get_or_create(
                learning_area=learning_area,
                code=strand_code,
                defaults={
                    "name": strand_name,
                    "order": self.order_from_code(strand_code),
                    "description": "",
                },
            )

            strand.name = strand_name
            strand.order = self.order_from_code(strand_code)
            strand.save()

            # ----------------------------------------------------------
            # SUB-STRANDS
            # ----------------------------------------------------------

            for index, (sub_code, sub_name) in enumerate(
                sub_strands,
                start=1,
            ):

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

                assessment_item.name = sub_name
                assessment_item.order = index
                assessment_item.description = ""
                assessment_item.active = True
                assessment_item.save()

                # ==============================================================
                # RESULT
                # ==============================================================

                learning_area_count = CurriculumLearningArea.objects.filter(
                    curriculum_grade=grade,
                    pathway=None,
                ).count()

                strand_count = CurriculumStrand.objects.filter(
                    learning_area__curriculum_grade=grade,
                ).count()

                sub_strand_count = CurriculumSubStrand.objects.filter(
                    strand__learning_area__curriculum_grade=grade,
                ).count()

                assessment_item_count = CurriculumAssessmentItem.objects.filter(
                    sub_strand__strand__learning_area__curriculum_grade=grade,
                ).count()

                self.stdout.write("")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Grade 1 CBC curriculum seeded successfully "
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
                return int(str(code).split("-")[-1])

            return int(float(code))

        except (TypeError, ValueError):
            return 0