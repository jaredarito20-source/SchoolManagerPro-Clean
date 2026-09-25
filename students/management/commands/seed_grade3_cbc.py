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
    help = "Seed Grade 3 CBC assessment-book curriculum for Terms 1-3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2026",
            help="Academic year to seed. Default: 2026.",
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
        # GRADE 3
        # ============================================================

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE3",
            defaults={
                "display_name": "Grade 3",
            },
        )

        # ============================================================
        # GRADE 3 CURRICULUM
        #
        # NOTE:
        # KICD themes are preserved in the sub-strand names so that
        # the assessment book can later display the theme/context
        # without requiring a new database model.
        #
        # E.E / M.E / A.E / B.E are NOT curriculum items.
        # They are assessment performance levels.
        # ============================================================

        curriculum = {

            # ========================================================
            # ENGLISH LANGUAGE ACTIVITIES
            # ========================================================

            "English Language Activities": {

                "1.0 Listening and Speaking": [
                    (
                        "Theme 1: Activities at Home and School — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 2: Sharing Duties and Responsibilities — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 3: Safety — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 4: Home and Family — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 5: Occupations — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 6: Road Safety — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 7: Safety and Security — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 8: Wildlife Conservation — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 9: Wildlife — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 10: Technology — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 11: Talents — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 12: Food and Diseases — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 13: Leisure Time Activities — "
                        "Pronunciation and Vocabulary"
                    ),
                    (
                        "Theme 14: Talents — "
                        "Pronunciation and Vocabulary"
                    ),
                ],

                "2.0 Reading": [
                    (
                        "Theme 1: Activities at Home and School — "
                        "Fluency"
                    ),
                    (
                        "Theme 1: Activities at Home and School — "
                        "Comprehension"
                    ),
                    (
                        "Theme 2: Sharing Duties and Responsibilities — "
                        "Fluency"
                    ),
                    (
                        "Theme 2: Sharing Duties and Responsibilities — "
                        "Comprehension"
                    ),
                    (
                        "Theme 3: Safety — Fluency"
                    ),
                    (
                        "Theme 3: Safety — Comprehension"
                    ),
                    (
                        "Theme 4: Home and Family — Fluency"
                    ),
                    (
                        "Theme 4: Home and Family — Comprehension"
                    ),
                    (
                        "Theme 5: Occupations — Fluency"
                    ),
                    (
                        "Theme 5: Occupations — Comprehension"
                    ),
                    (
                        "Theme 6: Road Safety — Fluency"
                    ),
                    (
                        "Theme 6: Road Safety — Comprehension"
                    ),
                    (
                        "Theme 7: Safety and Security — Fluency"
                    ),
                    (
                        "Theme 7: Safety and Security — Comprehension"
                    ),
                    (
                        "Theme 8: Wildlife Conservation — Fluency"
                    ),
                    (
                        "Theme 8: Wildlife Conservation — Comprehension"
                    ),
                    (
                        "Theme 9: Wildlife — Fluency"
                    ),
                    (
                        "Theme 9: Wildlife — Comprehension"
                    ),
                    (
                        "Theme 10: Technology — Fluency"
                    ),
                    (
                        "Theme 10: Technology — Comprehension"
                    ),
                    (
                        "Theme 11: Talents — Fluency"
                    ),
                    (
                        "Theme 11: Talents — Comprehension"
                    ),
                    (
                        "Theme 12: Food and Diseases — Fluency"
                    ),
                    (
                        "Theme 12: Food and Diseases — Comprehension"
                    ),
                    (
                        "Theme 13: Leisure Time Activities — Fluency"
                    ),
                    (
                        "Theme 13: Leisure Time Activities — Comprehension"
                    ),
                    (
                        "Theme 14: Talents — Fluency"
                    ),
                    (
                        "Theme 14: Talents — Comprehension"
                    ),
                ],

                "3.0 Language Use": [
                    (
                        "Theme 1: Activities at Home and School — "
                        "Language Structures"
                    ),
                    (
                        "Theme 2: Sharing Duties and Responsibilities — "
                        "Forms of the Verb 'to do' and Subject-Verb Agreement"
                    ),
                    (
                        "Theme 3: Safety — Language Structures"
                    ),
                    (
                        "Theme 4: Home and Family — Language Structures"
                    ),
                    (
                        "Theme 5: Occupations — Language Structures"
                    ),
                    (
                        "Theme 6: Road Safety — Language Structures"
                    ),
                    (
                        "Theme 7: Safety and Security — Language Structures"
                    ),
                    (
                        "Theme 8: Wildlife Conservation — Language Structures"
                    ),
                    (
                        "Theme 9: Wildlife — Opposites"
                    ),
                    (
                        "Theme 10: Technology — Language Structures"
                    ),
                    (
                        "Theme 11: Talents — Comparatives and Superlatives"
                    ),
                    (
                        "Theme 12: Food and Diseases — Language Structures"
                    ),
                    (
                        "Theme 13: Leisure Time Activities — Language Structures"
                    ),
                    (
                        "Theme 14: Talents — Language Structures"
                    ),
                ],

                "4.0 Writing": [
                    (
                        "Theme 1: Activities at Home and School — "
                        "Handwriting"
                    ),
                    (
                        "Theme 1: Activities at Home and School — "
                        "Spelling"
                    ),
                    (
                        "Theme 1: Activities at Home and School — "
                        "Punctuation"
                    ),
                    (
                        "Theme 1: Activities at Home and School — "
                        "Guided Writing"
                    ),
                    (
                        "Theme 2: Sharing Duties and Responsibilities — "
                        "Writing"
                    ),
                    (
                        "Theme 3: Safety — Writing"
                    ),
                    (
                        "Theme 4: Home and Family — Writing"
                    ),
                    (
                        "Theme 5: Occupations — Writing"
                    ),
                    (
                        "Theme 6: Road Safety — Writing"
                    ),
                    (
                        "Theme 7: Safety and Security — Writing"
                    ),
                    (
                        "Theme 8: Wildlife Conservation — Writing"
                    ),
                    (
                        "Theme 9: Wildlife — Punctuation"
                    ),
                    (
                        "Theme 10: Technology — Writing"
                    ),
                    (
                        "Theme 11: Talents — Guided Writing"
                    ),
                    (
                        "Theme 12: Food and Diseases — Writing"
                    ),
                    (
                        "Theme 13: Leisure Time Activities — Writing"
                    ),
                    (
                        "Theme 14: Talents — Guided Writing"
                    ),
                ],
            },

            # ========================================================
            # KISWAHILI LANGUAGE ACTIVITIES
            # ========================================================

            "Kiswahili Language Activities": {

                "1.0 Kusikiliza na Kuzungumza": [
                    "Matamshi na Msamiati",
                    "Mazungumzo",
                    "Kutoa Maagizo",
                    "Kusimulia",
                    "Kusikiliza na Kujibu",
                ],

                "2.0 Kusoma": [
                    "Kusoma kwa Ufasaha",
                    "Ufahamu",
                    "Msamiati",
                    "Kutabiri na Kueleza Maana",
                ],

                "3.0 Kuandika": [
                    "Hati Nadhifu",
                    "Tahajia",
                    "Alama za Uakifishaji",
                    "Uandishi wa Kuongozwa",
                    "Uandishi wa Aya Fupi",
                ],

                "4.0 Sarufi": [
                    "Matumizi ya Maneno",
                    "Nyakati",
                    "Umoja na Wingi",
                    "Sentensi",
                    "Msamiati",
                ],

                "5.0 Fasihi": [
                    "Nyimbo",
                    "Mashairi",
                    "Hadithi",
                    "Vitendawili",
                    "Methali",
                ],
            },

            # ========================================================
            # MATHEMATICAL ACTIVITIES
            # ========================================================

            "Mathematical Activities": {

                "1.0 Numbers": [
                    "Whole Numbers",
                    "Place Value",
                    "Addition",
                    "Subtraction",
                    "Multiplication",
                    "Division",
                    "Fractions",
                    "Patterns",
                ],

                "2.0 Measurement": [
                    "Length",
                    "Mass",
                    "Capacity",
                    "Time",
                    "Money",
                    "Area",
                ],

                "3.0 Geometry": [
                    "Lines",
                    "Angles",
                    "Shapes",
                    "Position and Direction",
                    "Symmetry",
                ],

                "4.0 Data Handling": [
                    "Collecting Data",
                    "Representing Data",
                    "Interpreting Data",
                ],
            },

            # ========================================================
            # ENVIRONMENTAL ACTIVITIES
            #
            # These names follow the Grade 3 KICD Environmental
            # Activities design more closely.
            # ========================================================

            "Environmental Activities": {

                "1.0 Social Environment": [
                    "Sleeping Area",
                    "Family Needs — Emotional Needs",
                    "Food in Our Environment",
                    "Our Community",
                    "Cultural Events",
                ],

                "2.0 Natural Environment": [
                    "Weather",
                    "Soil",
                    "Heat",
                ],

                "3.0 Resources in Our Environment": [
                    "Water",
                    "Plants",
                    "Animals",
                    "Waste Materials",
                ],
            },

            # ========================================================
            # CREATIVE ACTIVITIES
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
                    "Dancing",
                    "Games",
                    "Throwing and Catching",
                    "Creative Display",
                ],

                "3.0 Appreciation": [
                    "Musical Sounds",
                    "Art Work",
                    "Movement Activities",
                    "Safety Awareness",
                ],
            },

            # ========================================================
            # CHRISTIAN RELIGIOUS EDUCATION
            # ========================================================

            "Christian Religious Education Activities": {

                "1.0 God and Creation": [
                    "God the Creator",
                    "God's Creation",
                    "Caring for God's Creation",
                ],

                "2.0 The Holy Bible": [
                    "The Holy Bible",
                    "Bible Stories",
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
        # CREATE / UPDATE CURRICULUM
        # ============================================================

        for learning_area_name, strands in curriculum.items():

            learning_area, _ = (
                CurriculumLearningArea.objects.update_or_create(
                    curriculum_grade=grade,
                    name=learning_area_name,
                    pathway=None,
                    defaults={
                        "description": (
                            f"{learning_area_name} for Grade 3."
                        ),
                    },
                )
            )

            for strand_code_name, sub_strands in strands.items():

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

                    CurriculumAssessmentItem.objects.update_or_create(
                        sub_strand=sub_strand,
                        defaults={
                            "name": sub_strand_name,
                            "description": (
                                f"Grade 3 assessment item: "
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
                f"Grade 3 CBC curriculum seeded successfully "
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