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
    help = "Seed PP1 CBC assessment-book curriculum for Terms 1-3."

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
            code=f"CBC-{academic_year}",
            defaults={
                "name": f"CBC {academic_year}",
                "academic_year": academic_year,
                "description": "CBC PP1 curriculum.",
            },
        )

        version.name = f"CBC {academic_year}"
        version.academic_year = academic_year
        version.description = "CBC PP1 curriculum."
        version.save()

        grade, _ = CurriculumGrade.objects.get_or_create(
            curriculum_version=version,
            grade="PP1",
            defaults={"display_name": "PP1"},
        )

        grade.display_name = "PP1"
        grade.save()

        # ------------------------------------------------------------------
        # PP1 CBC assessment-book curriculum
        #
        # The PP1 source assessment book is organised by:
        #   Theme -> activity/skill -> assessment
        #
        # The existing curriculum models use:
        #   Learning Area -> Strand -> Sub-Strand -> Assessment Item
        #
        # Therefore PP1 THEMES are represented as strands and the visible
        # activities/skills are represented as sub-strands.
        #
        # Each assessment item is created from the visible assessment-book
        # activity/skill row. The E.E/M.E/A.E/B.E scoring is handled by the
        # existing assessment system rather than being duplicated in the seed.
        # ------------------------------------------------------------------

        curriculum = [
            # ==============================================================
            # TERM ONE
            # ==============================================================

            # MATHEMATICS ACTIVITIES
            (
                "Mathematics Activities",
                "T1-1",
                "THEME: MYSELF",
                "1",
                [
                    ("1.1", "Pre-number Activities - Sorting and grouping"),
                    ("1.2", "Pre-number Activities - Matching and pairing"),
                    ("1.3", "Pre-number Activities - Ordering"),
                    ("1.4", "Pre-number Activities - Patterns"),
                ],
            ),
            (
                "Mathematics Activities",
                "T1-2",
                "THEME: MY FAMILY",
                "1",
                [
                    ("2.1", "Numbers - Rote counting"),
                    ("2.2", "Numbers - Number recognition"),
                    ("2.3", "Capacity"),
                ],
            ),

            # ENGLISH LANGUAGE ACTIVITIES
            (
                "English Language Activities",
                "T1-1",
                "GREETINGS AND FAREWELL",
                "1",
                [
                    ("1.1", "Listening and speaking - Greeting and farewell"),
                    ("1.2", "Reading - Readiness"),
                    ("1.3", "Writing - Print awareness"),
                ],
            ),
            (
                "English Language Activities",
                "T1-2",
                "MYSELF",
                "1",
                [
                    ("2.1", "Listening and speaking - Self-awareness"),
                    ("2.2", "Listening for enjoyment"),
                    ("2.3", "Reading - Book handling"),
                    ("2.4", "Reading posture"),
                    ("2.5", "Writing - Posture"),
                    ("2.6", "Prewriting skills"),
                ],
            ),
            (
                "English Language Activities",
                "T1-3",
                "MY FAMILY",
                "1",
                [
                    ("3.1", "Listening and speaking - Active Listening"),
                    ("3.2", "Self-expression"),
                    ("3.3", "Polite Language"),
                    ("3.4", "Reading"),
                    ("3.5", "Phonic awareness"),
                    ("3.6", "Writing - Eye hand coordination"),
                ],
            ),

            # ENVIRONMENTAL ACTIVITIES
            (
                "Environmental Activities",
                "T1-1",
                "THEME: MYSELF",
                "1",
                [
                    ("1.1", "Self-awareness"),
                    ("1.2", "External body parts"),
                    ("1.3", "Hand washing"),
                    ("1.4", "Brushing teeth"),
                    ("1.5", "Family members"),
                ],
            ),

            # CHRISTIAN RELIGIOUS EDUCATION ACTIVITIES
            (
                "Christian Religious Education Activities",
                "T1-1",
                "CREATION",
                "1",
                [
                    ("1.1", "Our God"),
                    ("1.2", "God Our Creator"),
                    ("1.3", "God our Loving father"),
                ],
            ),
            (
                "Christian Religious Education Activities",
                "T1-2",
                "THE HOLY BIBLE",
                "1",
                [
                    ("2.1", "Bible as a Holy Book"),
                ],
            ),

            # CREATIVE ARTS ACTIVITIES
            (
                "Creative Arts Activities",
                "T1-1",
                "MYSELF",
                "1",
                [
                    ("1.1", "Scribbling"),
                    ("1.2", "Action, songs"),
                    ("1.3", "Play activities"),
                    ("1.4", "Printing"),
                    ("1.5", "Hand printing"),
                    ("1.6", "Foot printing"),
                    ("1.7", "Singing game"),
                ],
            ),
            (
                "Creative Arts Activities",
                "T1-2",
                "MY FAMILY",
                "1",
                [
                    ("2.1", "Colouring"),
                    ("2.2", "Recite simple rhymes - food eaten"),
                    ("2.3", "Movement"),
                    ("2.4", "Joining Dots"),
                    ("2.5", "Singing game"),
                ],
            ),

            # ==============================================================
            # TERM TWO
            # ==============================================================

            # MATHEMATICS ACTIVITIES
            (
                "Mathematics Activities",
                "T2-1",
                "THEME: MY FAMILY",
                "2",
                [
                    ("1.1", "Numbers - Counting concrete objects"),
                    ("1.2", "Numbers - Number Sequencing"),
                    ("1.3", "Numbers - Number Writing"),
                ],
            ),
            (
                "Mathematics Activities",
                "T2-2",
                "THEME: MY HOME",
                "2",
                [
                    ("2.1", "Measurement - Sides of objects"),
                    ("2.2", "Measurement - Mass (Heavy and Light)"),
                    ("2.3", "Measurement - Capacity (how much a container hold)"),
                    ("2.4", "Measurement - Time (Daily routines)"),
                ],
            ),

            # ENGLISH LANGUAGE ACTIVITIES
            (
                "English Language Activities",
                "T2-1",
                "MY HOME",
                "2",
                [
                    ("1.1", "Listening and speaking - Passing Information"),
                    ("1.2", "Visual Discrimination"),
                    ("1.3", "Naming"),
                    ("1.4", "Reading - Phonic Awareness"),
                    ("1.5", "Writing - Readiness and letter sounds"),
                ],
            ),
            (
                "English Language Activities",
                "T2-2",
                "MY NEIGHBOURHOOD",
                "2",
                [
                    ("2.1", "Listening and speaking - Environmental awareness"),
                    ("2.2", "Auditory discrimination"),
                    ("2.3", "Audience awareness"),
                    ("2.4", "Speaks clearly and audibly"),
                    ("2.5", "Reading posture"),
                    ("2.6", "Visual Memory"),
                    ("2.7", "Phonic Awareness"),
                    ("2.8", "Writing - Pattern writing"),
                ],
            ),

            # ENVIRONMENTAL ACTIVITIES
            (
                "Environmental Activities",
                "T2-1",
                "THEME: MY FAMILY",
                "2",
                [
                    ("1.1", "Feeding"),
                ],
            ),
            (
                "Environmental Activities",
                "T2-2",
                "THEME: MY HOME",
                "2",
                [
                    ("2.1", "Utensils Used at home"),
                    ("2.2", "Furniture at home"),
                ],
            ),
            (
                "Environmental Activities",
                "T2-3",
                "THEME: NEIGHBOURHOOD",
                "2",
                [
                    ("3.1", "My classmates and friends"),
                    ("3.2", "Parts of a plant"),
                ],
            ),

            # CHRISTIAN RELIGIOUS EDUCATION ACTIVITIES
            (
                "Christian Religious Education Activities",
                "T2-1",
                "THE HOLY BIBLE",
                "2",
                [
                    ("1.1", "Bible story David and Goliath"),
                    ("1.2", "Bible story"),
                    ("1.3", "Bible Verses"),
                ],
            ),
            (
                "Christian Religious Education Activities",
                "T2-2",
                "THE LIFE OF JESUS CHRIST",
                "2",
                [
                    ("2.1", "The birth of Jesus Christ"),
                    ("2.2", "Celebrating the birth of Jesus"),
                ],
            ),
            (
                "Christian Religious Education Activities",
                "T2-3",
                "CHRISTIAN VALUES",
                "2",
                [
                    ("3.1", "Love for God"),
                    ("3.2", "Love for neighbour"),
                ],
            ),

            # CREATIVE ARTS ACTIVITIES
            (
                "Creative Arts Activities",
                "T2-1",
                "MY HOME",
                "2",
                [
                    ("1.1", "Modelling"),
                    ("1.2", "Musical sounds"),
                    ("1.3", "Domestic animal sounds"),
                    ("1.4", "Birds sounds"),
                    ("1.5", "Objects sounds"),
                ],
            ),
            (
                "Creative Arts Activities",
                "T2-2",
                "MY SCHOOL",
                "2",
                [
                    ("2.1", "Crawling and bending"),
                ],
            ),

            # ==============================================================
            # TERM THREE
            # ==============================================================

            # MATHEMATICS ACTIVITIES
            (
                "Mathematics Activities",
                "T3-1",
                "THEME: MY HOME",
                "3",
                [
                    ("1.1", "Money - Kenya Ksh. 1 currency"),
                    ("1.2", "Area (surface area of objects)"),
                ],
            ),
            (
                "Mathematics Activities",
                "T3-2",
                "THEME: MY SCHOOL",
                "3",
                [
                    ("2.1", "Geometry - Lines"),
                    ("2.2", "Geometry - Shapes"),
                ],
            ),

            # ENGLISH LANGUAGE ACTIVITIES
            (
                "English Language Activities",
                "T3-1",
                "MY SCHOOL",
                "3",
                [
                    ("1.1", "Listening and speaking - Auditory memory"),
                    ("1.2", "Articulation of letter sounds"),
                    ("1.3", "Reading - Letter recognition & picture reading"),
                    ("1.4", "Writing - Letter formation and practice"),
                ],
            ),

            # ENVIRONMENTAL ACTIVITIES
            (
                "Environmental Activities",
                "T3-1",
                "THEME: MY SCHOOL",
                "3",
                [
                    ("1.1", "My class"),
                    ("1.2", "Care for my class"),
                    ("1.3", "Cleanliness and toileting"),
                ],
            ),

            # CHRISTIAN RELIGIOUS EDUCATION ACTIVITIES
            (
                "Christian Religious Education Activities",
                "T3-1",
                "CHRISTIAN VALUES",
                "3",
                [
                    ("1.1", "Sharing with others"),
                ],
            ),
            (
                "Christian Religious Education Activities",
                "T3-2",
                "THE CHURCH",
                "3",
                [
                    ("2.1", "Identifying the church"),
                    ("2.2", "The church as a house of God"),
                    ("2.3", "Church activities"),
                ],
            ),

            # CREATIVE ARTS ACTIVITIES
            (
                "Creative Arts Activities",
                "T3-1",
                "MY SCHOOL",
                "3",
                [
                    ("1.1", "Singing Game"),
                    ("1.2", "Waterplay"),
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
                    pathway=None,
                    name=learning_area_name,
                    defaults={
                        "code": self.make_code(learning_area_name),
                        "description": "PP1 CBC assessment learning area.",
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
                f"PP1 CBC curriculum seeded successfully for {academic_year}."
            )
        )
        self.stdout.write("")
        self.stdout.write(f"Curriculum Version : {version.name}")
        self.stdout.write(f"Grade              : {grade.display_name}")
        self.stdout.write(
            "Learning Areas     : "
            f"{CurriculumLearningArea.objects.filter(curriculum_grade=grade, pathway=None).count()}"
        )
        self.stdout.write(
            "Strands            : "
            f"{CurriculumStrand.objects.filter(learning_area__curriculum_grade=grade).count()}"
        )
        self.stdout.write(
            "Sub-Strands        : "
            f"{CurriculumSubStrand.objects.filter(strand__learning_area__curriculum_grade=grade).count()}"
        )
        self.stdout.write(
            "Assessment Items   : "
            f"{CurriculumAssessmentItem.objects.filter(sub_strand__strand__learning_area__curriculum_grade=grade).count()}"
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
            if "-" in str(code):
                return int(str(code).split("-")[-1])
            return int(float(code))
        except (TypeError, ValueError):
            return 0
