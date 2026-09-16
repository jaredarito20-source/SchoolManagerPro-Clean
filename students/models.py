from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib import admin





class SchoolProfile(models.Model):
    name = models.CharField(max_length=200, unique=True)
    motto = models.CharField(max_length=300, blank=True)
    address = models.CharField(max_length=300)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    website = models.CharField(max_length=100, blank=True)
    

    current_term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=20)
    principal_name = models.CharField(max_length=100, blank=True)

    principal_signature = models.ImageField(
        upload_to="signatures/",
        blank=True,
        null=True,
    )

    logo = models.ImageField(
        upload_to="school_logos/",
        blank=True,
        null=True,
    )
    CURRICULUM_SYSTEM_CHOICES = [
        ("CBC", "CBC"),
        ("8-4-4", "8-4-4"),
        ("BOTH", "Both CBC & 8-4-4"),
    ]

    curriculum_system = models.CharField(
        max_length=10,
        choices=CURRICULUM_SYSTEM_CHOICES,
        default="CBC",
    )
    closing_date = models.DateField(null=True, blank=True)
    opening_date = models.DateField(null=True, blank=True)
    school_stamp = models.ImageField(
        upload_to="school/",
        blank=True,
        null=True,
)
    

    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="teacher_profile",
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="teachers",
    )

    employee_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class SchoolClass(models.Model):

    CURRICULUM_CHOICES = [
        ("CBC", "CBC"),
        ("8-4-4", "8-4-4"),
    ]

    name = models.CharField(max_length=50)

    curriculum = models.CharField(
        max_length=10,
        choices=CURRICULUM_CHOICES,
        default="CBC",
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="classes",
    )

    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_teacher_for",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_class_per_school",
            )
        ]

    def __str__(self):
        return self.name

class Student(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="students",
    )

    admission_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=10,
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
        ],
    )

    date_of_birth = models.DateField()

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    enrollment_academic_year = models.CharField(
        max_length=20,
        default="",
    )

    enrollment_term = models.CharField(
        max_length=20,
        default="",
    )

    parent_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    parent_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )
    photo = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True,
    )

    def total_fee(self):
        fee = FeeStructure.objects.filter(
            school_class=self.school_class
        ).first()

        if fee:
            return fee.total_fee

        return 0
    def total_paid(self):
        total = self.feepayment_set.aggregate(
            total=Sum("amount")
        )["total"]

        return total or 0

    def balance(self):
        return self.total_fee() - self.total_paid()

    def payment_status(self):
        if self.total_paid() == 0:
            return "Not Paid"

        if self.balance() <= 0:
            return "Cleared"

        return "Partial"


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "admission_number"],
                name="unique_admission_number_per_school",
            )
        ]


    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subjects",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="subjects",
        null=True,
        blank=True,
    )
    

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
    )

    def __str__(self):
        if self.school_class:
            return f"{self.name} - {self.school_class.name}"
        return self.name
class Exam(models.Model):
    name = models.CharField(max_length=100)

    term = models.CharField(max_length=50)

    year = models.IntegerField()

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="exams",
        null=True,
        blank=True,
    )

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    def __str__(self):
        return f"{self.name} - {self.term} {self.year}"
class MarkSubmission(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_mark_batches",
    )

    class Meta:
        unique_together = (
            "school_class",
            "subject",
            "exam",
        )

    def __str__(self):
        return f"{self.school_class} - {self.subject} - {self.exam}"
    
class Mark(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
    )

    submission = models.ForeignKey(
        MarkSubmission,
        on_delete=models.CASCADE,
        related_name="marks",
        null=True,
        blank=True,
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    grade = models.CharField(
        max_length=2,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "exam"],
                name="unique_student_subject_exam",
            )
        ]
        ordering = [
            "student__school_class",
            "student__admission_number",
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.subject} - "
            f"{self.exam}"
        )




class SchoolUser(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="school_user",
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="users",
    )

    def __str__(self):
        return f"{self.user.username} - {self.school.name}"


class FeeStructure(models.Model):

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=20,
    )

    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    activity_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    exam_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    other_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school_class",
                    "academic_year",
                    "term",
                ],
                name="unique_fee_structure_per_class_year_term",
            )
        ]

    @property
    def total_fee(self):
        return (
            self.tuition_fee
            + self.activity_fee
            + self.exam_fee
            + self.other_fee
        )

    def __str__(self):
        return f"{self.school_class.name} Fee Structure"
class FeePayment(models.Model):

    PAYMENT_METHODS = [
        ("Cash", "Cash"),
        ("M-Pesa", "M-Pesa"),
        ("Bank", "Bank"),
        ("Cheque", "Cheque"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_date = models.DateField()

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="Cash",
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=20,
    )

    is_voided = models.BooleanField(
        default=False,
    )

    void_reason = models.TextField(
        blank=True,
    )

    voided_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    voided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voided_fee_payments",
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.amount}"
        )

