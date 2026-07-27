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
    path(
        "fees/payments/",
        views.fee_payment_list,
        name="fee_payment_list",
    ),

    path(
    "fees/payment/edit/<int:id>/",
    views.edit_payment,
    name="edit_payment",
    ),

    path(
        "fees/payment/delete/<int:id>/",
        views.delete_payment,
        name="delete_payment",
    ),
    
    path("payments/<int:id>/receipt/", views.print_receipt, name="print_receipt"),

    # Fee Balances
    path("fees/balances/", views.fee_balance_list, name="fee_balance_list"),

    # Fee Statements
    path("statement/<int:id>/", views.fee_statement, name="fee_statement"),
    path("statement/<int:id>/print/", views.print_fee_statement, name="print_fee_statement"),
    path(
        "fees/payment/add/",
        views.add_fee_payment,
        name="add_fee_payment",
    ),
    path(
        "finance/dashboard/",
        views.finance_dashboard,
        name="finance_dashboard",
    ),

    # Attendance
    
    path("attendance/add/", views.add_attendance, name="add_attendance"),
    
   
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

    # Logout
    path("logout/", views.logout_view, name="logout"),

    # print timetable
   
   # ------------------------
# Exam Timetable
# ------------------------

    path(
        "exam-timetable/",
        views.exam_timetable_list,
        name="exam_timetable_list",
    ),

    path(
        "exam-timetable/add/",
        views.add_exam_timetable,
        name="add_exam_timetable",
    ),

    path(
        "exam-timetable/edit/<int:id>/",
        views.edit_exam_timetable,
        name="edit_exam_timetable",
    ),

    path(
        "exam-timetable/delete/<int:id>/",
        views.delete_exam_timetable,
        name="delete_exam_timetable",
    ),

    # Print ALL exam timetables
    path(
        "exam-timetable/print/",
        views.print_exam_timetable,
        name="print_exam_timetable",
    ),

    # Print one class exam timetable
    path(
        "exam-timetable/print/<int:id>/",
        views.print_class_exam_timetable,
        name="print_class_exam_timetable",
    ),

    path(
        "get-class-exams/<int:class_id>/",
        views.get_class_exams,
        name="get_class_exams",
    ),

    path(
        "ajax/load-exams/",
        views.load_exams,
        name="ajax_load_exams",
),

    path(
        "timetable/print/",
        views.print_timetable,
        name="print_timetable",
),

# attendance register
    path(
    "attendance/take/",
    views.take_attendance,
    name="take_attendance",
),

    path(
    "attendance/",
    views.attendance_list,
    name="attendance_list",
),

path(
    "attendance/edit/<int:id>/",
    views.edit_attendance,
    name="edit_attendance",
),

path(
    "attendance/delete/<int:id>/",
    views.delete_attendance,
    name="delete_attendance",
),

path(
    "attendance/print/",
    views.print_attendance,
    name="print_attendance",
),

path(
    "inventory/",
    views.inventory_list,
    name="inventory_list",
),

path(
    "inventory/add/",
    views.add_inventory_item,
    name="add_inventory_item",
),



path(
    "inventory/delete/<int:id>/",
    views.delete_inventory_item,
    name="delete_inventory_item",
),

path(
    "inventory/categories/",
    views.inventory_category_list,
    name="inventory_category_list",
),

path(
    "inventory/categories/add/",
    views.add_inventory_category,
    name="add_inventory_category",
),

path(
    "inventory/",
    views.inventory_list,
    name="inventory_list",
),




path(
    "inventory/edit/<int:id>/",
    views.edit_inventory_item,
    name="edit_inventory_item",
),

path(
    "inventory/receive/<int:id>/",
    views.receive_stock,
    name="receive_stock",
),

path(
    "inventory/issue/<int:id>/",
    views.issue_stock,
    name="issue_stock",
),

path(
    "inventory/transactions/",
    views.stock_transaction_list,
    name="stock_transaction_list",
),

path(
    "library/",
    views.library_list,
    name="library_list",
),

path(
    "library/add/",
    views.add_book,
    name="add_book",
),

path(
    "library/edit/<int:id>/",
    views.edit_book,
    name="edit_book",
),

path(
    "library/delete/<int:id>/",
    views.delete_book,
    name="delete_book",
),


]