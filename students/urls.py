from django.urls import path
from . import views

urlpatterns = [
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


    path("reports/student/<int:id>/", views.student_report, name="student_report"),
    path("students/<int:id>/print/", views.print_report, name="print_report"),
            
    ]


    
