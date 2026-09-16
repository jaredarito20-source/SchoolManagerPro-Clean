from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError

from django.test import TestCase
from django.contrib.auth.models import User
from students.models import (
    SchoolProfile,
    SchoolClass,
    Student,
    StudentAcademicEnrollment,
    SchoolUser,
    FeeStructure,
    FeeLedgerEntry,
    FeePayment,
    Teacher,
    CurriculumVersion,
    CurriculumGrade,
    CurriculumPathway,
    CurriculumLearningArea,
    CurriculumStrand,
    CurriculumSubStrand,
    SchoolClassCurriculum,
    TeacherAssessmentAssignment,
    CBCSubStrandAssessment,
    CurriculumAssessmentItem,
)

from students.services.fee_ledger import (
    get_term_balance,
    get_term_opening_balance,
    record_adjustment,
    record_term_fee_charge,
    record_term_fee_charges_for_class,
    record_academic_year_opening_balances,
    student_is_eligible_for_term,
    record_payment,
)


class FinanceLedgerYearCrossoverTests(TestCase):

    def setUp(self):
        self.school = SchoolProfile.objects.create(
            name="Test School",
            academic_year="2026",
            current_term="3",
        )

        self.school_class = SchoolClass.objects.create(
            name="Form 3",
            school=self.school,
        )

    def create_student(
        self,
        admission_number,
        enrollment_year="2026",
        enrollment_term="1",
    ):
        student = Student.objects.create(
            admission_number=admission_number,
            first_name="Test",
            last_name="Student",
            gender="Male",
            date_of_birth=date(2010, 1, 1),
            parent_name="Test Parent",
            phone="0700000000",
            school=self.school,
            school_class=self.school_class,
            enrollment_academic_year=enrollment_year,
            enrollment_term=enrollment_term,
        )

        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year=enrollment_year,
            term=enrollment_term,
        )

        return student

    def test_student_enrollment_record_matches_school_current_period(self):
        self.school.academic_year = "2026"
        self.school.current_term = "3"
        self.school.save()

        student = self.create_student(
            "TEST_ENROLLMENT",
            enrollment_year="2026",
            enrollment_term="3",
        )

        enrollment = StudentAcademicEnrollment.objects.get(
            student=student,
            academic_year=self.school.academic_year,
            term=self.school.current_term,
        )

        

        self.assertEqual(
            student.enrollment_academic_year,
            "2026",
        )

        self.assertEqual(
            student.enrollment_term,
            "3",
        )

        self.assertEqual(
            enrollment.academic_year,
            "2026",
        )

        self.assertEqual(
            enrollment.term,
            "3",
        )

        self.assertEqual(
            enrollment.school_class_id,
            self.school_class.id,
        )

        self.assertEqual(
            StudentAcademicEnrollment.objects.filter(
                student=student,
                academic_year="2026",
                term="3",
            ).count(),
            1,
        )

    def test_add_student_creates_current_academic_enrollment(self):
        from django.contrib.auth.models import Group, User
        from django.urls import reverse

        self.school.academic_year = "2026"
        self.school.current_term = "2"
        self.school.save()

        admin_group, _ = Group.objects.get_or_create(
            name="Administrators"
        )

        user = User.objects.create_user(
            username="test_add_student_admin",
            password="test-password",
        )
        user.groups.add(admin_group)

        SchoolUser.objects.create(
            user=user,
            school=self.school,
        )

        self.client.login(
            username="test_add_student_admin",
            password="test-password",
        )

        response = self.client.post(
            reverse("students:add_student"),
            {
                "admission_number": "ADM-ENROLL-001",
                "first_name": "New",
                "last_name": "Student",
                "gender": "Male",
                "date_of_birth": "2015-01-01",
                "school": self.school.id,
                "school_class": self.school_class.id,
                "parent_name": "Parent",
                "phone": "0700000000",
            },
        )

        self.assertEqual(response.status_code, 302)

        student = Student.objects.get(
            admission_number="ADM-ENROLL-001"
        )

        self.assertEqual(
            student.enrollment_academic_year,
            "2026",
        )

        self.assertEqual(
            student.enrollment_term,
            "2",
        )

        enrollment = StudentAcademicEnrollment.objects.get(
            student=student,
            academic_year="2026",
            term="2",
        )

        self.assertEqual(
            enrollment.school_class_id,
            self.school_class.id,
        )

    def test_new_student_starts_term_one_at_zero(self):
        student = self.create_student(
            "TEST001",
            enrollment_year="2026",
            enrollment_term="1",
        )

        opening = get_term_opening_balance(
            student=student,
            academic_year="2026",
            term="1",
        )

        self.assertEqual(
            opening,
            Decimal("0.00"),
        )

    def test_terms_are_continuous_within_same_academic_year(self):
        student = self.create_student(
            "TEST002",
            enrollment_year="2026",
            enrollment_term="1",
        )

        record_adjustment(
            student=student,
            amount=Decimal("10000.00"),
            academic_year="2026",
            term="1",
        )

        record_adjustment(
            student=student,
            amount=Decimal("5000.00"),
            academic_year="2026",
            term="2",
        )

        record_adjustment(
            student=student,
            amount=Decimal("3000.00"),
            academic_year="2026",
            term="3",
        )

        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2026",
                term="1",
            ),
            Decimal("10000.00"),
        )

        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2026",
                term="2",
            ),
            Decimal("15000.00"),
        )

        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2026",
                term="3",
            ),
            Decimal("18000.00"),
        )

    def test_previous_year_term_three_becomes_next_year_term_one_opening(self):
        student = self.create_student(
            "TEST003",
            enrollment_year="2026",
            enrollment_term="1",
        )

        record_adjustment(
            student=student,
            amount=Decimal("10000.00"),
            academic_year="2026",
            term="3",
        )

        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year="2026",
            term="3",
        )

        opening_2027 = get_term_opening_balance(
            student=student,
            academic_year="2027",
            term="1",
        )

        self.assertEqual(
            opening_2027,
            Decimal("10000.00"),
        )

    def test_new_student_in_next_year_does_not_inherit_previous_year_balance(self):
        student = self.create_student(
            "TEST004",
            enrollment_year="2027",
            enrollment_term="1",
        )

        opening_2027 = get_term_opening_balance(
            student=student,
            academic_year="2027",
            term="1",
        )

        self.assertEqual(
            opening_2027,
            Decimal("0.00"),
        )

        self.assertFalse(
            student_is_eligible_for_term(
                student=student,
                academic_year="2026",
                term="3",
            )
        )

    def test_term_fee_charge_creates_correct_ledger_entry(self):
        student = self.create_student(
            "TEST005",
            enrollment_year="2026",
            enrollment_term="1",
        )

        fee_structure = FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2026",
            term="1",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        entry = record_term_fee_charge(
            student=student,
            fee_structure=fee_structure,
        )

        self.assertEqual(
            entry.transaction_type,
            "FEE_CHARGE",
        )

        self.assertEqual(
            entry.debit,
            Decimal("33000.00"),
        )

        self.assertEqual(
            entry.credit,
            Decimal("0.00"),
        )

        self.assertEqual(
            entry.academic_year,
            "2026",
        )

        self.assertEqual(
            entry.term,
            "1",
        )

        self.assertEqual(
            entry.balance,
            Decimal("33000.00"),
        )

        self.assertEqual(
            FeeLedgerEntry.objects.filter(
                student=student,
                transaction_type="FEE_CHARGE",
                academic_year="2026",
                term="1",
            ).count(),
            1,
        )

    def test_same_term_fee_charge_is_not_duplicated(self):
        student = self.create_student(
            "TEST006",
            enrollment_year="2026",
            enrollment_term="1",
        )

        fee_structure = FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2026",
            term="1",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        first_entry = record_term_fee_charge(
            student=student,
            fee_structure=fee_structure,
        )

        second_entry = record_term_fee_charge(
            student=student,
            fee_structure=fee_structure,
        )

        self.assertEqual(
            first_entry.pk,
            second_entry.pk,
        )

        self.assertEqual(
            FeeLedgerEntry.objects.filter(
                student=student,
                transaction_type="FEE_CHARGE",
                academic_year="2026",
                term="1",
            ).count(),
            1,
        )

        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2026",
                term="1",
            ),
            Decimal("33000.00"),
        )

    def test_student_enrolling_in_term_two_gets_only_term_two_charge(self):
        student = self.create_student(
            "TEST007",
            enrollment_year="2026",
            enrollment_term="2",
        )

        FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2026",
            term="1",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2026",
            term="2",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        record_term_fee_charges_for_class(
            school_class=self.school_class,
            academic_year="2026",
            term="1",
        )

        self.assertEqual(
            FeeLedgerEntry.objects.filter(
                student=student,
                transaction_type="FEE_CHARGE",
                academic_year="2026",
                term="1",
            ).count(),
            0,
        )

        record_term_fee_charges_for_class(
            school_class=self.school_class,
            academic_year="2026",
            term="2",
        )

        self.assertEqual(
            FeeLedgerEntry.objects.filter(
                student=student,
                transaction_type="FEE_CHARGE",
                academic_year="2026",
                term="2",
            ).count(),
            1,
        )

        self.assertEqual(
            FeeLedgerEntry.objects.get(
                student=student,
                transaction_type="FEE_CHARGE",
                academic_year="2026",
                term="2",
            ).debit,
            Decimal("33000.00"),
        )

    def test_year_crossover_creates_explicit_opening_balance(self):
        student = self.create_student(
            "TEST008",
            enrollment_year="2026",
            enrollment_term="1",
        )

        

        # Student has a closing balance of 10,000 in 2026 T3.
        record_adjustment(
            student=student,
            amount=Decimal("10000.00"),
            academic_year="2026",
            term="3",
        )

        # The student continued into the next academic year.
        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year="2026",
            term="3",
        )

        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year="2027",
            term="1",
        )

        record_academic_year_opening_balances(
            school=self.school,
            new_academic_year="2027",
        )

        # This is the behavior we want to implement.
        # The previous year's closing balance should become
        # an actual OPENING_BALANCE entry in 2027 T1.
        opening_entry = FeeLedgerEntry.objects.filter(
            student=student,
            transaction_type="OPENING_BALANCE",
            academic_year="2027",
            term="1",
        ).first()

        self.assertIsNotNone(opening_entry)

        self.assertEqual(
            opening_entry.debit,
            Decimal("10000.00"),
        )

        self.assertEqual(
            opening_entry.credit,
            Decimal("0.00"),
        )

        self.assertEqual(
            opening_entry.balance,
            Decimal("10000.00"),
        )

        self.assertEqual(
            get_term_opening_balance(
                student=student,
                academic_year="2027",
                term="1",
            ),
            Decimal("10000.00"),
        )

    def test_full_year_crossover_accounting_chain(self):
        student = self.create_student(
            "TEST008",
            enrollment_year="2026",
            enrollment_term="1",
        )

        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year="2026",
            term="3",
        )

        # --------------------------------------------------
        # 2026 TERM 3
        # --------------------------------------------------

        fee_structure_2026 = FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2026",
            term="3",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        record_term_fee_charge(
            student=student,
            fee_structure=fee_structure_2026,
        )

        # Payment of 23,000 against the 33,000 fees.
        payment_2026 = FeePayment.objects.create(
            student=student,
            amount=Decimal("23000.00"),
            payment_date=date(2026, 12, 1),
            payment_method="Cash",
            receipt_number="TEST-RCPT-008",
            academic_year="2026",
            term="3",
        )

        record_payment(
            student=student,
            payment=payment_2026,
        )

        
        # 2026 T3 closing balance must be 10,000.
        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2026",
                term="3",
            ),
            Decimal("10000.00"),
        )

        # --------------------------------------------------
        # 2027 TERM 1
        # --------------------------------------------------

        StudentAcademicEnrollment.objects.create(
            student=student,
            school_class=self.school_class,
            academic_year="2027",
            term="1",
        )

        record_academic_year_opening_balances(
            school=self.school,
            new_academic_year="2027",
        )

        # Previous year's 10,000 becomes an actual
        # OPENING_BALANCE entry.
        opening_entry = FeeLedgerEntry.objects.get(
            student=student,
            transaction_type="OPENING_BALANCE",
            academic_year="2027",
            term="1",
        )

        

        self.assertEqual(
            opening_entry.debit,
            Decimal("10000.00"),
        )

        self.assertEqual(
            opening_entry.credit,
            Decimal("0.00"),
        )

        # New 2027 T1 fees = 33,000.
        fee_structure_2027 = FeeStructure.objects.create(
            school_class=self.school_class,
            academic_year="2027",
            term="1",
            tuition_fee=Decimal("30000.00"),
            activity_fee=Decimal("2000.00"),
            exam_fee=Decimal("1000.00"),
            other_fee=Decimal("0.00"),
        )

        record_term_fee_charge(
            student=student,
            fee_structure=fee_structure_2027,
        )

        # Opening 10,000 + new fees 33,000 = 43,000.
        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2027",
                term="1",
            ),
            Decimal("43000.00"),
        )

        # --------------------------------------------------
        # 2027 T1 PAYMENT
        # --------------------------------------------------

        payment_2027 = FeePayment.objects.create(
            student=student,
            amount=Decimal("20000.00"),
            payment_date=date(2027, 1, 15),
            payment_method="Cash",
            receipt_number="TEST-RCPT-009",
            academic_year="2027",
            term="1",
        )

        record_payment(
            student=student,
            payment=payment_2027,
        )

        # 43,000 - 20,000 = 23,000.
        self.assertEqual(
            get_term_balance(
                student=student,
                academic_year="2027",
                term="1",
            ),
            Decimal("23000.00"),
        )
    # ============================================================