class FeeLedgerEntry(models.Model):

    TRANSACTION_TYPES = [
        ("OPENING_BALANCE", "Opening Balance"),
        ("FEE_CHARGE", "Fee Charge"),
        ("PAYMENT", "Payment"),
        ("CREDIT", "Credit"),
        ("ADJUSTMENT", "Adjustment"),
        ("REVERSAL", "Reversal"),
        ("CARRY_FORWARD", "Carry Forward"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=20,
    )

    transaction_date = models.DateField()

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
    )

    description = models.CharField(
        max_length=255,
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    fee_payment = models.ForeignKey(
        FeePayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries",
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries_recorded",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "transaction_date",
            "id",
        ]

        indexes = [
            models.Index(
                fields=["student", "transaction_date"],
                name="students_fe_student_5be1e5_idx",
            ),
            models.Index(
                fields=["school", "academic_year", "term"],
                name="students_fe_school__6d4a67_idx",
            ),
        ]


class StudentAcademicEnrollment(models.Model):

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=20,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.PROTECT,
        related_name="student_enrollments",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="academic_enrollments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "academic_year",
                    "term",
                ],
                name="unique_student_academic_period",
            )
        ]

class Attendance(models.Model):

    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Excused", "Excused"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Present",
    )

    remarks = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.date} - "
            f"{self.status}"
        )


class ExamTimetable(models.Model):

    DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    exam_date = models.DateField()

    day = models.CharField(
        max_length=15,
        choices=DAYS,
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    room = models.CharField(
        max_length=100,
        blank=True,
    )

    supervisor = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.school_class} - "
            f"{self.subject} - "
            f"{self.exam_date}"
        )
class InventoryCategory(models.Model):
    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="inventory_categories",
    )

    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_inventory_category_per_school",
            )
        ]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )

    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )

    name = models.CharField(max_length=150)

    quantity = models.PositiveIntegerField(default=0)

    unit = models.CharField(
        max_length=30,
        default="Pieces",
    )

    minimum_stock = models.PositiveIntegerField(default=5)

    location = models.CharField(
        max_length=100,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_inventory_item_per_school",
            )
        ]

    def __str__(self):
        return self.name


class StockTransaction(models.Model):

    TRANSACTION_TYPES = [
        ("RECEIVED", "Received"),
        ("ISSUED", "Issued"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="stock_transactions",
    )

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
    )

    quantity = models.PositiveIntegerField()

    transaction_date = models.DateField(
        auto_now_add=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.item.name} - {self.transaction_type}"
class Book(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="library_books",
    )

    title = models.CharField(max_length=200)

    author = models.CharField(max_length=200)

    isbn = models.CharField(
        max_length=30,
    )

    category = models.CharField(
        max_length=100,
    )

    publisher = models.CharField(
        max_length=200,
        blank=True,
    )

    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    copies = models.PositiveIntegerField(
        default=1,
    )

    available_copies = models.PositiveIntegerField(
        default=1,
    )

    shelf = models.CharField(
        max_length=100,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "isbn"],
                name="unique_book_isbn_per_school",
            )
        ]

    def __str__(self):
        return self.title


class BorrowBook(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="library_borrowings",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
    )

    borrow_date = models.DateField()

    due_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True,
    )

    STATUS = (
        ("Borrowed", "Borrowed"),
        ("Returned", "Returned"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Borrowed",
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.student} - {self.book}"

class SalaryStructure(models.Model):
    teacher = models.OneToOneField(
        Teacher,
        on_delete=models.CASCADE,
        related_name="salary_structure",
    )

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)

    house_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    medical_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    transport_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    other_allowance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    paye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    sha = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    nssf = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    other_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    bank_name = models.CharField(max_length=100, blank=True)

    account_number = models.CharField(
        max_length=50,
        blank=True,
    )

    def gross_salary(self):
        return (
            self.basic_salary
            + self.house_allowance
            + self.medical_allowance
            + self.transport_allowance
            + self.other_allowance
        )

    def total_deductions(self):
        return (
            self.paye
            + self.sha
            + self.nssf
            + self.other_deductions
        )

    def net_salary(self):
        return self.gross_salary() - self.total_deductions()

    def __str__(self):
        return str(self.teacher)


class Payroll(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payrolls",
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )

    year = models.IntegerField()

    month = models.CharField(
        max_length=20
    )

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    paye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    sha = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    nssf = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    other_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    generated_on = models.DateField(
        auto_now_add=True,
    )

    class Meta:

        unique_together = (
            "teacher",
            "month",
            "year",
        )

    def __str__(self):

        return (
            f"{self.teacher} - "
            f"{self.month} "
            f"{self.year}"
        )
class Driver(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    national_id = models.CharField(
        max_length=20,
        unique=True,
    )

    license_number = models.CharField(
        max_length=50,
        unique=True,
    )

    license_expiry = models.DateField()

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
class Vehicle(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    registration_number = models.CharField(
        max_length=30,
        unique=True,
    )

    vehicle_name = models.CharField(
        max_length=100,
    )

    make = models.CharField(
        max_length=100,
        blank=True,
    )

    capacity = models.PositiveIntegerField()

    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Maintenance", "Maintenance"),
        ],
        default="Active",
    )

    def __str__(self):
        return f"{self.registration_number} - {self.vehicle_name}"

class TransportRoute(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transport_routes",
    )

    route_name = models.CharField(
        max_length=100
    )

    start_point = models.CharField(
        max_length=150
    )

    end_point = models.CharField(
        max_length=150
    )

    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routes",
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transport_routes",
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.route_name

class StudentTransport(models.Model):

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="transport",
    )

    route = models.ForeignKey(
        TransportRoute,
        on_delete=models.CASCADE,
        related_name="students",
    )

    pickup_point = models.CharField(
        max_length=150,
        blank=True,
    )

    dropoff_point = models.CharField(
        max_length=150,
        blank=True,
    )

    active = models.BooleanField(
        default=True,
    )

    assigned_date = models.DateField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.student} - {self.route}"
