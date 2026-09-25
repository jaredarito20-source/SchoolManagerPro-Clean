from django.contrib.auth import views as auth_views
from django.urls import path
app_name = "students"
from .view_modules.sms import sms_dashboard
from .view_modules.sms_admin import sms_add_credits
from .view_modules.sms_admin import sms_packages
from .view_modules.mpesa import mpesa_stk_push
from .view_modules.cbc_assessment import (
    cbc_my_classes,
    cbc_learning_areas,
    cbc_assessment_book,
    cbc_assessment_book_print,
    cbc_subject_score_sheet,
    cbc_submission_review,
    cbc_submission_approve,
    cbc_submission_reject,
    cbc_mark_edit,
    cbc_subject_assessment_print,
    cbc_subject_assessment_book,
    cbc_upper_secondary_assessment_book,
    cbc_upper_secondary_mark_entry,
    cbc_upper_secondary_mark_list,
    cbc_upper_secondary_assessment_book_print,
    cbc_upper_secondary_mark_list_print,
    cbc_upper_secondary_strand_classes,
    cbc_upper_secondary_mark_edit,
    
)
from . import views
from students.view_modules.administration import register_school
from .view_modules.administration import assign_student_parent, academic_year_archive
from .view_modules.sms_admin import (
    sms_packages,
    sms_buy_package,
    sms_checkout,
)
from .view_modules.parent import (
    parent_dashboard,
    parent_students,
    parent_assessment_book,)




urlpatterns = [

# Dashboard / Authentication / User Management

path('users/reset-password/<int:id>/', views.reset_user_password, name='reset_user_password'),

path('users/<int:id>/reset-password/', views.admin_reset_user_password, name='admin_reset_user_password'),

path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html', email_template_name='registration/password_reset_email.html', subject_template_name='registration/password_reset_subject.txt', success_url='/password-reset/done/'), name='password_reset'),

path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),

path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html', success_url='/password-reset/complete/'), name='password_reset_confirm'),

path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

path('', views.home, name='home'),

path('students/', views.student_list, name='student_list'),

path('students/add/', views.add_student, name='add_student'),

path('students/edit/<int:id>/', views.edit_student, name='edit_student'),

path('students/delete/<int:id>/', views.delete_student, name='delete_student'),

path('schools/add/', views.add_school_profile, name='add_school_profile'),

path('schools/<int:id>/edit/',views.edit_school_profile,name='edit_school_profile'),
path('schools/<int:id>/delete/',views.delete_school,name='delete_school'),
path('schools/credentials/', views.school_credentials, name='school_credentials'),
path('schools/<int:id>/reset-password/',views.reset_school_password,name='reset_school_password'),
path('schools/',views.school_list,name='school_list'),
path(
    'academic-year-archive/',
    academic_year_archive,
    name='academic_year_archive',
),
path('teachers/', views.teacher_list, name='teacher_list'),

path('teachers/add/', views.add_teacher, name='add_teacher'),

path('teachers/edit/<int:id>/', views.edit_teacher, name='edit_teacher'),

path('teachers/delete/<int:id>/', views.delete_teacher, name='delete_teacher'),

path('subjects/', views.subject_list, name='subject_list'),

path('subjects/add/', views.add_subject, name='add_subject'),

path('subjects/edit/<int:id>/', views.edit_subject, name='edit_subject'),

path('subjects/delete/<int:id>/', views.delete_subject, name='delete_subject'),

path('classes/', views.class_list, name='class_list'),

path(
    'administration/cbc-teacher-assignments/',
    views.cbc_teacher_assignment_list,
    name='cbc_teacher_assignment_list',
),

path(
    'administration/cbc-teacher-assignments/add/',
    views.cbc_teacher_assignment_add,
    name='cbc_teacher_assignment_add',
),


path('classes/<int:id>/curriculum/',views.assign_class_curriculum,name='assign_class_curriculum',),
path('classes/add/', views.add_class, name='add_class'),

path('classes/edit/<int:id>/', views.edit_class, name='edit_class'),

path('classes/delete/<int:id>/', views.delete_class, name='delete_class'),

path('exams/', views.exam_list, name='exam_list'),

path('exams/add/', views.add_exam, name='add_exam'),