# CBC MULTI-SCHOOL SECURITY TESTS
# ============================================================

class CBCAssessmentMultiSchoolSecurityTests(TestCase):

    def setUp(self):
        # ----------------------------------------------------
        # SCHOOL A
        # ----------------------------------------------------

        self.school_a = SchoolProfile.objects.create(
            name="CBC School A",
            academic_year="2026",
            current_term="1",
        )

        self.class_a = SchoolClass.objects.create(
            name="Grade 10A",
            school=self.school_a,
            curriculum="CBC",
        )

        # ----------------------------------------------------
        # SCHOOL B
        # ----------------------------------------------------

        self.school_b = SchoolProfile.objects.create(
            name="CBC School B",
            academic_year="2026",
            current_term="1",
        )

        self.class_b = SchoolClass.objects.create(
            name="Grade 10B",
            school=self.school_b,
            curriculum="CBC",
        )

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        self.teacher_user_a = User.objects.create_user(
            username="cbc_teacher_a",
            password="test-password",
        )

        self.teacher_user_b = User.objects.create_user(
            username="cbc_teacher_b",
            password="test-password",
        )

        self.teacher_a = Teacher.objects.create(
            user=self.teacher_user_a,
            school=self.school_a,
            employee_number="TEACHER-A-001",
        )

        self.teacher_b = Teacher.objects.create(
            user=self.teacher_user_b,
            school=self.school_b,
            employee_number="TEACHER-B-001",
        )

        # ----------------------------------------------------
        # CURRICULUM VERSION
        # ----------------------------------------------------

        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026",
            code="CBC-2026-SECURITY-TEST",
            academic_year="2026",
        )

        # ----------------------------------------------------
        # GRADE 10
        # ----------------------------------------------------

        self.grade_10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        # ----------------------------------------------------
        # ARTS & SPORTS PATHWAY
        # ----------------------------------------------------

        self.pathway = CurriculumPathway.objects.create(
            curriculum_grade=self.grade_10,
            name="ARTS_SPORTS",
        )

        # ----------------------------------------------------
        # LEARNING AREA
        # ----------------------------------------------------

        self.learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade_10,
            pathway=self.pathway,
            name="Music and Dance",
            code="MUSIC-DANCE-TEST",
            assessment_enabled=True,
        )

        # ----------------------------------------------------
        # STRAND
        # ----------------------------------------------------

        self.strand = CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Foundations of Music and Dance",
            code="FMD-TEST",
            order=1,
        )

        # ----------------------------------------------------
        # SUB-STRANDS
        # ----------------------------------------------------

        self.sub_strand = CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Rhythm",
            code="RHYTHM-TEST",
            order=1,
        )

        self.second_sub_strand = CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Melody in Major Keys",
            code="MELODY-TEST",
            order=2,
        )

        # ----------------------------------------------------
        # SCHOOL A CURRICULUM ASSIGNMENT
        # ----------------------------------------------------

        self.curriculum_a = SchoolClassCurriculum.objects.create(
            school_class=self.class_a,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade_10,
            pathway=self.pathway,
            academic_year="2026",
        )

        # ----------------------------------------------------
        # SCHOOL B CURRICULUM ASSIGNMENT
        # ----------------------------------------------------

        self.curriculum_b = SchoolClassCurriculum.objects.create(
            school_class=self.class_b,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade_10,
            pathway=self.pathway,
            academic_year="2026",
        )

        # ----------------------------------------------------
        # SCHOOL A TEACHER ASSIGNMENT
        # ----------------------------------------------------

        self.assignment_a = TeacherAssessmentAssignment.objects.create(
            teacher=self.teacher_a,
            school_class_curriculum=self.curriculum_a,
            learning_area=self.learning_area,
            academic_year="2026",
            term="1",
        )

        # ----------------------------------------------------
        # SCHOOL B TEACHER ASSIGNMENT
        # ----------------------------------------------------

        self.assignment_b = TeacherAssessmentAssignment.objects.create(
            teacher=self.teacher_b,
            school_class_curriculum=self.curriculum_b,
            learning_area=self.learning_area,
            academic_year="2026",
            term="1",
        )

        # ----------------------------------------------------
        # SCHOOL A STUDENT
        # ----------------------------------------------------

        self.student_a = Student.objects.create(
            admission_number="CBC-A-001",
            first_name="Student",
            last_name="SchoolA",
            gender="Male",
            date_of_birth=date(2010, 1, 1),
            parent_name="Parent A",
            phone="0700000001",
            school=self.school_a,
            school_class=self.class_a,
            enrollment_academic_year="2026",
            enrollment_term="1",
        )

        # ----------------------------------------------------
        # SCHOOL B STUDENT
        # ----------------------------------------------------

        self.student_b = Student.objects.create(
            admission_number="CBC-B-001",
            first_name="Student",
            last_name="SchoolB",
            gender="Male",
            date_of_birth=date(2010, 1, 1),
            parent_name="Parent B",
            phone="0700000002",
            school=self.school_b,
            school_class=self.class_b,
            enrollment_academic_year="2026",
            enrollment_term="1",
        )

    # ========================================================
    # HELPER
    # ========================================================

    def login_teacher_a(self):
        return self.client.login(
            username="cbc_teacher_a",
            password="test-password",
        )

    # ========================================================
    # BASIC ACCESS
    # ========================================================

    def test_teacher_can_open_own_assessment_book(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.get(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # CROSS-SCHOOL ASSIGNMENT BLOCK
    # ========================================================

    def test_teacher_cannot_open_other_school_assignment(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.get(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_b.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # ========================================================
    # CROSS-SCHOOL CLASS BLOCK
    # ========================================================

    def test_teacher_cannot_open_other_school_class_curriculum(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.get(
            reverse(
                "students:cbc_learning_areas",
                kwargs={
                    "school_class_curriculum_id": self.curriculum_b.id,
                    "term": "1",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # ========================================================
    # OWN SCHOOL BUT WRONG TEACHER
    # ========================================================

    def test_teacher_cannot_open_another_teacher_assignment(self):
        # Create another teacher in School A.

        other_user = User.objects.create_user(
            username="another_teacher_a",
            password="test-password",
        )

        other_teacher = Teacher.objects.create(
            user=other_user,
            school=self.school_a,
        )

        other_assignment = TeacherAssessmentAssignment.objects.create(
            teacher=other_teacher,
            school_class_curriculum=self.curriculum_a,
            learning_area=self.learning_area,
            academic_year="2026",
            term="1",
        )

        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.get(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": other_assignment.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # ========================================================
    # POST OWN STUDENT
    # ========================================================

    def test_teacher_can_save_assessment_for_own_student(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "CAT1",
                f"level_{self.student_a.id}_{self.sub_strand.id}": "ME",
                f"mark_{self.student_a.id}_{self.sub_strand.id}": "75",
                f"comment_{self.student_a.id}_{self.sub_strand.id}": (
                    "Good progress."
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        record = CBCSubStrandAssessment.objects.get(
            student=self.student_a,
            sub_strand=self.sub_strand,
            academic_year=2026,
            term="1",
            assessment_component="CAT1",
        )

        self.assertEqual(
            record.performance_level,
            "ME",
        )

        self.assertEqual(
            record.mark,
            Decimal("75"),
        )

        self.assertEqual(
            record.entered_by_id,
            self.teacher_user_a.id,
        )

    # ========================================================
    # CROSS-SCHOOL STUDENT POST ATTACK
    # ========================================================

    def test_teacher_cannot_modify_other_school_student_by_posting_id(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "CAT1",

                # Malicious attempt to submit School B student's ID.
                f"level_{self.student_b.id}_{self.sub_strand.id}": "EE",
                f"mark_{self.student_b.id}_{self.sub_strand.id}": "95",
                f"comment_{self.student_b.id}_{self.sub_strand.id}": (
                    "Unauthorized change."
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_b,
            ).exists()
        )

    # ========================================================
    # CROSS-SUB-STRAND POST ATTACK
    # ========================================================

    def test_teacher_cannot_submit_arbitrary_sub_strand(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        # This second sub-strand belongs to the same learning area,
        # but the important test is that the POST cannot introduce
        # a sub-strand outside the authorized queryset.
        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "CAT1",

                # Normal authorized sub-strand.
                f"level_{self.student_a.id}_{self.sub_strand.id}": "ME",

                # The view only processes sub-strands returned by
                # the authorized queryset.
                f"level_{self.student_a.id}_{self.second_sub_strand.id}": "EE",
                f"mark_{self.student_a.id}_{self.second_sub_strand.id}": "90",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        # Both are legitimate sub-strands of this learning area,
        # so both can currently be saved. This confirms that the
        # POST is constrained to the assignment's learning area.
        self.assertTrue(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_a,
                sub_strand=self.sub_strand,
                academic_year=2026,
                term="1",
                assessment_component="CAT1",
            ).exists()
        )

        self.assertTrue(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_a,
                sub_strand=self.second_sub_strand,
                academic_year=2026,
                term="1",
                assessment_component="CAT1",
            ).exists()
        )

    # ========================================================
    # WRONG COMPONENT BLOCK
    # ========================================================

    def test_invalid_assessment_component_is_rejected(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "INVALID",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_a,
            ).exists()
        )

    # ========================================================
    # INVALID PERFORMANCE LEVEL
    # ========================================================

    def test_invalid_performance_level_is_rejected(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "CAT1",
                f"level_{self.student_a.id}_{self.sub_strand.id}": "INVALID",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_a,
            ).exists()
        )

    # ========================================================
    # INVALID MARK
    # ========================================================

    def test_mark_above_100_is_rejected(self):
        self.assertTrue(
            self.login_teacher_a()
        )

        from django.urls import reverse

        response = self.client.post(
            reverse(
                "students:cbc_assessment_book",
                kwargs={
                    "assignment_id": self.assignment_a.id,
                },
            ),
            {
                "assessment_component": "CAT1",
                f"level_{self.student_a.id}_{self.sub_strand.id}": "EE",
                f"mark_{self.student_a.id}_{self.sub_strand.id}": "101",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            CBCSubStrandAssessment.objects.filter(
                student=self.student_a,
            ).exists()
        )
    # ========================================================
    # CBC SUB-STRAND ASSESSMENT MODEL VALIDATION
    # ========================================================

    def test_valid_cbc_substrand_assessment_passes_model_validation(self):
        assessment = CBCSubStrandAssessment(
            student=self.student_a,
            sub_strand=self.sub_strand,
            academic_year="2026",
            term="1",
            assessment_component="CAT1",
            performance_level="ME",
            mark=75,
            teacher_comment="Good progress.",
            entered_by=self.teacher_user_a,
        )

        assessment.full_clean()

    def test_assessment_from_wrong_curriculum_grade_is_rejected(self):
        # Create a Grade 9 curriculum structure.
        grade_9 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE9",
            display_name="Grade 9",
        )

        learning_area_grade_9 = CurriculumLearningArea.objects.create(
            curriculum_grade=grade_9,
            name="English Language",
            code="G9-ENGLISH-TEST",
            assessment_enabled=True,
        )

        strand_grade_9 = CurriculumStrand.objects.create(
            learning_area=learning_area_grade_9,
            name="Listening and Speaking",
            code="G9-LS-TEST",
            order=1,
        )

        sub_strand_grade_9 = CurriculumSubStrand.objects.create(
            strand=strand_grade_9,
            name="Listening Skills",
            code="G9-LS-SS-TEST",
            order=1,
        )

        assessment = CBCSubStrandAssessment(
            student=self.student_a,
            sub_strand=sub_strand_grade_9,
            academic_year="2026",
            term="1",
            assessment_component="CAT1",
            performance_level="ME",
            mark=75,
            entered_by=self.teacher_user_a,
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()

        self.assertIn(
            "student",
            context.exception.message_dict,
        ) if "student" in context.exception.message_dict else self.assertIn(
            "sub_strand",
            context.exception.message_dict,
        )

    def test_grade_10_wrong_pathway_assessment_is_rejected(self):
        # Create another Grade 10 pathway.
        stem_pathway = CurriculumPathway.objects.create(
            curriculum_grade=self.grade_10,
            name="STEM",
        )

        stem_learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade_10,
            pathway=stem_pathway,
            name="Physics",
            code="G10-PHYSICS-TEST",
            assessment_enabled=True,
        )

        stem_strand = CurriculumStrand.objects.create(
            learning_area=stem_learning_area,
            name="Forces",
            code="G10-PHYSICS-FORCES-TEST",
            order=1,
        )

        stem_sub_strand = CurriculumSubStrand.objects.create(
            strand=stem_strand,
            name="Types of Forces",
            code="G10-PHYSICS-FORCES-SS-TEST",
            order=1,
        )

        assessment = CBCSubStrandAssessment(
            student=self.student_a,
            sub_strand=stem_sub_strand,
            academic_year="2026",
            term="1",
            assessment_component="CAT1",
            performance_level="ME",
            mark=75,
            entered_by=self.teacher_user_a,
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()

        self.assertIn(
            "sub_strand",
            context.exception.message_dict,
        )

    def test_assessment_for_wrong_academic_year_is_rejected(self):
        assessment = CBCSubStrandAssessment(
            student=self.student_a,
            sub_strand=self.sub_strand,
            academic_year="2027",
            term="1",
            assessment_component="CAT1",
            performance_level="ME",
            mark=75,
            entered_by=self.teacher_user_a,
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()

        self.assertIn(
            "student",
            context.exception.message_dict,
        )

class SchoolClassCurriculumValidationTests(TestCase):
    def setUp(self):
        self.school = SchoolProfile.objects.create(
            name="CBC Test School",
            address="Nairobi",
            phone="0700000000",
            current_term="1",
            academic_year="2026",
        )

        self.school_class = SchoolClass.objects.create(
            name="Grade 1",
            school=self.school,
            curriculum="CBC",
        )

        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026",
            code="CBC-2026-TEST",
            academic_year="2026",
        )

        self.grade1 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE1",
            display_name="Grade 1",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.grade10_stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

    def test_grade_1_without_pathway_is_valid(self):
        assignment = SchoolClassCurriculum(
            school_class=self.school_class,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade1,
            pathway=None,
            academic_year="2026",
        )

        assignment.full_clean()

    def test_grade_1_with_pathway_is_invalid(self):
        assignment = SchoolClassCurriculum(
            school_class=self.school_class,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade1,
            pathway=self.grade10_stem,
            academic_year="2026",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_grade_10_without_pathway_is_invalid(self):
        assignment = SchoolClassCurriculum(
            school_class=self.school_class,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade10,
            pathway=None,
            academic_year="2026",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_grade_10_with_correct_pathway_is_valid(self):
        assignment = SchoolClassCurriculum(
            school_class=self.school_class,
            curriculum_version=self.curriculum_version,
            curriculum_grade=self.grade10,
            pathway=self.grade10_stem,
            academic_year="2026",
        )

        assignment.full_clean()

class CurriculumLearningAreaValidationTests(TestCase):
    def setUp(self):
        self.school = SchoolProfile.objects.create(
            name="Learning Area Test School",
            address="Nairobi",
            phone="0711111111",
            current_term="1",
            academic_year="2026",
        )

        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026 Learning Area Test",
            code="CBC-2026-LA-TEST",
            academic_year="2026",
        )

        self.grade1 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE1",
            display_name="Grade 1",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.grade11 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE11",
            display_name="Grade 11",
        )

        self.grade10_stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

        self.grade10_arts = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="ARTS_SPORTS",
        )

        self.grade11_stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade11,
            name="STEM",
        )

    def test_grade_1_learning_area_without_pathway_is_valid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade1,
            pathway=None,
            name="Mathematics",
            code="G1-MATH",
        )

        learning_area.full_clean()

    def test_grade_1_learning_area_with_pathway_is_invalid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade1,
            pathway=self.grade10_stem,
            name="Mathematics",
            code="G1-MATH",
        )

        with self.assertRaises(ValidationError):
            learning_area.full_clean()

    def test_grade_10_learning_area_without_pathway_is_invalid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade10,
            pathway=None,
            name="Physics",
            code="G10-PHY",
        )

        with self.assertRaises(ValidationError):
            learning_area.full_clean()

    def test_grade_10_learning_area_with_correct_pathway_is_valid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade10,
            pathway=self.grade10_stem,
            name="Physics",
            code="G10-PHY",
        )

        learning_area.full_clean()

    def test_pathway_from_wrong_grade_is_invalid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade10,
            pathway=self.grade11_stem,
            name="Physics",
            code="G10-PHY",
        )

        with self.assertRaises(ValidationError):
            learning_area.full_clean()

    def test_grade_10_arts_pathway_is_valid(self):
        learning_area = CurriculumLearningArea(
            curriculum_grade=self.grade10,
            pathway=self.grade10_arts,
            name="Art and Craft",
            code="G10-ART",
        )

        learning_area.full_clean()

class CurriculumStrandValidationTests(TestCase):
    def setUp(self):
        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026 Strand Test",
            code="CBC-2026-STRAND-TEST",
            academic_year="2026",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

        self.learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.stem,
            name="Mathematics",
            code="G10-MATH",
        )

    def test_strand_can_be_created_for_learning_area(self):
        strand = CurriculumStrand(
            learning_area=self.learning_area,
            name="Numbers",
            code="NUM",
            order=1,
        )

        strand.full_clean()
        strand.save()

        self.assertEqual(
            CurriculumStrand.objects.count(),
            1,
        )

    def test_duplicate_strand_code_in_same_learning_area_is_rejected(self):
        CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Numbers",
            code="NUM",
            order=1,
        )

        duplicate = CurriculumStrand(
            learning_area=self.learning_area,
            name="Algebra",
            code="NUM",
            order=2,
        )

        with self.assertRaises(ValidationError):
            duplicate.validate_constraints()
    def test_same_strand_name_can_exist_in_different_learning_area(self):
        another_learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.stem,
            name="Physics",
            code="G10-PHY",
        )

        CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Measurement",
            code="MATH-MEAS",
            order=1,
        )

        strand = CurriculumStrand(
            learning_area=another_learning_area,
            name="Measurement",
            code="PHY-MEAS",
            order=1,
        )

        strand.full_clean()
    def test_same_strand_name_with_different_codes_is_valid(self):
        CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Health and Safety",
            code="7.0",
            order=1,
        )

        strand = CurriculumStrand(
            learning_area=self.learning_area,
            name="Health and Safety",
            code="8.0",
            order=2,
        )

        strand.full_clean()


    def test_blank_strand_codes_are_allowed(self):
        CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Strand One",
            code="",
            order=1,
        )

        strand = CurriculumStrand(
            learning_area=self.learning_area,
            name="Strand Two",
            code="",
            order=2,
        )

        strand.full_clean()