# hostels


class DisciplineCategory(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="discipline_categories",
    )

    def __str__(self):
        return self.name


class DisciplineCase(models.Model):

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Closed", "Closed"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="discipline_cases",
    )

    category = models.ForeignKey(
        DisciplineCategory,
        on_delete=models.PROTECT,
    )

    reported_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
    )

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="discipline_cases",
    )

    incident_date = models.DateField()

    description = models.TextField()

    action_taken = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Open",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.student} - {self.category}"
class Medication(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=0,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


class MedicalVisit(models.Model):

    STATUS_CHOICES = [
        ("Under Treatment", "Under Treatment"),
        ("Recovered", "Recovered"),
        ("Referred", "Referred"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="medical_visits",
    )

    attended_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_cases",
    )

    visit_date = models.DateField()

    complaint = models.CharField(
        max_length=200,
    )

    diagnosis = models.TextField(
        blank=True,
    )

    treatment = models.TextField(
        blank=True,
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="Under Treatment",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.student} - {self.visit_date}"




class HospitalReferral(models.Model):

    visit = models.OneToOneField(
        MedicalVisit,
        on_delete=models.CASCADE,
        related_name="referral",
    )

    hospital_name = models.CharField(
        max_length=150,
    )

    referral_reason = models.TextField()

    parent_notified = models.BooleanField(
        default=False,
    )

    referral_date = models.DateField()

    def __str__(self):
        return f"{self.visit.student} - {self.hospital_name}"

class Prescription(models.Model):

    medical_visit = models.ForeignKey(
        MedicalVisit,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )

    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
    )

    dosage = models.CharField(
        max_length=100,
    )

    frequency = models.CharField(
        max_length=100,
        help_text="Example: Twice Daily",
    )

    duration = models.CharField(
        max_length=100,
        help_text="Example: 5 Days",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    instructions = models.TextField(
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.medical_visit.student} - "
            f"{self.medication.name}"
        )


class Homework(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="homework",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="homework",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="homework",
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="homework",
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    date_given = models.DateField(
        auto_now_add=True
    )

    due_date = models.DateField()

    attachment = models.FileField(
        upload_to="homework/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.school_class} - {self.title}"
class HomeworkSubmission(models.Model):

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="homework_submissions",
    )

    submission_file = models.FileField(
        upload_to="homework_submissions/",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    teacher_comment = models.TextField(
        blank=True,
    )

    graded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    graded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_homework_submissions",
    )

    def __str__(self):
        return f"{self.student} - {self.homework}"
class Period(models.Model):
    name = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_break = models.BooleanField(default=False)

    order = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class SchoolDay(models.Model):

    DAYS = [

        ("Monday","Monday"),
        ("Tuesday","Tuesday"),
        ("Wednesday","Wednesday"),
        ("Thursday","Thursday"),
        ("Friday","Friday"),
        ("Saturday","Saturday"),

    ]

    name = models.CharField(
        max_length=20,
        choices=DAYS,
        unique=True,
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SubjectRequirement(models.Model):

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    lessons_per_week = models.PositiveIntegerField()

    double_lessons = models.PositiveIntegerField(default=0)

    def __str__(self):

        return f"{self.school_class} - {self.subject}"

class TeacherAvailability(models.Model):

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
    )

    day = models.ForeignKey(
        SchoolDay,
        on_delete=models.CASCADE,
    )

    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
    )

    available = models.BooleanField(default=True)

class Timetable(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="timetables",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    day = models.ForeignKey(
        SchoolDay,
        on_delete=models.CASCADE,
    )

    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
    )

    locked = models.BooleanField(
        default=False
    )

    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "school",
                    "school_class",
                    "day",
                    "period",
                ],
                name="unique_school_class_period",
            ),

            models.UniqueConstraint(
                fields=[
                    "school",
                    "teacher",
                    "day",
                    "period",
                ],
                name="unique_school_teacher_period",
            ),

        ]

    def __str__(self):
        return (
            f"{self.school_class} - "
            f"{self.day} - "
            f"{self.period} - "
            f"{self.subject}"
        )
class HostelBlock(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="hostel_blocks",
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    capacity = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_hostel_block_per_school",
            )
        ]

    def __str__(self):
        return self.name

class HostelRoom(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="hostel_rooms",
    )

    hostel_block = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="rooms",
    )

    room_number = models.CharField(
        max_length=50,
    )

    capacity = models.PositiveIntegerField(
        default=4,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "hostel_block", "room_number"],
                name="unique_hostel_room_per_block",
            )
        ]

    def __str__(self):
        return f"{self.hostel_block.name} - Room {self.room_number}"

class HostelBed(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="hostel_beds",
    )

    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="beds",
    )

    bed_number = models.CharField(
        max_length=50,
    )

    is_occupied = models.BooleanField(
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "room", "bed_number"],
                name="unique_hostel_bed_per_room",
            )
        ]

    def __str__(self):
        return f"{self.room} - Bed {self.bed_number}"

class StudentHostel(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="student_hostel_allocations",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="hostel_allocations",
    )

    hostel_block = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="student_allocations",
        null=True,
        blank=True,
    )

    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="student_allocations",
    )

    bed = models.ForeignKey(
        HostelBed,
        on_delete=models.CASCADE,
        related_name="student_allocations",
        null=True,
        blank=True,
    )

    admission_date = models.DateField()
    null=True,
    blank=True,

    leaving_date = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.student} - {self.hostel_block} - {self.room}"

