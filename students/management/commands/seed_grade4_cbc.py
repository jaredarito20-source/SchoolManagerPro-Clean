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
    help = "Seed Grade 4 CBC assessment-book curriculum for Terms 1-3."

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
                "description": "CBC Upper Primary curriculum.",
            },
        )

        # ============================================================
        # GRADE 4
        # ============================================================

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE4",
            defaults={
                "display_name": "Grade 4",
            },
        )

        # ============================================================
        # GRADE 4 CURRICULUM
        #
        # KICD Grade 4 has moved into Upper Primary.
        #
        # Do NOT add:
        # - E.E / M.E / A.E / B.E as curriculum items
        # - PPI as an academic learning area
        #
        # Those belong elsewhere in the assessment/reporting system.
        # ============================================================

        curriculum = {

            # ========================================================
            # 1. ENGLISH
            # ========================================================

            "English": {

                "1.0 Listening and Speaking": [
                    "Pronunciation and Vocabulary",
                    "Listening Comprehension",
                    "Oral Communication",
                    "Giving and Following Instructions",
                ],

                "2.0 Reading": [
                    "Pre-reading",
                    "Fluency",
                    "Comprehension",
                    "Intensive Reading",
                    "Extensive Reading",
                ],

                "3.0 Language Use": [
                    "Word Classes",
                    "Sentence Construction",
                    "Tenses",
                    "Punctuation",
                    "Vocabulary Development",
                ],

                "4.0 Writing": [
                    "Handwriting",
                    "Spelling",
                    "Guided Writing",
                    "Creative Writing",
                    "Functional Writing",
                ],
            },

            # ========================================================
            # 2. KISWAHILI
            # ========================================================

            "Kiswahili": {

                "1.0 Kusikiliza na Kuzungumza": [
                    "Matamshi",
                    "Msamiati",
                    "Mazungumzo",
                    "Kutoa Maagizo",
                    "Kusimulia",
                ],

                "2.0 Kusoma": [
                    "Kusoma kwa Ufasaha",
                    "Ufahamu",
                    "Msamiati",
                    "Kusoma kwa Kina",
                    "Kusoma kwa Mapana",
                ],

                "3.0 Kuandika": [
                    "Hati Nadhifu",
                    "Tahajia",
                    "Uakifishaji",
                    "Uandishi wa Kuongozwa",
                    "Uandishi wa Kiubunifu",
                ],

                "4.0 Sarufi": [
                    "Aina za Maneno",
                    "Nyakati",
                    "Umoja na Wingi",
                    "Sentensi",
                    "Msamiati",
                ],

                "5.0 Fasihi": [
                    "Hadithi",
                    "Mashairi",
                    "Nyimbo",
                    "Methali",
                    "Vitendawili",
                ],
            },

            # ========================================================
            # 3. MATHEMATICS
            # ========================================================

            "Mathematics": {

                "1.0 Numbers": [
                    "Whole Numbers",
                    "Place Value",
                    "Addition",
                    "Subtraction",
                    "Multiplication",
                    "Division",
                    "Fractions",
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
                    "Data Collection",
                    "Data Representation",
                    "Data Interpretation",
                ],

                "5.0 Algebraic Thinking": [
                    "Patterns",
                    "Sequences",
                    "Number Relationships",
                ],
            },

            # ========================================================
            # 4. SCIENCE & TECHNOLOGY
            # ========================================================

            "Science & Technology": {

                "1.0 Living Things": [
                    "Plants",
                    "Animals",
                    "Human Body",
                    "Life Processes",
                ],

                "2.0 Matter": [
                    "States of Matter",
                    "Properties of Matter",
                    "Changes in Matter",
                ],

                "3.0 Force and Energy": [
                    "Forces",
                    "Energy",
                    "Light",
                    "Heat",
                    "Sound",
                ],

                "4.0 Earth and Space": [
                    "Weather",
                    "Soil",
                    "Water",
                    "The Solar System",
                ],

                "5.0 Technology": [
                    "Technology in Everyday Life",
                    "Digital Devices",
                    "Safety in Technology Use",
                ],
            },

            # ========================================================
            # 5. AGRICULTURE AND NUTRITION
            # ========================================================

            "Agriculture and Nutrition": {

                "1.0 Agriculture and Environment": [
                    "Soil",
                    "Water in Agriculture",
                    "Environmental Conservation",
                ],

                "2.0 Crop Production": [
                    "Seeds",
                    "Planting",
                    "Crop Care",
                    "Harvesting",
                    "Storage",
                ],

                "3.0 Livestock Production": [
                    "Domestic Animals",
                    "Livestock Care",
                    "Livestock Products",
                ],

                "4.0 Food and Nutrition": [
                    "Food Sources",
                    "Food Groups",
                    "Balanced Diet",
                    "Food Hygiene",
                    "Food Preservation",
                ],
            },

            # ========================================================
            # 6. SOCIAL STUDIES
            # ========================================================

            "Social Studies": {

                "1.0 Natural and Built Environment": [
                    "Physical Features",
                    "Weather and Climate",
                    "Natural Resources",
                    "Human-Made Features",
                ],

                "2.0 People and Population": [
                    "Family",
                    "Community",
                    "Population",
                    "Settlement",
                ],

                "3.0 Citizenship": [
                    "Rights and Responsibilities",
                    "Leadership",
                    "Good Citizenship",
                    "National Values",
                ],

                "4.0 History": [
                    "Sources of History",
                    "Communities in Kenya",
                    "Historical Sites",
                    "Kenyan Heritage",
                ],

                "5.0 Geography": [
                    "Maps",
                    "Direction",
                    "Location",
                    "Kenya and Its Neighbours",
                ],

                "6.0 Resources and Economic Activities": [
                    "Natural Resources",
                    "Agriculture",
                    "Trade",
                    "Transport",
                    "Communication",
                ],
            },

            # ========================================================
            # 7. CREATIVE ARTS
            # ========================================================

            "Creative Arts": {

                "1.0 Creating and Executing": [
                    "Drawing",
                    "Painting",
                    "Colouring",
                    "Pattern Making",
                    "Modelling",
                    "Music",
                    "Movement",
                ],

                "2.0 Performing and Displaying": [
                    "Singing",
                    "Dancing",
                    "Drama",
                    "Games",
                    "Musical Performance",
                    "Art Display",
                ],

                "3.0 Appreciation in Creative Arts": [
                    "Appreciating Music",
                    "Appreciating Art",
                    "Appreciating Performance",
                    "Safety in Creative Activities",
                ],
            },

            # ========================================================
            # 8. CHRISTIAN RELIGIOUS EDUCATION
            # ========================================================

            "Christian Religious Education": {

                "1.0 Creation": [
                    "God the Creator",
                    "God's Creation",
                    "Caring for Creation",
                ],

                "2.0 The Bible": [
                    "The Bible",
                    "Bible Stories",
                    "Using the Bible",
                ],

                "3.0 Jesus Christ": [
                    "Life of Jesus",
                    "Teachings of Jesus",
                    "Miracles of Jesus",
                    "Jesus and Other People",
                ],

                "4.0 Christian Values": [
                    "Love",
                    "Respect",
                    "Responsibility",
                    "Honesty",
                    "Forgiveness",
                ],

                "5.0 Christian Living": [
                    "Prayer",
                    "Worship",
                    "Service",
                    "Living Peacefully with Others",
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
                            f"{learning_area_name} "
                            f"for Grade 4."
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
                                f"Grade 4 assessment item: "
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
                f"Grade 4 CBC curriculum seeded successfully "
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