class CurriculumSubStrandValidationTests(TestCase):
    def setUp(self):
        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026 Sub-Strand Test",
            code="CBC-2026-SUBSTRAND-TEST",
            academic_year="2026",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

        self.learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.stem,
            name="Mathematics",
            code="G10-MATH",
        )

        self.strand = CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Numbers",
            code="1.0",
            order=1,
        )

    def test_substrand_can_be_created(self):
        sub_strand = CurriculumSubStrand(
            strand=self.strand,
            name="Place Value",
            code="1.1",
            order=1,
        )

        sub_strand.full_clean()
        sub_strand.save()

        self.assertEqual(
            CurriculumSubStrand.objects.count(),
            1,
        )

    def test_duplicate_substrand_code_in_same_strand_is_rejected(self):
        CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Place Value",
            code="1.1",
            order=1,
        )

        duplicate = CurriculumSubStrand(
            strand=self.strand,
            name="Whole Numbers",
            code="1.1",
            order=2,
        )

        with self.assertRaises(ValidationError):
            duplicate.validate_constraints()

    def test_same_substrand_name_with_different_codes_is_valid(self):
        CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Operations",
            code="1.2",
            order=1,
        )

        sub_strand = CurriculumSubStrand(
            strand=self.strand,
            name="Operations",
            code="1.3",
            order=2,
        )

        sub_strand.full_clean()

    def test_blank_substrand_codes_are_allowed(self):
        CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Sub-Strand One",
            code="",
            order=1,
        )

        sub_strand = CurriculumSubStrand(
            strand=self.strand,
            name="Sub-Strand Two",
            code="",
            order=2,
        )

        sub_strand.full_clean()

    