path('exams/edit/<int:id>/', views.edit_exam, name='edit_exam'),
path('exams/setup-cbc/', views.setup_cbc_exams, name='setup_cbc_exams'),

path('exams/delete/<int:id>/', views.delete_exam, name='delete_exam'),

path('marks/', views.mark_list, name='mark_list'),

path('marks/add/', views.add_mark, name='add_mark'),

path('marks/edit/<int:id>/', views.edit_mark, name='edit_mark'),

path('marks/delete/<int:id>/', views.delete_mark, name='delete_mark'),

path('reports/student/<int:id>/', views.student_report, name='student_report'),

# ============================================================
# CBC ASSESSMENTS
# ============================================================

path(
    "cbc/my-classes/",
    cbc_my_classes,
    name="cbc_my_classes",
),
path(
    "cbc/upper-secondary-mark-edit/<int:assessment_id>/",
    cbc_upper_secondary_mark_edit,
    name="cbc_upper_secondary_mark_edit",
),

path(
    "cbc/learning-areas/<int:school_class_curriculum_id>/<str:term>/",
    cbc_learning_areas,
    name="cbc_learning_areas",
),
path(
    "cbc/assessment-book/<int:assignment_id>/student/<int:student_id>/print/",
        cbc_assessment_book_print,
        name="cbc_assessment_book_print",
    ),

path(
    "cbc/subject-score-sheet/",
    cbc_subject_score_sheet,
    name="cbc_subject_score_sheet",
),

path(
    "cbc/upper-secondary-assessment-book/<int:assignment_id>/",
    cbc_upper_secondary_assessment_book,
    name="cbc_upper_secondary_assessment_book",
),

path(
    "cbc/upper-secondary-assessment-book/<int:assignment_id>/print/",
    cbc_upper_secondary_assessment_book_print,
    name="cbc_upper_secondary_assessment_book_print",
),

path(
    "cbc/upper-secondary-mark-list/",
    cbc_upper_secondary_mark_list,
    name="cbc_upper_secondary_mark_list",
),
path(
    "cbc/upper-secondary-mark-list/print/",
    cbc_upper_secondary_mark_list_print,
    name="cbc_upper_secondary_mark_list_print",
),




path(
    "cbc/upper-secondary-mark-entry/<int:assignment_id>/",
    cbc_upper_secondary_mark_entry,
    name="cbc_upper_secondary_mark_entry",
),

path(
    "cbc/subject-assessment-book/<int:student_id>/",
    cbc_subject_assessment_book,
    name="cbc_subject_assessment_book",
),

path(
    "cbc/result/<int:assignment_id>/<int:student_id>/",
    views.cbc_student_result,
    name="cbc_student_result",
),

path(
    "cbc/submissions/",
    cbc_submission_review,
    name="cbc_submission_review",
),
path(
    "cbc/submissions/<int:submission_id>/approve/",
    cbc_submission_approve,
    name="cbc_submission_approve",
),
path(
    "cbc/upper-secondary-strand-assessment/",
    views.cbc_upper_secondary_strand_classes,
    name="cbc_upper_secondary_strand_classes",
),

path(
    "cbc/upper-secondary-strand-assessment/<int:assignment_id>/",
    views.cbc_upper_secondary_strands,
    name="cbc_upper_secondary_strands",
),

path(
    "cbc/upper-secondary-strand-assessment/<int:assignment_id>/strand/<int:strand_id>/",
    views.cbc_upper_secondary_strand_assessment,
    name="cbc_upper_secondary_strand_assessment",
),

path(
    "cbc/subject-assessment-print/<int:assignment_id>/<int:student_id>/",
    cbc_subject_assessment_print,
    name="cbc_subject_assessment_print",
),

path(
    "cbc/submissions/<int:submission_id>/reject/",
    cbc_submission_reject,
    name="cbc_submission_reject",
),
path(
    "cbc/mark-edit/<int:assessment_id>/",
    cbc_mark_edit,
    name="cbc_mark_edit",
),


path(
    "cbc/assessment-book/<int:assignment_id>/",
    cbc_assessment_book,
    name="cbc_assessment_book",
),

path('students/<int:id>/print/', views.print_report, name='print_report'),

