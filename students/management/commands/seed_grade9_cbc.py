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
    help = "Seed Grade 9 CBC assessment-book curriculum for Terms 1-3."

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

        # =========================================================
        # CURRICULUM VERSION
        # =========================================================

        version, _ = CurriculumVersion.objects.update_or_create(
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC Junior School curriculum.",
            },
        )

        # =========================================================
        # GRADE
        # =========================================================

        grade, _ = CurriculumGrade.objects.update_or_create(
            curriculum_version=version,
            grade="GRADE9",
            defaults={
                "display_name": "Grade 9",
            },
        )

        # =========================================================
        # GRADE 9 CURRICULUM
        # =========================================================

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
                    "Oral Presentation",
                ],

                "2.0 Reading": [
                    "Reading Fluency",
                    "Reading Comprehension",
                    "Intensive Reading",
                    "Extensive Reading",
                    "Reading for Information",
                    "Reading for Enjoyment",
                    "Critical Reading",
                ],

                "3.0 Grammar in Use": [
                    "Parts of Speech",
                    "Nouns",
                    "Pronouns",
                    "Verbs",
                    "Adjectives",
                    "Adverbs",
                    "Prepositions",
                    "Conjunctions",
                    "Tenses",
                    "Subject-Verb Agreement",
                    "Sentence Construction",
                    "Punctuation",
                    "Direct and Indirect Speech",
                ],

                "4.0 Writing": [
                    "Paragraph Writing",
                    "Guided Writing",
                    "Functional Writing",
                    "Creative Writing",
                    "Narrative Writing",
                    "Descriptive Writing",
                    "Argumentative Writing",
                    "Report Writing",
                    "Composition Writing",
                ],

                "5.0 Literature": [
                    "Oral Literature",
                    "Prose",
                    "Poetry",
                    "Drama",
                    "Literary Appreciation",
                    "Themes and Messages",
                    "Characterisation",
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
                    "Hotuba",
                    "Mjadala",
                ],

                "2.0 Kusoma": [
                    "Kusoma kwa Ufasaha",
                    "Ufahamu",
                    "Msamiati",
                    "Kusoma kwa Kina",
                    "Kusoma kwa Mapana",
                    "Kusoma kwa Kujifurahisha",
                    "Kusoma kwa Kihakiki",
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
                    "Usemi wa Moja kwa Moja na Usio wa Moja kwa Moja",
                ],

                "4.0 Kuandika": [
                    "Hati Nadhifu",
                    "Tahajia",
                    "Uakifishaji",
                    "Uandishi wa Kuongozwa",
                    "Uandishi wa Kiubunifu",
                    "Uandishi wa Kitaaluma",
                    "Insha ya Masimulizi",
                    "Insha ya Maelezo",
                    "Insha ya Hoja",
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
                    "Uhakiki wa Fasihi",
                ],
            },

            # =====================================================
            # MATHEMATICS
            # =====================================================

            "Mathematics": {

                "1.0 Numbers": [
                    "Integers",
                    "Fractions",
                    "Decimals",
                    "Percentages",
                    "Ratio",
                    "Proportion",
                    "Rates",
                    "Factors and Multiples",
                    "Indices",
                    "Standard Form",
                    "Approximation and Estimation",
                ],

                "2.0 Algebra": [
                    "Algebraic Expressions",
                    "Simplifying Algebraic Expressions",
                    "Linear Equations",
                    "Linear Inequalities",
                    "Sequences and Patterns",
                    "Substitution",
                    "Algebraic Fractions",
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
                    "Surface Area",
                ],

                "4.0 Geometry": [
                    "Lines and Angles",
                    "Triangles",
                    "Quadrilaterals",
                    "Polygons",
                    "Circles",
                    "Symmetry",
                    "Coordinates",
                    "Geometrical Constructions",
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
                    "Probability Experiments",
                    "Probability of Simple Events",
                ],
            },

            # =====================================================
            # INTEGRATED SCIENCE
            # =====================================================

            "Integrated Science": {

                "1.0 Scientific Investigation": [
                    "Scientific Inquiry",
                    "Laboratory Safety",
                    "Scientific Apparatus",
                    "Measurement",
                    "Experimental Procedures",
                    "Recording Data",
                    "Analysis of Results",
                    "Presentation of Findings",
                ],

                "2.0 Matter": [
                    "Elements",
                    "Compounds",
                    "Mixtures",
                    "Physical Properties of Matter",
                    "Chemical Changes",
                    "Physical Changes",
                    "Separation of Mixtures",
                ],

                "3.0 Living Things": [
                    "Cells",
                    "Cell Structure and Functions",
                    "Specialised Cells",
                    "Micro-organisms",
                    "Classification of Living Things",
                    "Nutrition in Plants",
                    "Reproduction in Plants",
                ],

                "4.0 Human Health": [
                    "Nutrition",
                    "Digestive System",
                    "Respiratory System",
                    "Circulatory System",
                    "Excretion",
                    "Reproduction and Adolescence",
                    "Personal Hygiene",
                    "Disease Prevention",
                ],

                "5.0 Force and Energy": [
                    "Force",
                    "Pressure",
                    "Work",
                    "Energy",
                    "Forms of Energy",
                    "Heat",
                    "Light",
                    "Sound",
                ],

                "6.0 Electricity and Magnetism": [
                    "Electric Current",
                    "Electric Circuits",
                    "Conductors and Insulators",
                    "Magnetism",
                    "Electromagnets",
                    "Uses of Electricity",
                    "Electrical Safety",
                ],

                "7.0 Earth and Space": [
                    "The Earth",
                    "Weather and Climate",
                    "Water Cycle",
                    "Soil",
                    "The Solar System",
                    "Environmental Conservation",
                    "Climate Change",
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
                    "Agricultural Entrepreneurship",
                ],

                "2.0 Soil and Water Conservation": [
                    "Soil Formation",
                    "Soil Properties",
                    "Soil Fertility",
                    "Soil Conservation",
                    "Water Conservation",
                    "Soil Improvement",
                ],

                "3.0 Crop Production": [
                    "Seed Selection",
                    "Land Preparation",
                    "Planting",
                    "Crop Management",
                    "Weed Management",
                    "Pest Management",
                    "Disease Management",
                    "Harvesting",
                    "Storage",
                ],

                "4.0 Livestock Production": [
                    "Types of Livestock",
                    "Livestock Breeds",
                    "Livestock Feeds",
                    "Livestock Housing",
                    "Livestock Health",
                    "Livestock Diseases",
                    "Livestock Products",
                ],

                "5.0 Food and Nutrition": [
                    "Food Groups",
                    "Nutrients",
                    "Balanced Diet",
                    "Food Preparation",
                    "Food Preservation",
                    "Food Hygiene",
                    "Food Safety",
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
                    "Environmental Conservation",
                ],

                "2.0 People, Population and Social Organisation": [
                    "Population",
                    "Population Distribution",
                    "Population Density",
                    "Migration",
                    "Culture",
                    "Social Organisation",
                    "Family and Community",
                    "Urbanisation",
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
                    "Industrialisation",
                ],

                "4.0 Political Systems and Governance": [
                    "Traditional Forms of Government",
                    "Colonial Administration",
                    "Struggle for Independence",
                    "Self-Government",
                    "Government of Kenya",
                    "Leadership and Governance",
                    "Devolution",
                ],

                "5.0 Citizenship": [
                    "Meaning of Citizenship",
                    "Rights and Responsibilities",
                    "National Values",
                    "Patriotism",
                    "National Unity",
                    "Good Citizenship",
                    "Responsible Citizenship",
                ],
            },

            # =====================================================
            # CREATIVE ARTS & SPORTS
            # =====================================================

            "Creative Arts & Sports": {

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
                    "Ball Games",
                    "Net Games",
                    "Gymnastics",
                    "Dance and Movement",
                    "Physical Fitness",
                    "Sportsmanship",
                    "Safety in Sports",
                ],
            },

            # =====================================================
            # PRE-TECHNICAL STUDIES
            # =====================================================

            "Pre-Technical Studies": {

                "1.0 Foundations of Pre-Technical Studies": [
                    "Introduction to Pre-Technical Studies",
                    "Workshop Safety",
                    "Workshop Rules",
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
                    "Material Processing",
                    "Production Processes",
                ],

                "4.0 Computer Studies": [
                    "Computer Systems",
                    "Computer Hardware",
                    "Computer Software",
                    "Input and Output Devices",
                    "File Management",
                    "Digital Communication",
                    "Digital Safety",
                ],

                "5.0 Entrepreneurship": [
                    "Entrepreneurship",
                    "Entrepreneurial Opportunities",
                    "Business Ideas",
                    "Production Unit",
                    "Financial Literacy",
                    "Marketing",
                    "Entrepreneurial Skills",
                ],
            },
        }

        # =========================================================
        # CREATE / UPDATE CURRICULUM
        # =========================================================

        for learning_area_name, strands in curriculum.items():

            learning_area, _ = (
                CurriculumLearningArea.objects.update_or_create(
                    curriculum_grade=grade,
                    name=learning_area_name,
                    pathway=None,
                    defaults={
                        "description": (
                            f"{learning_area_name} "
                            f"for Grade 9."
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
                                f"Grade 9 assessment item: "
                                f"{sub_strand_name}."
                            ),
                        },
                    )

        # =========================================================
        # COUNTS
        # =========================================================

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

        # =========================================================
        # OUTPUT
        # =========================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Grade 9 CBC curriculum seeded successfully "
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