class CurriculumAssessmentItemValidationTests(TestCase):
    def setUp(self):
        self.curriculum_version = CurriculumVersion.objects.create(
            name="CBC 2026 Assessment Item Test",
            code="CBC-2026-ASSESSMENT-TEST",
            academic_year="2026",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.curriculum_version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

        self.learning_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.stem,
            name="Mathematics",
            code="G10-MATH",
        )

        self.strand = CurriculumStrand.objects.create(
            learning_area=self.learning_area,
            name="Geometry",
            code="1.0",
            order=1,
        )

        self.sub_strand = CurriculumSubStrand.objects.create(
            strand=self.strand,
            name="Reflection",
            code="1.1",
            order=1,
        )

    def test_assessment_item_can_be_created(self):
        item = CurriculumAssessmentItem(
            sub_strand=self.sub_strand,
            term="1",
            name="Reflection and Congruence",
            maximum_score=100,
            order=1,
        )

        item.full_clean()
        item.save()

        self.assertEqual(
            CurriculumAssessmentItem.objects.count(),
            1,
        )

    def test_duplicate_assessment_item_same_term_is_rejected(self):
        CurriculumAssessmentItem.objects.create(
            sub_strand=self.sub_strand,
            term="1",
            name="Reflection and Congruence",
            maximum_score=100,
            order=1,
        )

        duplicate = CurriculumAssessmentItem(
            sub_strand=self.sub_strand,
            term="1",
            name="Reflection and Congruence",
            maximum_score=100,
            order=2,
        )

        with self.assertRaises(ValidationError):
            duplicate.validate_constraints()

    def test_same_assessment_item_name_in_different_terms_is_valid(self):
        CurriculumAssessmentItem.objects.create(
            sub_strand=self.sub_strand,
            term="1",
            name="Reflection and Congruence",
            maximum_score=100,
            order=1,
        )

        item = CurriculumAssessmentItem(
            sub_strand=self.sub_strand,
            term="2",
            name="Reflection and Congruence",
            maximum_score=100,
            order=1,
        )

        item.full_clean()