class HostelTransfer(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="hostel_transfers",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="hostel_transfers",
    )

    from_hostel = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="transfers_from",
        null=True,
        blank=True,
    )

    from_room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="transfers_from",
        null=True,
        blank=True,
    )

    from_bed = models.ForeignKey(
        HostelBed,
        on_delete=models.CASCADE,
        related_name="transfers_from",
        null=True,
        blank=True,
    )

    to_hostel = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="transfers_to",
        null=True,
        blank=True,
    )

    to_room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="transfers_to",
        null=True,
        blank=True,
    )

    to_bed = models.ForeignKey(
        HostelBed,
        on_delete=models.CASCADE,
        related_name="transfers_to",
        null=True,
        blank=True,
    )

    transfer_date = models.DateField()

    reason = models.TextField(
        blank=True,
    )

    transferred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hostel_transfers_made",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.student} - Hostel Transfer"

class HostelWarden(models.Model):

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="hostel_wardens",
    )

    hostel_block = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="wardens",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hostel_warden_assignments",
    )

    name = models.CharField(
        max_length=200,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    assigned_date = models.DateField(
        auto_now_add=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    def __str__(self):
        return f"{self.name} - {self.hostel_block}"

class SMSWallet(models.Model):
    school = models.OneToOneField(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="sms_wallet",
    )

    balance = models.PositiveIntegerField(
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.school.name} - {self.balance} SMS"

class SMSTransaction(models.Model):

    TRANSACTION_TYPES = [
        ("purchase", "Purchase"),
        ("send", "SMS Sent"),
        ("refund", "Refund"),
        ("adjustment", "Adjustment"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="sms_transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
    )

    quantity = models.IntegerField()

    balance_after = models.IntegerField()

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.school.name} - "
            f"{self.transaction_type} - "
            f"{self.quantity}"
        )


class SMSMessage(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="sms_messages",
    )

    recipient = models.CharField(
        max_length=20
    )

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    sms_count = models.PositiveIntegerField(
        default=1
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_sms",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.recipient} - {self.status}"

class SMSPackage(models.Model):

    name = models.CharField(max_length=100)

    sms_count = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.sms_count:,} SMS - KSh {self.price}"

    class Meta:
        ordering = ["price"]

class SMSPurchase(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Cancelled", "Cancelled"),
    ]

    school = models.ForeignKey(
        SchoolProfile,
        on_delete=models.CASCADE,
        related_name="sms_purchases",
    )

    package = models.ForeignKey(
        SMSPackage,
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    sms_count = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_purchases_created",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.school.name} - "
            f"{self.package.name} - "
            f"{self.status}"
        )


class MpesaTransaction(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="mpesa_transactions",
    )

    phone_number = models.CharField(
        max_length=20
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    merchant_request_id = models.CharField(
        max_length=100,
        blank=True,
    )

    checkout_request_id = models.CharField(
        max_length=100,
        unique=True,
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        blank=True,
    )

    transaction_date = models.CharField(
        max_length=30,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    result_code = models.IntegerField(
        null=True,
        blank=True,
    )

    result_description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.amount} - "
            f"{self.status}"
        )

# ============================================================
# CBC CURRICULUM AND ASSESSMENT MODELS
# ============================================================

class CurriculumVersion(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Example: CBC 2026"
    )
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Example: CBC-2026"
    )
    academic_year = models.CharField(
        max_length=20,
        help_text="Academic year this curriculum version applies from."
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-academic_year", "-id"]

    def __str__(self):
        return self.name


class CurriculumGrade(models.Model):
    GRADE_CHOICES = [
        ("PP1", "PP1"),
        ("PP2", "PP2"),
        ("GRADE1", "Grade 1"),
        ("GRADE2", "Grade 2"),
        ("GRADE3", "Grade 3"),
        ("GRADE4", "Grade 4"),
        ("GRADE5", "Grade 5"),
        ("GRADE6", "Grade 6"),
        ("GRADE7", "Grade 7"),
        ("GRADE8", "Grade 8"),
        ("GRADE9", "Grade 9"),
        ("GRADE10", "Grade 10"),
        ("GRADE11", "Grade 11"),
        ("GRADE12", "Grade 12"),
    ]

    curriculum_version = models.ForeignKey(
        CurriculumVersion,
        on_delete=models.CASCADE,
        related_name="grades",
    )

    grade = models.CharField(
        max_length=20,
        choices=GRADE_CHOICES,
    )

    display_name = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum_version", "grade"],
                name="unique_curriculum_grade_version",
            )
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.curriculum_version} - {self.display_name}"


class CurriculumPathway(models.Model):
    PATHWAY_CHOICES = [
        ("ARTS_SPORTS", "Arts & Sports"),
        ("STEM", "STEM"),
        ("SOCIAL_SCIENCES", "Social Sciences"),
    ]

    curriculum_grade = models.ForeignKey(
        CurriculumGrade,
        on_delete=models.CASCADE,
        related_name="pathways",
    )

    name = models.CharField(
        max_length=30,
        choices=PATHWAY_CHOICES,
    )

    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum_grade", "name"],
                name="unique_grade_pathway",
            )
        ]

    def __str__(self):
        return f"{self.curriculum_grade} - {self.get_name_display()}"