path('fees/', views.fee_structure_list, name='fee_structure_list'),

path('fees/add/', views.add_fee_structure, name='add_fee_structure'),

path('fees/payments/', views.fee_payment_list, name='fee_payment_list'),

path('fees/payment/edit/<int:id>/', views.edit_payment, name='edit_payment'),

path('fees/payment/delete/<int:id>/', views.delete_payment, name='delete_payment'),
path('fees/edit/<int:id>/',views.edit_fee_structure,name='edit_fee_structure',),

path('fees/delete/<int:id>/',views.delete_fee_structure,name='delete_fee_structure',),
path('payments/<int:id>/receipt/', views.print_receipt, name='print_receipt'),

path('fees/balances/', views.fee_balance_list, name='fee_balance_list'),

path('statement/<int:id>/', views.fee_statement, name='fee_statement'),

path('statement/<int:id>/print/', views.print_fee_statement, name='print_fee_statement'),

path('fees/payment/add/', views.add_fee_payment, name='add_fee_payment'),

path('finance/dashboard/', views.finance_dashboard, name='finance_dashboard'),

path('attendance/add/', views.add_attendance, name='add_attendance'),

path('timetable/', views.timetable_list, name='timetable_list'),

path('timetable/add/', views.add_timetable, name='add_timetable'),

path('timetable/edit/<int:id>/', views.edit_timetable, name='edit_timetable'),

path('timetable/delete/<int:id>/', views.delete_timetable, name='delete_timetable'),

path('users/', views.user_list, name='user_list'),

path('users/add/', views.add_user, name='add_user'),

path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),

path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

path('promotion/', views.promotion_list, name='promotion_list'),

path('promotion/promote/', views.promote_students, name='promote_students'),

path('logout/', views.logout_view, name='logout'),

path('exam-timetable/', views.exam_timetable_list, name='exam_timetable_list'),

path('exam-timetable/add/', views.add_exam_timetable, name='add_exam_timetable'),

path('exam-timetable/edit/<int:id>/', views.edit_exam_timetable, name='edit_exam_timetable'),

path('exam-timetable/delete/<int:id>/', views.delete_exam_timetable, name='delete_exam_timetable'),

path('exam-timetable/print/', views.print_exam_timetable, name='print_exam_timetable'),

path('exam-timetable/print/<int:id>/', views.print_class_exam_timetable, name='print_class_exam_timetable'),

path('get-class-exams/<int:class_id>/', views.get_class_exams, name='get_class_exams'),

path('ajax/load-exams/', views.load_exams, name='ajax_load_exams'),

path('exam/<int:id>/toggle/', views.toggle_exam_status, name='toggle_exam_status'),

path('marks/<int:id>/submit/', views.submit_mark, name='submit_mark'),

path('mark-submissions/', views.mark_submission_list, name='mark_submission_list'),

path('mark-submissions/<int:id>/submit/', views.submit_mark_submission, name='submit_mark_submission'),

path('administration/mark-submissions/', views.admin_mark_submission_list, name='admin_mark_submission_list'),

path('administration/mark-submissions/<int:id>/view/', views.view_mark_submission, name='view_mark_submission'),
path(
    "administration/cbc-mark-list/",
    views.cbc_mark_list,
    name="cbc_mark_list",
),
path('administration/mark-submissions/<int:id>/approve/', views.approve_mark_submission, name='approve_mark_submission'),

path('administration/mark-submissions/<int:id>/reject/', views.reject_mark_submission, name='reject_mark_submission'),

path('teacher/drafts/', views.teacher_draft_submissions, name='teacher_draft_submissions'),

path('marks/draft/<int:id>/', views.continue_mark_entry, name='continue_mark_entry'),

path('timetable/print/', views.print_timetable, name='print_timetable'),

path('parents/dashboard/', views.parent_dashboard, name='parent_dashboard'),

path('parents/students/', views.parent_students, name='parent_students'),

path('parents/student/<int:student_id>/', views.parent_student_profile, name='parent_student_profile'),

path('parents/attendance/', views.parent_attendance, name='parent_attendance'),

path('parents/results/<int:student_id>/', views.parent_results, name='parent_results'),

