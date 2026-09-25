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
    help = "Seed Grade 7 CBC assessment-book curriculum for Terms 1-3."

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

        # ---------------------------------------------------------
        # CURRICULUM VERSION
        # ---------------------------------------------------------

        version, _ = CurriculumVersion.objects.update_or_create(
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC Junior School curriculum.",
            },
        )

        # ---------------------------------------------------------
        # GRADE
        # ---------------------------------------------------------

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE7",
            defaults={
                "display_name": "Grade 7",
            },
        )

        # ---------------------------------------------------------
        # GRADE 7 CURRICULUM
        # ---------------------------------------------------------

        curriculum = {

            # =====================================================
            # ENGLISH
            # =====================================================

            "English": {

                "1.0 Listening and Speaking": [
                    "Listening Comprehension",
                    "Pronunciation and Intonation",
                    "Vocabulary Development",
                    "Oral Communication",
                    "Conversation",
                    "Discussion",
                    "Debate",
                ],

                "2.0 Reading": [
                    "Reading Fluency",
                    "Reading Comprehension",
                    "Intensive Reading",
                    "Extensive Reading",
                    "Reading for Information",
                    "Reading for Enjoyment",
                ],

                "3.0 Grammar in Use": [
                    "Parts of Speech",
                    "Nouns",
                    "Pronouns",
                    "Verbs",
                    "Adjectives and Adverbs",
                    "Prepositions",
                    "Conjunctions",
                    "Tenses",
                    "Subject-Verb Agreement",
                    "Sentence Construction",
                    "Punctuation",
                ],

                "4.0 Writing": [
                    "Handwriting",
                    "Spelling",
                    "Paragraph Writing",
                    "Guided Writing",
                    "Functional Writing",
                    "Creative Writing",
                    "Composition Writing",
                ],

                "5.0 Literature": [
                    "Oral Literature",
                    "Prose",
                    "Poetry",
                    "Drama",
                    "Literary Appreciation",
                ],
            },

            # =====================================================
            # KISWAHILI
            # =====================================================

            "Kiswahili": {

                "1.0 Kusikiliza na Kuzungumza": [
                    "Matamshi",
                    "Msamiati",
                    "Mazungumzo",
                    "Majadiliano",
                    "Usimulizi",
                    "Uwasilishaji wa Mawazo",
                ],

                "2.0 Kusoma": [
                    "Kusoma kwa Ufasaha",
                    "Ufahamu",
                    "Msamiati",
                    "Kusoma kwa Kina",
                    "Kusoma kwa Mapana",
                    "Kusoma kwa Kujifurahisha",
                ],

                "3.0 Sarufi": [
                    "Aina za Maneno",
                    "Nomino",
                    "Vitenzi",
                    "Vivumishi",
                    "Vielezi",
                    "Viwakilishi",
                    "Viunganishi",
                    "Nyakati",
                    "Umoja na Wingi",
                    "Uundaji wa Sentensi",
                    "Uakifishaji",
                ],

                "4.0 Kuandika": [
                    "Hati Nadhifu",
                    "Tahajia",
                    "Uakifishaji",
                    "Uandishi wa Kuongozwa",
                    "Uandishi wa Kiubunifu",
                    "Uandishi wa Kitaaluma",
                    "Insha",
                ],

                "5.0 Fasihi": [
                    "Fasihi Simulizi",
                    "Hadithi",
                    "Mashairi",
                    "Nyimbo",
                    "Methali",
                    "Vitendawili",
                    "Misemo",
                    "Fasihi Andishi",
                ],
            },

            # =====================================================
            # MATHEMATICS
            # =====================================================

            "Mathematics": {

                "1.0 Numbers": [
                    "Integers",
                    "Factors and Multiples",
                    "Fractions",
                    "Decimals",
                    "Percentages",
                    "Ratio",
                    "Proportion",
                    "Number Patterns",
                    "Approximation and Estimation",
                ],

                "2.0 Algebra": [
                    "Algebraic Expressions",
                    "Simplifying Algebraic Expressions",
                    "Linear Equations",
                    "Sequences and Patterns",
                    "Substitution",
                ],

                "3.0 Measurement": [
                    "Length",
                    "Mass",
                    "Capacity",
                    "Time",
                    "Money",
                    "Perimeter",
                    "Area",
                    "Volume",
                ],

                "4.0 Geometry": [
                    "Lines and Angles",
                    "Triangles",
                    "Quadrilaterals",
                    "Polygons",
                    "Circles",
                    "Symmetry",
                    "Coordinates",
                ],

                "5.0 Data Handling": [
                    "Data Collection",
                    "Data Representation",
                    "Tables",
                    "Bar Graphs",
                    "Line Graphs",
                    "Pie Charts",
                    "Data Interpretation",
                    "Measures of Central Tendency",
                ],

                "6.0 Probability": [
                    "Chance and Probability",
                    "Simple Probability Experiments",
                ],
            },

            # =====================================================
            # INTEGRATED SCIENCE
            # =====================================================

            "Integrated Science": {

                "1.0 Scientific Investigation": [
                    "Science and Scientific Inquiry",
                    "Laboratory Safety",
                    "Scientific Equipment",
                    "Measurement",
                    "Recording and Presenting Data",
                ],

                "2.0 Matter": [
                    "States of Matter",
                    "Physical Properties of Matter",
                    "Changes of State",
                    "Mixtures",
                    "Separation of Mixtures",
                ],

                "3.0 Living Things": [
                    "Characteristics of Living Things",
                    "Cells",
                    "Cell Structure and Functions",
                    "Micro-organisms",
                    "Classification of Living Things",
                ],

                "4.0 The Human Body": [
                    "Nutrition",
                    "Digestive System",
                    "Respiratory System",
                    "Circulatory System",
                    "Excretory System",
                    "Personal Hygiene",
                ],

                "5.0 Force and Energy": [
                    "Force",
                    "Work",
                    "Energy",
                    "Forms of Energy",
                    "Heat",
                    "Light",
                    "Sound",
                ],

                "6.0 Electricity and Magnetism": [
                    "Electricity",
                    "Simple Electric Circuits",
                    "Conductors and Insulators",
                    "Magnetism",
                    "Uses of Electricity",
                    "Electrical Safety",
                ],

                "7.0 Earth and Space": [
                    "The Earth",
                    "Weather",
                    "Water Cycle",
                    "Soil",
                    "The Solar System",
                    "Environmental Conservation",
                ],
            },

            # =====================================================
            # AGRICULTURE
            # =====================================================

            "Agriculture": {

                "1.0 Agricultural Production": [
                    "Importance of Agriculture",
                    "Agricultural Tools and Equipment",
                    "Farm Records",
                    "Farm Safety",
                ],

                "2.0 Soil and Water Conservation": [
                    "Soil Formation",
                    "Soil Properties",
                    "Soil Fertility",
                    "Soil Conservation",
                    "Water Conservation",
                ],

                "3.0 Crop Production": [
                    "Seed Selection",
                    "Land Preparation",
                    "Planting",
                    "Crop Management",
                    "Weed Management",
                    "Pest and Disease Management",
                    "Harvesting",
                    "Storage",
                ],

                "4.0 Livestock Production": [
                    "Types of Livestock",
                    "Livestock Breeds",
                    "Livestock Feeds",
                    "Livestock Housing",
                    "Livestock Health",
                    "Livestock Products",
                ],

                "5.0 Food and Nutrition": [
                    "Food Groups",
                    "Nutrients",
                    "Balanced Diet",
                    "Food Preparation",
                    "Food Preservation",
                    "Food Hygiene",
                ],
            },

            # =====================================================
            # SOCIAL STUDIES
            # =====================================================

            "Social Studies": {

                "1.0 Natural and Built Environments": [
                    "Map Reading",
                    "Physical Features",
                    "Weather and Climate",
                    "Vegetation",
                    "Natural Resources",
                    "Built Environments",
                ],

                "2.0 People, Population and Social Organisation": [
                    "Population",
                    "Population Distribution",
                    "Population Density",
                    "Migration",
                    "Culture",
                    "Social Organisation",
                    "Family and Community",
                ],

                "3.0 Resources and Economic Activities": [
                    "Natural Resources",
                    "Agriculture",
                    "Livestock Keeping",
                    "Fishing",
                    "Mining",
                    "Trade",
                    "Tourism",
                    "Transport and Communication",
                ],

                "4.0 Political Systems and Governance": [
                    "Traditional Forms of Government",
                    "Colonial Administration",
                    "Struggle for Independence",
                    "Self-Government",
                    "Government of Kenya",
                    "Leadership and Governance",
                ],

                "5.0 Citizenship": [
                    "Meaning of Citizenship",
                    "Rights and Responsibilities",
                    "National Values",
                    "Patriotism",
                    "National Unity",
                    "Good Citizenship",
                ],
            },

            # =====================================================
            # CREATIVE ARTS
            # =====================================================

            "Creative Arts": {

                "1.0 Creating and Executing": [
                    "Drawing",
                    "Painting",
                    "Colour",
                    "Pattern Making",
                    "Modelling",
                    "Crafts",
                    "Music Creation",
                    "Movement",
                ],

                "2.0 Performing and Displaying": [
                    "Singing",
                    "Dancing",
                    "Drama",
                    "Musical Performance",
                    "Art Display",
                    "Creative Performance",
                ],

                "3.0 Appreciation in Creative Arts": [
                    "Appreciation of Music",
                    "Appreciation of Visual Art",
                    "Appreciation of Drama",
                    "Appreciation of Dance",
                    "Creative Arts and Culture",
                    "Safety in Creative Arts",
                ],

                "4.0 Sports and Physical Activities": [
                    "Athletics",
                    "Games",
                    "Ball Games",
                    "Gymnastics",
                    "Dance and Movement",
                    "Physical Fitness",
                    "Safety in Sports",
                ],
            },

            # =====================================================
            # PRE-TECHNICAL STUDIES
            # =====================================================

            "Pre-Technical Studies": {

                "1.0 Foundations of Pre-Technical Studies": [
                    "Introduction to Pre-Technical Studies",
                    "Safety in the Workshop",
                    "Workshop Tools",
                    "Workshop Materials",
                ],

                "2.0 Drawing and Design": [
                    "Freehand Drawing",
                    "Geometrical Construction",
                    "Technical Drawing",
                    "Orthographic Drawing",
                    "Design Process",
                ],

                "3.0 Materials and Production": [
                    "Wood",
                    "Metals",
                    "Plastics",
                    "Paper and Board",
                    "Textile Materials",
                    "Production Processes",
                ],

                "4.0 Computer Studies": [
                    "Introduction to Computers",
                    "Computer Hardware",
                    "Computer Software",
                    "Input and Output Devices",
                    "File Management",
                    "Digital Safety",
                ],

                "5.0 Entrepreneurship": [
                    "Introduction to Entrepreneurship",
                    "Entrepreneurial Opportunities",
                    "Business Ideas",
                    "Production Unit",
                    "Financial Literacy",
                    "Entrepreneurial Skills",
                ],
            },

            # =====================================================
            # CHRISTIAN RELIGIOUS EDUCATION
            # =====================================================

            "Christian Religious Education": {

                "1.0 Creation and the Environment": [
                    "Creation",
                    "God's Creation",
                    "Human Responsibility in Creation",
                    "Environmental Conservation",
                ],

                "2.0 The Bible": [
                    "The Bible",
                    "Bible Study",
                    "Biblical Teachings",
                    "Lessons from Biblical Characters",
                ],

                "3.0 The Life and Teachings of Jesus Christ": [
                    "Birth of Jesus",
                    "Ministry of Jesus",
                    "Teachings of Jesus",
                    "Miracles of Jesus",
                    "Parables of Jesus",
                    "Death and Resurrection of Jesus",
                ],

                "4.0 Christian Values": [
                    "Love",
                    "Respect",
                    "Responsibility",
                    "Honesty",
                    "Integrity",
                    "Forgiveness",
                    "Peace",
                    "Justice",
                ],

                "5.0 Christian Living": [
                    "Prayer",
                    "Worship",
                    "Service to Others",
                    "Christian Leadership",
                    "Living Peacefully with Others",
                    "Responsible Use of Resources",
                ],
            },
        }

        # ---------------------------------------------------------
        # CREATE / UPDATE CURRICULUM
        # ---------------------------------------------------------

        for learning_area_name, strands in curriculum.items():

            learning_area, _ = (
                CurriculumLearningArea.objects.update_or_create(
                    curriculum_grade=grade,
                    name=learning_area_name,
                    pathway=None,
                    defaults={
                        "description": (
                            f"{learning_area_name} "
                            f"for Grade 7."
                        ),
                    },
                )
            )

            for strand_code_name, sub_strands in strands.items():

                parts = strand_code_name.split(" ", 1)

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
                                f"Grade 7 assessment item: "
                                f"{sub_strand_name}."
                            ),
                        },
                    )

        # ---------------------------------------------------------
        # COUNTS
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # OUTPUT
        # ---------------------------------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Grade 7 CBC curriculum seeded successfully "
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