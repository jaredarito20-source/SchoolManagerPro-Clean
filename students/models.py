from django.db import models


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

    # Replace class_name with this:
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )

    parent_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

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