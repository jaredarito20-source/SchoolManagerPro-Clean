from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import (
    CurriculumVersion,
    CurriculumGrade,
    CurriculumPathway,
    CurriculumLearningArea,
    CurriculumStrand,
    CurriculumSubStrand,
    CurriculumAssessmentItem,
)
from students.management.commands.cbc_grade10_helpers import (
    seed_grade10_performance_levels,
)


class Command(BaseCommand):
    help = "Seed Grade 10 CBC Arts & Sports Pathway curriculum for Terms 1-3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2026",
            help="Academic year for the curriculum version.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        academic_year = str(options["academic_year"])

        version, _ = CurriculumVersion.objects.get_or_create(
            code=f"CBC{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC Grade 10 curriculum.",
            },
        )

        version.name = f"CBC {academic_year}"
        version.academic_year = academic_year
        version.description = "CBC Grade 10 curriculum."
        version.save()

        grade, _ = CurriculumGrade.objects.get_or_create(
            curriculum_version=version,
            grade="GRADE10",
            defaults={
                "display_name": "Grade 10",
            },
        )

        grade.display_name = "Grade 10"
        grade.save()

        seed_grade10_performance_levels(grade)

        pathway, _ = CurriculumPathway.objects.get_or_create(
            curriculum_grade=grade,
            name="ARTS_SPORTS",
            defaults={
                "description": "Arts and Sports Pathway",
            },
        )

        pathway.description = "Arts and Sports Pathway"
        pathway.save()

        # ------------------------------------------------------------------
        # Curriculum data
        #
        # Each tuple is:
        # (
        #     learning_area,
        #     strand_code,
        #     strand_name,
        #     term,
        #     [
        #         (sub_strand_code, sub_strand_name),
        #         ...
        #     ]
        # )
        #
        # The visible assessment-book rows are used as the assessment rows.
        # No blank rows or unrelated summative-template rows are seeded.
        # ------------------------------------------------------------------

        curriculum = [

            # ==============================================================
            # ENGLISH LANGUAGE
            # ==============================================================

            (
                "English Language",
                "1.0",
                "ETIQUETTE: SOCIAL",
                "1",
                [
                    ("1.1", "Listening and Speaking"),
                    ("1.2", "Reading"),
                    ("1.3", "Grammar in use"),
                    ("1.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "2.0",
                "ENVIRONMENT: CLIMATE CHANGE",
                "1",
                [
                    ("2.1", "Listening and Speaking"),
                    ("2.2", "Reading"),
                    ("2.3", "Grammar in use"),
                    ("2.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "3.0",
                "ARTIFICIAL INTELLIGENCE AND SOCIETY: HEALTHCARE",
                "1",
                [
                    ("3.1", "Listening and Speaking"),
                    ("3.2", "Reading"),
                    ("3.3", "Grammar in use"),
                    ("3.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "4.0",
                "TRAVEL: ADVENTURE",
                "1",
                [
                    ("4.1", "Listening and Speaking"),
                    ("4.2", "Reading"),
                    ("4.3", "Grammar in use"),
                    ("4.4", "Writing"),
                ],
            ),

            (
                "English Language",
                "5.0",
                "CARRIER: PUBLIC SECTOR",
                "2",
                [
                    ("5.1", "Listening and Speaking"),
                    ("5.2", "Reading"),
                    ("5.3", "Grammar in use"),
                    ("5.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "6.0",
                "SPORTS AND GAMES: POPULAR SPORTS",
                "2",
                [
                    ("6.1", "Listening and Speaking"),
                    ("6.2", "Reading"),
                    ("6.3", "Grammar in use"),
                    ("6.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "7.0",
                "HEALTH AND SAFETY: PERSONAL SAFETY",
                "2",
                [
                    ("7.1", "Listening and Speaking"),
                    ("7.2", "Reading"),
                    ("7.3", "Grammar in use"),
                    ("7.4", "Writing"),
                ],
            ),

            (
                "English Language",
                "8.0",
                "HEALTH AND SAFETY: PERSONAL SAFETY",
                "3",
                [
                    ("8.1", "Listening and Speaking"),
                    ("8.2", "Reading"),
                    ("8.3", "Grammar in use"),
                    ("8.4", "Writing"),
                ],
            ),
            (
                "English Language",
                "9.0",
                "INCOME : TYPES AND SOURCES",
                "3",
                [
                    ("9.1", "Listening and Speaking"),
                    ("9.2", "Reading"),
                    ("9.3", "Grammar in use"),
                    ("9.4", "Writing"),
                ],
            ),

            # ==============================================================
            # KISWAHILI LUGHA
            # ==============================================================

            (
                "Kiswahili Lugha",
                "1.0",
                "MIKONDO YA FURSA ZA AJIRA",
                "1",
                [
                    ("1.1", "Kusikiliza na Kuzungumza"),
                    ("1.2", "Kusoma"),
                    ("1.3", "Kuandika"),
                    ("1.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "2.0",
                "KUKABILIANA NA SHINIKIZORIKA",
                "1",
                [
                    ("2.1", "Kusikiliza na Kuzungumza"),
                    ("2.2", "Kusoma"),
                    ("2.3", "Kuandika"),
                    ("2.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "3.0",
                "UTAMBUZI WA UWEZO NA VIPAJI MBALIMBALI",
                "1",
                [
                    ("3.1", "Kusikiliza na Kuzungumza"),
                    ("3.2", "Kusoma"),
                    ("3.3", "Kuandika"),
                    ("3.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "4.0",
                "USALAMA BARABARANI",
                "2",
                [
                    ("4.1", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "5.0",
                "KUKABILIANA NA MABADILIKO YA MAISHA YA KIBINAFSI",
                "2",
                [
                    ("5.1", "Kusikiliza na Kuzungumza"),
                    ("5.2", "Kusoma"),
                    ("5.3", "Kuandika"),
                    ("5.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "6.0",
                "KUDHIBITI TAKA KATIKA MAZINGIRA",
                "2",
                [
                    ("6.1", "Kusikiliza na Kuzungumza"),
                    ("6.2", "Kusoma"),
                    ("6.3", "Kuandika"),
                    ("6.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "7.0",
                "UADILIFU KATIKA UONGOZI SHULENI",
                "2",
                [
                    ("7.1", "Kusikiliza na Kuzungumza"),
                    ("7.2", "Kusoma"),
                    ("7.3", "Kuandika"),
                    ("7.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "8.0",
                "JINSIA YA TAALUMA",
                "2",
                [
                    ("8.1", "Kusikiliza na Kuzungumza"),
                    ("8.2", "Kusoma"),
                    ("8.3", "Kuandika"),
                    ("8.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "9.0",
                "KUHESHIMU TAMADUNI ZA WENGINE",
                "3",
                [
                    ("9.1", "Kusikiliza na Kuzungumza"),
                    ("9.2", "Kusoma"),
                    ("9.3", "Kuandika"),
                    ("9.4", "Matumizi ya Lugha"),
                ],
            ),
            (
                "Kiswahili Lugha",
                "10.0",
                "HUDUMA YA KWANZA",
                "3",
                [
                    ("10.1", "Kusikiliza na Kuzungumza"),
                    ("10.2", "Kusoma"),
                    ("10.3", "Kuandika"),
                    ("10.4", "Matumizi ya Lugha"),
                ],
            ),

            # ==============================================================
            # CORE MATHEMATICS
            # ==============================================================

            (
                "Core Mathematics",
                "1.0",
                "NUMBERS AND ALGEBRA",
                "1",
                [
                    ("1.1", "Real Numbers"),
                    ("1.2", "Indices and Logarithms"),
                    ("1.3", "Quadratic Expressions and Equations I"),
                ],
            ),
            (
                "Core Mathematics",
                "2.0",
                "MEASUREMENTS AND GEOMETRY",
                "1",
                [
                    ("2.1", "Similarity and Enlargement"),
                    ("2.2", "Reflection and Congruence"),
                ],
            ),
            (
                "Core Mathematics",
                "2.0",
                "MEASUREMENTS AND GEOMETRY",
                "2",
                [
                    ("2.2", "Reflection and Congruence"),
                    ("2.3", "Rotation"),
                    ("2.4", "Trigonometry I"),
                ],
            ),
            (
                "Core Mathematics",
                "3.0",
                "STATISTICS AND PROBABILITY",
                "3",
                [
                    ("3.1", "Statistics I"),
                    ("3.2", "Probability I"),
                ],
            ),

            # ==============================================================
            # ESSENTIAL MATHEMATICS
            # ==============================================================

            (
                "Essential Mathematics",
                "1.0",
                "NUMBERS AND ALGEBRA",
                "1",
                [
                    ("1.1", "Real Numbers"),
                    ("1.2", "Indices"),
                    ("1.3", "Quadratic Equations"),
                ],
            ),
            (
                "Essential Mathematics",
                "2.0",
                "MEASUREMENTS AND GEOMETRY",
                "1",
                [
                    ("2.1", "Similarity and Enlargement"),
                    ("2.2", "Reflection"),
                    ("2.3", "Trigonometry"),
                ],
            ),
            (
                "Essential Mathematics",
                "2.0",
                "MEASUREMENTS AND GEOMETRY",
                "2",
                [
                    ("2.4", "Area of Polygons"),
                    ("2.5", "Area of Part of a Circle"),
                    ("2.6", "Surface Area of Solids"),
                    ("2.7", "Volume and Capacity"),
                    ("2.8", "Commercial Arithmetic I"),
                ],
            ),
            (
                "Essential Mathematics",
                "3.0",
                "STATISTICS AND PROBABILITY",
                "3",
                [
                    ("3.1", "Statistics I"),
                    ("3.2", "Probability I"),
                ],
            ),

            # ==============================================================
            # COMMUNITY SERVICE LEARNING
            # ==============================================================

            (
                "Community Service Learning",
                "1.0",
                "CITIZENSHIP",
                "1",
                [
                    ("1.1", "Concept of CSL"),
                    ("1.2", "Community Needs"),
                    ("1.3", "Leadership Development"),
                    ("1.4", "Intercultural Competence"),
                ],
            ),
            (
                "Community Service Learning",
                "2.0",
                "LIFE SKILLS IN EDUCATION",
                "1",
                [
                    ("2.1", "Self-Awareness in the Community"),
                    ("2.2", "Conflict Resolution"),
                ],
            ),
            (
                "Community Service Learning",
                "2.0",
                "LIFE SKILLS IN EDUCATION",
                "2",
                [
                    ("2.3", "Responsible Decision Making"),
                ],
            ),
            (
                "Community Service Learning",
                "3.0",
                "ACTION RESEARCH",
                "2",
                [
                    ("3.1", "Introduction to Action Research"),
                    ("3.2", "Problem Identification"),
                    ("3.3", "Designing and Implementing an Intervention"),
                ],
            ),
            (
                "Community Service Learning",
                "4.0",
                "LIFE SKILLS IN EDUCATION",
                "3",
                [
                    ("4.1", "Introduction to Social Entrepreneurship"),
                    ("4.2", "Opportunity Identification"),
                    ("4.3", "Social Enterprise Planning"),
                    ("4.4", "Resource Mobilisation"),
                ],
            ),

            # ==============================================================
            # SPORTS AND RECREATION
            # ==============================================================

            (
                "Sports and Recreation",
                "1.0",
                "HEALTH AND FITNESS",
                "1",
                [
                    ("1.1", "Sports and Society"),
                    ("1.2", "Body Composition"),
                    ("1.3", "Posture for Efficient Performance"),
                    ("1.4", "Aerobics"),
                    ("1.5", "Recreation and Wellness"),
                    ("1.6", "Injuries in Sports"),
                ],
            ),
            (
                "Sports and Recreation",
                "2.0",
                "COACHING",
                "2",
                [
                    ("2.1", "Introduction to Coaching"),
                    ("2.2", "Facilities and Equipment in Sports and Recreation"),
                    ("2.3", "Improvisation of Equipment and Modification of Facilities"),
                    ("2.4", "Tactical Skills in Athletics"),
                    ("2.5", "Formations in Game"),
                    ("2.6", "Talent Detection and Identification"),
                ],
            ),
            (
                "Sports and Recreation",
                "3.0",
                "OFFICIATING",
                "3",
                [
                    ("3.1", "PRINCIPLES OF OFFICIATING"),
                    ("3.2", "TEAM AND MEET/GAME OFFICIALS"),
                ],
            ),

            # ==============================================================
            # THEATRE AND FILM
            # ==============================================================

            (
                "Theatre and Film",
                "1.0",
                "CREATING",
                "1",
                [
                    ("1.1", "INTRODUCTION TO TRADITIONAL KENYAN THEATRE"),
                    ("1.2", "PLAY WRITING"),
                    ("1.3", "POETRY WRITING"),
                ],
            ),
            (
                "Theatre and Film",
                "2.0",
                "PRODUCTION",
                "2",
                [
                    ("2.1", "Acting"),
                ],
            ),
            (
                "Theatre and Film",
                "3.0",
                "THEATRE, FILM AND SOCIETY",
                "3",
                [
                    ("3.1", "THEATRE ADJUDICATION"),
                    ("3.2", "THEATRE COMMUNITY"),
                ],
            ),

            # ==============================================================
            # MUSIC AND DANCE
            # ==============================================================

            (
                "Music and Dance",
                "1.0",
                "FOUNDATIONS OF MUSIC AND DANCE",
                "1",
                [
                    ("1.1", "RHYTHM"),
                    ("1.2", "MELODY IN MAJOR KEYS"),
                    ("1.3", "TRANSPOSITION"),
                    ("1.4", "SETTING TEXT TO MUSIC"),
                    ("1.5", "TWO-PART HARMONY"),
                    ("1.6", "MUSIC NOTATION SOFTWARE"),
                    ("1.7", "DANCE PRODUCTION"),
                ],
            ),
            (
                "Music and Dance",
                "2.0",
                "PERFORMING",
                "2",
                [
                    ("2.1", "Kenyan Folk Songs"),
                    ("2.2", "Western Style Solo Songs"),
                    ("2.3", "Kenyan Indigenous Musical Instruments"),
                    ("2.4", "Western Musical Instruments (Solo Performer)"),
                    ("2.5", "Contemporary Dances - Kenyan"),
                ],
            ),
            (
                "Music and Dance",
                "3.0",
                "CRITICAL APPRECIATION",
                "3",
                [
                    ("3.1", "KENYAN FOLK SONGS"),
                    ("3.2", "CLASSICAL MUSIC (MEDIEVAL AND RENAISSANCE)"),
                    ("3.3", "MUSIC AND DANCE IN SOCIO-CULTURAL CONTEXT"),
                ],
            ),

            # ==============================================================
            # ART AND CRAFT / FINE ARTS
            # ==============================================================

            (
                "Art and Craft",
                "1.0",
                "PICTURE MAKING TECHNIQUES (2D ART)",
                "1",
                [
                    ("1.1", "DRAWING"),
                    ("1.2", "PAINTING"),
                    ("1.3", "COLLAGE"),
                ],
            ),
            (
                "Art and Craft",
                "2.0",
                "MULTIMEDIA ARTS (2D ART)",
                "2",
                [
                    ("2.1", "Graphic Design"),
                    ("2.2", "Fabric Decoration: Tie and Dye"),
                    ("2.3", "Fabric Decoration: Batik"),
                ],
            ),
            (
                "Art and Craft",
                "3.0",
                "INDIGENOUS CRAFTS (3D ART)",
                "2",
                [
                    ("3.1", "Pottery"),
                ],
            ),
            (
                "Art and Craft",
                "1.0",
                "INDEGENOUS SCRAFTS (3D ARTS)",
                "3",
                [
                    ("3.2", "SCULPTURE"),
                    ("3.3", "MACRAMÉ"),
                    ("3.4", "JEWELLERY AND ORNAMENTATION"),
                    ("3.5", "ART APPRECIATION"),
                ],
            ),
        ]

        learning_area_cache = {}

        for (
            learning_area_name,
            strand_code,
            strand_name,
            term,
            sub_strands,
        ) in curriculum:

            cache_key = learning_area_name

            if cache_key not in learning_area_cache:
                learning_area, _ = CurriculumLearningArea.objects.get_or_create(
                    curriculum_grade=grade,
                    pathway=pathway,
                    name=learning_area_name,
                    defaults={
                        "code": self.make_code(learning_area_name),
                        "description": "",
                        "assessment_enabled": True,
                    },
                )

                learning_area.assessment_enabled = True
                learning_area.save()

                learning_area_cache[cache_key] = learning_area

            else:
                learning_area = learning_area_cache[cache_key]

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

            for index, (sub_code, sub_name) in enumerate(sub_strands, start=1):

                sub_strand, _ = CurriculumSubStrand.objects.get_or_create(
                    strand=strand,
                    code=sub_code,
                    defaults={
                        "name": sub_name,
                        "order": index,
                        "description": "",
                    },
                )

                sub_strand.name = sub_name
                sub_strand.order = index
                sub_strand.save()

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

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Grade 10 Arts & Sports curriculum seeded successfully for {academic_year}."
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
            f"Pathway            : Arts & Sports"
        )
        self.stdout.write(
            f"Learning Areas     : {CurriculumLearningArea.objects.filter(curriculum_grade=grade, pathway=pathway).count()}"
        )
        self.stdout.write(
            f"Strands            : {CurriculumStrand.objects.filter(learning_area__curriculum_grade=grade, learning_area__pathway=pathway).count()}"
        )
        self.stdout.write(
            f"Sub-Strands        : {CurriculumSubStrand.objects.filter(strand__learning_area__curriculum_grade=grade, strand__learning_area__pathway=pathway).count()}"
        )
        self.stdout.write(
            f"Assessment Items   : {CurriculumAssessmentItem.objects.filter(sub_strand__strand__learning_area__curriculum_grade=grade, sub_strand__strand__learning_area__pathway=pathway).count()}"
        )

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
            return int(float(code))
        except (TypeError, ValueError):
            return 0