path('parents/fee-statement/<int:student_id>/', views.parent_fee_statement, name='parent_fee_statement'),
path(
    "parents/assessment-book/<int:student_id>/",
    parent_assessment_book,
    name="parent_assessment_book",
),
path('parents/fee-statement/<int:student_id>/print/', views.print_fee_statement, name='parent_print_fee_statement'),

path('parents/fee-balance/', views.parent_fee_balance, name='parent_fee_balance'),

path('homework/', views.homework_list, name='homework_list'),

path('homework/add/', views.add_homework, name='add_homework'),

path('homework/edit/<int:pk>/', views.edit_homework, name='edit_homework'),

path('homework/delete/<int:pk>/', views.delete_homework, name='delete_homework'),

path('parents/homework/', views.parent_homework, name='parent_homework'),

path('student/homework/submit/<int:homework_id>/', views.submit_homework, name='submit_homework'),

path('homework/<int:homework_id>/submissions/', views.homework_submissions, name='homework_submissions'),

path('homework/submission/<int:submission_id>/mark/', views.mark_homework, name='mark_homework'),

path('attendance/take/', views.add_attendance, name='take_attendance'),

path('attendance/', views.attendance_list, name='attendance_list'),

path('attendance/edit/<int:id>/', views.edit_attendance, name='edit_attendance'),

path('attendance/delete/<int:id>/', views.delete_attendance, name='delete_attendance'),

path('attendance/print/', views.print_attendance, name='print_attendance'),

path('inventory/', views.inventory_list, name='inventory_list'),

path('inventory/add/', views.add_inventory_item, name='add_inventory_item'),

path('inventory/delete/<int:id>/', views.delete_inventory_item, name='delete_inventory_item'),

path('inventory/categories/', views.inventory_category_list, name='inventory_category_list'),

path('inventory/categories/add/', views.add_inventory_category, name='add_inventory_category'),

path('inventory/edit/<int:id>/', views.edit_inventory_item, name='edit_inventory_item'),

path('inventory/receive/<int:id>/', views.receive_stock, name='receive_stock'),

path('inventory/issue/<int:id>/', views.issue_stock, name='issue_stock'),

path('inventory/transactions/', views.stock_transaction_list, name='stock_transaction_list'),

path('library/', views.library_list, name='library_list'),

path('library/add/', views.add_book, name='add_book'),

path('library/edit/<int:id>/', views.edit_book, name='edit_book'),

path('library/delete/<int:id>/', views.delete_book, name='delete_book'),

path('library/borrow/', views.borrow_book, name='borrow_book'),

path('library/borrow/list/', views.borrow_list, name='borrow_list'),

path('library/return/<int:id>/', views.return_book, name='return_book'),

path('library/dashboard/', views.library_dashboard, name='library_dashboard'),

path('library/reports/', views.library_reports, name='library_reports'),

path('library/reports/print/', views.print_library_report, name='print_library_report'),

path('results/class/', views.class_results, name='class_results'),

path('results/class/print/', views.print_class_results, name='print_class_results'),

path('payroll/salary-structure/', views.salary_structure_list, name='salary_structure_list'),

path('payroll/salary-structure/add/', views.add_salary_structure, name='add_salary_structure'),

path('payroll/salary-structure/edit/<int:id>/', views.edit_salary_structure, name='edit_salary_structure'),

path('payroll/salary-structure/delete/<int:id>/', views.delete_salary_structure, name='delete_salary_structure'),

path('payroll/generate/', views.generate_payroll, name='generate_payroll'),

path('payroll/', views.payroll_list, name='payroll_list'),

path('payroll/payslip/<int:id>/', views.print_payslip, name='print_payslip'),

path('payroll/salary-structure/print/<int:id>/', views.print_salary_structure, name='print_salary_structure'),

path('transport/vehicles/', views.vehicle_list, name='vehicle_list'),

path('transport/vehicles/add/', views.add_vehicle, name='add_vehicle'),

path('transport/vehicles/edit/<int:id>/', views.edit_vehicle, name='edit_vehicle'),

path('transport/vehicles/delete/<int:id>/', views.delete_vehicle, name='delete_vehicle'),

path('transport/vehicles/print/<int:id>/', views.print_vehicle, name='print_vehicle'),

