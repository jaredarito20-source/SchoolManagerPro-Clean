from django.db import models
from django.db.models import Sum


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

    def total_fee(self):
        fee = FeeStructure.objects.filter(
            school_class=self.school_class
        ).first()

        if fee:
            return fee.total_fee()

        return 0

    def total_paid(self):
        total = self.feepayment_set.aggregate(
            total=Sum("amount_paid")
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

    logo = models.ImageField(
        upload_to="school_logos/",
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
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
    )

    payment_date = models.DateField(auto_now_add=True)

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
    )

    def __str__(self):
        return f"{self.student} - {self.amount_paid}"

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