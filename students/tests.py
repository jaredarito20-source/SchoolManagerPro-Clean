from datetime import date
from decimal import Decimal

from django.test import TestCase

from students.models import (
    SchoolProfile,
    SchoolClass,
    Student,
    StudentAcademicEnrollment,
    SchoolUser,
    FeeStructure,
    FeeLedgerEntry,
    FeePayment,
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
            reverse("add_student"),
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