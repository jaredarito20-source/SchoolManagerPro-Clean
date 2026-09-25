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
    help = "Seed Grade 2 CBC assessment-book curriculum for Terms 1-3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2026",
            help="Academic year to seed. Default: 2026",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        academic_year = str(
            options["academic_year"]
        ).strip()

        # ============================================================
        # CURRICULUM VERSION
        # ============================================================

        version, _ = CurriculumVersion.objects.update_or_create(
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC Lower Primary curriculum.",
            },
        )

        # ============================================================
        # GRADE
        # ============================================================

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE2",
            defaults={
                "display_name": "Grade 2",
            },
        )

        # ============================================================
        # GRADE 2 CURRICULUM
        #
        # Structure:
        #
        # Learning Area
        #     -> Strand
        #          -> Sub-Strand
        #               -> Assessment Item
        #
        # Terms are deliberately kept on the assessment item.
        # ============================================================

        curriculum = {

            # ========================================================
            # 1. ENGLISH LANGUAGE ACTIVITIES
            # ========================================================

            "English Language Activities": {

                "1.0 Listening and Speaking": [
                    "Pronunciation and Vocabulary",
                    "Listening Comprehension",
                    "Polite Language",
                    "Giving and Following Instructions",
                ],

                "2.0 Reading": [
                    "Pre-reading",
                    "Word Reading",
                    "Reading Fluency",
                    "Reading Comprehension",
                ],

                "3.0 Language Use": [
                    "Word Classes",
                    "Tenses",
                    "Sentence Construction",
                    "Punctuation",
                ],

                "4.0 Writing": [
                    "Handwriting",
                    "Spelling",
                    "Guided Writing",
                    "Creative Writing",
                ],
            },

            # ========================================================
            # 2. KISWAHILI LANGUAGE ACTIVITIES
            # ========================================================

            "Kiswahili Language Activities": {

                "1.0 Kusikiliza na Kuzungumza": [
                    "Matamshi",
                    "Msamiati",
                    "Maamkuzi na Maagano",
                    "Kutoa Maagizo",
                    "Kusikiliza na Kujibu",
                ],

                "2.0 Kusoma": [
                    "Kusoma kwa Ufasaha",
                    "Kuelewa Kile Kinachosomwa",
                    "Msamiati wa Kusoma",
                ],

                "3.0 Kuandika": [
                    "Hati Nadhifu",
                    "Tahajia",
                    "Alama za Uakifishaji",
                    "Uandishi wa Kuongozwa",
                ],

                "4.0 Sarufi": [
                    "Matumizi ya Maneno",
                    "Sentensi",
                    "Nyakati",
                    "Umoja na Wingi",
                ],

                "5.0 Fasihi": [
                    "Nyimbo",
                    "Mashairi",
                    "Hadithi",
                    "Vitendawili",
                ],
            },

            # ========================================================
            # 3. MATHEMATICAL ACTIVITIES
            #
            # KICD Grade 2 Mathematics is organised under:
            # Numbers, Measurement and Geometry.
            # ========================================================

            "Mathematical Activities": {

                "1.0 Numbers": [
                    "Whole Numbers",
                    "Place Value",
                    "Addition",
                    "Subtraction",
                    "Multiplication",
                    "Division",
                ],

                "2.0 Measurement": [
                    "Length",
                    "Mass",
                    "Capacity",
                    "Time",
                    "Money",
            ],

                "3.0 Geometry": [
                    "Lines",
                    "Shapes",
                    "Position and Direction",
                ],
            },

            # ========================================================
            # 4. ENVIRONMENTAL ACTIVITIES
            # ========================================================

            "Environmental Activities": {

                "1.0 SOCIAL ENVIRONMENT": [
                    "Our Home",
                    "Our School",
                    "Our Community",
                    "People in Our Community",
                    "Transport and Communication",
                ],

                "2.0 NATURAL ENVIRONMENT": [
                    "Weather",
                    "Soil",
                    "Plants",
                    "Animals",
                    "Water",
                ],

                "3.0 RESOURCES IN OUR ENVIRONMENT": [
                    "Sources of Water",
                    "Uses of Water",
                    "Sources of Food",
                    "Energy and Fuel",
                    "Environmental Conservation",
                ],

                "4.0 HYGIENE AND NUTRITION": [
                    "Personal Hygiene",
                    "Food and Nutrition",
                    "Safety and First Aid",
                ],
            },

            # ========================================================
            # 5. CREATIVE ACTIVITIES
            # ========================================================

            "Creative Activities": {

                "1.0 Creating and Executing": [
                    "Drawing",
                    "Painting and Colouring",
                    "Pattern Making",
                    "Modelling",
                    "Music and Rhythm",
                    "Movement",
                ],

                "2.0 Performing and Display": [
                    "Singing",
                    "Action Songs",
                    "Games",
                    "Dancing",
                    "Throwing and Catching",
                    "Creative Display",
                ],

                "3.0 Appreciation": [
                    "Appreciating Musical Sounds",
                    "Appreciating Art Work",
                    "Safety Awareness",
                ],
            },

            # ========================================================
            # 6. CHRISTIAN RELIGIOUS EDUCATION
            # ========================================================

            "Christian Religious Education Activities": {

                "1.0 God the Creator": [
                    "God's Creation",
                    "Caring for God's Creation",
                    "Appreciating God's Creation",
                ],

                "2.0 The Holy Bible": [
                    "The Holy Bible",
                    "Stories from the Bible",
                    "Using the Bible",
                ],

                "3.0 Life of Jesus Christ": [
                    "Birth of Jesus",
                    "Jesus Shows Love",
                    "Jesus Helps Others",
                    "Jesus Teaches People",
                ],

                "4.0 Christian Values": [
                    "Love",
                    "Respect",
                    "Responsibility",
                    "Honesty",
                    "Obedience",
                ],

                "5.0 The Church": [
                    "The Church as a Place of Worship",
                    "Activities in the Church",
                    "Serving Others",
                ],
            },
        }

        # ============================================================
        # CREATE CURRICULUM
        # ============================================================

        for learning_area_name, strands in curriculum.items():

            learning_area, _ = (
                CurriculumLearningArea.objects.update_or_create(
                    curriculum_grade=grade,
                    name=learning_area_name,
                    pathway=None,
                    defaults={
                        "description": (
                            f"{learning_area_name} for Grade 2."
                        ),
                    },
                )
            )

            for strand_code_name, sub_strands in strands.items():

                # Split "1.0 Numbers" into code + name
                parts = strand_code_name.split(
                    " ",
                    1,
                )

                if len(parts) == 2:
                    strand_code = parts[0]
                    strand_name = parts[1]
                else:
                    strand_code = strand_code_name
                    strand_name = strand_code_name

                strand, _ = (
                    CurriculumStrand.objects.update_or_create(
                        learning_area=learning_area,
                        code=strand_code,
                        defaults={
                            "name": strand_name,
                        },
                    )
                )

                for index, sub_strand_name in enumerate(
                    sub_strands,
                    start=1,
                ):

                    sub_strand, _ = (
                        CurriculumSubStrand.objects.update_or_create(
                            strand=strand,
                            code=f"{strand_code}.{index}",
                            defaults={
                                "name": sub_strand_name,
                            },
                        )
                    )

                    # ------------------------------------------------
                    # One assessment item per sub-strand.
                    #
                    # E.E / M.E / A.E / B.E are performance levels
                    # handled by the assessment system, NOT separate
                    # curriculum items.
                    # ------------------------------------------------

                    CurriculumAssessmentItem.objects.update_or_create(
                        sub_strand=sub_strand,
                        defaults={
                            "name": sub_strand_name,
                            "description": (
                                f"Grade 2 assessment item: "
                                f"{sub_strand_name}."
                            ),
                        },
                    )

        # ============================================================
        # RESULT
        # ============================================================

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
                f"Grade 2 CBC curriculum seeded successfully "
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