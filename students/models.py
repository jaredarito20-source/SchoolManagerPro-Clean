from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User


class Teacher(models.Model):
    employee_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SchoolClass(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_teacher_for",
    )

    def __str__(self):
        return self.name


class Student(models.Model):
    admission_number = models.CharField(max_length=20, unique=True)
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

    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
    )

    def __str__(self):
        return self.name


class Exam(models.Model):
    name = models.CharField(max_length=50)
    term = models.CharField(max_length=20)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.name} - Term {self.term} ({self.year})"

class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "exam"],
                name="unique_student_subject_exam",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam}"


class SchoolProfile(models.Model):
    name = models.CharField(max_length=200)
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


class FeeStructure(models.Model):
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
    )

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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