class CurriculumLearningArea(models.Model):
    curriculum_grade = models.ForeignKey(
        CurriculumGrade,
        on_delete=models.CASCADE,
        related_name="learning_areas",
    )

    # NULL means this is a normal learning area for PP1–Grade 9.
    # Grade 10–12 learning areas must belong to a pathway.
    pathway = models.ForeignKey(
        CurriculumPathway,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="learning_areas",
    )

    name = models.CharField(max_length=150)

    code = models.CharField(max_length=50)

    description = models.TextField(blank=True)

    assessment_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

        constraints = [
            # For PP1–Grade 9, pathway is NULL.
            # Prevent duplicate learning areas within a grade.
            models.UniqueConstraint(
                fields=[
                    "curriculum_grade",
                    "name",
                ],
                condition=models.Q(pathway__isnull=True),
                name="unique_lower_grade_learning_area",
            ),

            # For Grade 10–12, the same learning area name can exist
            # under different pathways, but not twice within one pathway.
            models.UniqueConstraint(
                fields=[
                    "curriculum_grade",
                    "pathway",
                    "name",
                ],
                name="unique_pathway_learning_area",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.curriculum_grade_id:
            grade_code = self.curriculum_grade.grade

            lower_grades = {
                "PP1",
                "PP2",
                "GRADE1",
                "GRADE2",
                "GRADE3",
                "GRADE4",
                "GRADE5",
                "GRADE6",
                "GRADE7",
                "GRADE8",
                "GRADE9",
            }

            senior_grades = {
                "GRADE10",
                "GRADE11",
                "GRADE12",
            }

            # PP1–Grade 9 must NOT have a pathway.
            if grade_code in lower_grades and self.pathway_id:
                errors["pathway"] = (
                    "PP1 to Grade 9 learning areas do not use "
                    "CBC pathways."
                )

            # Grade 10–12 MUST have a pathway.
            if grade_code in senior_grades and not self.pathway_id:
                errors["pathway"] = (
                    "Grade 10 to Grade 12 learning areas must "
                    "belong to a CBC pathway."
                )

        # A pathway must belong to this exact curriculum grade.
        if (
            self.pathway_id
            and self.curriculum_grade_id
            and self.pathway.curriculum_grade_id
            != self.curriculum_grade_id
        ):
            errors["pathway"] = (
                "The selected pathway does not belong to the "
                "selected curriculum grade."
            )

        # The grade itself belongs to a curriculum version.
        # Therefore the pathway/learning-area relationship remains
        # inside the same curriculum version through the grade.

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        if self.pathway:
            return (
                f"{self.name} "
                f"({self.pathway.get_name_display()})"
            )

        return self.name

class CurriculumStrand(models.Model):
    learning_area = models.ForeignKey(
        CurriculumLearningArea,
        on_delete=models.CASCADE,
        related_name="strands",
    )

    name = models.CharField(max_length=200)

    code = models.CharField(
        max_length=50,
        blank=True,
    )

    order = models.PositiveIntegerField(default=1)

    description = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "learning_area",
                    "code",
                ],
                condition=~models.Q(code=""),
                name="unique_strand_code_per_learning_area",
            ),
        ]
    def __str__(self):
        return f"{self.learning_area.name} - {self.name}"

class CurriculumSubStrand(models.Model):
    strand = models.ForeignKey(
        CurriculumStrand,
        on_delete=models.CASCADE,
        related_name="sub_strands",
    )

    name = models.CharField(max_length=250)

    code = models.CharField(
        max_length=50,
        blank=True,
    )

    order = models.PositiveIntegerField(default=1)

    description = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "strand",
                    "code",
                ],
                condition=~models.Q(code=""),
                name="unique_substrand_code_per_strand",
            ),
        ]

    def __str__(self):
        return f"{self.strand.name} - {self.name}"
class CurriculumAssessmentItem(models.Model):
    TERM_CHOICES = [
        ("1", "Term 1"),
        ("2", "Term 2"),
        ("3", "Term 3"),
    ]

    sub_strand = models.ForeignKey(
        CurriculumSubStrand,
        on_delete=models.PROTECT,
        related_name="assessment_items",
    )

    term = models.CharField(
        max_length=20,
        choices=TERM_CHOICES,
    )

    name = models.CharField(max_length=300)

    description = models.TextField(blank=True)

    maximum_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100,
    )

    order = models.PositiveIntegerField(default=1)

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["term", "order", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "sub_strand",
                    "term",
                    "name",
                ],
                name="unique_assessment_item_per_substrand_term",
            ),
        ]
    def __str__(self):
        return (
            f"{self.sub_strand} - "
            f"{self.name}"
        )

    

