from django.urls import path
from . import views

urlpatterns = [

    # Dashboard
    path("", views.home, name="home"),

    # Students
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.add_student, name="add_student"),
    path("students/edit/<int:id>/", views.edit_student, name="edit_student"),
    path("students/delete/<int:id>/", views.delete_student, name="delete_student"),

    # Teachers
    path("teachers/", views.teacher_list, name="teacher_list"),
    path("teachers/add/", views.add_teacher, name="add_teacher"),
    path("teachers/edit/<int:id>/", views.edit_teacher, name="edit_teacher"),
    path("teachers/delete/<int:id>/", views.delete_teacher, name="delete_teacher"),

    # Subjects
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/add/", views.add_subject, name="add_subject"),
    path("subjects/edit/<int:id>/", views.edit_subject, name="edit_subject"),
    path("subjects/delete/<int:id>/", views.delete_subject, name="delete_subject"),

    # Classes
    path("classes/", views.class_list, name="class_list"),
    path("classes/add/", views.add_class, name="add_class"),
    path("classes/edit/<int:id>/", views.edit_class, name="edit_class"),
    path("classes/delete/<int:id>/", views.delete_class, name="delete_class"),

    # Exams
    path("exams/", views.exam_list, name="exam_list"),
    path("exams/add/", views.add_exam, name="add_exam"),
    path("exams/edit/<int:id>/", views.edit_exam, name="edit_exam"),
    path("exams/delete/<int:id>/", views.delete_exam, name="delete_exam"),

    # Marks
    path("marks/", views.mark_list, name="mark_list"),
    path("marks/add/", views.add_mark, name="add_mark"),
    path("marks/edit/<int:id>/", views.edit_mark, name="edit_mark"),
    path("marks/delete/<int:id>/", views.delete_mark, name="delete_mark"),

    # Reports
    path("reports/student/<int:id>/", views.student_report, name="student_report"),
    path("students/<int:id>/print/", views.print_report, name="print_report"),

    # Fee Structure
    path("fees/", views.fee_structure_list, name="fee_structure_list"),
    path("fees/add/", views.add_fee_structure, name="add_fee_structure"),

    # Fee Payments
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/add/", views.add_payment, name="add_payment"),
    path("payments/<int:id>/receipt/", views.print_receipt, name="print_receipt"),

    # Fee Balances
    path("fees/balances/", views.fee_balance_list, name="fee_balance_list"),

    # Fee Statements
    path("statement/<int:id>/", views.fee_statement, name="fee_statement"),
    path("statement/<int:id>/print/", views.print_fee_statement, name="print_fee_statement"),

    # Attendance
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/add/", views.add_attendance, name="add_attendance"),
    path("attendance/take/", views.take_attendance, name="take_attendance"),
    path("attendance/edit/<int:id>/", views.edit_attendance, name="edit_attendance"),
    path("attendance/delete/<int:id>/", views.delete_attendance, name="delete_attendance"),

    # Timetable
    path("timetable/", views.timetable_list, name="timetable_list"),
    path("timetable/add/", views.add_timetable, name="add_timetable"),
    path("timetable/edit/<int:id>/", views.edit_timetable, name="edit_timetable"),
    path("timetable/delete/<int:id>/", views.delete_timetable, name="delete_timetable"),

    # User Management
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.add_user, name="add_user"),
    path("users/edit/<int:id>/", views.edit_user, name="edit_user"),
    path("users/delete/<int:id>/", views.delete_user, name="delete_user"),

    # Student Promotion
    path("promotion/", views.promotion_list, name="promotion_list"),
    path("promotion/promote/", views.promote_students, name="promote_students"),
]