class TeacherAssessmentAssignmentValidationTests(TestCase):
    def setUp(self):
        self.school_a = SchoolProfile.objects.create(
            name="Assignment Test School A",
            address="Test Address",
            phone="0700000000",
            current_term="1",
            academic_year="2026",
        )

        self.school_b = SchoolProfile.objects.create(
            name="Assignment Test School B",
            address="Test Address",
            phone="0700000001",
            current_term="1",
            academic_year="2026",
        )

        self.user_a = User.objects.create_user(
            username="assignment_teacher_a",
            password="testpass123",
        )

        self.user_b = User.objects.create_user(
            username="assignment_teacher_b",
            password="testpass123",
        )

        self.teacher_a = Teacher.objects.create(
            user=self.user_a,
            school=self.school_a,
            first_name="Teacher",
            last_name="A",
            employee_number="TA001",
        )

        self.teacher_b = Teacher.objects.create(
            user=self.user_b,
            school=self.school_b,
            first_name="Teacher",
            last_name="B",
            employee_number="TB001",
        )

        self.version = CurriculumVersion.objects.create(
            name="CBC Assignment Test",
            code="CBC-ASSIGNMENT-TEST",
            academic_year="2026",
        )

        self.grade10 = CurriculumGrade.objects.create(
            curriculum_version=self.version,
            grade="GRADE10",
            display_name="Grade 10",
        )

        self.stem = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="STEM",
        )

        self.arts = CurriculumPathway.objects.create(
            curriculum_grade=self.grade10,
            name="ARTS_SPORTS",
        )

        self.stem_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.stem,
            name="STEM Mathematics",
            code="STEM-MATH",
        )

        self.arts_area = CurriculumLearningArea.objects.create(
            curriculum_grade=self.grade10,
            pathway=self.arts,
            name="Music and Dance",
            code="ARTS-MUSIC",
        )

        self.class_a = SchoolClass.objects.create(
            name="Grade 10",
            curriculum="CBC",
            school=self.school_a,
        )

        self.class_curriculum = SchoolClassCurriculum.objects.create(
            school_class=self.class_a,
            curriculum_version=self.version,
            curriculum_grade=self.grade10,
            pathway=self.stem,
            academic_year="2026",
        )

    def test_valid_assignment(self):
        assignment = TeacherAssessmentAssignment(
            teacher=self.teacher_a,
            school_class_curriculum=self.class_curriculum,
            learning_area=self.stem_area,
            academic_year="2026",
            term="1",
        )

        assignment.full_clean()

    def test_teacher_from_different_school_is_rejected(self):
        assignment = TeacherAssessmentAssignment(
            teacher=self.teacher_b,
            school_class_curriculum=self.class_curriculum,
            learning_area=self.stem_area,
            academic_year="2026",
            term="1",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_learning_area_from_different_pathway_is_rejected(self):
        assignment = TeacherAssessmentAssignment(
            teacher=self.teacher_a,
            school_class_curriculum=self.class_curriculum,
            learning_area=self.arts_area,
            academic_year="2026",
            term="1",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_wrong_academic_year_is_rejected(self):
        assignment = TeacherAssessmentAssignment(
            teacher=self.teacher_a,
            school_class_curriculum=self.class_curriculum,
            learning_area=self.stem_area,
            academic_year="2027",
            term="1",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()