class SchoolClassCurriculum(models.Model):
    """
    Connects a school's class to the exact CBC curriculum version,
    grade and, where applicable, pathway for an academic year.
    """

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="curriculum_assignments",
    )

    curriculum_version = models.ForeignKey(
        CurriculumVersion,
        on_delete=models.PROTECT,
        related_name="school_class_assignments",
    )

    curriculum_grade = models.ForeignKey(
        CurriculumGrade,
        on_delete=models.PROTECT,
        related_name="school_class_assignments",
    )

    pathway = models.ForeignKey(
        CurriculumPathway,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="school_class_assignments",
    )

    academic_year = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["academic_year", "school_class__name"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school_class",
                    "academic_year",
                ],
                name="unique_class_curriculum_year",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        # ---------------------------------------------------------
        # 1. Grade must belong to the selected curriculum version
        # ---------------------------------------------------------
        if (
            self.curriculum_version_id
            and self.curriculum_grade_id
            and self.curriculum_grade.curriculum_version_id
            != self.curriculum_version_id
        ):
            errors["curriculum_grade"] = (
                "The selected grade does not belong to the selected "
                "curriculum version."
            )

        # ---------------------------------------------------------
        # 2. Pathway must belong to the selected grade
        # ---------------------------------------------------------
        if (
            self.pathway_id
            and self.curriculum_grade_id
            and self.pathway.curriculum_grade_id
            != self.curriculum_grade_id
        ):
            errors["pathway"] = (
                "The selected pathway does not belong to the "
                "selected curriculum grade."
            )

        # ---------------------------------------------------------
        # 3. PP1–Grade 9 do NOT have pathways
        # ---------------------------------------------------------
        lower_grades = {
            "PP1",
            "PP2",
            "GRADE1",
            "GRADE2",
            "GRADE3",
            "GRADE4",
            "GRADE5",
            "GRADE6",
            "GRADE7",
            "GRADE8",
            "GRADE9",
        }

        # ---------------------------------------------------------
        # 4. Grade 10–12 MUST have a pathway
        # ---------------------------------------------------------
        senior_grades = {
            "GRADE10",
            "GRADE11",
            "GRADE12",
        }

        if self.curriculum_grade_id:
            grade_code = self.curriculum_grade.grade

            if grade_code in lower_grades and self.pathway_id:
                errors["pathway"] = (
                    "PP1 to Grade 9 do not use CBC pathways."
                )

            if grade_code in senior_grades and not self.pathway_id:
                errors["pathway"] = (
                    "Grade 10 to Grade 12 must have a CBC pathway."
                )

        # ---------------------------------------------------------
        # 5. Class must belong to a school
        # ---------------------------------------------------------
        if self.school_class_id and not self.school_class.school_id:
            errors["school_class"] = (
                "The class must belong to a school."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        pathway_name = self.pathway.name if self.pathway else "No Pathway"

        return (
            f"{self.school_class} - "
            f"{self.curriculum_grade.display_name} - "
            f"{pathway_name} - "
            f"{self.academic_year}"
        )

class TeacherAssessmentAssignment(models.Model):
    """
    Determines which teacher is responsible for a learning area
    within a class, academic year and term.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="cbc_assessment_assignments",
    )

    school_class_curriculum = models.ForeignKey(
        SchoolClassCurriculum,
        on_delete=models.CASCADE,
        related_name="teacher_assignments",
    )

    learning_area = models.ForeignKey(
        CurriculumLearningArea,
        on_delete=models.PROTECT,
        related_name="teacher_assignments",
    )

    academic_year = models.CharField(max_length=20)

    term = models.CharField(
        max_length=1,
        choices=[
            ("1", "Term 1"),
            ("2", "Term 2"),
            ("3", "Term 3"),
        ],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            "academic_year",
            "term",
            "school_class_curriculum",
            "learning_area",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "school_class_curriculum",
                    "learning_area",
                    "academic_year",
                    "term",
                ],
                name="unique_teacher_cbc_assignment",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.school_class_curriculum_id:
            class_curriculum = self.school_class_curriculum

            # Assignment year must match the class curriculum year.
            if (
                self.academic_year
                and class_curriculum.academic_year
                and self.academic_year != class_curriculum.academic_year
            ):
                errors["academic_year"] = (
                    "The assignment academic year must match "
                    "the class curriculum academic year."
                )

            # Teacher and class must belong to the same school.
            if (
                self.teacher_id
                and self.teacher.school_id
                and class_curriculum.school_class_id
                and class_curriculum.school_class.school_id
                and self.teacher.school_id
                != class_curriculum.school_class.school_id
            ):
                errors["teacher"] = (
                    "The teacher must belong to the same school "
                    "as the assigned class."
                )

            grade = class_curriculum.curriculum_grade
            pathway = class_curriculum.pathway

            if self.learning_area_id:
                learning_area = self.learning_area

                # Learning area must belong to the same curriculum grade.
                if (
                    learning_area.curriculum_grade_id
                    != grade.id
                ):
                    errors["learning_area"] = (
                        "The learning area must belong to "
                        "the assigned curriculum grade."
                    )

                # Senior grades require the learning area to belong
                # to the class pathway.
                if grade.grade in {
                    "GRADE10",
                    "GRADE11",
                    "GRADE12",
                }:
                    if not pathway:
                        errors["learning_area"] = (
                            "Grade 10 to Grade 12 assignments "
                            "must have a CBC pathway."
                        )
                    elif learning_area.pathway_id != pathway.id:
                        errors["learning_area"] = (
                            "The learning area must belong to "
                            "the assigned CBC pathway."
                        )

                # PP1 to Grade 9 must not use pathways.
                elif pathway:
                    errors["school_class_curriculum"] = (
                        "PP1 to Grade 9 do not use CBC pathways."
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.learning_area.name} - "
            f"{self.school_class_curriculum.school_class} - "
            f"T{self.term}"
        )


class CBCAssessmentRecord(models.Model):
    """
    Individual learner assessment record.

    The assessment item is tied to the exact curriculum version through:
    CurriculumAssessmentItem
        -> CurriculumSubStrand
        -> CurriculumStrand
        -> CurriculumLearningArea
        -> CurriculumGrade
        -> CurriculumVersion
    """

    ASSESSMENT_COMPONENTS = [
        ("CAT1", "CAT 1"),
        ("MID", "Mid Term"),
        ("END", "End Term"),
    ]

    PERFORMANCE_LEVELS = [
        ("EE", "Exceeds Expectations"),
        ("ME", "Meets Expectations"),
        ("AE", "Approaches Expectations"),
        ("BE", "Below Expectations"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="cbc_assessment_records",
    )

    assessment_item = models.ForeignKey(
        CurriculumAssessmentItem,
        on_delete=models.PROTECT,
        related_name="assessment_records",
    )

    academic_year = models.CharField(max_length=20)

    term = models.CharField(
        max_length=1,
        choices=[
            ("1", "Term 1"),
            ("2", "Term 2"),
            ("3", "Term 3"),
        ],
    )

    assessment_component = models.CharField(
        max_length=10,
        choices=ASSESSMENT_COMPONENTS,
    )

    mark = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    performance_level = models.CharField(
        max_length=10,
        blank=True,
    )

    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    teacher_comment = models.TextField(
        blank=True,
    )

    entered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="cbc_assessment_records_entered",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "academic_year",
            "term",
            "student",
            "assessment_item",
            "assessment_component",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "assessment_item",
                    "academic_year",
                    "term",
                    "assessment_component",
                ],
                name="unique_cbc_student_item_component",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.assessment_item.name} - "
            f"{self.assessment_component}"
        )


class CBCEndYearLearnerProfile(models.Model):
    """
    End-year learner assessment profile for transition.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="cbc_end_year_profiles",
    )

    academic_year = models.CharField(max_length=20)

    core_competencies_achieved = models.TextField(
        blank=True,
    )

    skills_acquired = models.TextField(
        blank=True,
    )

    weaknesses_observed = models.TextField(
        blank=True,
    )

    learner_strengths = models.TextField(
        blank=True,
    )

    areas_of_improvement = models.TextField(
        blank=True,
    )

    assessor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="cbc_end_year_profiles_assessed",
    )

    assessment_date = models.DateField(
        null=True,
        blank=True,
    )

    assessor_signature = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "academic_year",
                ],
                name="unique_cbc_end_year_profile",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"CBC End Year Profile - "
            f"{self.academic_year}"
        )

