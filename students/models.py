from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User


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
    name = models.CharField(max_length=50)

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
            return fee.total_fee()

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
    )

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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
        on_delete=models.CASCADE
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

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.amount}"
        )
class Attendance(models.Model):
    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Excused", "Excused"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
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
        return f"{self.student} - {self.date} - {self.status}"

class Timetable(models.Model):
    DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE
    )

    day = models.CharField(
        max_length=10,
        choices=DAYS,
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    class Meta:
        ordering = ["day", "start_time"]

    def __str__(self):
        return (
            f"{self.school_class} - "
            f"{self.subject} - "
            f"{self.day}"
        ) 

class ExamTimetable(models.Model):
    DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
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
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.CASCADE,
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

    def __str__(self):
        return self.name

class StockTransaction(models.Model):

    TRANSACTION_TYPES = [

        ("RECEIVED", "Received"),

        ("ISSUED", "Issued"),

    ]

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

    title = models.CharField(max_length=200)

    author = models.CharField(max_length=200)

    isbn = models.CharField(
        max_length=30,
        unique=True,
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

    copies = models.PositiveIntegerField(default=1)

    available_copies = models.PositiveIntegerField(default=1)

    shelf = models.CharField(
        max_length=100,
        blank=True,
    )

    def __str__(self):
        return self.title

class BorrowBook(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    borrow_date = models.DateField()

    due_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True
    )

    STATUS = (
        ("Borrowed", "Borrowed"),
        ("Returned", "Returned"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Borrowed"
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
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

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
    )

    year = models.IntegerField()

    month = models.CharField(max_length=20)

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
        unique_together = ("teacher", "month", "year")

    def __str__(self):
        return f"{self.teacher} - {self.month} {self.year}"

    # Transport

class Driver(models.Model):

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
    route_name = models.CharField(max_length=100)

    start_point = models.CharField(max_length=150)

    end_point = models.CharField(max_length=150)

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
        related_name="routes"
    )

    driver = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transport_routes"
    )

    active = models.BooleanField(default=True)

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

class HostelBlock(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name

class HostelRoom(models.Model):

    block = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="rooms",
    )

    room_number = models.CharField(max_length=30)

    capacity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("block", "room_number")

    @property
    def occupied_beds(self):
        return self.students.count()

    @property
    def available_beds(self):
        return self.capacity - self.occupied_beds

    @property
    def is_full(self):
        return self.occupied_beds >= self.capacity

    def __str__(self):
        return f"{self.block.name} - Room {self.room_number}"

class HostelBed(models.Model):

    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="beds",
    )

    bed_number = models.CharField(
        max_length=20,
    )

    occupied = models.BooleanField(
        default=False,
    )

    class Meta:
        unique_together = ("room", "bed_number")
        ordering = ["bed_number"]

    def __str__(self):
        return f"{self.room} - Bed {self.bed_number}"
class StudentHostel(models.Model):

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="hostel",
    )

    room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="students",
    )

    bed_number = models.CharField(max_length=20)

    assigned_date = models.DateField(
        auto_now_add=True,
    )

    active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.student} - {self.room}"

class HostelWarden(models.Model):

    hostel_block = models.ForeignKey(
        HostelBlock,
        on_delete=models.CASCADE,
        related_name="wardens",
    )

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    designation = models.CharField(
        max_length=50,
        choices=[
            ("Senior Warden", "Senior Warden"),
            ("Assistant Warden", "Assistant Warden"),
            ("Night Warden", "Night Warden"),
            ("Matron", "Matron"),
            ("Patron", "Patron"),
        ],
    )

    gender = models.CharField(
        max_length=10,
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
        ],
    )

    phone = models.CharField(max_length=20, blank=True)

    email = models.EmailField(blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class HostelTransfer(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="hostel_transfers",
    )

    from_room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="transfers_from",
    )

    to_room = models.ForeignKey(
        HostelRoom,
        on_delete=models.CASCADE,
        related_name="transfers_to",
    )

    transfer_date = models.DateField(
        auto_now_add=True,
    )

    reason = models.TextField(
        blank=True,
    )

    transferred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.student} ({self.from_room} → {self.to_room})"

class DisciplineCategory(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
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

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    date_given = models.DateField(auto_now_add=True)

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
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
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
    )

    def __str__(self):
        return f"{self.student} - {self.homework}"

    # Timetable

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

    locked = models.BooleanField(default=False)

    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=["school_class","day","period"],
                name="unique_class_period",
            ),

            models.UniqueConstraint(
                fields=["teacher","day","period"],
                name="unique_teacher_period",
            ),

        ]