path('transport/routes/', views.transport_route_list, name='transport_route_list'),

path('transport/routes/add/', views.add_transport_route, name='add_transport_route'),

path('transport/routes/edit/<int:id>/', views.edit_transport_route, name='edit_transport_route'),

path('transport/routes/delete/<int:id>/', views.delete_transport_route, name='delete_transport_route'),

path('transport/students/', views.student_transport_list, name='student_transport_list'),

path('transport/students/add/', views.add_student_transport, name='add_student_transport'),

path('transport/students/edit/<int:id>/', views.edit_student_transport, name='edit_student_transport'),

path('transport/students/delete/<int:id>/', views.delete_student_transport, name='delete_student_transport'),

path('transport/students/print/<int:id>/', views.print_student_transport, name='print_student_transport'),

path('transport/routes/print/<int:id>/', views.print_transport_route, name='print_transport_route'),

path('drivers/', views.driver_list, name='driver_list'),

path('drivers/add/', views.add_driver, name='add_driver'),

path('drivers/edit/<int:id>/', views.edit_driver, name='edit_driver'),

path('drivers/delete/<int:id>/', views.delete_driver, name='delete_driver'),

path('drivers/print/<int:id>/', views.print_driver, name='print_driver'),

path('transport/dashboard/', views.transport_dashboard, name='transport_dashboard'),

path('hostel/', views.hostel_dashboard, name='hostel_dashboard'),

path('hostel/blocks/', views.hostel_block_list, name='hostel_block_list'),

path('hostel/blocks/add/', views.add_hostel_block, name='add_hostel_block'),

path('hostel/blocks/edit/<int:id>/', views.edit_hostel_block, name='edit_hostel_block'),

path('hostel/blocks/delete/<int:id>/', views.delete_hostel_block, name='delete_hostel_block'),

path('hostel/blocks/print/<int:id>/', views.print_hostel_block, name='print_hostel_block'),

path('hostel/rooms/', views.hostel_room_list, name='hostel_room_list'),

path('hostel/rooms/add/', views.add_hostel_room, name='add_hostel_room'),

path('hostel/rooms/edit/<int:id>/', views.edit_hostel_room, name='edit_hostel_room'),

path('hostel/rooms/delete/<int:id>/', views.delete_hostel_room, name='delete_hostel_room'),

path('hostel/rooms/print/<int:id>/', views.print_hostel_room, name='print_hostel_room'),

path('hostel/students/', views.student_hostel_list, name='student_hostel_list'),

path('hostel/students/add/', views.add_student_hostel, name='add_student_hostel'),

path('hostel/students/edit/<int:id>/', views.edit_student_hostel, name='edit_student_hostel'),

path('hostel/students/delete/<int:id>/', views.delete_student_hostel, name='delete_student_hostel'),

path('hostel/students/print/<int:id>/', views.print_student_hostel, name='print_student_hostel'),

path('hostel/wardens/', views.hostel_warden_list, name='hostel_warden_list'),

path('hostel/wardens/add/', views.add_hostel_warden, name='add_hostel_warden'),

path('hostel/wardens/edit/<int:id>/', views.edit_hostel_warden, name='edit_hostel_warden'),

path('hostel/wardens/delete/<int:id>/', views.delete_hostel_warden, name='delete_hostel_warden'),

path('hostel/wardens/print/<int:id>/', views.print_hostel_warden, name='print_hostel_warden'),

path('hostel/transfers/', views.hostel_transfer_list, name='hostel_transfer_list'),

path('hostel/transfers/add/', views.add_hostel_transfer, name='add_hostel_transfer'),

path('hostel/transfers/print/<int:id>/', views.print_hostel_transfer, name='print_hostel_transfer'),

path('hostel/occupancy-report/', views.hostel_occupancy_report, name='hostel_occupancy_report'),

path('hostel/occupancy-report/print/<int:id>/', views.print_hostel_occupancy_report, name='print_hostel_occupancy_report'),

path('hostel/beds/', views.hostel_bed_list, name='hostel_bed_list'),

path('hostel/beds/add/', views.add_hostel_bed, name='add_hostel_bed'),