class CBCAssessmentSubmission(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="cbc_assessment_submissions",
    )

    school_class_curriculum = models.ForeignKey(
        SchoolClassCurriculum,
        on_delete=models.CASCADE,
        related_name="assessment_submissions",
    )

    learning_area = models.ForeignKey(
        CurriculumLearningArea,
        on_delete=models.PROTECT,
        related_name="assessment_submissions",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=1,
        choices=[
            ("1", "Term 1"),
            ("2", "Term 2"),
            ("3", "Term 3"),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_cbc_assessment_submissions",
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "academic_year",
            "term",
            "school_class_curriculum",
            "learning_area",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school_class_curriculum",
                    "learning_area",
                    "academic_year",
                    "term",
                ],
                name="unique_cbc_assessment_submission",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.school_class_curriculum_id:

            class_curriculum = (
                self.school_class_curriculum
            )

            if (
                self.academic_year
                and class_curriculum.academic_year
                and self.academic_year
                != class_curriculum.academic_year
            ):
                errors["academic_year"] = (
                    "The academic year must match "
                    "the class curriculum year."
                )

            if self.learning_area_id:

                learning_area = self.learning_area

                if (
                    learning_area.curriculum_grade_id
                    != class_curriculum.curriculum_grade_id
                ):
                    errors["learning_area"] = (
                        "The learning area does not belong "
                        "to the class curriculum grade."
                    )

                if (
                    class_curriculum.curriculum_grade.grade
                    in {
                        "GRADE10",
                        "GRADE11",
                        "GRADE12",
                    }
                ):
                    if (
                        learning_area.pathway_id
                        != class_curriculum.pathway_id
                    ):
                        errors["learning_area"] = (
                            "The learning area does not belong "
                            "to the class pathway."
                        )

        if self.teacher_id and self.school_class_curriculum_id:

            teacher_school = self.teacher.school_id
            class_school = (
                self.school_class_curriculum
                .school_class
                .school_id
            )

            if (
                teacher_school
                and class_school
                and teacher_school != class_school
            ):
                errors["teacher"] = (
                    "The teacher must belong to the "
                    "same school as the class."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.school_class_curriculum.school_class} - "
            f"{self.learning_area.name} - "
            f"T{self.term} - "
            f"{self.academic_year}"
        )


class CBCPerformanceLevel(models.Model):
    """
    Defines the mark range, actual performance level and points
    used by CBC assessment for a particular curriculum grade.
    """

    CATEGORY_CHOICES = [
        ("EE", "Exceeding Expectation"),
        ("ME", "Meeting Expectation"),
        ("AE", "Approaching Expectation"),
        ("BE", "Below Expectation"),
    ]

    curriculum_grade = models.ForeignKey(
        CurriculumGrade,
        on_delete=models.CASCADE,
        related_name="performance_levels",
    )

    category = models.CharField(
        max_length=2,
        choices=CATEGORY_CHOICES,
    )

    code = models.CharField(
        max_length=10,
    )

    minimum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    maximum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    order = models.PositiveIntegerField(
        default=1,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "curriculum_grade",
                    "code",
                ],
                name="unique_cbc_performance_code_per_grade",
            ),
        ]

    def __str__(self):
        return (
            f"{self.curriculum_grade.display_name} - "
            f"{self.code}"
        )

