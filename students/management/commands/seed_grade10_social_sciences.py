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
    help = (
        "Seed Grade 10 CBC Social Sciences pathway "
        "from the Grade 10 Social Sciences Assessment Record Book."
    )

    VERSION_CODE = "CBC2026"
    VERSION_NAME = "CBC 2026"
    ACADEMIC_YEAR = 2026

    PATHWAY_NAME = "SOCIAL SCIENCES"

    def field_exists(self, model, field_name):
        return any(
            field.name == field_name
            for field in model._meta.get_fields()
        )

    # ---------------------------------------------------------
    # CURRICULUM VERSION
    # ---------------------------------------------------------

    def get_or_create_version(self):

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
                "Cannot determine how to identify CurriculumVersion."
            )

        defaults = {}

        if "name" in fields and "name" not in lookup:
            defaults["name"] = self.VERSION_NAME

        if (
            "academic_year" in fields
            and "academic_year" not in lookup
        ):
            defaults["academic_year"] = self.ACADEMIC_YEAR

        if "is_active" in fields:
            defaults["is_active"] = True

        version, created = (
            CurriculumVersion.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
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
            if (
                getattr(version, "academic_year", None)
                != self.ACADEMIC_YEAR
            ):
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

    # ---------------------------------------------------------
    # GRADE
    # ---------------------------------------------------------

    def create_grade(self, version):

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

                grade.save(
                    update_fields=["display_name"]
                )

            self.stdout.write(
                "Using existing Grade 10 curriculum record."
            )

        return grade

    # ---------------------------------------------------------
    # PATHWAY
    # ---------------------------------------------------------

    def create_pathway(self, grade):

        fields = {
            field.name
            for field in CurriculumPathway._meta.get_fields()
        }

        lookup = {
            "curriculum_grade": grade,
            "name": self.PATHWAY_NAME,
        }

        defaults = {}

        if "description" in fields:
            defaults["description"] = (
                "Grade 10 Social Sciences pathway"
            )

        pathway, created = (
            CurriculumPathway.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
        )

        if created:

            self.stdout.write(
                self.style.SUCCESS(
                    "Created Grade 10 Social Sciences pathway."
                )
            )

        else:

            self.stdout.write(
                "Using existing Grade 10 Social Sciences pathway."
            )

        return pathway

    # ---------------------------------------------------------
    # LEARNING AREA
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # STRAND
    # ---------------------------------------------------------

    def create_strand(
        self,
        learning_area,
        name,
        order,
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

        if changed:

            strand.save()

        return strand

    # ---------------------------------------------------------
    # SUB-STRAND
    # ---------------------------------------------------------

    def create_substrand(
        self,
        strand,
        name,
        order,
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

        if changed:

            substrand.save()

        return substrand

    # ---------------------------------------------------------
    # ASSESSMENT ITEM
    # ---------------------------------------------------------

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

                item.save(
                    update_fields=["order"]
                )

        return item

    # ---------------------------------------------------------
    # SEED STRUCTURE
    # ---------------------------------------------------------

    def seed_structure(
        self,
        learning_area,
        term,
        strands,
        counters,
    ):

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

            counters["strands"] += 1

            for substrand_order, substrand_name in enumerate(
                substrands,
                start=1,
            ):

                substrand = self.create_substrand(
                    strand=strand,
                    name=substrand_name,
                    order=substrand_order,
                )

                counters["substrands"] += 1

                self.create_assessment_item(
                    substrand=substrand,
                    term=term,
                    name=substrand_name,
                    order=substrand_order,
                )

                counters["items"] += 1

    # =========================================================
    # MAIN SEED
    # =========================================================

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
                "GRADE 10 SOCIAL SCIENCES CURRICULUM SEED"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write("")

        version = self.get_or_create_version()

        grade = self.create_grade(version)

        pathway = self.create_pathway(grade)

        # =====================================================
        # SOCIAL SCIENCES CURRICULUM
        # =====================================================

        curriculum = {

            # -------------------------------------------------
            # ENGLISH LANGUAGE
            # -------------------------------------------------

            "English Language": {

                1: {
                    "1.0 ETIQUETTE : SOCIAL": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "2.0 ENVIRONMENT : CLIMATE CHANGE": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "3.0 ARTIFICIAL INTELLIGENCE AND SOCIETY : HEALTHCARE": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "4.0 TRAVEL : ADVENTURE": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                },

                2: {
                    "CARRIER : PUBLIC SECTOR": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "SPORTS AND GAMES : POPULAR SPORTS": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "HEALTH AND SAFETY: PERSONAL SAFETY": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                },

                3: {
                    "8.0 HEALTH AND SAFETY: PERSONAL SAFETY": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                    "9.0 INCOME : TYPES AND SOURCES": [
                        "Listening and Speaking",
                        "Reading",
                        "Grammar in use",
                        "Writing",
                    ],
                },
            },

            # -------------------------------------------------
            # KISWAHILI LUGHA
            # -------------------------------------------------

            "Kiswahili Lugha": {

                1: {
                    "1.0 MIKONDO YA FURSA ZA AJIRA": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "2.0 KUKABILIANA NA SHINIKIZORIKA": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "3.0 UTAMBUZI WA UWEZO NA VIPAJI MBALIMBALI": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "4.0 USALAMA BARABARANI": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                },

                2: {
                    "4.0 USALAMA BARABARANI": [
                        "Matumizi ya Lugha",
                    ],
                    "5.0 KUKABILIANA NA MABADILIKO YA MAISHA YA KIBINAFSI": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "6.0 KUDHIBITI TAKA KATIKA MAZINGIRA": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "7.0 UADILIFU KATIKA UONGOZI SHULENI": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "8.0 JINSIA YA TAALUMA": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                },

                3: {
                    "9.0 KUHESHIMU TAMADUNI ZA WENGINE": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                    "10.0 HUDUMA YA KWANZA": [
                        "Kusikiliza na Kuzungumza",
                        "Kusoma",
                        "Kuandika",
                        "Matumizi ya Lugha",
                    ],
                },
            },

            # -------------------------------------------------
            # CORE MATHEMATICS
            # -------------------------------------------------

            "Core Mathematics": {

                1: {
                    "1.0 NUMBERS AND ALGEBRA": [
                        "Real Numbers",
                        "Indices and Logarithms",
                        "Quadratic Expressions and Equations I",
                    ],
                    "2.0 MEASUREMENTS AND GEOMETRY": [
                        "Similarity and Enlargement",
                        "Reflection and Congruence",
                    ],
                },

                2: {
                    "1.0 MEASUREMENTS AND GEOMETRY": [
                        "Reflection and Congruence",
                        "Rotation",
                        "Trigonometry I",
                    ],
                },

                3: {
                    "3.0 STATISTICS AND PROBABILITY": [
                        "Statistics I",
                        "Probability I",
                    ],
                },
            },

            # -------------------------------------------------
            # ESSENTIAL MATHEMATICS
            # -------------------------------------------------

            "Essential Mathematics": {

                1: {
                    "1.0 NUMBERS AND ALGEBRA": [
                        "Real Numbers",
                        "Indices",
                        "Quadratic Equations",
                    ],
                    "2.0 MEASUREMENTS AND GEOMETRY": [
                        "Similarity and Enlargement",
                        "Reflection",
                        "Trigonometry",
                    ],
                },

                2: {
                    "MEASUREMENTS AND GEOMETRY": [
                        "2.4 Area of Polygons",
                        "2.5 Area of Part of a Circle",
                        "2.6 Surface Area of Solids",
                        "2.7 Volume and Capacity",
                        "2.8 Commercial Arithmetic I",
                    ],
                },

                3: {
                    "3.0 STATISTICS AND PROBABILITY": [
                        "Statistics I",
                        "Probability I",
                    ],
                },
            },

            # -------------------------------------------------
            # LITERATURE IN ENGLISH
            # -------------------------------------------------

            "Literature in English": {

                1: {
                    "1.0 ORAL LITERATURE": [
                        "1.1 Introduction to Oral Literature",
                        "1.2 Oral Narratives",
                        "1.3 Songs / Oral Poetry",
                        "1.4 Short Forms of Oral Literature",
                        "1.5 Performance of Oral Literature",
                        "1.6 Oral Literature Fieldwork (Project)",
                    ],
                },

                2: {
                    "2.0 POETRY": [
                        "2.1 Introduction to Poetry",
                        "2.2 Appreciation of Poetry",
                    ],
                    "3.0 FICTION AND NON-FICTION": [
                        "3.1 Fiction",
                        "3.2 The Novel from Kenya",
                    ],
                },

                3: {
                    "FICTION AND NON-FICTION": [
                        "3.3 The Play from Kenya",
                        "3.4 Anthology of Short Stories",
                        "3.5 Non-Fiction",
                    ],
                },
            },

            # -------------------------------------------------
            # INDIGENOUS LANGUAGES
            # -------------------------------------------------

            "Indigenous Languages": {

                1: {
                    "1.0 INDEGENOUS KNOWLEDGE": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                    "2.0 COMMUNICATION": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                },

                2: {
                    "3.0 CULTURE": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                    "4.0 HEALTH": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                    "5.0 ENVIRONMENT": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                },

                3: {
                    "6.0 GENDER": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                    "7.0 CAREERS": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                    "8.0 BUSINESS AND ENTREPRENEURSHIP": [
                        "Listening and speaking",
                        "Reading",
                        "Grammar",
                        "Writing",
                    ],
                },
            },

            # -------------------------------------------------
            # FASIHI YA KISWAHILI
            # -------------------------------------------------

            "Fasihi ya Kiswahili": {

                1: {
                    "1.0 FASIHI SIMULIZI": [
                        "1.1.1 Misingi ya Fasihi Simulizi",
                        "2.1.1 Uchanganuzi wa Hadithi: Hekaya na Hurafa",
                        "3.1.1 Uchanganuzi wa Semi: Utangulizi",
                        "4.1.1 Uchanganuzi wa Ushairi Simulizi: Nyimbo",
                        "5.1.1 Uchanganuzi wa Mazungumzo: Utangulizi",
                        "6.1.1 Uchanganuzi wa Maigizo: Utangulizi",
                        "7.1.1 Uchanganuzi wa Hadithi: Ngano za Mazimwi na Mighani",
                        "8.1.1 Uchanganuzi wa Semi: Misemo na Nahau",
                        "9.1.1 Ushairi Simulizi: Maghani ya Kawaida",
                        "10.1.1 Utafiti: Utafiti wa Maktabani na wa Nyanjani",
                    ],
                    "2.0 USHAIRI": [
                        "1.2.1 Uainishaji wa Mashairi: Utangulizi",
                        "2.2.1 Makundi ya Mashairi: Huru na ya Arudhi",
                    ],
                },

                2: {
                    "2.0 USHAIRI": [
                        "3.2.1 Uchambuzi wa Mashairi: Maudhui na Dhamira",
                        "4.2.1 Uchambuzi wa Mashairi: Maudhui na Dhamira",
                        "5.2.1 Ushairi: Mandhari na Wahusika",
                        "6.2.1 Uchambuzi wa Mashairi: Muundo",
                        "7.2.1 Uchambuzi wa Mashairi: Mtindo",
                        "8.2.1 Uchambuzi wa Mashairi: Mtindo",
                        "9.2.1 Ushairi: Uhuru wa Kishairi",
                        "10.2.1 Utunzi wa Mashairi",
                    ],
                    "3.0 BUNILIZI NA KAZI ZA KIHALISIA": [
                        "1.3.1 Utangulizi wa Bunilizi na Kazi za Kihalisia",
                    ],
                },

                3: {
                    "3.0 BUNILIZI NA KAZI ZA KIHALISIA": [
                        "2.3.1 Uchambuzi wa Tamthilia: Maudhui, Dhamira na Wahusika",
                        "3.3.1 Uchambuzi wa Tamthilia: Mandhari, Muundo na Mtindo",
                        "4.3.1 Uchambuzi wa Riwaya: Maudhui, Dhamira na Wahusika",
                        "5.3.1 Uchambuzi wa Riwaya: Mandhari, Muundo na Mtindo",
                        "6.3.1 Uchambuzi wa Tawasifu: Maudhui, Dhamira na Wahusika",
                        "7.3.1 Uchambuzi wa Tawasifu: Mandhari, Muundo na Mtindo",
                        "8.3.1 Uchambuzi wa Hadithi Fupi: Maudhui, Dhamira na Wahusika",
                        "9.3.1 Uchambuzi wa Hadithi Fupi: Mandhari, Muundo na Mtindo",
                        "10.3.1 Utunzi wa Bunilizi na Kazi za Kihalisia",
                    ],
                },
            },

            # -------------------------------------------------
            # ARABIC
            #
            # The record book exposes the T2/T3 structure clearly.
            # T1 does not expose strand names in the parsed source,
            # so T1 is intentionally not invented.
            # -------------------------------------------------

            "Arabic": {

                2: {
                    "3.0 TOURISM": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "4.0 HEALTH": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "5.0 SCHOOL AND THE WORLD OF WORK": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                3: {
                    "5.0 SCHOOL AND THE WORLD OF WORK": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "6.0 THE WORLD OF BUSINESS": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },
            },

            # -------------------------------------------------
            # FRENCH
            # -------------------------------------------------

            "French": {

                1: {
                    "1.0 SOCIAL LIFE : MY FRIEND": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "2.0 MY ENVIRONMENT : MY HOME": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                2: {
                    "3.0 TOURISM : MEANS OF TRANSPORT": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "4.0 HEALTH : MY BODY": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "HEALTH : FOOD AND DRINKS": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                3: {
                    "5.0 SCHOOL AND WORLD OF WORK : SCHOOL ROUTINE": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "6.0 WORLD OF BUSINESS : SHOPPING": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },
            },

            # -------------------------------------------------
            # MANDARIN CHINESE
            # -------------------------------------------------

            "Mandarin Chinese": {

                1: {
                    "1.0 SOCIAL LIFE": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "2.0 MY ENVIRONMENT": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                2: {
                    "3.0 TOURISM": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "4.0 HEALTH": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                3: {
                    "5.0 SCHOOL AND WORLD OF WORK": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "6.0 WORLD OF BUSINESS": [
                        "Listening and speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },
            },

            # -------------------------------------------------
            # CRE
            # -------------------------------------------------

            "CRE": {

                1: {
                    "1.0 THE OLD TESTAMENT": [
                        "1.1 The Holy Bible",
                        "1.2 Methods of Studying the Holy Bible",
                        "1.3 Redemption after the Fall of Man",
                        "1.4 Stewardship over Creation",
                        "1.5 The Exodus",
                        "1.6 The Sinai Covenant",
                        "1.7 Loyalty to God (Elijah)",
                        "1.8 The Old Testament Prophecies",
                        "1.9.1 Background of Prophet Amos",
                    ],
                },

                2: {
                    "2.0 THE NEW TESTAMENT": [
                        "2.1 The New Testament Books",
                        "2.2 Infancy and Early Life of Jesus Christ",
                        "2.3 Galilean Ministry",
                        "2.4 Paul's First Letter to the Corinthians",
                    ],
                    "3.0 CHURCH IN ACTION": [
                        "3.1 The Holy Spirit",
                        "3.2 The Gifts of the Holy Spirit",
                        "3.3 The Holy Trinity",
                        "3.4 Sacraments",
                    ],
                },

                3: {
                    "4.0 CHRISTIAN LIVING TODAY": [
                        "4.1 Christian Ethics and Morality",
                        "4.2 Human Rights (Gender Based Violence)",
                        "4.3 Human Sexuality",
                        "4.4 Marriage and Family",
                        "4.5 Christian Response to Modern Medicine, Science and Technology",
                    ],
                },
            },

            # -------------------------------------------------
            # IRE
            # -------------------------------------------------

            "IRE": {

                1: {
                    "1.0 STUDY OF THE QURAN AND HADITH": [
                        "1.1 Compilation and Standardisation of the Qur'an",
                        "1.2 Diacriticalisation of the Qur'an",
                        "1.3 Types of Verses",
                        "1.4 Asbabu al-Nuzuul (Reasons for Revelation)",
                        "1.5 Selected Verses: Surah al-Furqan (Q. 25:61-77)",
                        "1.6 Ulum al-Hadith: Isnad and Matn",
                        "1.7 Selected Hadith",
                    ],
                    "2.0 FIQH AL IBADAT WAL MUAMALAT (JURISPRUDENCE OF DEVOTIONAL ACTS AND RELATIONSHIPS)": [
                        "2.1 Prayers on Special Occasions",
                        "2.2 Funeral Rites: Ghusul, Kafan, Swalah, Dafan",
                        "2.3 Administration of Zakat",
                    ],
                },

                2: {
                    "FIQH AL IBADAT WAL MUAMALAT (JURISPRUDENCE OF DEVOTIONAL ACTS AND RELATIONSHIPS)": [
                        "2.4 Types of Divorce",
                        "2.5 Care for Widows",
                        "2.6 Governance in Islam: Shura, Accountability and Justice",
                        "2.7 Labour Relations in Islam",
                        "2.8 Ethics of Da'wa (Propagation)",
                    ],
                    "3.0 AKHLAQ (MORAL TEACHINGS)": [
                        "3.1 Foods and Drinks: Carrion, Blood, Pork, Animals Dedicated to Other than Allah (S.W.T.)",
                        "3.2 Virtues: Islamic Clothing and Adornment",
                        "3.3 Virtues: Manners of Walking",
                    ],
                },

                3: {
                    "3.0 AKHLAQ (MORAL TEACHINGS)": [
                        "3.4 Virtues: Honesty",
                        "3.5 Prohibitions in Islam",
                    ],
                    "4.0 ISLAMIC HISTORY AND CIVILISATION": [
                        "4.1 Muslim Dynasties: Rise of the Umayyad Dynasty; Selected Umayyad Caliphs (Muawiya ibn Abi Sufyan, Abdulmalik ibn Marwan, Umar ibn Abdulaziz); Achievements and Decline",
                        "4.2 Islam in Tanzania and Uganda",
                        "4.3 Muslim Scholars",
                    ],
                },
            },

            # -------------------------------------------------
            # HRE
            # -------------------------------------------------

            "Hindu Religious Education": {

                1: {
                    "1.0 MANIFESTATIONS OF PARAMATMA": [
                        "1.1 Trimurti and DashAvatars",
                        "1.2 Jain Tirthankar",
                        "1.3 Buddhist Views",
                        "1.4 Guru's Grace - Sikh Faith",
                    ],
                },

                2: {
                    "2.0 SCRIPTURES": [
                        "2.1 Origin and Development",
                        "2.2 Ethical and Moral Teachings",
                        "2.3 Prominent Personalities",
                    ],
                    "3.0 PRINCIPLES OF DHARMA": [
                        "3.1 Core Beliefs",
                        "3.2 Introduction to the Law of Karma",
                    ],
                },

                3: {
                    "4.0 CULTURAL PRACTICES": [
                        "4.1 Music - Vocal Music",
                        "4.2 Instrumental Music",
                        "4.3 Dances (Folk and Classical)",
                    ],
                },
            },

            # -------------------------------------------------
            # BUSINESS STUDIES
            # -------------------------------------------------

            "Business Studies": {

                1: {
                    "1.0 BUSINESS AND MONEY MANAGEMENT": [
                        "1.1 Money",
                        "1.2 Business Goals",
                        "1.3 Budgeting in Business",
                        "1.4 Banking",
                    ],
                    "2.0 BUSINESS AND ITS ENVIRONMENT": [
                        "2.1 Business Activities",
                    ],
                },

                2: {
                    "2.0 BUSINESS AND ITS ENVIRONMENT": [
                        "2.2 Types of Business Ownership",
                        "2.3 Social Responsibility of Business",
                        "2.4 Entrepreneurship",
                        "2.5 Production",
                        "2.6 Consumer Satisfaction",
                    ],
                    "3.0 GOVERNMENT AND GLOBAL INFLUENCE IN BUSINESS": [
                        "3.1 Public Finance",
                        "3.2 International Trade",
                    ],
                },

                3: {
                    "4.0 FINANCIAL RECORDS IN BUSINESS": [
                        "4.1 Business Transactions",
                        "4.2 Effects of Business Transactions",
                        "4.3 Source Documents and Journals",
                    ],
                },
            },

            # -------------------------------------------------
            # HISTORY AND CITIZENSHIP
            # -------------------------------------------------

            "History and Citizenship": {

                1: {
                    "1.0 THEMES IN KENYAN HISTORY AND CITIZENSHIP": [
                        "1.1 Introduction to History and Citizenship",
                        "1.2 Linguistic Groups in Kenya",
                        "1.3 Establishment of Colonial Rule",
                        "1.4 Public Participation",
                        "1.5 Political Developments and Challenges Since Independence",
                        "1.6 Elections in Kenya",
                        "1.7 National Integration",
                    ],
                    "2.0 THEMES IN AFRICAN HISTORY AND CITIZENSHIP": [
                        "2.1 Human Developments in Africa",
                        "2.2 African Civilisations up to 19th Century",
                        "2.3 Colonization of Africa",
                        "2.4 Modern Nationalism in Africa",
                        "2.5 Global Wars",
                    ],
                },

                2: {
                    "2.0 THEMES IN AFRICAN HISTORY AND CITIZENSHIP": [
                        "2.1 Human Developments in Africa",
                        "2.2 African Civilisations up to 19th Century",
                        "2.3 Colonization of Africa",
                        "2.4 Modern Nationalism in Africa",
                        "2.5 Global Wars",
                    ],
                    "3.0 THEMES IN WORLD HISTORY AND CITIZENSHIP": [
                        "3.1 Enlightenment Ideas and the American Revolution",
                    ],
                },

                3: {
                    "3.0 THEMES IN WORLD HISTORY AND CITIZENSHIP": [
                        "3.2 International Organisations - Commonwealth of Nations",
                        "3.3 Modern Slavery and Servitude",
                        "3.4 Global Governance",
                        "3.5 1st Generation of Industrial Revolution in Europe and Africa",
                    ],
                    "4.0 THEMES IN CONTEMPORARY HISTORY AND CITIZENSHIP": [
                        "4.1 Peace and Conflict Transformations in Kenya",
                        "4.2 Digital Citizenship: Technology Communication and Evolution of the Internet (Global Movement)",
                        "4.3 Equality and Non-Discrimination",
                    ],
                },
            },

            # -------------------------------------------------
            # GERMAN
            # -------------------------------------------------

            "German": {

                1: {
                    "1.0 SOCIAL LIFE : MY FAMILY": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "2.0 MY ENVIRONMENT : MY HOME": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                2: {
                    "3.0 SCHOOL AND WORLD OF WORK : SCHOOL ROUTINES": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "4.0 HEALTH: FOOD AND EATING HABITS": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                    "5.0 TOURISM : MEANS OF TRANSPORT": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },

                3: {
                    "TOURISM : MEANS OF TRANSPORT": [
                        "Writing",
                        "Grammar",
                    ],
                    "6.0 WORLD OF BUSINESS : SHOPPING": [
                        "Listening and Speaking",
                        "Reading",
                        "Writing",
                        "Grammar",
                    ],
                },
            },

            # -------------------------------------------------
            # GEOGRAPHY
            # -------------------------------------------------

            "Geography": {

                1: {
                    "1.0 PRACTICAL GEOGRAPHY": [
                        "1.1 Introduction to Geography",
                        "1.2 Map Reading and Interpretation",
                        "1.3 Statistical Methods",
                        "1.4 Geographic Information System",
                    ],
                },

                2: {
                    "2.0 NATURAL SYSTEMS AND PROCESSES": [
                        "2.1 Rocks",
                        "2.2 Folding",
                        "2.3 Vulcanicity",
                        "2.4 Earthquakes",
                    ],
                },

                3: {
                    "3.0 HUMAN AND ECONOMIC ACTIVITIES": [
                        "3.1 Agriculture",
                        "3.2 Mining",
                        "3.3 Energy",
                        "3.4 Industry",
                    ],
                },
            },

            # -------------------------------------------------
            # SIGN LANGUAGE
            #
            # The uploaded record book lists Sign Language as
            # a Social Sciences learning area in the summative
            # tables, but its detailed strand/sub-strand section
            # is not exposed in the available parsed source.
            #
            # Therefore no structure is invented here.
            # -------------------------------------------------

            "Sign Language": {},
        }

        total_learning_areas = 0
        total_strands = 0
        total_substrands = 0
        total_items = 0

        # -----------------------------------------------------
        # CREATE STRUCTURE
        # -----------------------------------------------------

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

                if not strands:

                    self.stdout.write(
                        "    No detailed strand structure "
                        "was available in the source."
                    )

                    continue

                counters = {
                    "strands": 0,
                    "substrands": 0,
                    "items": 0,
                }

                self.seed_structure(
                    learning_area=learning_area,
                    term=term,
                    strands=strands,
                    counters=counters,
                )

                total_strands += counters["strands"]
                total_substrands += counters["substrands"]
                total_items += counters["items"]

        # -----------------------------------------------------
        # FINAL REPORT
        # -----------------------------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "GRADE 10 SOCIAL SCIENCES SEED COMPLETE"
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

        self.stdout.write(
            self.style.WARNING(
                "NOTE: Sign Language has been created as a "
                "learning area, but no strand/sub-strand data "
                "was invented because its detailed section was "
                "not available in the parsed assessment book."
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "NOTE: Arabic Term 1 detailed strand names were "
                "not available in the parsed assessment book, "
                "so they were intentionally not invented."
            )
        )

        self.stdout.write("")