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


class Command(BaseCommand):
    help = "Seed Grade 10 CBC STEM pathway from the Grade 10 STEM Assessment Record Book."

    VERSION_CODE = "CBC2026"
    VERSION_NAME = "CBC 2026"
    ACADEMIC_YEAR = 2026

    def field_exists(self, model, field_name):
        return any(
            field.name == field_name
            for field in model._meta.get_fields()
        )

    def set_if_exists(self, obj, field_name, value):
        if self.field_exists(obj.__class__, field_name):
            setattr(obj, field_name, value)

    def get_or_create_version(self):
        """
        CurriculumVersion field names are handled defensively because
        the existing project schema may differ from the original seed.
        """

        fields = {
            field.name
            for field in CurriculumVersion._meta.get_fields()
        }

        lookup = {}

        if "code" in fields:
            lookup["code"] = self.VERSION_CODE
        elif "name" in fields:
            lookup["name"] = self.VERSION_NAME
        elif "academic_year" in fields:
            lookup["academic_year"] = self.ACADEMIC_YEAR

        if not lookup:
            raise RuntimeError(
                "Cannot determine how to identify CurriculumVersion. "
                "Please inspect CurriculumVersion in students/models.py."
            )

        defaults = {}

        if "name" in fields and "name" not in lookup:
            defaults["name"] = self.VERSION_NAME

        if "academic_year" in fields and "academic_year" not in lookup:
            defaults["academic_year"] = self.ACADEMIC_YEAR

        if "is_active" in fields:
            defaults["is_active"] = True

        version, created = CurriculumVersion.objects.get_or_create(
            **lookup,
            defaults=defaults,
        )

        changed = False

        if "code" in fields:
            if getattr(version, "code", None) != self.VERSION_CODE:
                version.code = self.VERSION_CODE
                changed = True

        if "name" in fields:
            if getattr(version, "name", None) != self.VERSION_NAME:
                version.name = self.VERSION_NAME
                changed = True

        if "academic_year" in fields:
            if getattr(version, "academic_year", None) != self.ACADEMIC_YEAR:
                version.academic_year = self.ACADEMIC_YEAR
                changed = True

        if "is_active" in fields:
            if not version.is_active:
                version.is_active = True
                changed = True

        if changed:
            version.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created curriculum version: {self.VERSION_NAME}"
                )
            )
        else:
            self.stdout.write(
                f"Using existing curriculum version: {self.VERSION_NAME}"
            )

        return version

    def create_grade(self, version):
        """
        IMPORTANT:
        CurriculumGrade was confirmed to contain:

            curriculum_version
            display_name
            grade

        There is NO code field.
        """

        grade = CurriculumGrade.objects.filter(
            curriculum_version=version,
            grade="GRADE10",
        ).first()

        if grade is None:
            grade = CurriculumGrade.objects.create(
                curriculum_version=version,
                grade="GRADE10",
                display_name="Grade 10",
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Created Grade 10 curriculum record."
                )
            )
        else:
            if grade.display_name != "Grade 10":
                grade.display_name = "Grade 10"
                grade.save(update_fields=["display_name"])

            self.stdout.write(
                "Using existing Grade 10 curriculum record."
            )

        return grade

    def create_pathway(self, grade):
        fields = {
            field.name
            for field in CurriculumPathway._meta.get_fields()
        }

        lookup = {
            "curriculum_grade": grade,
            "name": "STEM",
        }

        defaults = {}

        if "description" in fields:
            defaults["description"] = (
                "Grade 10 STEM pathway"
            )

        pathway, created = CurriculumPathway.objects.get_or_create(
            **lookup,
            defaults=defaults,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Created Grade 10 STEM pathway."
                )
            )
        else:
            self.stdout.write(
                "Using existing Grade 10 STEM pathway."
            )

        return pathway

    def create_learning_area(
        self,
        grade,
        pathway,
        name,
    ):
        fields = {
            field.name
            for field in CurriculumLearningArea._meta.get_fields()
        }

        lookup = {
            "curriculum_grade": grade,
            "pathway": pathway,
            "name": name,
        }

        defaults = {}

        if "assessment_enabled" in fields:
            defaults["assessment_enabled"] = True

        learning_area, created = (
            CurriculumLearningArea.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
        )

        if created:
            self.stdout.write(
                f"  Created learning area: {name}"
            )

        return learning_area

    def create_strand(
        self,
        learning_area,
        name,
        order,
        code=None,
    ):
        fields = {
            field.name
            for field in CurriculumStrand._meta.get_fields()
        }

        lookup = {
            "learning_area": learning_area,
            "name": name,
        }

        strand, created = (
            CurriculumStrand.objects.get_or_create(
                **lookup
            )
        )

        changed = False

        if "order" in fields:
            if strand.order != order:
                strand.order = order
                changed = True

        if "code" in fields and code:
            if getattr(strand, "code", None) != code:
                strand.code = code
                changed = True

        if changed:
            strand.save()

        return strand

    def create_substrand(
        self,
        strand,
        name,
        order,
        code=None,
    ):
        fields = {
            field.name
            for field in CurriculumSubStrand._meta.get_fields()
        }

        lookup = {
            "strand": strand,
            "name": name,
        }

        substrand, created = (
            CurriculumSubStrand.objects.get_or_create(
                **lookup
            )
        )

        changed = False

        if "order" in fields:
            if substrand.order != order:
                substrand.order = order
                changed = True

        if "code" in fields and code:
            if getattr(substrand, "code", None) != code:
                substrand.code = code
                changed = True

        if changed:
            substrand.save()

        return substrand

    def create_assessment_item(
        self,
        substrand,
        term,
        name,
        order,
    ):
        fields = {
            field.name
            for field in CurriculumAssessmentItem._meta.get_fields()
        }

        lookup = {
            "sub_strand": substrand,
            "term": term,
            "name": name,
        }

        defaults = {}

        if "order" in fields:
            defaults["order"] = order

        item, created = (
            CurriculumAssessmentItem.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
        )

        if not created and "order" in fields:
            if item.order != order:
                item.order = order
                item.save(update_fields=["order"])

        return item

    def seed_topic_structure(
        self,
        learning_area,
        term,
        strand_name,
        substrands,
        strand_order,
    ):
        strand = self.create_strand(
            learning_area=learning_area,
            name=strand_name,
            order=strand_order,
        )

        for index, substrand_name in enumerate(
            substrands,
            start=1,
        ):
            substrand = self.create_substrand(
                strand=strand,
                name=substrand_name,
                order=index,
            )

            self.create_assessment_item(
                substrand=substrand,
                term=term,
                name=substrand_name,
                order=index,
            )

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "GRADE 10 STEM CURRICULUM SEED"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write("")

        # -------------------------------------------------
        # VERSION
        # -------------------------------------------------

        version = self.get_or_create_version()

        # -------------------------------------------------
        # GRADE 10
        # -------------------------------------------------

        grade = self.create_grade(version)

        # -------------------------------------------------
        # STEM PATHWAY
        # -------------------------------------------------

        pathway = self.create_pathway(grade)

        # -------------------------------------------------
        # CURRICULUM
        # -------------------------------------------------

        curriculum = {
            "Core Mathematics": {
                1: {
                    "Numbers and Algebra": [
                        "Real Numbers",
                        "Indices and Logarithms",
                        "Quadratic Expressions and Equations I",
                    ],
                    "Measurements and Geometry": [
                        "Similarity and Enlargement",
                        "Reflection and Congruence",
                    ],
                },
                2: {
                    "Measurements and Geometry": [
                        "Reflection and Congruence",
                        "Rotation",
                        "Trigonometry I",
                    ],
                },
                3: {
                    "Statistics and Probability": [
                        "Statistics I",
                        "Probability I",
                    ],
                },
            },

            "Essential Mathematics": {
                1: {
                    "Numbers and Algebra": [
                        "Real Numbers",
                        "Indices",
                        "Quadratic Equations",
                    ],
                    "Measurements and Geometry": [
                        "Similarity and Enlargement",
                        "Reflection",
                        "Trigonometry",
                    ],
                },
                2: {
                    "Measurements and Geometry": [
                        "Area of Polygons",
                        "Area of Part of a Circle",
                        "Surface Area of Solids",
                        "Volume and Capacity",
                        "Commercial Arithmetic I",
                    ],
                },
                3: {
                    "Statistics and Probability": [
                        "Statistics I",
                        "Probability I",
                    ],
                },
            },

            "Biology": {
                1: {
                    "Cell Biology and Biodiversity": [
                        "Introduction to Biology",
                        "Specimen Collection and Preservation",
                        "Cell Structure and Specializations",
                        "Chemicals of Life",
                    ],
                },
                2: {
                    "Anatomy and Physiology of Plants": [
                        "Nutrition",
                        "Transport",
                        "Gaseous Exchange and Respiration",
                    ],
                },
                3: {
                    "Anatomy and Physiology of Animals": [
                        "Nutrition",
                        "Transport",
                        "Gaseous Exchange and Respiration",
                    ],
                },
            },

            "Chemistry": {
                1: {
                    "Inorganic Chemistry": [
                        "Introduction to Chemistry",
                        "The Atom",
                        "The Periodic Table",
                        "Chemical Bonding",
                        "Periodicity",
                    ],
                },
                2: {
                    "Physical Chemistry": [
                        "Acids and Bases",
                        "Introduction to Salts",
                    ],
                },
                3: {
                    "Organic Chemistry": [
                        "Introduction to Organic Chemistry",
                        "Polymers",
                        "Fats, Oils and Soaps",
                    ],
                },
            },

            "Physics": {
                1: {
                    "Mechanics and Thermal Physics": [
                        "Introduction to Physics",
                        "Pressure",
                        "Mechanical Properties of Materials",
                        "Temperature and Thermal Expansion",
                        "Moments and Equilibrium",
                        "Energy, Work, Power and Machines",
                    ],
                },
                2: {
                    "Waves and Optics": [
                        "Properties of Waves",
                        "Radioactivity and Stability of Isotopes",
                    ],
                    "Electricity and Magnetism": [
                        "Electrostatics",
                        "Current Electricity",
                        "Introduction to Electronics",
                    ],
                },
                3: {
                    "Environmental and Space Physics": [
                        "Greenhouse Effect and Climate Change",
                        "Introduction to Space Physics",
                    ],
                },
            },

            "General Science": {
                1: {
                    "Life Science": [
                        "Introduction to General Science",
                        "The Cell",
                        "Nutrition in Animals",
                        "Transport in Plants",
                        "Respiration",
                        "Plant Growth and Development",
                        "Microorganisms",
                    ],
                },
                2: {
                    "Matter and Chemical Reactions": [
                        "The Periodic Table",
                        "Chemical Families",
                        "Chemical Bonding",
                        "Acids, Bases and Salts",
                        "Rates of Reactions",
                    ],
                },
                3: {
                    "Natural Physical Science": [
                        "Turning Effect of Force",
                        "Linear Motion",
                        "Waves",
                        "Magnetism and Electromagnetic Induction",
                    ],
                },
            },

            "Electricity": {
                1: {
                    "Fundamentals of Electricity": [
                        "Introduction to Electricity",
                        "D.C Electric Circuits",
                        "Cells and Batteries",
                        "Capacitors and Capacitance",
                        "Pictorial Drawings",
                    ],
                },
                2: {
                    "Electrical Machines": [
                        "Magnetism",
                        "Electromagnetism",
                        "Inductors and Inductance",
                    ],
                    "Electrical Installation": [
                        "Generation, Transmission and Distribution of Electricity",
                        "Equipment at the Consumer's Intake Point",
                        "Final Circuits",
                        "Computer Setup",
                    ],
                },
                3: {
                    "Electronics": [
                        "Semiconductor Theory",
                        "Semiconductor Diodes",
                        "Transistors",
                    ],
                },
            },

            "Computer Studies": {
                1: {
                    "Foundation of Computer Studies": [
                        "Evolution of Computers",
                        "Computer Architecture",
                        "Input/output (I/O) Devices",
                        "Computer Storage",
                        "Central Processing Unit (CPU)",
                        "Operating System (OS)",
                    ],
                },
                2: {
                    "Computer Networking": [
                        "Data Communication",
                        "Data Transmission Media",
                        "Computer Network Elements",
                        "Network Topologies",
                        "Internet and Email",
                    ],
                },
                3: {
                    "Computer Applications": [
                        "Word Processing",
                        "Spreadsheets",
                    ],
                },
            },

            "Home Science": {
                1: {
                    "Food and Nutrition": [
                        "Overview of Home Science",
                        "Kitchen Layouts and Equipment",
                        "Food Hygiene and Safety",
                        "Nutritive Value of Foods",
                    ],
                },
                2: {
                    "Food and Nutrition": [
                        "Methods of Cooking",
                    ],
                    "Home Management": [
                        "Hygiene During Puberty",
                        "Safety in the Home",
                        "Housing the Family",
                        "Cleaning the House",
                        "Consumer Education",
                    ],
                    "Clothing and Textiles": [
                        "Sewing Tools, Equipment and Materials",
                    ],
                },
                3: {
                    "Clothing and Textiles": [
                        "Textile Fibres",
                        "Clothing Construction Processes: Stitches",
                        "Seams",
                        "Management of Fullness",
                    ],
                },
            },

            "ICT": {
                1: {
                    "ICT and Society": [
                        "Introduction to ICT",
                        "Application Areas of ICT",
                        "Operating Systems",
                        "Digital Citizenship",
                    ],
                },
                2: {
                    "Productivity Tools": [
                        "Word Processing",
                        "Presentation",
                        "Desktop Publishing",
                    ],
                },
                3: {
                    "Internet and Web Technologies": [
                        "The Internet",
                        "Digital Communication",
                    ],
                },
            },

            "Metalwork": {
                1: {
                    "Fundamentals of Metalwork": [
                        "Introduction to Metalwork",
                        "Safety at Workshop",
                    ],
                    "Tools and Materials in Metalwork": [
                        "Hand Tools and Bench Tools",
                        "Measuring and Marking Out Tools",
                        "Ferrous and Non-Ferrous Metals",
                    ],
                },
                2: {
                    "Tools and Materials in Metalwork": [
                        "Project",
                    ],
                    "Related Drawing in Metalwork": [
                        "Scales and Conventions",
                        "Pictorial Drawing",
                    ],
                },
                3: {
                    "Metal Joining and Finishing Processes": [
                        "Methods of Joining Sheet Metal",
                        "Sheet Metal Processes",
                        "Project",
                    ],
                },
            },

            "Power Mechanics": {
                1: {
                    "Fundamentals of Power Mechanics": [
                        "Overview of Power Mechanics as a Learning Area",
                        "Evolution of Motor Vehicles",
                        "Power Mechanics Workshop Layout",
                        "General Workshop Rules and Regulations",
                    ],
                    "Related Technical Drawing": [
                        "Diagonal Scale",
                        "Loci",
                    ],
                },
                2: {
                    "Related Technical Drawing": [
                        "Tangency",
                        "Blending of Lines and Curves",
                    ],
                    "Motor Vehicle Systems": [
                        "Road Wheels",
                        "Motor Vehicle Body",
                        "Motor Vehicle Chassis",
                        "Motor Vehicle Body Joining Processes",
                    ],
                },
                3: {
                    "Engines": [
                        "Introduction to Engines",
                        "Types of Engines",
                        "Classifications of Engine",
                        "Engine Components",
                    ],
                },
            },

            "Building Technology": {
                1: {
                    "Foundation of Building Construction": [
                        "Introduction to Building Construction",
                        "Site Preparation",
                    ],
                    "Related Drawing": [
                        "Isometric Drawing",
                        "Computer Aided Drawing",
                    ],
                },
                2: {
                    "Building Construction Processes": [
                        "Concreting",
                        "Foundations",
                        "Timbering",
                        "Foundation Walling",
                        "Ground Floors",
                    ],
                },
                3: {
                    "Building Services": [
                        "Plumbing Tools and Equipment",
                        "Plumbing Materials",
                        "Pipework",
                    ],
                },
            },

            "Aviation Technology": {
                1: {
                    "Foundations of Aviation": [
                        "Introduction to Aviation",
                        "Safety in the Aviation Workplace",
                        "Airport Safety",
                    ],
                    "Aircraft Basic Construction": [
                        "Aircraft Components",
                        "Aircraft Tools and Materials",
                    ],
                },
                2: {
                    "Aircraft Basic Construction": [
                        "Aircraft Related Drawing: Isometric Drawing",
                    ],
                    "Flight Operations": [
                        "Aviation Weather",
                        "Aviation Communication",
                        "Aerodynamics of Flight",
                    ],
                },
                3: {
                    "Airport Operations": [
                        "The Airport",
                        "Airport Business Services",
                    ],
                },
            },

            "Media Technology": {
                1: {
                    "Fundamentals of Media Technology": [
                        "Introduction to Media Technology",
                        "Pre-Production",
                        "Production",
                        "Post-Production",
                    ],
                },
                2: {
                    "Media Components": [
                        "Photography",
                        "Digital Video Production",
                        "Audio Production",
                    ],
                },
                3: {
                    "Media Entrepreneurship & Management": [
                        "Media Ownership and Management",
                        "Media Business Planning",
                        "Marketing and Promotion",
                        "Legal and Ethical Issues in Media",
                    ],
                },
            },

            "Community Service Learning": {
                1: {
                    "Citizenship": [
                        "Concept of CSL",
                        "Community Needs",
                        "Leadership Development",
                        "Intercultural Competence",
                    ],
                    "Life Skills in Education": [
                        "Self-Awareness in the Community",
                        "Conflict Resolution",
                    ],
                },
                2: {
                    "Life Skills in Education": [
                        "Responsible Decision Making",
                    ],
                    "Action Research": [
                        "Introduction to Action Research",
                        "Problem Identification",
                        "Designing and Implementing an Intervention",
                    ],
                },
                3: {
                    "Life Skills in Education": [
                        "Introduction to Social Entrepreneurship",
                        "Opportunity Identification",
                        "Social Enterprise Planning",
                        "Resource Mobilisation",
                    ],
                },
            },
        }

        # -------------------------------------------------
        # CREATE EVERYTHING
        # -------------------------------------------------

        total_learning_areas = 0
        total_strands = 0
        total_substrands = 0
        total_items = 0

        for learning_area_name, terms in curriculum.items():

            learning_area = self.create_learning_area(
                grade=grade,
                pathway=pathway,
                name=learning_area_name,
            )

            total_learning_areas += 1

            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(
                    f"LEARNING AREA: {learning_area_name}"
                )
            )

            for term, strands in terms.items():

                self.stdout.write(
                    f"  TERM {term}"
                )

                for strand_order, (
                    strand_name,
                    substrands,
                ) in enumerate(
                    strands.items(),
                    start=1,
                ):

                    strand = self.create_strand(
                        learning_area=learning_area,
                        name=strand_name,
                        order=strand_order,
                    )

                    total_strands += 1

                    for substrand_order, substrand_name in enumerate(
                        substrands,
                        start=1,
                    ):

                        substrand = self.create_substrand(
                            strand=strand,
                            name=substrand_name,
                            order=substrand_order,
                        )

                        total_substrands += 1

                        self.create_assessment_item(
                            substrand=substrand,
                            term=term,
                            name=substrand_name,
                            order=substrand_order,
                        )

                        total_items += 1

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "GRADE 10 STEM SEED COMPLETE"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write(
            f"Curriculum Version : {version}"
        )
        self.stdout.write(
            f"Grade              : {grade.display_name}"
        )
        self.stdout.write(
            f"Pathway            : {pathway.name}"
        )
        self.stdout.write(
            f"Learning Areas     : {total_learning_areas}"
        )
        self.stdout.write(
            f"Strands            : {total_strands}"
        )
        self.stdout.write(
            f"Sub-Strands        : {total_substrands}"
        )
        self.stdout.write(
            f"Assessment Items   : {total_items}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "No existing curriculum records were deleted."
            )
        )
        self.stdout.write("")