class CBCSubStrandAssessment(models.Model):
    """
    Stores a learner's CBC assessment at Sub-Strand level.

    Teachers enter the learner's mark against the Sub-Strand.
    The system determines the applicable CBC performance level
    and points automatically.
    """

    ASSESSMENT_COMPONENT_CHOICES = [
        ("CAT1", "CAT 1"),
        ("MID", "Mid-Term"),
        ("END", "End-Term"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="cbc_substrand_assessments",
    )

    submission = models.ForeignKey(
        CBCAssessmentSubmission,
        on_delete=models.CASCADE,
        related_name="assessments",
        null=True,
        blank=True,
    )

    sub_strand = models.ForeignKey(
        CurriculumSubStrand,
        on_delete=models.PROTECT,
        related_name="cbc_assessments",
    )

    academic_year = models.CharField(
        max_length=20,
    )

    term = models.CharField(
        max_length=1,
        choices=[
            ("1", "Term 1"),
            ("2", "Term 2"),
            ("3", "Term 3"),
        ],
    )

    assessment_component = models.CharField(
        max_length=10,
        choices=ASSESSMENT_COMPONENT_CHOICES,
    )
    legacy_performance_level = models.CharField(
        max_length=2,
        blank=True,
        editable=False,
    )

    performance_level = models.ForeignKey(
        CBCPerformanceLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assessments",
    )

    mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    teacher_comment = models.TextField(
        blank=True,
    )

    entered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="cbc_substrand_assessments_entered",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "sub_strand",
                    "academic_year",
                    "term",
                    "assessment_component",
                ],
                name="unique_cbc_substrand_assessment",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "student",
                    "academic_year",
                    "term",
                ],
                name="cbc_assess_student_period_idx",
            ),
            models.Index(
                fields=[
                    "sub_strand",
                    "academic_year",
                    "term",
                ],
                name="cbc_assess_substrand_idx",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        # ---------------------------------------------------------
        # 1. Basic student/class school consistency
        # ---------------------------------------------------------
        if self.student_id:
            student = self.student

            if not student.school_id:
                errors["student"] = (
                    "The student must belong to a school."
                )

            if (
                student.school_class_id
                and student.school_class.school_id
                and student.school_id
                and student.school_class.school_id
                != student.school_id
            ):
                errors["student"] = (
                    "The student's class must belong to "
                    "the same school as the student."
                )

        # ---------------------------------------------------------
        # 2. Find the student's academic class for this
        #    academic year and term.
        # ---------------------------------------------------------
        academic_class = None

        if (
            self.student_id
            and self.academic_year
            and self.term
        ):
            enrollment = (
                self.student.academic_enrollments
                .filter(
                    academic_year=self.academic_year,
                    term=self.term,
                )
                .select_related(
                    "school_class",
                    "school_class__school",
                )
                .first()
            )

            if enrollment:
                academic_class = enrollment.school_class

            elif self.student.school_class_id:
                # Compatibility with existing/legacy students
                # that do not yet have a historical enrollment row.
                academic_class = self.student.school_class

        # ---------------------------------------------------------
        # 3. The class must have a CBC curriculum assignment
        #    for this academic year.
        # ---------------------------------------------------------
        class_curriculum = None

        if academic_class:
            class_curriculum = (
                academic_class.curriculum_assignments
                .filter(
                    academic_year=self.academic_year,
                )
                .select_related(
                    "curriculum_grade",
                    "curriculum_grade__curriculum_version",
                    "pathway",
                )
                .first()
            )

            if not class_curriculum:
                errors["student"] = (
                    "The student's class does not have a CBC "
                    "curriculum assignment for this academic year."
                )

        # ---------------------------------------------------------
        # 4. The assessment sub-strand must belong to the
        #    student's assigned curriculum grade.
        # ---------------------------------------------------------
        if self.sub_strand_id and class_curriculum:
            sub_strand = self.sub_strand

            strand = sub_strand.strand
            learning_area = strand.learning_area
            curriculum_grade = class_curriculum.curriculum_grade

            if (
                learning_area.curriculum_grade_id
                != curriculum_grade.id
            ):
                errors["sub_strand"] = (
                    "The assessment sub-strand does not belong "
                    "to the student's assigned curriculum grade."
                )

            # -----------------------------------------------------
            # 5. Grade 10–12 pathway validation
            # -----------------------------------------------------
            if curriculum_grade.grade in {
                "GRADE10",
                "GRADE11",
                "GRADE12",
            }:
                if not class_curriculum.pathway_id:
                    errors["sub_strand"] = (
                        "Grade 10 to Grade 12 assessments must "
                        "have a CBC pathway."
                    )

                elif (
                    learning_area.pathway_id
                    != class_curriculum.pathway_id
                ):
                    errors["sub_strand"] = (
                        "The assessment sub-strand does not belong "
                        "to the student's assigned CBC pathway."
                    )

            # -----------------------------------------------------
            # 6. PP1–Grade 9 must not use pathways
            # -----------------------------------------------------
            else:
                if class_curriculum.pathway_id:
                    errors["sub_strand"] = (
                        "PP1 to Grade 9 assessments must not "
                        "use CBC pathways."
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.sub_strand} - "
            f"{self.academic_year} T{self.term} "
            f"{self.assessment_component}"
        )