path('hostel/beds/edit/<int:id>/', views.edit_hostel_bed, name='edit_hostel_bed'),

path('hostel/beds/delete/<int:id>/', views.delete_hostel_bed, name='delete_hostel_bed'),

path('hostel/beds/print/<int:id>/', views.print_hostel_bed, name='print_hostel_bed'),

path('hostel/rooms/generate-beds/<int:id>/', views.generate_hostel_beds, name='generate_hostel_beds'),

path('hostel/available-beds/<int:room_id>/', views.available_beds, name='available_beds'),

path('hostel/dashboard/print/', views.print_hostel_dashboard, name='print_hostel_dashboard'),

path('discipline/', views.discipline_case_list, name='discipline_case_list'),

path('discipline/add/', views.add_discipline_case, name='add_discipline_case'),

path('discipline/edit/<int:id>/', views.edit_discipline_case, name='edit_discipline_case'),

path('discipline/delete/<int:id>/', views.delete_discipline_case, name='delete_discipline_case'),

path('discipline/print/<int:id>/', views.print_discipline_case, name='print_discipline_case'),

path('discipline/categories/', views.discipline_category_list, name='discipline_category_list'),

path('discipline/categories/add/', views.add_discipline_category, name='add_discipline_category'),

path('discipline/categories/edit/<int:id>/', views.edit_discipline_category, name='edit_discipline_category'),

path('discipline/categories/delete/<int:id>/', views.delete_discipline_category, name='delete_discipline_category'),

path('discipline/dashboard/', views.discipline_dashboard, name='discipline_dashboard'),

path('discipline/dashboard/print/', views.print_discipline_dashboard, name='print_discipline_dashboard'),

path('medical/medications/', views.medication_list, name='medication_list'),

path('medical/medications/add/', views.add_medication, name='add_medication'),

path('medical/medications/edit/<int:pk>/', views.edit_medication, name='edit_medication'),

path('medical/medications/delete/<int:pk>/', views.delete_medication, name='delete_medication'),

path('medical/medications/print/', views.print_medication_list, name='print_medication_list'),

path('medical/visits/', views.medical_visit_list, name='medical_visit_list'),

path('medical/visits/add/', views.add_medical_visit, name='add_medical_visit'),

path('medical/visits/edit/<int:pk>/', views.edit_medical_visit, name='edit_medical_visit'),

path('medical/visits/delete/<int:pk>/', views.delete_medical_visit, name='delete_medical_visit'),

path('medical/visits/print/<int:pk>/', views.print_medical_visit, name='print_medical_visit'),

path('medical/dashboard/', views.medical_dashboard, name='medical_dashboard'),

path('medical/dashboard/print/', views.print_medical_dashboard, name='print_medical_dashboard'),

path('medical/reports/', views.medical_reports, name='medical_reports'),

path('medical/reports/print/', views.print_medical_reports, name='print_medical_reports'),

path('prescriptions/', views.prescription_list, name='prescription_list'),

path('prescriptions/add/', views.add_prescription, name='add_prescription'),

path('prescriptions/<int:pk>/edit/', views.edit_prescription, name='edit_prescription'),

path('prescriptions/<int:pk>/delete/', views.delete_prescription, name='delete_prescription'),

path('prescriptions/<int:pk>/print/', views.print_prescription, name='print_prescription'),

path('prescriptions/print/', views.print_prescription_register, name='print_prescription_register'),

path('login/', views.login_view, name='login'),

path('change-password/', views.change_password, name='change_password'),

path('profile/', views.profile, name='profile'),

path('timetable/generate/', views.generate_timetable, name='generate_timetable'),

path('register-school/', register_school, name='register_school'),

path( "users/assign-parent/",assign_student_parent,name="assign_student_parent",),

path("sms/",sms_dashboard,name="sms_dashboard",),

path("sms/add-credits/",sms_add_credits,name="sms_add_credits"),

path("sms/packages/",sms_packages,name="sms_packages",),

path("sms/buy/<int:package_id>/",sms_buy_package,name="sms_buy_package",),

path("sms/checkout/<int:purchase_id>/",sms_checkout,name="sms_checkout",),

path("mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),

path("mpesa/pay/", mpesa_stk_push, name="mpesa_stk_push"),



]
