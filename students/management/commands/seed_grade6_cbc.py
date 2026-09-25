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
    help = "Seed Grade 6 CBC assessment-book curriculum for Terms 1-3."

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
        # GRADE 6
        # ============================================================

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE6",
            defaults={
                "display_name": "Grade 6",
            },
        )

        # ============================================================
        # GRADE 6 CURRICULUM
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
                    "Conversation",
                    "Debate and Discussion",
                ],

                "2.0 Reading": [
                    "Fluency",
                    "Comprehension",
                    "Intensive Reading",
                    "Extensive Reading",
                    "Reading for Information",
                ],

                "3.0 Language Use": [
                    "Word Classes",
                    "Sentence Construction",
                    "Tenses",
                    "Subject-Verb Agreement",
                    "Vocabulary Development",
                    "Punctuation",
                ],

                "4.0 Writing": [
                    "Handwriting",
                    "Spelling",
                    "Guided Writing",
                    "Creative Writing",
                    "Functional Writing",
                    "Composition Writing",
                ],

                "5.0 Reading for Enjoyment": [
                    "Fiction",
                    "Non-Fiction",
                    "Poetry",
                    "Storytelling",
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
                    "Majadiliano",
                    "Usimulizi",
                    "Kutoa Maagizo",
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
                    "Uandishi wa Kitaaluma",
                ],

                "4.0 Sarufi": [
                    "Aina za Maneno",
                    "Nomino",
                    "Vitenzi",
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
                    "Misemo",
                ],
            },

            # ========================================================
            # 3. MATHEMATICS
            # ========================================================

            "Mathematics": {

                "1.0 Numbers": [
                    "Whole Numbers",
                    "Factors",
                    "Multiples",
                    "Fractions",
                    "Decimals",
                    "Percentages",
                    "Integers",
                    "Ratio",
                    "Number Patterns",
                ],

                "2.0 Measurement": [
                    "Length",
                    "Mass",
                    "Capacity",
                    "Time",
                    "Money",
                    "Area",
                    "Volume",
                ],

                "3.0 Geometry": [
                    "Lines",
                    "Angles",
                    "Triangles",
                    "Quadrilaterals",
                    "Circles",
                    "Position and Direction",
                    "Symmetry",
                ],

                "4.0 Data Handling": [
                    "Data Collection",
                    "Tables",
                    "Bar Graphs",
                    "Line Graphs",
                    "Pie Charts",
                    "Data Interpretation",
                ],

                "5.0 Algebraic Thinking": [
                    "Patterns and Sequences",
                    "Simple Equations",
                    "Number Relationships",
                ],
            },

            # ========================================================
            # 4. SCIENCE & TECHNOLOGY
            # ========================================================

            "Science & Technology": {

                "1.0 Living Things and Their Environment": [
                    "Plants",
                    "Animals",
                    "Human Body",
                    "Micro-organisms",
                    "Adaptation",
                    "Ecosystems",
                ],

                "2.0 Matter": [
                    "States of Matter",
                    "Properties of Matter",
                    "Changes in Matter",
                    "Mixtures",
                    "Separation of Mixtures",
                ],

                "3.0 Force and Energy": [
                    "Force",
                    "Energy",
                    "Light",
                    "Heat",
                    "Sound",
                    "Electricity",
                ],

                "4.0 Earth and Space": [
                    "Weather",
                    "Water",
                    "Soil",
                    "The Earth",
                    "The Solar System",
                ],

                "5.0 Technology": [
                    "Digital Devices",
                    "Information Technology",
                    "Technology in Everyday Life",
                    "Digital Citizenship",
                    "Safety in Technology Use",
                ],
            },

            # ========================================================
            # 5. AGRICULTURE AND NUTRITION
            # ========================================================

            "Agriculture and Nutrition": {

                "1.0 Conservation of Resources": [
                    "Soil Conservation",
                    "Water Conservation",
                    "Environmental Conservation",
                    "Organic Waste Management",
                ],

                "2.0 Crop Production": [
                    "Seed Selection",
                    "Land Preparation",
                    "Planting",
                    "Crop Management",
                    "Harvesting",
                    "Storage",
                ],

                "3.0 Livestock Production": [
                    "Livestock Types",
                    "Livestock Feeds",
                    "Livestock Housing",
                    "Livestock Health",
                    "Livestock Products",
                ],

                "4.0 Food and Nutrition": [
                    "Food Groups",
                    "Nutrients",
                    "Balanced Diet",
                    "Food Preparation",
                    "Food Preservation",
                    "Food Hygiene",
                ],
            },

            # ========================================================
            # 6. SOCIAL STUDIES
            #
            # The main KICD Grade 6 strands include:
            # Natural and Built Environments
            # People, Population and Social Organisations
            # Resources and Economic Activities
            # Political Systems and Governance
            # Citizenship
            # ========================================================

            "Social Studies": {

                "1.0 Natural and the Built Environments": [
                    "Position and Size of Countries in Eastern Africa",
                    "Main Physical Features in Eastern Africa",
                    "Climatic Regions in Eastern Africa",
                    "Vegetation in Eastern Africa",
                    "Historic Built Environments in Eastern Africa",
                ],

                "2.0 People, Population and Social Organisations": [
                    "Culture and Social Organisation",
                    "Language Groups in Eastern Africa",
                    "Population Distribution in Eastern Africa",
                    "Traditional Culture",
                    "Social Organisation",
                ],

                "3.0 Resources and Economic Activities": [
                    "Resources in Eastern Africa",
                    "Agriculture in Eastern Africa",
                    "Beef Farming",
                    "Fishing",
                    "Mining",
                    "Tourism",
                    "Transport and Communication",
                ],

                "4.0 Political Systems and Governance": [
                    "Traditional Forms of Government",
                    "Colonial Administration",
                    "Independence and Self-Government",
                    "Government of Kenya",
                ],

                "5.0 Citizenship": [
                    "Rights and Responsibilities",
                    "Qualities of a Good Citizen",
                    "National Values",
                    "Patriotism",
                    "National Unity",
                ],
            },

            # ========================================================
            # 7. CREATIVE ARTS
            # ========================================================

            "Creative Arts": {

                "1.0 Creating and Executing": [
                    "Drawing",
                    "Painting",
                    "Colour and Design",
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
                    "Creative Arts and Culture",
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
                    "Caring for God's Creation",
                ],

                "2.0 The Bible": [
                    "The Bible",
                    "Bible Stories",
                    "Lessons from the Bible",
                    "Using the Bible",
                ],

                "3.0 Jesus Christ": [
                    "Life of Jesus",
                    "Teachings of Jesus",
                    "Miracles of Jesus",
                    "Jesus and Other People",
                    "Death and Resurrection of Jesus",
                ],

                "4.0 Christian Values": [
                    "Love",
                    "Respect",
                    "Responsibility",
                    "Honesty",
                    "Forgiveness",
                    "Peace",
                ],

                "5.0 Christian Living": [
                    "Prayer",
                    "Worship",
                    "Service",
                    "Christian Responsibility",
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
                            f"for Grade 6."
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
                                f"Grade 6 assessment item: "
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
                f"Grade 6 CBC curriculum seeded successfully "
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