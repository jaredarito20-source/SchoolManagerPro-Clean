from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from decimal import Decimal, InvalidOperation,ROUND_HALF_UP
from students.decorators import (
    admin_or_bursar,
    admin_or_teacher,
     admin_required,
    
)

from django.db import transaction
from django.utils import timezone
from students.utils import (
    get_user_school,
    get_cbc_subject_performance_level,
    cbc_performance_level_label,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from students.models import (
    Teacher,
    Exam,
    
    SchoolClassCurriculum,
    TeacherAssessmentAssignment,
    Student,
    CurriculumLearningArea,
    CurriculumStrand,
    CurriculumSubStrand,
    CBCSubStrandAssessment,
    CBCAssessmentSubmission,
    SchoolUser,
    CBCPerformanceLevel,
    CBCStrandSummativeAssessment,
    CBCSubjectAssessment,
    SchoolAcademicYear,
    SchoolClass,
    CBCUpperSecondaryAssessment,
    CurriculumGrade,
    StudentAcademicEnrollment,
    CurriculumPathway,
    CBCUpperSecondarySubStrandAssessment,
    CBCUpperSecondaryStrandSummativeAssessment,
)


# ============================================================
# CBC HELPERS
# ============================================================

def get_cbc_teacher(request):
    """
    Return the Teacher profile belonging to the logged-in user.

    Superusers are handled separately because they may not have
    a Teacher profile.
    """
    if request.user.is_superuser:
        return None

    return Teacher.objects.filter(
        user=request.user
    ).select_related(
        "school",
        "user",
    ).first()


def get_teacher_assignments(request):
    """
    Return CBC assessment assignments available to the user.

    Ordinary teachers:
        - ONLY their own assignments
        - ONLY assignments belonging to their school

    Superusers:
        - may administer assignments across schools
    """

    base_queryset = TeacherAssessmentAssignment.objects.select_related(
        "teacher",
        "teacher__school",
        "school_class_curriculum",
        "school_class_curriculum__school_class",
        "school_class_curriculum__school_class__school",
        "school_class_curriculum__curriculum_grade",
        "school_class_curriculum__curriculum_version",
        "school_class_curriculum__pathway",
        "learning_area",
        "learning_area__curriculum_grade",
        "learning_area__pathway",
    )

    if request.user.is_superuser:
        return base_queryset.order_by(
            "academic_year",
            "school_class_curriculum__school_class__name",
            "learning_area__name",
        )

    teacher = get_cbc_teacher(request)

    if not teacher or not teacher.school:
        return TeacherAssessmentAssignment.objects.none()

    return base_queryset.filter(
        teacher=teacher,
        teacher__school=teacher.school,
        school_class_curriculum__school_class__school=teacher.school,
    ).order_by(
        "academic_year",
    
        "school_class_curriculum__school_class__name",
        "learning_area__name",
    )


def assignment_belongs_to_user(request, assignment):


    print("=== CBC AUTH DEBUG ===")
    print("REQUEST USER:", request.user)
    print("REQUEST USER ID:", request.user.id)
    print("USERNAME:", request.user.username)
    print("IS SUPERUSER:", request.user.is_superuser)

    school_user = getattr(request.user, "school_user", None)

    print("SCHOOL USER:", school_user)
    print(
        "USER SCHOOL ID:",
        school_user.school_id if school_user else None,
    )

    curriculum = assignment.school_class_curriculum
    school_class = curriculum.school_class if curriculum else None

    print("ASSIGNMENT ID:", assignment.id)
    print("ASSIGNMENT TEACHER ID:", assignment.teacher_id)
    print(
        "ASSIGNMENT CLASS:",
        school_class.name if school_class else None,
    )
    print(
        "ASSIGNMENT CLASS SCHOOL ID:",
        school_class.school_id if school_class else None,
    )

    teacher = get_cbc_teacher(request)

    print("CBC TEACHER:", teacher)
    print(
        "CBC TEACHER ID:",
        teacher.id if teacher else None,
    )
    print(
        "CBC TEACHER USER ID:",
        teacher.user_id if teacher else None,
    )
    print(
        "CBC TEACHER SCHOOL ID:",
        teacher.school_id if teacher else None,
    )

    print("ADMINISTRATOR:", request.user.groups.filter(
        name="Administrators"
    ).exists())

    print("=== END CBC AUTH DEBUG ===")
    """
    Check whether the current user may access a CBC assignment.

    Access rules:
    - Superuser: may access any school.
    - School Administrator: may access assignments belonging
      to their own school.
    - Assigned teacher: may access their own assignment
      within their own school.
    """

    # ---------------------------------------------------------
    # SYSTEM SUPERUSER
    # ---------------------------------------------------------

    if request.user.is_superuser:
        return True

    # ---------------------------------------------------------
    # GET USER'S SCHOOL
    # ---------------------------------------------------------

    school_user = (
        SchoolUser.objects
        .select_related("school", "user")
        .filter(user=request.user)
        .first()
    )

    if not school_user or not school_user.school:
        return False

    user_school_id = school_user.school_id

    # ---------------------------------------------------------
    # ASSIGNMENT SCHOOL
    # ---------------------------------------------------------

    curriculum = assignment.school_class_curriculum

    if not curriculum:
        return False

    school_class = curriculum.school_class

    if not school_class:
        return False

    if school_class.school_id != user_school_id:
        return False

    # ---------------------------------------------------------
    # SCHOOL ADMINISTRATOR
    # ---------------------------------------------------------

    if request.user.groups.filter(
        name="Administrators"
    ).exists():
        return True

    # ---------------------------------------------------------
    # ASSIGNED TEACHER
    # ---------------------------------------------------------

    teacher = get_cbc_teacher(request)

    if not teacher or not teacher.school:
        return False

    if teacher.id != assignment.teacher_id:
        return False

    if teacher.school_id != user_school_id:
        return False

    return True

def curriculum_integrity_is_valid(assignment):
    """
    Validate that the teacher assignment is internally consistent.

    This is important even for superusers.

    Returns:
        True  -> valid
        False -> invalid
    """

    curriculum = assignment.school_class_curriculum
    school_class = curriculum.school_class
    learning_area = assignment.learning_area

    # --------------------------------------------------------
    # The class must actually be CBC.
    # --------------------------------------------------------

    if school_class.curriculum != "CBC":
        return False

    # --------------------------------------------------------
    # Assignment year must match class curriculum year.
    # --------------------------------------------------------

    if curriculum.academic_year != assignment.academic_year:
        return False

    # --------------------------------------------------------
    # Learning area must belong to the same curriculum grade.
    # --------------------------------------------------------

    if learning_area.curriculum_grade_id != curriculum.curriculum_grade_id:
        return False

    grade_code = curriculum.curriculum_grade.grade

    # --------------------------------------------------------
    # Grade 10-12 require a pathway.
    # --------------------------------------------------------

    if grade_code in {"GRADE10", "GRADE11", "GRADE12"}:

        if curriculum.pathway_id is None:
            return False

        if learning_area.pathway_id != curriculum.pathway_id:
            return False

    # --------------------------------------------------------
    # PP1-Grade 9 should use non-pathway learning areas.
    # --------------------------------------------------------

    else:

        if learning_area.pathway_id is not None:
            return False

    return True


# ============================================================
# MY CBC CLASSES
# ============================================================


@login_required
def cbc_my_classes(request):
    """
    Teacher-facing CBC Assessment landing page.

    Shows only CBC classes for which the current user has
    authorized assessment assignments.

    Assessment system:
        - PP1–Grade 9  -> existing qualitative CBC Assessment Book
        - Grade 10–12  -> numerical Upper Secondary Assessment system

    Security:
        - Ordinary teachers only see their own assignments.
        - Ordinary teachers are restricted to their own school.
        - Superusers may see all valid assignments.
        - Invalid curriculum configurations are excluded.
    """

    # ============================================================
    # GET AUTHORIZED CBC ASSIGNMENTS
    # ============================================================

    assignments = (
        get_teacher_assignments(request)
        .select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        )
        .order_by(
            "academic_year",
            "school_class_curriculum__school_class__name",
            "learning_area__name",
        )
    )

    # ============================================================
    # GET TEACHER
    # ============================================================

    teacher = None

    if not request.user.is_superuser:

        teacher = get_cbc_teacher(request)

        if not teacher or not teacher.school:
            return render(
                request,
                "students/cbc/my_classes.html",
                {
                    "classes": [],
                    "assignments": assignments,
                },
                status=403,
            )

    # ============================================================
    # BUILD CLASS ENTRIES
    # ============================================================

    class_entries = {}

    for assignment in assignments:

        # --------------------------------------------------------
        # Assignment must have a curriculum
        # --------------------------------------------------------

        curriculum = assignment.school_class_curriculum

        if not curriculum:
            continue

        # --------------------------------------------------------
        # Curriculum integrity
        # --------------------------------------------------------

        if not curriculum_integrity_is_valid(assignment):
            continue

        # --------------------------------------------------------
        # Get class
        # --------------------------------------------------------

        school_class = curriculum.school_class

        if not school_class:
            continue

        # --------------------------------------------------------
        # CBC class protection
        # --------------------------------------------------------

        if school_class.curriculum != "CBC":
            continue

        # --------------------------------------------------------
        # SCHOOL SECURITY
        # --------------------------------------------------------

        if not request.user.is_superuser:

            # Assignment must belong to logged-in teacher
            if assignment.teacher_id != teacher.id:
                continue

            # Assignment teacher and logged-in teacher must
            # belong to the same school
            if assignment.teacher.school_id != teacher.school_id:
                continue

            # Class must belong to teacher's school
            if school_class.school_id != teacher.school_id:
                continue

        # --------------------------------------------------------
        # DETERMINE CBC ASSESSMENT SYSTEM
        # --------------------------------------------------------

        curriculum_grade = curriculum.curriculum_grade

        if not curriculum_grade:
            continue

        grade_code = (
            curriculum_grade.grade or ""
        ).strip().upper().replace(" ", "")

        # --------------------------------------------------------
        # Grade 10–12 use numerical Upper Secondary Assessment
        # --------------------------------------------------------

        upper_secondary_codes = {
            "GRADE10",
            "GRADE11",
            "GRADE12",
            "10",
            "11",
            "12",
        }

        if grade_code in upper_secondary_codes:
            assessment_system = "upper_secondary"
        else:
            # PP1–Grade 9 continue using the existing
            # qualitative CBC Assessment Book.
            assessment_system = "qualitative"

        # --------------------------------------------------------
        # One entry per:
        #
        # curriculum + academic year
        # --------------------------------------------------------

        key = (
            curriculum.id,
            assignment.academic_year,
        )

        if key not in class_entries:

            class_entries[key] = {
                "curriculum": curriculum,
                "school_class": school_class,
                "academic_year": assignment.academic_year,

                # ------------------------------------------------
                # NEW
                # ------------------------------------------------
                "curriculum_grade": curriculum_grade,
                "grade_code": grade_code,
                "assessment_system": assessment_system,

                # Useful for Grade 10–12 display
                "pathway": curriculum.pathway,
            }

    # ============================================================
    # SORT CLASSES
    # ============================================================

    classes = sorted(
        class_entries.values(),
        key=lambda item: (
            str(item["academic_year"]),
            item["school_class"].name or "",
        ),
    )

    # ============================================================
    # DEBUG
    # ============================================================

    print("=== CBC MY CLASSES RESULT ===")
    print("USER:", request.user.username)
    print("ASSIGNMENTS:", assignments.count())
    print("CLASSES:", len(classes))

    for item in classes:
        print(
            "CLASS:",
            item["school_class"].name,
            "| SCHOOL:",
            item["school_class"].school_id,
            "| YEAR:",
            item["academic_year"],
            "| GRADE:",
            item["grade_code"],
            "| SYSTEM:",
            item["assessment_system"],
            "| PATHWAY:",
            (
                item["pathway"].name
                if item["pathway"]
                else "-"
            ),
        )

    print("=== END CBC MY CLASSES RESULT ===")

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "students/cbc/my_classes.html",
        {
            "classes": classes,
            "assignments": assignments,
        },
    )

@login_required
@admin_or_teacher
def cbc_upper_secondary_strand_classes(request):
    """
    Display Grade 10–12 CBC assignments available for
    Upper Secondary Strand Assessment.

    This is a separate workflow from the existing
    Upper Secondary numerical Mark Entry.
    """

    assignments = get_teacher_assignments(request)

    upper_secondary_assignments = []

    for assignment in assignments:

        # --------------------------------------------------
        # Assignment ownership / school security
        # --------------------------------------------------

        if not assignment_belongs_to_user(request, assignment):
            continue

        # --------------------------------------------------
        # Curriculum integrity
        # --------------------------------------------------

        if not curriculum_integrity_is_valid(assignment):
            continue

        curriculum = assignment.school_class_curriculum

        if not curriculum:
            continue

        # --------------------------------------------------
        # Grade 10–12 only
        # --------------------------------------------------

        grade_code = curriculum.curriculum_grade.grade

        if grade_code not in {"GRADE10", "GRADE11", "GRADE12"}:
            continue

        # --------------------------------------------------
        # Grade 10–12 must have a pathway
        # --------------------------------------------------

        if curriculum.pathway_id is None:
            continue

        if assignment.learning_area.pathway_id != curriculum.pathway_id:
            continue

        upper_secondary_assignments.append(assignment)

    return render(
        request,
        "students/cbc/upper_secondary_strand_classes.html",
        {
            "assignments": upper_secondary_assignments,
        },
    )

@login_required
@admin_or_teacher
def cbc_upper_secondary_strand_assessment(
    request,
    assignment_id,
    strand_id,
):
    """
    Teacher-facing Upper Secondary Strand Assessment Book.

    Grade 10–12 only.

    Teacher enters qualitative performance levels for every
    sub-strand in the selected strand:

        EE = Exceeding Expectations
        ME = Meeting Expectations
        AE = Approaching Expectations
        BE = Below Expectations

    The Strand Summative is automatically calculated from
    ALL assessed sub-strands using the established CBC rule:

        1. Count all assessed sub-strand performance levels.
        2. Select the most frequent level.
        3. If tied, select the higher performance level.

    This workflow is completely separate from the existing
    numerical Upper Secondary Mark Entry.
    """

    # =========================================================
    # LOAD ASSIGNMENT
    # =========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )
    curriculum = assignment.school_class_curriculum

    # =========================================================
    # SECURITY
    # =========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorized to access this assessment assignment."
        )

    if not curriculum_integrity_is_valid(
        assignment
    ):
        messages.error(
            request,
            "This assessment assignment has invalid curriculum configuration.",
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    # =========================================================
    # CLASS CURRICULUM
    # =========================================================

    school_class_curriculum = (
        assignment.school_class_curriculum
    )

    if not school_class_curriculum:
        messages.error(
            request,
            "This assignment is not linked to a class curriculum.",
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    school_class = school_class_curriculum.school_class
    school = school_class.school
    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )
    pathway = school_class_curriculum.pathway
    learning_area = assignment.learning_area

    # =========================================================
    # GRADE 10–12 ONLY
    # =========================================================

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    if (
        grade_code.startswith("GRADE")
        and grade_code[5:].isdigit()
    ):
        grade_code = f"GRADE {grade_code[5:]}"

    if grade_code not in {
        "GRADE 10",
        "GRADE 11",
        "GRADE 12",
    }:
        messages.error(
            request,
            "This assessment book is only available for Grade 10–12.",
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    # =========================================================
    # PATHWAY
    # =========================================================

    if not pathway:
        messages.error(
            request,
            "This Grade 10–12 class does not have a pathway configured.",
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    if learning_area.pathway_id != pathway.id:
        return HttpResponseForbidden(
            "The learning area does not belong to this class pathway."
        )

    # =========================================================
    # ACADEMIC YEAR
    # =========================================================

    try:
        academic_year = int(
            assignment.academic_year
        )

    except (
        TypeError,
        ValueError,
    ):
        messages.error(
            request,
            "Invalid academic year on this assessment assignment.",
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    # =========================================================
    # VERIFY SCHOOL ACADEMIC YEAR
    # =========================================================

    school_academic_year = (
        SchoolAcademicYear.objects.filter(
            school=school,
            year=academic_year,
        ).first()
    )

    if not school_academic_year:
        messages.error(
            request,
            (
                f"Academic year {academic_year} is not "
                "configured for this school."
            ),
        )

        return redirect(
            "students:cbc_upper_secondary_strand_classes"
        )

    # =========================================================
    # STRAND
    #
    # IMPORTANT:
    # The strand MUST belong to this exact learning area.
    # =========================================================

    strand = get_object_or_404(
        CurriculumStrand,
        pk=strand_id,
        learning_area=learning_area,
    )

    # =========================================================
    # SUB-STRANDS
    # =========================================================

    sub_strands = list(
        CurriculumSubStrand.objects.filter(
            strand=strand,
        ).order_by(
            "order",
            "id",
        )
    )

    # =========================================================
    # TERM
    # =========================================================

    valid_terms = {
        "1": "Term 1",
        "2": "Term 2",
        "3": "Term 3",
    }

    selected_term = (
        request.POST.get("term")
        or request.GET.get("term")
        or "1"
    )

    selected_term = str(
        selected_term
    ).strip()

    if selected_term not in valid_terms:
        selected_term = "1"

    # =========================================================
    # ASSESSMENT COMPONENT
    # =========================================================

    valid_components = {
        value
        for value, label in (
            CBCUpperSecondarySubStrandAssessment
            .ASSESSMENT_COMPONENT_CHOICES
        )
    }

    assessment_component = (
        request.POST.get("assessment_component")
        or request.GET.get("assessment_component")
        or "CAT1"
    )

    assessment_component = str(
        assessment_component
    ).strip().upper()

    if assessment_component not in valid_components:
        assessment_component = "CAT1"

    submission = (
        CBCAssessmentSubmission.objects.filter(
            school_class_curriculum=curriculum,
            learning_area=learning_area,
            academic_year=str(academic_year),
            term=selected_term,
            assessment_component=assessment_component,
        )
        .first()
    )

    # =========================================================
    # STUDENTS
    #
    # Students are term-specific.
    # =========================================================

    students = list(
        Student.objects.filter(
            school_id=school.id,
            academic_enrollments__academic_year=str(
                academic_year
            ),
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=(
                school_class.id
            ),
        )
        .distinct()
        .order_by(
            "admission_number",
            "first_name",
            "last_name",
        )
    )

    # =========================================================
    # GET / CREATE SUBMISSION
    #
    # Only when saving.
    # =========================================================

    submission = None

    if request.method == "POST":

        # -----------------------------------------------------
        # SECURITY RECHECK
        # -----------------------------------------------------

        if not assignment_belongs_to_user(
            request,
            assignment,
        ):
            return HttpResponseForbidden(
                "You are not authorized to access this assessment assignment."
            )

        if not curriculum_integrity_is_valid(
            assignment
        ):
            messages.error(
                request,
                "This assessment assignment has invalid curriculum configuration.",
            )

            return redirect(
                "students:cbc_upper_secondary_strand_classes"
            )

        # -----------------------------------------------------
        # CREATE / GET TERM-SPECIFIC SUBMISSION
        # -----------------------------------------------------

        submission, created = (
            CBCAssessmentSubmission.objects.get_or_create(
                school_class_curriculum=(
                    school_class_curriculum
                ),
                learning_area=learning_area,
                academic_year=str(
                    academic_year
                ),
                term=selected_term,
                assessment_component=(
                    assessment_component
                ),
                defaults={
                    "teacher": assignment.teacher,
                    "status": "DRAFT",
                },
            )
        )

        # -----------------------------------------------------
        # APPROVED = LOCKED
        # -----------------------------------------------------

        if submission.status == "APPROVED":
            messages.error(
                request,
                (
                    "This assessment has already been "
                    "approved and cannot be edited."
                ),
            )

            return redirect(
                "students:cbc_upper_secondary_strand_assessment",
                assignment_id=assignment.id,
                strand_id=strand.id,
            )

        # -----------------------------------------------------
        # SUBMISSION OWNER
        # -----------------------------------------------------

        if (
            submission.teacher_id
            != assignment.teacher_id
        ):
            return HttpResponseForbidden(
                "You are not authorized to edit this assessment submission."
            )

        # =====================================================
        # VALIDATE ALL INPUT FIRST
        # =====================================================

        values_to_save = []

        valid_levels = {
            "EE",
            "ME",
            "AE",
            "BE",
        }

        for student in students:

            for sub_strand in sub_strands:

                field_name = (
                    f"level_{student.id}_{sub_strand.id}"
                )

                selected_level = (
                    request.POST.get(
                        field_name,
                        "",
                    )
                    .strip()
                    .upper()
                )

                comment = (
                    request.POST.get(
                        f"comment_{student.id}_{sub_strand.id}",
                        "",
                    )
                    .strip()
                )

                if selected_level and (
                    selected_level
                    not in valid_levels
                ):
                    messages.error(
                        request,
                        (
                            f"Invalid performance level for "
                            f"{student.first_name} "
                            f"{student.last_name} - "
                            f"{sub_strand.name}."
                        ),
                    )

                    return redirect(
                        "students:cbc_upper_secondary_strand_assessment",
                        assignment_id=assignment.id,
                        strand_id=strand.id,
                    )

                values_to_save.append(
                    {
                        "student": student,
                        "sub_strand": sub_strand,
                        "performance_level": selected_level,
                        "teacher_comment": comment,
                    }
                )

        # =====================================================
        # SAVE ATOMICALLY
        # =====================================================

        with transaction.atomic():

            # =================================================
            # 1. SAVE SUB-STRAND ASSESSMENTS
            # =================================================

            for item in values_to_save:

                student = item["student"]
                sub_strand = item["sub_strand"]
                performance_level = (
                    item["performance_level"]
                )
                teacher_comment = (
                    item["teacher_comment"]
                )

                record_filter = {
                    "student": student,
                    "sub_strand": sub_strand,
                    "academic_year": str(
                        academic_year
                    ),
                    "term": selected_term,
                    "assessment_component": (
                        assessment_component
                    ),
                }

                # -------------------------------------------------
                # EMPTY = DELETE
                # -------------------------------------------------

                if (
                    not performance_level
                    and not teacher_comment
                ):
                    (
                        CBCUpperSecondarySubStrandAssessment
                        .objects
                        .filter(
                            **record_filter
                        )
                        .delete()
                    )

                    continue

                # -------------------------------------------------
                # SAVE
                # -------------------------------------------------

                (
                    CBCUpperSecondarySubStrandAssessment
                    .objects
                    .update_or_create(
                        **record_filter,
                        defaults={
                            "submission": submission,
                            "learning_area": learning_area,
                            "strand": strand,
                            "performance_level": (
                                performance_level
                            ),
                            "teacher_comment": (
                                teacher_comment
                            ),
                            "entered_by": request.user,
                        },
                    )
                )

            # =================================================
            # 2. CALCULATE STRAND SUMMATIVE
            # =================================================

            level_values = {
                "BE": 1,
                "AE": 2,
                "ME": 3,
                "EE": 4,
            }

            level_counts_template = {
                "BE": 0,
                "AE": 0,
                "ME": 0,
                "EE": 0,
            }

            for student in students:

                assessments = (
                    CBCUpperSecondarySubStrandAssessment
                    .objects
                    .filter(
                        student=student,
                        sub_strand__strand=strand,
                        academic_year=str(
                            academic_year
                        ),
                        term=selected_term,
                        assessment_component=(
                            assessment_component
                        ),
                        submission=(
                            submission
                        ),
                    )
                    .only(
                        "performance_level",
                    )
                )

                level_counts = (
                    level_counts_template.copy()
                )

                for assessment in assessments:

                    level = (
                        assessment.performance_level
                        or ""
                    ).strip().upper()

                    if level in level_counts:
                        level_counts[level] += 1

                assessed_count = sum(
                    level_counts.values()
                )

                summative_filter = {
                    "student": student,
                    "strand": strand,
                    "academic_year": str(
                        academic_year
                    ),
                    "term": selected_term,
                    "assessment_component": (
                        assessment_component
                    ),
                }

                # -------------------------------------------------
                # NO ASSESSED SUB-STRANDS
                # -------------------------------------------------

                if assessed_count == 0:

                    (
                        CBCUpperSecondaryStrandSummativeAssessment
                        .objects
                        .filter(
                            **summative_filter
                        )
                        .delete()
                    )

                    continue

                # -------------------------------------------------
                # MODE
                #
                # Tie → higher performance level
                # -------------------------------------------------

                summative_level = max(
                    level_counts,
                    key=lambda level: (
                        level_counts[level],
                        level_values[level],
                    ),
                )

                # -------------------------------------------------
                # SAVE STRAND SUMMATIVE
                # -------------------------------------------------

                (
                    CBCUpperSecondaryStrandSummativeAssessment
                    .objects
                    .update_or_create(
                        **summative_filter,
                        defaults={
                            "submission": submission,
                            "learning_area": learning_area,
                            "performance_level": (
                                summative_level
                            ),
                            "entered_by": request.user,
                        },
                    )
                )

        messages.success(
            request,
            (
                f"{strand.name} assessment saved successfully "
                f"for {len(students)} learners."
            ),
        )

        return redirect(
            "students:cbc_upper_secondary_strand_assessment",
            assignment_id=assignment.id,
            strand_id=strand.id,
        )

    # =========================================================
    # EXISTING SUB-STRAND RECORDS
    # =========================================================

    existing_records = {}

    if students and sub_strands:

        records = (
            CBCUpperSecondarySubStrandAssessment
            .objects
            .filter(
                student__in=students,
                sub_strand__in=sub_strands,
                academic_year=str(
                    academic_year
                ),
                term=selected_term,
                assessment_component=(
                    assessment_component
                ),
                submission__school_class_curriculum=(
                    school_class_curriculum
                ),
                submission__learning_area=(
                    learning_area
                ),
            )
        )

        for record in records:

            existing_records[
                (
                    record.student_id,
                    record.sub_strand_id,
                )
            ] = record

    # =========================================================
    # EXISTING STRAND SUMMATIVES
    # =========================================================

    existing_summatives = {}

    if students:

        summatives = (
            CBCUpperSecondaryStrandSummativeAssessment
            .objects
            .filter(
                student__in=students,
                strand=strand,
                academic_year=str(
                    academic_year
                ),
                term=selected_term,
                assessment_component=(
                    assessment_component
                ),
                submission__school_class_curriculum=(
                    school_class_curriculum
                ),
                submission__learning_area=(
                    learning_area
                ),
            )
        )

        for summative in summatives:

            existing_summatives[
                summative.student_id
            ] = summative

    # =========================================================
    # STUDENT ROWS
    # =========================================================

    student_rows = []

    for index, student in enumerate(
        students,
        start=1,
    ):

        sub_strand_rows = []

        for sub_strand in sub_strands:

            sub_strand_rows.append(
                {
                    "sub_strand": sub_strand,
                    "record": existing_records.get(
                        (
                            student.id,
                            sub_strand.id,
                        )
                    ),
                }
            )

        student_rows.append(
            {
                "number": index,
                "student": student,
                "sub_strands": sub_strand_rows,
                "summative": existing_summatives.get(
                    student.id
                ),
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "assignment": assignment,

        "curriculum": school_class_curriculum,

        "school": school,

        "school_class": school_class,

        "curriculum_grade": curriculum_grade,

        "pathway": pathway,

        "learning_area": learning_area,

        "academic_year": academic_year,

        "term": selected_term,

        "selected_term": selected_term,

        "terms": valid_terms.items(),

        "assessment_component": (
            assessment_component
        ),

        "components": (
            CBCUpperSecondarySubStrandAssessment
            .ASSESSMENT_COMPONENT_CHOICES
        ),

        "strand": strand,

        "sub_strands": sub_strands,

        "students": students,

        "student_rows": student_rows,

        "existing_records": existing_records,

        "existing_summatives": existing_summatives,
        "submission": submission,
        "submission_status": submission.status if submission else "",

        "qualitative_levels": [
            {
                "code": "EE",
                "label": "EE — Exceeding Expectations",
            },
            {
                "code": "ME",
                "label": "ME — Meeting Expectations",
            },
            {
                "code": "AE",
                "label": "AE — Approaching Expectations",
            },
            {
                "code": "BE",
                "label": "BE — Below Expectations",
            },
        ],
    }

    return render(
        request,
        "students/cbc/upper_secondary_strand_assessment.html",
        context,
    )

@login_required
@admin_or_teacher
def cbc_upper_secondary_strands(request, assignment_id):
    """
    Display the strands belonging to the teacher's
    Grade 10–12 CBC learning-area assignment.

    This is the intermediate page between:
        Upper Secondary Strand Assessment Classes
    and:
        Individual Strand Assessment Book
    """

    # ============================================================
    # LOAD ASSIGNMENT
    # ============================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # ============================================================
    # SECURITY
    # ============================================================

    if not assignment_belongs_to_user(request, assignment):
        return HttpResponseForbidden(
            "You are not authorized to access this assessment."
        )

    # ============================================================
    # CURRICULUM INTEGRITY
    # ============================================================

    if not curriculum_integrity_is_valid(assignment):
        return HttpResponseForbidden(
            "Invalid CBC curriculum assignment."
        )

    # ============================================================
    # CURRICULUM / CLASS
    # ============================================================

    curriculum = assignment.school_class_curriculum

    if not curriculum:
        return HttpResponseForbidden(
            "This assignment has no school curriculum."
        )

    school_class = curriculum.school_class
    learning_area = assignment.learning_area

    # ============================================================
    # SCHOOL
    # ============================================================

    school = school_class.school

    # ============================================================
    # GRADE
    # ============================================================

    grade_code = curriculum.curriculum_grade.grade

    normalized_grade = str(grade_code).replace(" ", "").upper()

    if normalized_grade not in {
        "GRADE10",
        "GRADE11",
        "GRADE12",
    }:
        return HttpResponseForbidden(
            "Upper Secondary strand assessment is only available "
            "for Grade 10–12."
        )

    # ============================================================
    # PATHWAY
    # ============================================================

    if curriculum.pathway_id is None:
        return HttpResponseForbidden(
            "Upper Secondary classes must have a pathway."
        )

    if learning_area.pathway_id != curriculum.pathway_id:
        return HttpResponseForbidden(
            "Learning area does not belong to this pathway."
        )

    pathway = curriculum.pathway

    # ============================================================
    # ACADEMIC YEAR
    # ============================================================

    academic_year = assignment.academic_year

    try:
        academic_year_int = int(academic_year)
    except (TypeError, ValueError):
        return HttpResponseForbidden(
            "Invalid academic year."
        )

    # ============================================================
    # VERIFY SCHOOL ACADEMIC YEAR
    # ============================================================

    if not SchoolAcademicYear.objects.filter(
        school=school,
        year=academic_year_int,
    ).exists():
        return HttpResponseForbidden(
            "This academic year is not configured for the school."
        )

    # ============================================================
    # GET STRANDS
    # ============================================================

    strands = (
        CurriculumStrand.objects
        .filter(
            learning_area=learning_area,
        )
        .prefetch_related("sub_strands")
        .order_by("order", "id")
    )

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "students/cbc/upper_secondary_strands.html",
        {
            "assignment": assignment,
            "curriculum": curriculum,
            "school": school,
            "school_class": school_class,
            "curriculum_grade": curriculum.curriculum_grade,
            "pathway": pathway,
            "learning_area": learning_area,
            "academic_year": academic_year,
            "strands": strands,
        },
    )
# ============================================================
# SELECT LEARNING AREA
# ============================================================

@login_required
def cbc_learning_areas(
    request,
    school_class_curriculum_id,
    term,
):
    """
    Show Learning Areas assigned to the teacher for this
    CBC class curriculum and academic year.

    IMPORTANT:
    TeacherAssessmentAssignment is NOT term-specific.

    The assignment determines:
        - teacher
        - school
        - class curriculum
        - academic year
        - learning area

    The selected term is used only by the assessment workflow.
    """

    curriculum = get_object_or_404(
        SchoolClassCurriculum.objects.select_related(
            "school_class",
            "school_class__school",
            "curriculum_grade",
            "curriculum_version",
            "pathway",
        ),
        id=school_class_curriculum_id,
    )

    # --------------------------------------------------------
    # The class itself must be CBC.
    # --------------------------------------------------------

    if curriculum.school_class.curriculum != "CBC":
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # --------------------------------------------------------
    # SECURITY: ordinary teacher must belong to same school.
    # --------------------------------------------------------

    if not request.user.is_superuser:

        teacher = get_cbc_teacher(request)

        if not teacher or not teacher.school:
            return render(
                request,
                "students/cbc/access_denied.html",
                status=403,
            )

        if curriculum.school_class.school_id != teacher.school_id:
            return render(
                request,
                "students/cbc/access_denied.html",
                status=403,
            )

        # ----------------------------------------------------
        # IMPORTANT:
        # NO TERM FILTER HERE.
        #
        # Assignment is valid for the whole academic year.
        # ----------------------------------------------------

        assignments = (
            TeacherAssessmentAssignment.objects.filter(
                teacher=teacher,
                teacher__school=teacher.school,
                school_class_curriculum=curriculum,
                academic_year=curriculum.academic_year,
            )
            .select_related(
                "teacher",
                "teacher__school",
                "learning_area",
                "learning_area__curriculum_grade",
                "learning_area__pathway",
            )
        )

    else:

        # ----------------------------------------------------
        # SUPERUSER
        #
        # Also NO TERM FILTER.
        # ----------------------------------------------------

        assignments = (
            TeacherAssessmentAssignment.objects.filter(
                school_class_curriculum=curriculum,
                academic_year=curriculum.academic_year,
            )
            .select_related(
                "teacher",
                "teacher__school",
                "learning_area",
                "learning_area__curriculum_grade",
                "learning_area__pathway",
            )
        )

    # --------------------------------------------------------
    # Remove internally invalid assignments.
    # --------------------------------------------------------

    valid_assignments = []

    for assignment in assignments:

        # Academic year must match the class curriculum.
        if (
            assignment.academic_year
            != curriculum.academic_year
        ):
            continue

        # Curriculum configuration must be valid.
        if not curriculum_integrity_is_valid(
            assignment
        ):
            continue

        # ----------------------------------------------------
        # Ordinary teacher gets an explicit ownership check.
        # ----------------------------------------------------

        if not request.user.is_superuser:

            teacher = get_cbc_teacher(request)

            if not teacher:
                continue

            if assignment.teacher_id != teacher.id:
                continue

            if (
                assignment.teacher.school_id
                != teacher.school_id
            ):
                continue

        valid_assignments.append(
            assignment
        )

    return render(
        request,
        "students/cbc/learning_areas.html",
        {
            "curriculum": curriculum,
            "assignments": valid_assignments,

            # The selected term remains available to the
            # assessment workflow/UI, but does NOT determine
            # teacher authorization.
            "term": term,
        },
    )


@login_required
def cbc_assessment_book(
    request,
    assignment_id,
):

    print(
        "=== CBC ASSESSMENT BOOK ENTERED ===",
        assignment_id,
    )

    """
    Teacher-facing CBC Assessment Book.

    PP1 - Grade 9
        Teacher enters:
            4 = EE
            3 = ME
            2 = AE
            1 = BE

        Strand summative performance is automatically
        calculated from the assessed sub-strands.

    IMPORTANT ARCHITECTURE:

        TeacherAssessmentAssignment
            = NOT term-specific

        CBCAssessmentSubmission
            = term-specific

        CBCSubStrandAssessment
            = term-specific

        CBCStrandSummativeAssessment
            = term-specific

    IMPORTANT GRADE BOUNDARY:

        PP1 - Grade 9
            = New qualitative CBC Assessment Book

        Grade 10+
            = Existing numerical assessment system

        Grade 10 remains CBC, but does NOT use
        this qualitative Assessment Book.
    """

    # =========================================================
    # LOAD ENTRY ASSIGNMENT
    # =========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # =========================================================
    # SECURITY
    # =========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorized to access this assessment assignment."
        )

    if not curriculum_integrity_is_valid(
        assignment
    ):
        messages.error(
            request,
            "This assessment assignment has invalid curriculum configuration.",
        )

        return redirect(
            "students:cbc_my_classes"
        )

    # =========================================================
    # BASIC ASSIGNMENT DATA
    # =========================================================

    school_class_curriculum = (
        assignment.school_class_curriculum
    )

    school_class = (
        school_class_curriculum.school_class
    )

    school = school_class.school

    learning_area = assignment.learning_area

    try:

        academic_year = int(
            assignment.academic_year
        )

    except (
        TypeError,
        ValueError,
    ):

        messages.error(
            request,
            "Invalid academic year on this assessment assignment.",
        )

        return redirect(
            "students:cbc_my_classes"
        )
    
    # =========================================================
    # VERIFY SCHOOL ACADEMIC YEAR
    #
    # The assignment may contain an academic year, but that
    # year must also be configured for the selected school.
    #
    # This prevents CBC assessment records from being opened
    # against an academic year that does not belong to the
    # school.
    # =========================================================

    school_academic_year = (
        SchoolAcademicYear.objects.filter(
            school=school,
            year=academic_year,
        ).first()
    )

    if not school_academic_year:

        messages.error(
            request,
            (
                f"Academic year {academic_year} is not "
                "configured for this school."
            ),
        )

        return redirect(
            "students:cbc_my_classes"
        )



    # =========================================================
    # CURRICULUM GRADE
    # =========================================================

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    # ---------------------------------------------------------
    # NORMALIZE GRADE CODE
    #
    # Database may contain:
    #
    #     GRADE2
    #     GRADE3
    #
    # while the assessment logic uses:
    #
    #     GRADE 2
    #     GRADE 3
    # ---------------------------------------------------------

    if (
        grade_code.startswith("GRADE")
        and grade_code[5:].isdigit()
    ):
        grade_code = f"GRADE {grade_code[5:]}"

    # =========================================================
    # CBC ASSESSMENT BOOK GRADE BOUNDARY
    # =========================================================
    #
    # The new CBC Assessment Book is for:
    #
    #     PP1 - Grade 9
    #
    # Grade 10 and above use the existing numerical
    # assessment system.
    #
    # Grade 10 remains CBC, but it does NOT use this
    # qualitative Assessment Book.
    # =========================================================

    qualitative_grades = {
        "PP1",
        "PP2",
        "GRADE 1",
        "GRADE 2",
        "GRADE 3",
        "GRADE 4",
        "GRADE 5",
        "GRADE 6",
        "GRADE 7",
        "GRADE 8",
        "GRADE 9",
    }

    if grade_code not in qualitative_grades:

        messages.error(
            request,
            (
                f"{grade_code} does not use the PP1–Grade 9 "
                "CBC Assessment Book. Please use the existing "
                "numerical assessment system."
            ),
        )

        return redirect(
            "students:cbc_my_classes"
        )

    is_qualitative_cbc = True
    is_grade_10 = False

    # =========================================================
    # QUALITATIVE LEVELS
    # =========================================================

    qualitative_levels = [
        {
            "code": "4",
            "label": "EE — Exceeding Expectations",
        },
        {
            "code": "3",
            "label": "ME — Meeting Expectations",
        },
        {
            "code": "2",
            "label": "AE — Approaching Expectations",
        },
        {
            "code": "1",
            "label": "BE — Below Expectations",
        },
    ]

    qualitative_level_codes = {
        "1",
        "2",
        "3",
        "4",
    }

    # =========================================================
    # LEGACY COMPATIBILITY
    # =========================================================

    legacy_level_map = {
        "EE": "4",
        "ME": "3",
        "AE": "2",
        "BE": "1",
    }

    # =========================================================
    # ASSESSMENT COMPONENT
    # =========================================================

    valid_components = {
        value
        for value, label
        in (
            CBCSubStrandAssessment
            .ASSESSMENT_COMPONENT_CHOICES
        )
    }

    assessment_component = (
        request.POST.get(
            "assessment_component"
        )
        or request.GET.get(
            "assessment_component"
        )
        or "CAT1"
    )

    if assessment_component not in valid_components:
        assessment_component = "CAT1"

    # =========================================================
    # TERM
    #
    # IMPORTANT:
    # The term belongs to the assessment.
    # It does NOT belong to teacher authorization.
    # =========================================================

    valid_terms = {
        "1": "Term 1",
        "2": "Term 2",
        "3": "Term 3",
    }

    requested_term = (
        request.POST.get("term")
        or request.GET.get("term")
    )

    if requested_term:

        requested_term = str(
            requested_term
        ).strip()

    if requested_term not in valid_terms:
        requested_term = "1"

    selected_term = requested_term

    # =========================================================
    # AUTHORIZED ASSIGNMENTS
    #
    # IMPORTANT:
    # DO NOT FILTER TeacherAssessmentAssignment BY TERM.
    #
    # The teacher's assignment is valid for the academic year.
    #
    # Term applies later to:
    #
    #   - students
    #   - CBCAssessmentSubmission
    #   - CBCSubStrandAssessment
    #   - CBCStrandSummativeAssessment
    # =========================================================

    authorized_assignments = (
        get_teacher_assignments(request)
        .filter(
            academic_year=assignment.academic_year,
            learning_area=learning_area,
        )
        .select_related(
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
        )
    )

    valid_authorized_assignments = []

    for candidate in authorized_assignments:

        if not curriculum_integrity_is_valid(
            candidate
        ):
            continue

        valid_authorized_assignments.append(
            candidate
        )

    # =========================================================
    # AUTHORIZED CLASSES
    # =========================================================

    authorized_classes = []

    seen_class_ids = set()

    for candidate in valid_authorized_assignments:

        candidate_class = (
            candidate
            .school_class_curriculum
            .school_class
        )

        if candidate_class.id in seen_class_ids:
            continue

        authorized_classes.append(
            candidate_class
        )

        seen_class_ids.add(
            candidate_class.id
        )

    authorized_classes.sort(
        key=lambda item: (
            item.name or "",
        )
    )

    # =========================================================
    # SELECT CLASS
    #
    # IMPORTANT:
    # Class authorization is checked against the
    # year-level teacher assignment.
    #
    # NOT against a term-specific assignment.
    # =========================================================

    requested_class_id = (
        request.POST.get("class_id")
        or request.GET.get("class_id")
    )

    if requested_class_id:

        try:

            requested_class_id = int(
                requested_class_id
            )

        except (
            TypeError,
            ValueError,
        ):

            requested_class_id = None

    current_class_id = (
        assignment
        .school_class_curriculum
        .school_class_id
    )

    selected_assignment = None

    if not requested_class_id:

        requested_class_id = current_class_id

    matching_assignments = [
        candidate
        for candidate in valid_authorized_assignments
        if (
            candidate
            .school_class_curriculum
            .school_class_id
            == requested_class_id
        )
    ]

    if matching_assignments:

        selected_assignment = (
            matching_assignments[0]
        )

    else:

        messages.error(
            request,
            (
                "You are not authorized to assess "
                "that class for this academic year."
            ),
        )

        return redirect(
            "students:cbc_my_classes"
        )

    # =========================================================
    # REFRESH SELECTED ASSIGNMENT DATA
    # =========================================================

    school_class_curriculum = (
        selected_assignment
        .school_class_curriculum
    )

    school_class = (
        school_class_curriculum
        .school_class
    )

    school = school_class.school

    learning_area = (
        selected_assignment.learning_area
    )

    curriculum_grade = (
        school_class_curriculum
        .curriculum_grade
    )

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    # ---------------------------------------------------------
    # NORMALIZE GRADE CODE AGAIN
    #
    # This is important because the teacher may have changed
    # the selected class above.
    # ---------------------------------------------------------

    if (
        grade_code.startswith("GRADE")
        and grade_code[5:].isdigit()
    ):
        grade_code = f"GRADE {grade_code[5:]}"

    # =========================================================
    # SECOND GRADE BOUNDARY CHECK
    #
    # This protects the view after class selection.
    #
    # Example:
    #
    # Initial assignment = Grade 2
    # Requested class   = Grade 10
    #
    # The Grade 10 class must NOT enter this Assessment Book.
    # =========================================================

    if grade_code not in qualitative_grades:

        messages.error(
            request,
            (
                f"{grade_code} does not use the PP1–Grade 9 "
                "CBC Assessment Book. Please use the existing "
                "numerical assessment system."
            ),
        )

        return redirect(
            "students:cbc_my_classes"
        )

    is_qualitative_cbc = (
        grade_code in qualitative_grades
    )

    is_grade_10 = (
        grade_code == "GRADE 10"
    )

    try:

        academic_year = int(
            selected_assignment
            .academic_year
        )

    except (
        TypeError,
        ValueError,
    ):

        messages.error(
            request,
            "Invalid academic year on this assessment assignment.",
        )

        return redirect(
            "students:cbc_my_classes"
        )

    # =========================================================
    # STRANDS
    # =========================================================

    strands = list(
        CurriculumStrand.objects.filter(
            learning_area=learning_area,
        ).order_by(
            "order",
            "name",
        )
    )

    requested_strand_id = (
        request.POST.get("strand_id")
        or request.GET.get("strand_id")
    )

    if requested_strand_id:

        try:

            requested_strand_id = int(
                requested_strand_id
            )

        except (
            TypeError,
            ValueError,
        ):

            requested_strand_id = None

    selected_strand = None

    if requested_strand_id:

        selected_strand = next(
            (
                strand
                for strand in strands
                if strand.id
                == requested_strand_id
            ),
            None,
        )

    if (
        selected_strand is None
        and strands
    ):

        selected_strand = strands[0]

    # =========================================================
    # SUB-STRANDS
    # =========================================================

    sub_strands = []

    if selected_strand:

        sub_strands = list(
            CurriculumSubStrand.objects.filter(
                strand=selected_strand,
            ).order_by(
                "order",
                "name",
            )
        )

    requested_sub_strand_id = (
        request.POST.get("sub_strand_id")
        or request.GET.get("sub_strand_id")
    )

    if requested_sub_strand_id:

        try:

            requested_sub_strand_id = int(
                requested_sub_strand_id
            )

        except (
            TypeError,
            ValueError,
        ):

            requested_sub_strand_id = None

    selected_sub_strand = None

    if requested_sub_strand_id:

        selected_sub_strand = next(
            (
                sub_strand
                for sub_strand in sub_strands
                if sub_strand.id
                == requested_sub_strand_id
            ),
            None,
        )

    if (
        selected_sub_strand is None
        and sub_strands
    ):

        selected_sub_strand = sub_strands[0]

    # =========================================================
    # STUDENTS
    #
    # TERM-SPECIFIC
    # =========================================================

    
    students = list(
        Student.objects.filter(
            school_id=school.id,
            academic_enrollments__academic_year=str(
                academic_year
            ),
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=school_class.id,
        )
        .distinct()
        .order_by(
            "admission_number",
            "first_name",
            "last_name",
        )
    )

    
    # =========================================================
    # GRADE 10 PERFORMANCE LEVELS
    #
    # Kept for compatibility with the existing numerical
    # assessment architecture.
    #
    # Because Grade 10+ is blocked above, this Assessment Book
    # will not normally reach this branch.
    # =========================================================

    performance_levels = []

    if is_grade_10:

        performance_levels = list(
            CBCPerformanceLevel.objects.filter(
                curriculum_grade=curriculum_grade,
            ).order_by(
                "order",
            )
        )

    def get_performance_level(mark):

        if mark is None:
            return None

        for level in performance_levels:

            if (
                mark >= level.minimum_mark
                and mark <= level.maximum_mark
            ):
                return level

        return None

    # =========================================================
    # SUBMIT ASSESSMENT
    # =========================================================

    if request.method == "POST":

        # -----------------------------------------------------
        # VALIDATE STRAND
        # -----------------------------------------------------

        if selected_strand is None:

            messages.error(
                request,
                "Please select a strand.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        # -----------------------------------------------------
        # VALIDATE SUB-STRAND
        # -----------------------------------------------------

        if selected_sub_strand is None:

            messages.error(
                request,
                "Please select a sub-strand.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        # -----------------------------------------------------
        # SECURITY RECHECK
        # -----------------------------------------------------

        if not assignment_belongs_to_user(
            request,
            selected_assignment,
        ):

            return HttpResponseForbidden(
                "You are not authorized to access this assessment assignment."
            )

        if not curriculum_integrity_is_valid(
            selected_assignment
        ):

            messages.error(
                request,
                "This assessment assignment has invalid curriculum configuration.",
            )

            return redirect(
                "students:cbc_my_classes"
            )

        if selected_strand.learning_area_id != learning_area.id:
            return HttpResponseForbidden(
                "Invalid strand for this learning area."
            )

        if selected_sub_strand.strand_id != selected_strand.id:
            return HttpResponseForbidden(
                "Invalid sub-strand for this strand."
            )

        # =====================================================
        # SUBMISSION
        #
        # TERM-SPECIFIC
        # =====================================================

        submission, created = (
            CBCAssessmentSubmission.objects.get_or_create(
                school_class_curriculum=(
                    selected_assignment
                    .school_class_curriculum
                ),
                learning_area=(
                    selected_assignment
                    .learning_area
                ),
                academic_year=(
                    selected_assignment
                    .academic_year
                ),
                term=selected_term,
                assessment_component=assessment_component,


                defaults={
                    "teacher": (
                        selected_assignment.teacher
                    ),
                    "status": "DRAFT",
                },
            )
        )

        # -----------------------------------------------------
        # APPROVED CANNOT BE EDITED
        # -----------------------------------------------------

        if submission.status == "APPROVED":

            messages.error(
                request,
                "This assessment has already been approved and cannot be edited.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        # -----------------------------------------------------
        # TEACHER OWNERSHIP
        # -----------------------------------------------------

        if (
            submission.teacher_id
            != selected_assignment.teacher_id
        ):

            messages.error(
                request,
                "You are not authorized to edit this assessment submission.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        # =====================================================
        # VALIDATE ALL CLASS RECORDS FIRST
        # =====================================================

        values_to_save = []

        for student in students:

            teacher_comment = request.POST.get(
                f"comment_{student.id}",
                "",
            ).strip()

            # =================================================
            # PP1 - GRADE 9
            # =================================================

            if is_qualitative_cbc:

                selected_level = request.POST.get(
                    f"level_{student.id}",
                    "",
                ).strip()

                if (
                    selected_level
                    and selected_level
                    not in qualitative_level_codes
                ):

                    messages.error(
                        request,
                        (
                            f"Invalid performance level for "
                            f"{student.first_name} "
                            f"{student.last_name}."
                        ),
                    )

                    return redirect(
                        "students:cbc_assessment_book",
                        assignment_id=selected_assignment.id,
                    )

                values_to_save.append(
                    {
                        "student": student,
                        "mark": None,
                        "performance_level": None,
                        "qualitative_level": (
                            selected_level
                        ),
                        "points": None,
                        "teacher_comment": (
                            teacher_comment
                        ),
                    }
                )

            # =================================================
            # GRADE 10+
            # =================================================

            else:

                mark_value = request.POST.get(
                    f"mark_{student.id}",
                    "",
                ).strip()

                mark = None

                if mark_value:

                    try:

                        mark = Decimal(
                            mark_value
                        )

                    except (
                        InvalidOperation,
                        ValueError,
                    ):

                        messages.error(
                            request,
                            (
                                f"Invalid mark for "
                                f"{student.first_name} "
                                f"{student.last_name}."
                            ),
                        )

                        return redirect(
                            "students:cbc_assessment_book",
                            assignment_id=selected_assignment.id,
                        )

                    if (
                        mark < 0
                        or mark > 100
                    ):

                        messages.error(
                            request,
                            (
                                f"Mark for "
                                f"{student.first_name} "
                                f"{student.last_name} "
                                f"must be between 0 and 100."
                            ),
                        )

                        return redirect(
                            "students:cbc_assessment_book",
                            assignment_id=selected_assignment.id,
                        )

                performance_level = (
                    get_performance_level(mark)
                )

                if (
                    mark is not None
                    and performance_level is None
                    and mark != Decimal("0")
                ):

                    messages.error(
                        request,
                        (
                            f"No CBC performance level is "
                            f"configured for mark {mark} "
                            f"for {student.first_name} "
                            f"{student.last_name}."
                        ),
                    )

                    return redirect(
                        "students:cbc_assessment_book",
                        assignment_id=selected_assignment.id,
                    )

                values_to_save.append(
                    {
                        "student": student,
                        "mark": mark,
                        "performance_level": (
                            performance_level
                        ),
                        "qualitative_level": "",
                        "points": (
                            performance_level.points
                            if performance_level
                            else None
                        ),
                        "teacher_comment": (
                            teacher_comment
                        ),
                    }
                )
        

        # =====================================================
        # SAVE ATOMICALLY
        # =====================================================

        with transaction.atomic():

            # =================================================
            # 1. SAVE / DELETE SUB-STRAND RECORDS
            # =================================================

            for item in values_to_save:

                student = item["student"]

                mark = item["mark"]

                performance_level = (
                    item["performance_level"]
                )

                qualitative_level = (
                    item["qualitative_level"]
                )

                points = item["points"]

                teacher_comment = (
                    item["teacher_comment"]
                )

                existing_filter = {
                    "student": student,
                    "sub_strand": selected_sub_strand,
                    "academic_year": str(academic_year),
                    "term": selected_term,
                    "assessment_component": assessment_component,
                }
                # ---------------------------------------------
                # DELETE EMPTY RECORD
                # ---------------------------------------------

                if (
                    mark is None
                    and not qualitative_level
                    and not teacher_comment
                ):

                    CBCSubStrandAssessment.objects.filter(
                        **existing_filter
                    ).delete()

                else:

                    CBCSubStrandAssessment.objects.update_or_create(
                        **existing_filter,
                        defaults={
                            "submission": submission,
                            "performance_level": (
                                performance_level
                            ),
                            "mark": mark,
                            "points": points,
                            "teacher_comment": (
                                teacher_comment
                            ),
                            "entered_by": request.user,
                            "legacy_performance_level": (
                                qualitative_level
                            ),
                        },
                    )

            # =================================================
            # 2. CALCULATE STRAND SUMMATIVE
            # =================================================

            if is_qualitative_cbc:

                for student in students:

                    strand_assessments = (
                        CBCSubStrandAssessment.objects.filter(
                            student=student,
                            sub_strand__strand=selected_strand,
                            academic_year=str(
                                academic_year
                            ),
                            term=selected_term,
                            assessment_component=(
                                assessment_component
                            ),
                            submission__school_class_curriculum=(
                                selected_assignment
                                .school_class_curriculum
                            ),
                            submission__learning_area=(
                                selected_assignment
                                .learning_area
                            ),
                        )
                    )

                    level_counts = {
                        1: 0,
                        2: 0,
                        3: 0,
                        4: 0,
                    }

                    for assessment in strand_assessments:

                        saved_level = (
                            assessment
                            .legacy_performance_level
                            or ""
                        ).strip().upper()

                        if saved_level in {
                            "1",
                            "2",
                            "3",
                            "4",
                        }:

                            level = int(
                                saved_level
                            )

                            level_counts[level] += 1

                        elif saved_level in legacy_level_map:

                            level = int(
                                legacy_level_map[
                                    saved_level
                                ]
                            )

                            level_counts[level] += 1

                    assessed_count = sum(
                        level_counts.values()
                    )

                    summative_filter = {
                        "student": student,
                        "strand": selected_strand,
                        "academic_year": str(
                            academic_year
                        ),
                        "term": selected_term,
                        "assessment_component": (
                            assessment_component
                        ),
                    }

                    if assessed_count == 0:

                        CBCStrandSummativeAssessment.objects.filter(
                            **summative_filter
                        ).delete()

                        continue

                    summative_level = max(
                        level_counts,
                        key=lambda level: (
                            level_counts[level],
                            level,
                        ),
                    )

                    CBCStrandSummativeAssessment.objects.update_or_create(
                        **summative_filter,
                        defaults={
                            "performance_level": (
                                summative_level
                            ),
                            "entered_by": request.user,
                        },
                    )

        # =====================================================
        # SUCCESS
        # =====================================================

        messages.success(
            request,
            (
                f"{selected_sub_strand.name} "
                f"assessment saved for "
                f"{len(students)} students."
            ),
        )

        return redirect(
            "students:cbc_assessment_book",
            assignment_id=selected_assignment.id,
        )

    # =========================================================
    # EXISTING SUB-STRAND RECORDS
    # =========================================================

    existing_records = {}

    if (
        selected_sub_strand
        and students
    ):

        records = (
            CBCSubStrandAssessment.objects.filter(
                student__in=students,
                sub_strand=selected_sub_strand,
                academic_year=str(
                    academic_year
                ),
                term=selected_term,
                assessment_component=(
                    assessment_component
                ),
                submission__school_class_curriculum=(
                    selected_assignment
                    .school_class_curriculum
                ),
                submission__learning_area=(
                    selected_assignment
                    .learning_area
                ),
            )
            .select_related(
                "performance_level"
            )
        )

        for record in records:

            existing_records[
                record.student_id
            ] = record

    # =========================================================
    # EXISTING STRAND SUMMATIVES
    # =========================================================

    existing_summatives = {}

    if (
        is_qualitative_cbc
        and selected_strand
        and students
    ):

        summative_records = (
            CBCStrandSummativeAssessment.objects.filter(
                student__in=students,
                strand=selected_strand,
                academic_year=str(
                    academic_year
                ),
                term=selected_term,
                assessment_component=(
                    assessment_component
                ),
            )
        )

        for summative in summative_records:

            existing_summatives[
                summative.student_id
            ] = summative

    # =========================================================
    # CLASS LIST
    # =========================================================

    student_rows = []

    for index, student in enumerate(
        students,
        start=1,
    ):

        record = existing_records.get(
            student.id
        )

        summative = existing_summatives.get(
            student.id
        )

        student_rows.append(
            {
                "number": index,
                "student": student,
                "record": record,
                "summative": summative,
            }
        )

    # =========================================================
    # PREVIOUS / NEXT SUB-STRAND
    # =========================================================

    previous_sub_strand = None
    next_sub_strand = None

    if selected_sub_strand:

        current_index = next(
            (
                index
                for index, item
                in enumerate(sub_strands)
                if item.id
                == selected_sub_strand.id
            ),
            None,
        )

        if current_index is not None:

            if current_index > 0:

                previous_sub_strand = (
                    sub_strands[
                        current_index - 1
                    ]
                )

            if (
                current_index
                <
                len(sub_strands) - 1
            ):

                next_sub_strand = (
                    sub_strands[
                        current_index + 1
                    ]
                )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "assignment": selected_assignment,

        "curriculum": (
            school_class_curriculum
        ),

        "school": school,

        "school_class": school_class,

        "learning_area": learning_area,

        "academic_year": academic_year,

        "term": selected_term,

        "selected_term": selected_term,

        "terms": valid_terms,

        "components": (
            CBCSubStrandAssessment
            .ASSESSMENT_COMPONENT_CHOICES
        ),

        "assessment_component": (
            assessment_component
        ),

        "authorized_classes": (
            authorized_classes
        ),

        "selected_class": school_class,

        "strands": strands,

        "selected_strand": selected_strand,

        "sub_strands": sub_strands,

        "selected_sub_strand": (
            selected_sub_strand
        ),

        "students": students,

        "student_rows": student_rows,

        "performance_levels": (
            performance_levels
        ),

        "qualitative_levels": (
            qualitative_levels
        ),

        "is_qualitative_cbc": (
            is_qualitative_cbc
        ),

        "is_grade_10": (
            is_grade_10
        ),

        "previous_sub_strand": (
            previous_sub_strand
        ),

        "next_sub_strand": (
            next_sub_strand
        ),
    }

    return render(
        request,
        "students/cbc/assessment_book.html",
        context,
    )
@login_required
def cbc_assessment_book_print(
    request,
    assignment_id,
    student_id,
):
    """
    Printable CBC Assessment Book for ONE student.

    PP1–Grade 9:
        EE / ME / AE / BE
        No numerical marks
        No points
        Strand summative is automatically calculated
        from the dominant performance level.

    Grade 10:
        Mark
        Performance Level
        Points
    """
     # ========================================================
    # TERM
    # ========================================================

    try:
        term = int(request.GET.get("term", "1"))
    except (TypeError, ValueError):
        term = 1

    if term not in {1, 2, 3}:
        term = 1

    # ========================================================
    # ASSESSMENT COMPONENT
    # ========================================================

    assessment_component = request.GET.get(
        "assessment_component",
        "CAT1",
    )

    valid_components = {
        value
        for value, label
        in CBCSubStrandAssessment.ASSESSMENT_COMPONENT_CHOICES
    }

    if assessment_component not in valid_components:
        assessment_component = "CAT1"

    # ========================================================
    # GET ASSIGNMENT
    # ========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        id=assignment_id,
    )

    # ========================================================
    # SECURITY — ASSIGNMENT
    # ========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # CURRICULUM INTEGRITY
    # ========================================================

    if not curriculum_integrity_is_valid(
        assignment
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # CURRICULUM / CLASS / SCHOOL
    # ========================================================

    curriculum = assignment.school_class_curriculum
    school_class = curriculum.school_class
    school = school_class.school
    learning_area = assignment.learning_area

    academic_year = assignment.academic_year
    curriculum_grade = (
        curriculum.curriculum_grade
    )

    # ========================================================
    # DETERMINE CBC ASSESSMENT MODE
    # ========================================================

    grade_code = (
        str(
            getattr(
                curriculum_grade,
                "grade",
                "",
            )
        )
        .strip()
        .upper()
    )

    qualitative_grades = {
        "PP1",
        "PP2",
        "GRADE 1",
        "GRADE 2",
        "GRADE 3",
        "GRADE 4",
        "GRADE 5",
        "GRADE 6",
        "GRADE 7",
        "GRADE 8",
        "GRADE 9",
    }

    is_qualitative_cbc = (
        grade_code in qualitative_grades
    )

    is_grade_10 = (
        grade_code == "GRADE 10"
    )

    # ========================================================
    # QUALITATIVE DISPLAY LEVELS
    # ========================================================
    #
    # IMPORTANT:
    #
    # The system stores 1-4 internally.
    #
    # The Assessment Book NEVER displays those numbers.
    #
    # ========================================================

    qualitative_levels = [
        {
            "code": "EE",
            "label": "EE — Exceeding Expectations",
        },
        {
            "code": "ME",
            "label": "ME — Meeting Expectations",
        },
        {
            "code": "AE",
            "label": "AE — Approaching Expectations",
        },
        {
            "code": "BE",
            "label": "BE — Below Expectations",
        },
    ]

    # --------------------------------------------------------
    # Internal numeric -> visible qualitative label
    # --------------------------------------------------------

    numeric_to_qualitative = {
        "4": "EE",
        "3": "ME",
        "2": "AE",
        "1": "BE",
    }

    legacy_to_qualitative = {
        "EE": "EE",
        "ME": "ME",
        "AE": "AE",
        "BE": "BE",
    }

    # ========================================================
    # GRADE 10 PERFORMANCE LEVELS ONLY
    # ========================================================

    if is_grade_10:

        performance_levels = (
            CBCPerformanceLevel.objects.filter(
                curriculum_grade=curriculum_grade,
            )
            .order_by(
                "order",
                "minimum_mark",
            )
        )

    else:

        performance_levels = []

    # ========================================================
    # GET STUDENT
    # ========================================================

    student = get_object_or_404(
        Student.objects.select_related(
            "school",
            "school_class",
        ),
        id=student_id,
    )

    # ========================================================
    # STUDENT SECURITY
    # ========================================================

    if student.school_id != school.id:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    if student.school_class_id != school_class.id:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # STRANDS
    # ========================================================

    strands = (
        CurriculumStrand.objects.filter(
            learning_area=learning_area,
        )
        .order_by(
            "order",
            "id",
        )
    )

    # ========================================================
    # BUILD PRINTABLE DATA
    # ========================================================

    printable_strands = []

    for strand in strands:

        sub_strands = (
            CurriculumSubStrand.objects.filter(
                strand=strand,
            )
            .order_by(
                "order",
                "id",
            )
        )

        printable_sub_strands = []

        for sub_strand in sub_strands:

            # ------------------------------------------------
            # GET SAVED ASSESSMENT
            # ------------------------------------------------

            assessment = (
                CBCSubStrandAssessment.objects.filter(
                    student=student,
                    sub_strand=sub_strand,
                    academic_year=academic_year,
                    term=term,
                    assessment_component=(
                        assessment_component
                    ),
                    submission__school_class_curriculum=(
                        curriculum
                    ),
                    submission__learning_area=(
                        learning_area
                    ),
                )
                .select_related(
                    "performance_level",
                    "submission",
                )
                .first()
            )

            # ------------------------------------------------
            # DEFAULT VALUES
            # ------------------------------------------------

            saved_mark = None
            saved_performance_level = None
            saved_points = None

            # Visible PP1–Grade 9 level
            saved_qualitative_level = ""

            saved_comment = ""

            # ------------------------------------------------
            # LOAD SAVED DATA
            # ------------------------------------------------

            if assessment is not None:

                # =================================================
                # GRADE 10
                # =================================================

                if is_grade_10:

                    saved_mark = assessment.mark

                    saved_performance_level = (
                        assessment.performance_level
                    )

                    if saved_performance_level is not None:

                        saved_points = (
                            saved_performance_level.points
                        )

                # =================================================
                # PP1–GRADE 9
                # =================================================

                elif is_qualitative_cbc:

                    raw_level = (
                        assessment
                        .legacy_performance_level
                        or ""
                    ).strip().upper()

                    # ---------------------------------------------
                    # New internal numeric values
                    #
                    # NEVER expose these numbers to the user.
                    # ---------------------------------------------

                    if raw_level in numeric_to_qualitative:

                        saved_qualitative_level = (
                            numeric_to_qualitative[
                                raw_level
                            ]
                        )

                    # ---------------------------------------------
                    # Old EE / ME / AE / BE records
                    # ---------------------------------------------

                    elif raw_level in legacy_to_qualitative:

                        saved_qualitative_level = (
                            legacy_to_qualitative[
                                raw_level
                            ]
                        )

                # =================================================
                # TEACHER COMMENT
                # =================================================

                saved_comment = (
                    assessment.teacher_comment
                    or ""
                )
            

            # ------------------------------------------------
            # PRINT ROW
            # ------------------------------------------------

            printable_sub_strands.append(
                {
                    "sub_strand": sub_strand,

                    # Grade 10
                    "mark": saved_mark,

                    "performance_level": (
                        saved_performance_level
                    ),

                    "points": saved_points,

                    # PP1–Grade 9
                    # Visible EE / ME / AE / BE only
                    "qualitative_level": (
                        saved_qualitative_level
                    ),

                    # Both
                    "comment": saved_comment,

                    "assessment": assessment,
                }
            )

        # ====================================================
        # STRAND SUMMATIVE
        # ====================================================
        #
        # PP1–Grade 9 only.
        #
        # This is already calculated and stored by the
        # assessment-book save process.
        #
        # The number is NEVER displayed.
        #
        # ====================================================

        summative = None
        summative_label = ""

        if is_qualitative_cbc:

            summative = (
                CBCStrandSummativeAssessment.objects.filter(
                    student=student,
                    strand=strand,
                    academic_year=str(
                        academic_year
                    ),
                    term=term,
                    assessment_component=(
                        assessment_component
                    ),
                )
                .first()
            )

            if summative is not None:

                summative_label = (
                    numeric_to_qualitative.get(
                        str(
                            summative.performance_level
                        ),
                        "",
                    )
                )

        # ====================================================
        # ADD STRAND
        # ====================================================

        printable_strands.append(
            {
                "strand": strand,

                "sub_strands": (
                    printable_sub_strands
                ),

                # PP1–Grade 9
                "summative": summative,

                # Human-readable only
                "summative_label": (
                    summative_label
                ),
            }
        )

    # ========================================================
    # PRINT
    # ========================================================

    return render(
        request,
        "students/cbc/assessment_book_print.html",
        {
            "assignment": assignment,

            "curriculum": curriculum,

            "school": school,

            "school_class": school_class,

            "learning_area": learning_area,

            "academic_year": academic_year,

            "term": term,

            "assessment_component": (
                assessment_component
            ),

            # ONE STUDENT
            "student": student,

            # PRINT DATA
            "strands": printable_strands,

            # ASSESSMENT MODE
            "is_qualitative_cbc": (
                is_qualitative_cbc
            ),

            "is_grade_10": (
                is_grade_10
            ),

            # QUALITATIVE DISPLAY LEVELS
            "qualitative_levels": (
                qualitative_levels
            ),

            # GRADE 10 LEVELS
            "performance_levels": (
                performance_levels
            ),
        },
    )

@login_required
@admin_or_teacher
def cbc_subject_score_sheet(request):
    """
    CBC Subject Score Sheet

    PP1–Grade 9:
        Teacher/Admin enters numerical subject scores.

        CAT 1
        Mid-Term
        End-Term

        The system calculates:
            Average
            Performance Level

        Performance bands:

            75–100 -> EE
            50–74  -> ME
            25–49  -> AE
            0–24   -> BE

    Numerical scores are stored internally.

    Grade 10–12 continue using the existing numerical
    assessment system and are excluded here.
    """

    # =========================================================
    # ASSESSMENT COMPONENTS
    # =========================================================

    assessment_components = [
        ("CAT1", "CAT 1"),
        ("MID", "Mid-Term"),
        ("END", "End-Term"),
    ]

    valid_components = {
        "CAT1": "CAT 1",
        "MID": "Mid-Term",
        "END": "End-Term",
    }

    # =========================================================
    # BASE ASSIGNMENTS
    # =========================================================

    assignments = (
        TeacherAssessmentAssignment.objects
        .select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        )
    )

    # =========================================================
    # SCHOOL / TEACHER SECURITY
    # =========================================================

    if not request.user.is_superuser:

        school_user = (
            SchoolUser.objects
            .select_related(
                "school",
                "user",
            )
            .filter(
                user=request.user,
            )
            .first()
        )

        if not school_user or not school_user.school:
            return HttpResponseForbidden(
                "Your account is not associated with a school."
            )

        user_school_id = school_user.school_id

        # -----------------------------------------------------
        # SCHOOL ADMINISTRATOR
        # -----------------------------------------------------

        if request.user.groups.filter(
            name="Administrators"
        ).exists():

            assignments = assignments.filter(
                school_class_curriculum__school_class__school_id=(
                    user_school_id
                ),
            )

        # -----------------------------------------------------
        # TEACHER
        # -----------------------------------------------------

        else:

            teacher = get_cbc_teacher(request)

            if not teacher or not teacher.school:
                return HttpResponseForbidden(
                    "Your account does not have a valid teacher profile."
                )

            if teacher.school_id != user_school_id:
                return HttpResponseForbidden(
                    "Your teacher profile is not associated "
                    "with your school."
                )

            assignments = assignments.filter(
                teacher=teacher,
                teacher__school_id=user_school_id,
                school_class_curriculum__school_class__school_id=(
                    user_school_id
                ),
            )

    # =========================================================
    # VALID ASSIGNMENTS
    # =========================================================

    valid_assignments = []

    for assignment in assignments:

        if not assignment_belongs_to_user(
            request,
            assignment,
        ):
            continue

        if not curriculum_integrity_is_valid(
            assignment,
        ):
            continue

        curriculum = assignment.school_class_curriculum

        school_class = curriculum.school_class

        if not school_class:
            continue

        curriculum_grade = curriculum.curriculum_grade

        grade_code = str(
            getattr(
                curriculum_grade,
                "grade",
                "",
            )
        ).strip().upper()

        # -----------------------------------------------------
        # Grade 10–12 remain on existing system.
        # -----------------------------------------------------

        if grade_code in {
            "GRADE 10",
            "GRADE 11",
            "GRADE 12",
            "10",
            "11",
            "12",
        }:
            continue

        valid_assignments.append(
            assignment
        )

    # =========================================================
    # SORT ASSIGNMENTS
    # =========================================================

    valid_assignments.sort(
        key=lambda assignment: (
            str(assignment.academic_year),
            
            (
                assignment
                .school_class_curriculum
                .school_class
                .name
                or ""
            ),
            (
                assignment
                .learning_area
                .name
                or ""
            ),
        )
    )

    # =========================================================
    # CURRENT SELECTION
    # =========================================================

    selected_assignment_id = (
        request.GET.get("assignment")
        or request.POST.get("assignment")
    )

    selected_component = (
        request.GET.get("assessment_component")
        or request.POST.get("assessment_component")
        or "CAT1"
    )

    selected_component = (
        str(selected_component)
        .strip()
        .upper()
    )
    selected_term = (
        request.GET.get("term")
        or request.POST.get("term")
        or "1"
    )

    selected_term = (
        str(selected_term)
        .strip()
    )

    valid_terms = {
        "1": "Term 1",
        "2": "Term 2",
        "3": "Term 3",
    }

    if selected_term not in valid_terms:
        selected_term = "1"

    # =========================================================
    # VALIDATE COMPONENT
    # =========================================================

    if selected_component not in valid_components:
        selected_component = "CAT1"

    selected_assignment = None

    # =========================================================
    # VALIDATE ASSIGNMENT ID
    # =========================================================

    if selected_assignment_id:

        try:
            selected_assignment_id = int(
                selected_assignment_id
            )

        except (
            TypeError,
            ValueError,
        ):
            selected_assignment_id = None

    # =========================================================
    # FIND AUTHORIZED ASSIGNMENT
    # =========================================================

    if selected_assignment_id:

        selected_assignment = next(
            (
                assignment
                for assignment in valid_assignments
                if assignment.id == selected_assignment_id
            ),
            None,
        )

    # =========================================================
    # DEFAULT ASSIGNMENT
    # =========================================================

    if (
        selected_assignment is None
        and len(valid_assignments) == 1
    ):
        selected_assignment = valid_assignments[0]

    # =========================================================
    # INITIAL VALUES
    # =========================================================

    academic_year = ""
    term = selected_term
    school_class = None
    learning_area = None
    students = []
    marks_out_of = None

    # =========================================================
    # LOAD SELECTED ASSIGNMENT
    # =========================================================

    if selected_assignment:

        # -----------------------------------------------------
        # FINAL SECURITY CHECK
        # -----------------------------------------------------

        if not assignment_belongs_to_user(
            request,
            selected_assignment,
        ):
            return HttpResponseForbidden(
                "You are not authorized to access this "
                "assessment assignment."
            )

        if not curriculum_integrity_is_valid(
            selected_assignment,
        ):
            return HttpResponseForbidden(
                "Invalid curriculum assignment."
            )

        school_class = (
            selected_assignment
            .school_class_curriculum
            .school_class
        )

        learning_area = (
            selected_assignment
            .learning_area
        )

        academic_year = str(
            selected_assignment.academic_year
        )

        school = school_class.school

        selected_exam = get_cbc_open_exam(
            school=school,
            academic_year=academic_year,
            term=term,
            assessment_component=selected_component,
        )

        # -----------------------------------------------------
        # EXAM MAXIMUM MARKS
        # -----------------------------------------------------

        if selected_exam:
            marks_out_of = selected_exam.marks_out_of
        

        # -----------------------------------------------------
        # Grade 10–12 protection
        # -----------------------------------------------------

        grade_code = str(
            getattr(
                selected_assignment
                .school_class_curriculum
                .curriculum_grade,
                "grade",
                "",
            )
        ).strip().upper()

        if grade_code in {
            "GRADE 10",
            "GRADE 11",
            "GRADE 12",
            "10",
            "11",
            "12",
        }:

            return HttpResponseForbidden(
                "Grade 10 and above use the existing "
                "numerical assessment system."
            )

        
        # =====================================================
        # STUDENTS
        #
        # TERM-SPECIFIC ENROLLMENT
        #
        # A learner must be enrolled in this exact:
        #
        #   school
        #   class
        #   academic year
        #   term
        #
        # Student.school_class is NOT used as the source of
        # term-specific class membership.
        # =====================================================

        students = list(
            Student.objects
            .filter(
                school_id=school.id,
                academic_enrollments__academic_year=academic_year,
                academic_enrollments__term=term,
                academic_enrollments__school_class_id=school_class.id,
            )
            .distinct()
            .order_by(
                "admission_number",
                "first_name",
                "last_name",
            )
        )


    # =========================================================
    # LOAD ALL THREE SUBJECT ASSESSMENT COMPONENTS
    # =========================================================

    component_records = {
        "CAT1": {},
        "MID": {},
        "END": {},
    }

    if (
        selected_assignment
        and students
    ):

        existing_scores = (
            CBCSubjectAssessment.objects
            .filter(
                student__in=students,
                learning_area=learning_area,
                academic_year=academic_year,
                term=term,
                assessment_component__in=[
                    "CAT1",
                    "MID",
                    "END",
                ],
            )
            .select_related(
                "student",
            )
        )

        for record in existing_scores:

            component = (
                record.assessment_component
            )

            if component not in component_records:
                continue

            component_records[
                component
            ][record.student_id] = record
    # =========================================================
    # CBC SUBMISSION STATUS
     # Available for both GET and POST
    # =========================================================
    
    existing_submission = None
    
    if selected_assignment:
            existing_submission = (
            CBCAssessmentSubmission.objects.filter(
                school_class_curriculum=selected_assignment.school_class_curriculum,
                learning_area=learning_area,
                academic_year=academic_year,
                term=term,
                assessment_component=selected_component,
                )
                .first()
                )

    # =========================================================
    # POST — SAVE SELECTED COMPONENT
    # =========================================================

    # =========================================================
    # POST — SAVE SELECTED COMPONENT
    # =========================================================

    if (
        request.method == "POST"
        and selected_assignment
    ):
        # -----------------------------------------------------
        # SUBMIT CBC ASSESSMENT
        # -----------------------------------------------------

        post_action = (
            request.POST.get("action", "")
            .strip()
            .lower()
        )

        if post_action == "submit":

            submission = (
                CBCAssessmentSubmission.objects.filter(
                    school_class_curriculum=(
                        selected_assignment.school_class_curriculum
                    ),
                    learning_area=learning_area,
                    academic_year=academic_year,
                    term=term,
                    assessment_component=selected_component,
                )
                .first()
            )

            if not submission:
                messages.error(
                    request,
                    "There is no saved CBC assessment to submit."
                )

                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            if (
                submission.teacher_id
                != selected_assignment.teacher_id
            ):
                return HttpResponseForbidden(
                    "This CBC assessment submission belongs "
                    "to another teacher."
                )

            if submission.status == "SUBMITTED":
                messages.info(
                    request,
                    "This CBC assessment has already been submitted."
                )

                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            if submission.status == "APPROVED":
                messages.info(
                    request,
                    "This CBC assessment has already been approved."
                )

                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            if submission.status == "REJECTED":
                submission.status = "DRAFT"
                submission.rejection_reason = ""
                submission.save(
                    update_fields=[
                        "status",
                        "rejection_reason",
                        "updated_at",
                    ]
                )

            elif submission.status != "DRAFT":
                messages.error(
                    request,
                    "This CBC assessment cannot be submitted "
                    f"while its status is {submission.status}."
                )
                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            submission.status = "SUBMITTED"
            submission.submitted_at = timezone.now()
            submission.save(
                update_fields=[
                    "status",
                    "submitted_at",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "CBC assessment submitted successfully."
            )

            return redirect(
                request.path
                + f"?assignment={selected_assignment.id}"
                + f"&assessment_component={selected_component}"
                + f"&term={term}"
            )

    

        # -----------------------------------------------------
        # SECURITY
        # -----------------------------------------------------

        if not assignment_belongs_to_user(
            request,
            selected_assignment,
        ):
            return HttpResponseForbidden(
                "You are not authorized to enter scores "
                "for this assignment."
            )

        if not curriculum_integrity_is_valid(
            selected_assignment,
        ):
            return HttpResponseForbidden(
                "Invalid curriculum assignment."
            )

        # -----------------------------------------------------
        # Grade protection
        # -----------------------------------------------------

        grade_code = str(
            getattr(
                selected_assignment
                .school_class_curriculum
                .curriculum_grade,
                "grade",
                "",
            )
        ).strip().upper()

        if grade_code in {
            "GRADE 10",
            "GRADE 11",
            "GRADE 12",
            "10",
            "11",
            "12",
        }:

            return HttpResponseForbidden(
                "Grade 10 and above use the existing "
                "numerical assessment system."
            )

                # -----------------------------------------------------
        # CBC EXAM MUST BE OPEN
        # -----------------------------------------------------

        if not selected_exam:
            messages.error(
                request,
                "This assessment cannot be entered because "
                "the corresponding exam is not OPEN."
            )

            return redirect(
                request.path
                + f"?assignment={selected_assignment.id}"
                + f"&assessment_component={selected_component}"
                + f"&term={term}"
            )
        # -----------------------------------------------------
        # CBC SUBMISSION MUST BE DRAFT FOR MARK EDITING
        # -----------------------------------------------------

        

        if existing_submission:

            if existing_submission.teacher_id != selected_assignment.teacher_id:
                return HttpResponseForbidden(
                    "This CBC assessment submission belongs to another teacher."
                )

            if existing_submission.status == "SUBMITTED":
                messages.error(
                    request,
                    "This CBC assessment has already been submitted and cannot be edited."
                )
                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            if existing_submission.status == "APPROVED":
                messages.error(
                    request,
                    "This CBC assessment has already been approved and cannot be edited."
                )
                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

        # =====================================================
        # SAVE ATOMICALLY
        # =====================================================

        with transaction.atomic():

            # -------------------------------------------------
            # GET OR CREATE CBC SUBMISSION
            # -------------------------------------------------

            submission, created = (
                CBCAssessmentSubmission.objects.get_or_create(
                    school_class_curriculum=(
                        selected_assignment.school_class_curriculum
                    ),
                    learning_area=learning_area,
                    academic_year=academic_year,
                    term=term,
                    assessment_component=selected_component,
                    defaults={
                        "teacher": selected_assignment.teacher,
                        "status": "DRAFT",
                    },
                )
            )

            # -------------------------------------------------
            # VERIFY SUBMISSION OWNER
            # -------------------------------------------------

            if (
                submission.teacher_id
                != selected_assignment.teacher_id
            ):
                messages.error(
                    request,
                    (
                        "This CBC assessment submission "
                        "belongs to another teacher."
                    ),
                )

                return redirect(
                    request.path
                    + f"?assignment={selected_assignment.id}"
                    + f"&assessment_component={selected_component}"
                    + f"&term={term}"
                )

            for student in students:

                field_name = (
                    f"score_{student.id}"
                )

                raw_score = (
                    request.POST
                    .get(
                        field_name,
                        "",
                    )
                    .strip()
                )

                # -------------------------------------------------
                # EMPTY SCORE
                # -------------------------------------------------

                if raw_score == "":

                    CBCSubjectAssessment.objects.filter(
                        student=student,
                        learning_area=learning_area,
                        academic_year=academic_year,
                        term=term,
                        assessment_component=(
                            selected_component
                        ),
                    ).delete()

                    continue

                # -------------------------------------------------
                # VALIDATE DECIMAL
                # -------------------------------------------------

                try:

                    score = Decimal(
                        raw_score
                    )

                except (
                    InvalidOperation,
                    TypeError,
                    ValueError,
                ):

                    messages.error(
                        request,
                        (
                            f"Invalid score for "
                            f"{student.first_name} "
                            f"{student.last_name}."
                        ),
                    )

                    return redirect(
                        request.path
                        + f"?assignment={selected_assignment.id}"
                        + f"&assessment_component={selected_component}"
                    )

                # -------------------------------------------------
                # RAW SCORE RANGE
                # -------------------------------------------------

                if score < 0 or score > marks_out_of:

                    messages.error(
                        request,
                        (
                            f"Score for "
                            f"{student.first_name} "
                            f"{student.last_name} "
                            f"must be between 0 and "
                            f"{marks_out_of}."
                        ),
                    )

                    return redirect(
                        request.path
                        + f"?assignment={selected_assignment.id}"
                        + f"&assessment_component={selected_component}"
                        + f"&term={term}"
                    )

                # -------------------------------------------------
                # CONVERT RAW SCORE TO PERCENTAGE
                # -------------------------------------------------

                percentage_score = (
                    (score / marks_out_of)
                    * Decimal("100")
                ).quantize(
                    Decimal("0.01")
                )
                # -------------------------------------------------
                # DERIVE PERFORMANCE LEVEL
                # -------------------------------------------------

                performance_level = (
                    get_cbc_subject_performance_level(
                        percentage_score
                    )
                )

                # -------------------------------------------------
                # SAVE
                # -------------------------------------------------

                CBCSubjectAssessment.objects.update_or_create(
                    student=student,
                    learning_area=learning_area,
                    academic_year=academic_year,
                    term=term,
                    assessment_component=(
                        selected_component
                    ),
                    defaults={
                        "submission": submission,
                        "score": percentage_score,
                        "performance_level": (
                            performance_level
                        ),
                        "entered_by": request.user,
                    },
                )

        # =====================================================
        # SUCCESS
        # =====================================================

        messages.success(
            request,
            (
                f"{valid_components[selected_component]} "
                f"scores saved successfully."
            ),
        )

        return redirect(
            request.path
            + f"?assignment={selected_assignment.id}"
            + f"&assessment_component={selected_component}"
        )

    # =========================================================
    # PREPARE DISPLAY ROWS
    # =========================================================

    student_rows = []

    for index, student in enumerate(
        students,
        start=1,
    ):

        cat1_record = (
            component_records["CAT1"]
            .get(student.id)
        )

        mid_record = (
            component_records["MID"]
            .get(student.id)
        )

        end_record = (
            component_records["END"]
            .get(student.id)
        )

        # -----------------------------------------------------
        # Extract scores
        # -----------------------------------------------------

        cat1_score = (
            cat1_record.score
            if cat1_record
            and cat1_record.score is not None
            else None
        )

        mid_score = (
            mid_record.score
            if mid_record
            and mid_record.score is not None
            else None
        )

        end_score = (
            end_record.score
            if end_record
            and end_record.score is not None
            else None
        )

        # -----------------------------------------------------
        # Calculate final average ONLY when all 3 exist
        # -----------------------------------------------------

        average = None
        performance_level = None
        performance_label = ""

        if (
            cat1_score is not None
            and mid_score is not None
            and end_score is not None
        ):

            average = (
                (
                    cat1_score
                    + mid_score
                    + end_score
                ) / Decimal("3")
            ).quantize(
                Decimal("0.01")
            )

            performance_level = (
                get_cbc_subject_performance_level(
                    average
                )
            )

            performance_label = (
                cbc_performance_level_label(
                    performance_level
                )
            )

        # -----------------------------------------------------
        # Selected component record
        # -----------------------------------------------------

        selected_record = (
            component_records[
                selected_component
            ].get(student.id)
        )

        # -----------------------------------------------------
        # Selected component performance
        # -----------------------------------------------------

        selected_performance_level = None
        selected_performance_label = ""

        if selected_record:

            selected_performance_level = (
                selected_record.performance_level
            )

            selected_performance_label = (
                cbc_performance_level_label(
                    selected_performance_level
                )
            )

                # -----------------------------------------------------
        # SELECTED COMPONENT RAW SCORE
        # -----------------------------------------------------

        selected_raw_score = None

        if (
            selected_record
            and selected_record.score is not None
            and marks_out_of
        ):
            selected_raw_score = (
                (
                    selected_record.score
                    * marks_out_of
                )
                / Decimal("100")
            ).quantize(
                Decimal("0.01")
            )

        student_rows.append(
            {
                "number": index,

                "student": student,

                "record": selected_record,

                "cat1_score": cat1_score,

                "mid_score": mid_score,

                "end_score": end_score,

                "average": average,

                "performance_level": (
                    performance_level
                ),

                "performance_label": (
                    performance_label
                ),
                

                "selected_performance_level": (
                    selected_performance_level
                ),

                "selected_performance_label": (
                    selected_performance_label
                ),

                "selected_raw_score": (selected_raw_score,
                ),                      
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "assignments": valid_assignments,

        "selected_assignment": (
            selected_assignment
        ),

        "selected_component": (
            selected_component
        ),

        "assessment_components": (
            assessment_components
        ),

        "assessment_component_label": (
            valid_components.get(
                selected_component,
                "CAT 1",
            )
        ),
        
        "marks_out_of": marks_out_of,

        "academic_year": academic_year,

        "term": term,

        "school_class": school_class,

        "learning_area": learning_area,

        "submission_status": (
            existing_submission.status
            if existing_submission
            else None
        ),

        "rejection_reason": (
            existing_submission.rejection_reason
            if existing_submission
            and existing_submission.status == "REJECTED"
            else ""
        ),

        "student_rows": student_rows,
    }

    return render(
        request,
        "students/cbc_subject_score_sheet.html",
        context,
    )

def get_upper_secondary_performance(
    *,
    curriculum_grade,
    percentage,
):
    """
    Convert a normalized percentage into the CBC performance
    level and points configured for the curriculum grade.

    This is used by Grade 10-12 numerical assessment.

    Performance bands are read from CBCPerformanceLevel rather
    than hard-coded, allowing curriculum grading structures to
    change safely.
    """

    if curriculum_grade is None or percentage is None:
        return None, None

    try:
        percentage = Decimal(str(percentage))
    except (TypeError, ValueError, InvalidOperation):
        return None, None

    if percentage < Decimal("0") or percentage > Decimal("100"):
        return None, None

    performance_level = (
        CBCPerformanceLevel.objects
        .filter(
            curriculum_grade=curriculum_grade,
            minimum_mark__lte=percentage,
            maximum_mark__gte=percentage,
        )
        .order_by("order", "minimum_mark")
        .first()
    )

    if not performance_level:
        return None, None

    return performance_level, performance_level.points


@login_required
@admin_or_teacher
def cbc_upper_secondary_assessment_book(
    request,
    assignment_id,
):
    """
    Grade 10-12 CBC Subject Assessment Book.

    Teacher enters raw marks for:
        CAT 1
        MID TERM
        END TERM

    The system calculates:
        normalized percentage
        performance level
        points

    Teacher assignments are NOT term-specific.
    The selected term controls:
        - student enrollment
        - assessment records
        - open examinations
    """

    # =========================================================
    # LOAD ASSIGNMENT
    # =========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # =========================================================
    # SECURITY
    # =========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorised to access this assessment book."
        )

    if not curriculum_integrity_is_valid(
        assignment,
    ):
        return HttpResponseForbidden(
            "The curriculum configuration for this assignment is invalid."
        )

    # =========================================================
    # SCHOOL / CLASS / CURRICULUM
    # =========================================================

    school_class_curriculum = (
        assignment.school_class_curriculum
    )

    school_class = (
        school_class_curriculum.school_class
    )

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    curriculum_version = (
        school_class_curriculum.curriculum_version
    )

    pathway = (
        school_class_curriculum.pathway
    )

    learning_area = assignment.learning_area

    academic_year = str(
        assignment.academic_year
    )

    school = (
        school_class.school
        if school_class
        else None
    )

    if not school:
        return HttpResponseForbidden(
            "This class is not associated with a school."
        )

    # =========================================================
    # ENSURE UPPER SECONDARY
    # =========================================================

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    upper_secondary_grades = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "GRADE 10",
        "GRADE 11",
        "GRADE 12",
        "10",
        "11",
        "12",
    }

    if grade_code not in upper_secondary_grades:
        return HttpResponseForbidden(
            "This assessment book is only available for "
            "Grade 10, Grade 11 and Grade 12."
        )

    # =========================================================
    # SELECT TERM
    # =========================================================

    selected_term = (
        request.POST.get("term")
        or request.GET.get("term")
        or "1"
    )

    if str(selected_term) not in {
        "1",
        "2",
        "3",
    }:
        selected_term = "1"

    selected_term = str(selected_term)

    # =========================================================
    # OPEN EXAMS
    # =========================================================

    exams = {}

    for component in (
        "CAT1",
        "MID",
        "END",
    ):
        exams[component] = get_cbc_open_exam(
            school=school,
            academic_year=academic_year,
            term=selected_term,
            assessment_component=component,
        )

    # =========================================================
    # STUDENTS
    # =========================================================

    students = list(
        Student.objects
        .filter(
            school_id=school.id,
            academic_enrollments__academic_year=academic_year,
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=school_class.id,
        )
        .distinct()
        .order_by(
            "first_name",
            "last_name",
            "admission_number",
        )
    )

    # =========================================================
    # PERFORMANCE LEVEL HELPER
    # =========================================================

    performance_levels = list(
        CBCPerformanceLevel.objects.filter(
            curriculum_grade=curriculum_grade,
        ).order_by(
            "order",
        )
    )

    def get_performance_level(percentage):
        """
        Find the CBC performance level whose percentage range
        contains the normalized percentage.
        """

        if percentage is None:
            return None

        for level in performance_levels:

            if (
                percentage >= level.minimum_mark
                and percentage <= level.maximum_mark
            ):
                return level

        return None

    # =========================================================
    # SAVE ASSESSMENTS
    # =========================================================

    if request.method == "POST":

        # -----------------------------------------------------
        # A submitted form must have a valid exam configuration
        # -----------------------------------------------------

        for component in (
            "CAT1",
            "MID",
            "END",
        ):

            # No marks submitted for this component is allowed.
            # However, if the teacher attempts to enter a mark,
            # an open exam must exist.
            exam = exams.get(component)

            for student in students:

                raw_value = request.POST.get(
                    f"{component}_student_{student.id}",
                    "",
                ).strip()

                comment = request.POST.get(
                    f"{component}_comment_{student.id}",
                    "",
                ).strip()

                # -------------------------------------------------
                # EMPTY ENTRY
                # -------------------------------------------------

                if not raw_value:

                    # If there is no comment either, leave the
                    # existing assessment untouched.
                    if not comment:
                        continue

                    # A comment without an exam is not useful.
                    if exam is None:
                        messages.error(
                            request,
                            f"No open {component} examination is "
                            f"configured for this term.",
                        )

                        return redirect(
                            "students:cbc_upper_secondary_assessment_book",
                            assignment_id=assignment.id,
                        )

                    continue

                # -------------------------------------------------
                # EXAM MUST EXIST
                # -------------------------------------------------

                if exam is None:
                    messages.error(
                        request,
                        f"No open {component} examination is "
                        f"configured for this term.",
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                # -------------------------------------------------
                # RAW MARK
                # -------------------------------------------------

                try:
                    raw_score = Decimal(
                        raw_value
                    )

                except (
                    InvalidOperation,
                    ValueError,
                ):

                    messages.error(
                        request,
                        f"Invalid {component} mark for "
                        f"{student.first_name} "
                        f"{student.last_name}.",
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                # -------------------------------------------------
                # MARKS OUT OF
                # -------------------------------------------------

                marks_out_of = (
                    exam.marks_out_of
                )

                if marks_out_of is None:
                    messages.error(
                        request,
                        f"The {component} examination does not "
                        f"have a valid marks-out-of value.",
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                marks_out_of = Decimal(
                    marks_out_of
                )

                if marks_out_of <= 0:
                    messages.error(
                        request,
                        f"The {component} examination has an "
                        f"invalid marks-out-of value.",
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                # -------------------------------------------------
                # RANGE VALIDATION
                # -------------------------------------------------

                if raw_score < 0:

                    messages.error(
                        request,
                        f"{component} mark for "
                        f"{student.first_name} "
                        f"{student.last_name} "
                        f"cannot be negative.",
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                if raw_score > marks_out_of:

                    messages.error(
                        request,
                        (
                            f"{component} mark for "
                            f"{student.first_name} "
                            f"{student.last_name} "
                            f"cannot exceed "
                            f"{marks_out_of}."
                        ),
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                # -------------------------------------------------
                # NORMALIZE TO 100
                # -------------------------------------------------

                percentage = (
                    raw_score
                    / marks_out_of
                    * Decimal("100")
                )

                percentage = percentage.quantize(
                    Decimal("0.01")
                )

                # -------------------------------------------------
                # PERFORMANCE LEVEL
                # -------------------------------------------------

                performance_level = (
                    get_performance_level(
                        percentage
                    )
                )

                if performance_level is None:

                    messages.error(
                        request,
                        (
                            f"No CBC performance level is "
                            f"configured for {percentage}% "
                            f"for {student.first_name} "
                            f"{student.last_name}."
                        ),
                    )

                    return redirect(
                        "students:cbc_upper_secondary_assessment_book",
                        assignment_id=assignment.id,
                    )

                # -------------------------------------------------
                # POINTS
                # -------------------------------------------------

                points = performance_level.points

                # -------------------------------------------------
                # SAVE
                # -------------------------------------------------

                with transaction.atomic():

                    CBCUpperSecondaryAssessment.objects.update_or_create(
                        student=student,
                        learning_area=learning_area,
                        academic_year=academic_year,
                        term=selected_term,
                        assessment_component=component,
                        defaults={
                            "exam": exam,
                            "raw_score": raw_score,
                            "marks_out_of": marks_out_of,
                            "percentage_score": percentage,
                            "performance_level": performance_level,
                            "points": points,
                            "teacher_comment": comment,
                            "entered_by": request.user,
                        },
                    )

        messages.success(
            request,
            "Upper Secondary CBC marks saved successfully.",
        )

        return redirect(
            "students:cbc_upper_secondary_assessment_book",
            assignment_id=assignment.id,
        )

    # =========================================================
    # EXISTING ASSESSMENTS
    # =========================================================

    assessments = (
        CBCUpperSecondaryAssessment.objects
        .filter(
            student__in=students,
            learning_area=learning_area,
            academic_year=academic_year,
            term=selected_term,
        )
        .select_related(
            "exam",
            "performance_level",
        )
    )

    assessment_map = {}

    for assessment in assessments:

        assessment_map[
            (
                assessment.student_id,
                assessment.assessment_component,
            )
        ] = assessment

    # =========================================================
    # BUILD STUDENT ROWS
    # =========================================================

    student_rows = []

    for student in students:

        components = {}

        for component in (
            "CAT1",
            "MID",
            "END",
        ):

            assessment = assessment_map.get(
                (
                    student.id,
                    component,
                )
            )

            components[component] = {
                "assessment": assessment,
                "exam": exams.get(component),
                "raw_score": (
                    assessment.raw_score
                    if assessment
                    else None
                ),
                "marks_out_of": (
                    assessment.marks_out_of
                    if assessment
                    else (
                        exams[component].marks_out_of
                        if exams.get(component)
                        else None
                    )
                ),
                "percentage": (
                    assessment.percentage_score
                    if assessment
                    else None
                ),
                "performance": (
                    assessment.performance_level
                    if assessment
                    else None
                ),
                "points": (
                    assessment.points
                    if assessment
                    else None
                ),
                "teacher_comment": (
                    assessment.teacher_comment
                    if assessment
                    else ""
                ),
            }

        percentages = [
            components[component]["percentage"]
            for component in (
                "CAT1",
                "MID",
                "END",
            )
            if components[component]["percentage"]
            is not None
        ]

        points = [
            components[component]["points"]
            for component in (
                "CAT1",
                "MID",
                "END",
            )
            if components[component]["points"]
            is not None
        ]

        average_percentage = (
            sum(percentages) / len(percentages)
            if percentages
            else None
        )

        average_points = (
            sum(points) / len(points)
            if points
            else None
        )

        student_rows.append(
            {
                "student": student,
                "components": components,
                "average_percentage": average_percentage,
                "average_points": average_points,
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "assignment": assignment,
        "school": school,
        "school_class": school_class,
        "school_class_curriculum": school_class_curriculum,
        "curriculum_grade": curriculum_grade,
        "curriculum_version": curriculum_version,
        "pathway": pathway,
        "learning_area": learning_area,
        "academic_year": academic_year,
        "term": selected_term,
        "students": student_rows,
        "exams": exams,
        "assessment_components": [
            ("CAT1", "CAT 1"),
            ("MID", "MID TERM"),
            ("END", "END TERM"),
        ],
    }

    return render(
        request,
        "students/cbc/upper_secondary_assessment_book.html",
        context,
    )

@login_required
@admin_or_teacher
def cbc_upper_secondary_assessment_book_print(
    request,
    assignment_id,
):
    """
    Printable CBC Upper Secondary Assessment Book.

    Grade 10–12 only.

    PRINT STRUCTURE:
        One selected student
        -> all learning areas for the student's Grade/Pathway
        -> CAT 1 / MID / END assessments

    This view is read-only.

    IMPORTANT:
        TeacherAssessmentAssignment remains the authorization
        anchor. We do not change teacher assignment behaviour.
    """

    # =========================================================
    # LOAD ASSIGNMENT
    # =========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # =========================================================
    # SECURITY
    # =========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorised to print this assessment book."
        )

    if not curriculum_integrity_is_valid(
        assignment,
    ):
        return HttpResponseForbidden(
            "The curriculum configuration for this assignment is invalid."
        )

    # =========================================================
    # SCHOOL / CLASS / CURRICULUM
    # =========================================================

    school_class_curriculum = (
        assignment.school_class_curriculum
    )

    school_class = (
        school_class_curriculum.school_class
    )

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    curriculum_version = (
        school_class_curriculum.curriculum_version
    )

    pathway = (
        school_class_curriculum.pathway
    )

    academic_year = str(
        assignment.academic_year
    )

    school = (
        school_class.school
        if school_class
        else None
    )

    if not school:
        return HttpResponseForbidden(
            "This class is not associated with a school."
        )

    # =========================================================
    # ENSURE UPPER SECONDARY
    # =========================================================

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    normalized_grade_code = (
        grade_code
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )

    upper_secondary_grades = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "10",
        "11",
        "12",
    }

    if normalized_grade_code not in upper_secondary_grades:
        return HttpResponseForbidden(
            "This assessment book is only available for "
            "Grade 10, Grade 11 and Grade 12."
        )

    # =========================================================
    # SELECT TERM
    # =========================================================

    selected_term = (
        request.GET.get("term")
        or "1"
    )

    if str(selected_term) not in {
        "1",
        "2",
        "3",
    }:
        selected_term = "1"

    selected_term = str(selected_term)

    # =========================================================
    # SELECT STUDENT
    #
    # The print book is now for ONE student.
    #
    # The student must:
    #   - belong to this school
    #   - be enrolled in this academic year
    #   - be enrolled in the selected term
    #   - belong to this class
    # =========================================================

    selected_student = (
        request.GET.get("student")
        or ""
    ).strip()

    if not selected_student.isdigit():
        return HttpResponseForbidden(
            "A valid student must be selected before printing "
            "the assessment book."
        )

    student = (
        Student.objects
        .filter(
            id=int(selected_student),
            school_id=school.id,
            academic_enrollments__academic_year=academic_year,
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=school_class.id,
        )
        .distinct()
        .first()
    )

    if student is None:
        return HttpResponseForbidden(
            "The selected student is not enrolled in this class "
            "for the selected academic year and term."
        )

    # =========================================================
    # LEARNING AREAS
    #
    # IMPORTANT:
    # Use the class Grade + Pathway curriculum.
    #
    # We do NOT use assignment.learning_area here because
    # the printed assessment book must contain all learning
    # areas for the student's Grade/Pathway.
    # =========================================================

    learning_areas = (
        CurriculumLearningArea.objects
        .filter(
            curriculum_grade=curriculum_grade,
            assessment_enabled=True,
        )
        .order_by("name")
    )

    if pathway is not None:
        learning_areas = learning_areas.filter(
            Q(pathway__isnull=True)
            | Q(pathway=pathway)
        )
    else:
        learning_areas = learning_areas.filter(
            pathway__isnull=True
        )

    learning_areas = list(
        learning_areas
    )

    # =========================================================
    # OPEN EXAMS
    # =========================================================

    exams = {}

    for component in (
        "CAT1",
        "MID",
        "END",
    ):
        exams[component] = get_cbc_open_exam(
            school=school,
            academic_year=academic_year,
            term=selected_term,
            assessment_component=component,
        )

    # =========================================================
    # EXISTING ASSESSMENTS
    #
    # Only assessments belonging to:
    #   - selected student
    #   - selected year
    #   - selected term
    #   - valid learning areas
    # =========================================================

    assessments = (
        CBCUpperSecondaryAssessment.objects
        .filter(
            student=student,
            learning_area__in=learning_areas,
            academic_year=academic_year,
            term=selected_term,
        )
        .select_related(
            "learning_area",
            "exam",
            "performance_level",
        )
    )

    # =========================================================
    # MAP ASSESSMENTS
    #
    # key = learning area + assessment component
    # =========================================================

    assessment_map = {}

    for assessment in assessments:

        assessment_map[
            (
                assessment.learning_area_id,
                assessment.assessment_component,
            )
        ] = assessment

    # =========================================================
    # BUILD LEARNING AREA ROWS
    # =========================================================

    learning_area_rows = []

    for learning_area in learning_areas:

        components = {}

        for component in (
            "CAT1",
            "MID",
            "END",
        ):

            assessment = assessment_map.get(
                (
                    learning_area.id,
                    component,
                )
            )

            components[component] = {
                "assessment": assessment,

                "exam": exams.get(component),

                "raw_score": (
                    assessment.raw_score
                    if assessment
                    else None
                ),

                "marks_out_of": (
                    assessment.marks_out_of
                    if assessment
                    else (
                        exams[component].marks_out_of
                        if exams.get(component)
                        else None
                    )
                ),

                "percentage": (
                    assessment.percentage_score
                    if assessment
                    else None
                ),

                "performance": (
                    assessment.performance_level
                    if assessment
                    else None
                ),

                "points": (
                    assessment.points
                    if assessment
                    else None
                ),

                "teacher_comment": (
                    assessment.teacher_comment
                    if assessment
                    else ""
                ),
            }

        # =====================================================
        # AVERAGE PERCENTAGE
        # =====================================================

        percentages = [
            components[component]["percentage"]
            for component in (
                "CAT1",
                "MID",
                "END",
            )
            if components[component]["percentage"]
            is not None
        ]

        average_percentage = (
            sum(percentages) / len(percentages)
            if percentages
            else None
        )

        # =====================================================
        # AVERAGE POINTS
        # =====================================================

        points = [
            components[component]["points"]
            for component in (
                "CAT1",
                "MID",
                "END",
            )
            if components[component]["points"]
            is not None
        ]

        average_points = (
            sum(points) / len(points)
            if points
            else None
        )

        # =====================================================
        # APPEND ONE LEARNING AREA ROW
        # =====================================================

        learning_area_rows.append(
            {
                "learning_area": learning_area,
                "components": components,
                "average_percentage": average_percentage,
                "average_points": average_points,
            }
        )

        # =========================================================
        # TOTAL MARKS AND TOTAL POINTS
        # =========================================================

        total_marks = Decimal("0")
        total_points = Decimal("0")

        for row in learning_area_rows:

            if row["average_percentage"] is not None:
                total_marks += row["average_percentage"]

            if row["average_points"] is not None:
                total_points += row["average_points"]

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "assignment": assignment,

        "school": school,

        "school_class": school_class,

        "school_class_curriculum": (
            school_class_curriculum
        ),

        "curriculum_grade": (
            curriculum_grade
        ),

        "curriculum_version": (
            curriculum_version
        ),

        "pathway": pathway,

        "learning_area": (
            assignment.learning_area
        ),

        "academic_year": academic_year,

        "term": selected_term,

        # -----------------------------------------------------
        # ONE STUDENT
        # -----------------------------------------------------

        "student": student,

        # -----------------------------------------------------
        # LEARNING AREA ROWS
        # -----------------------------------------------------

        "learning_area_rows": learning_area_rows,
        "total_marks": total_marks,
        "total_points": total_points,

        "exams": exams,

        "assessment_components": [
            ("CAT1", "CAT 1"),
            ("MID", "MID TERM"),
            ("END", "END TERM"),
        ],
    }

    return render(
        request,
        "students/cbc/upper_secondary_assessment_book_print.html",
        context,
    )
@login_required
@admin_required
def cbc_upper_secondary_mark_list(request):
    """
    Management-side Upper Secondary CBC Mark List.

    Structure:
        One selected student
        One row per learning area
        CAT 1 / MID TERM / END TERM
        Average percentage
        Average points

    This view is for Grade 10, 11 and 12 only.
    It does not replace the PP1-Grade 9 CBC mark list.
    """

    # ============================================================
    # 1. DETERMINE USER SCHOOL
    # ============================================================

    if request.user.is_superuser:
        school = None
    else:
        school_user = getattr(request.user, "school_user", None)

        if not school_user or not school_user.school:
            messages.error(
                request,
                "Your account is not linked to a school."
            )
            return redirect("students:home")

        school = school_user.school

    # ============================================================
    # 2. FILTER VALUES
    # ============================================================

    selected_year = request.GET.get("year", "").strip()
    selected_term = request.GET.get("term", "").strip()
    selected_grade = request.GET.get("grade", "").strip()
    selected_pathway = request.GET.get("pathway", "").strip()
    selected_class_id = request.GET.get("school_class", "").strip()
    selected_learning_area_id = request.GET.get("learning_area", "").strip()
    selected_student_id = request.GET.get("student", "").strip()

    valid_terms = {"1", "2", "3"}

    if selected_term not in valid_terms:
        selected_term = ""

    # ============================================================
    # 3. ACADEMIC YEARS
    # ============================================================

    academic_years = SchoolAcademicYear.objects.all()

    if school is not None:
        academic_years = academic_years.filter(
            school=school
        )

    academic_years = academic_years.order_by("-year")

    # Default to current academic year where possible.
    if not selected_year:
        current_year = academic_years.filter(
            is_current=True
        ).first()

        if current_year:
            selected_year = current_year.year

    # ============================================================
    # 4. UPPER SECONDARY CURRICULUM GRADES
    # ============================================================

    upper_grade_codes = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "10",
        "11",
        "12",
    }

    curriculum_grades = (
        CurriculumGrade.objects
        .filter(grade__in=upper_grade_codes)
    )

    if school is not None:
        curriculum_grades = curriculum_grades.filter(
            school_class_assignments__school_class__school=school
        )

    curriculum_grades = (
        curriculum_grades
        .select_related("curriculum_version")
        .distinct()
        .order_by("grade", "display_name")
    )
    # ============================================================
    # 5. RESOLVE SELECTED GRADE
    # ============================================================

    selected_curriculum_grade_ids = []

    if selected_grade:
        for curriculum_grade in curriculum_grades:
            grade_code = (
                curriculum_grade.grade or ""
            ).strip().upper().replace(" ", "")

            if grade_code == selected_grade.upper().replace(" ", ""):
                selected_curriculum_grade_ids.append(
                    curriculum_grade.id
                )

    # ============================================================
    # 6. SCHOOL CLASS CURRICULUMS
    # ============================================================

    class_curriculums = SchoolClassCurriculum.objects.select_related(
        "school_class",
        "curriculum_version",
        "curriculum_grade",
        "pathway",
    )

    if school is not None:
        class_curriculums = class_curriculums.filter(
            school_class__school=school
        )

    if selected_year:
        class_curriculums = class_curriculums.filter(
            academic_year=selected_year
        )

    if selected_curriculum_grade_ids:
        class_curriculums = class_curriculums.filter(
            curriculum_grade_id__in=selected_curriculum_grade_ids
        )

    if selected_pathway:
        class_curriculums = class_curriculums.filter(
            pathway__name=selected_pathway
        )

    class_curriculums = (
        class_curriculums
        .distinct()
        .order_by("school_class__name")
    )

    # ============================================================
    # 7. PATHWAYS
    # ============================================================

    pathways = (
        CurriculumPathway.objects
        .filter(
            school_class_assignments__in=class_curriculums
        )
        .distinct()
        .order_by("name")
    )

    # ============================================================
    # 8. CLASSES
    # ============================================================

    school_classes = (
        SchoolClass.objects
        .filter(
            curriculum_assignments__in=class_curriculums
        )
        .distinct()
        .order_by("name")
    )

    # ============================================================
    # 9. SELECTED CLASS CURRICULUM
    # ============================================================

    selected_class_curriculum = None

    if selected_class_id:
        try:
            selected_class_curriculum = class_curriculums.filter(
                school_class_id=int(selected_class_id)
            ).first()
        except (TypeError, ValueError):
            selected_class_curriculum = None

    # ============================================================
    # 10. LEARNING AREAS
    # ============================================================

    learning_areas = CurriculumLearningArea.objects.none()

    if selected_class_curriculum:
        learning_areas = (
            CurriculumLearningArea.objects
            .filter(
                curriculum_grade=selected_class_curriculum.curriculum_grade,
                assessment_enabled=True,
            )
            .filter(
                Q(pathway__isnull=True)
                |
                Q(pathway=selected_class_curriculum.pathway)
            )
            .distinct()
            .order_by("name")
        )

    # ============================================================
    # 11. STUDENTS
    # ============================================================

    students = Student.objects.none()

    if selected_class_curriculum and selected_term:
        students = Student.objects.filter(
            school=selected_class_curriculum.school_class.school,
            academic_enrollments__academic_year=selected_year,
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=(
                selected_class_curriculum.school_class_id
            ),
        ).distinct().order_by(
            "admission_number",
            "first_name",
            "last_name",
        )

    # ============================================================
    # 12. SELECTED STUDENT
    # ============================================================

    selected_student = None

    if selected_student_id and students.exists():
        try:
            selected_student = students.filter(
                id=int(selected_student_id)
            ).first()
        except (TypeError, ValueError):
            selected_student = None

    # ============================================================
    # 13. FINAL LEARNING AREA FILTER
    # ============================================================

    selected_learning_area = None

    if selected_learning_area_id and learning_areas.exists():
        try:
            selected_learning_area = learning_areas.filter(
                id=int(selected_learning_area_id)
            ).first()
        except (TypeError, ValueError):
            selected_learning_area = None

    if selected_learning_area:
        report_learning_areas = learning_areas.filter(
            id=selected_learning_area.id
        )
    else:
        report_learning_areas = learning_areas

    # ============================================================
    # 14. BUILD MARK LIST
    # ============================================================

    mark_rows = []

    if (
        selected_student
        and selected_class_curriculum
        and selected_year
        and selected_term
    ):
        assessments = (
            CBCUpperSecondaryAssessment.objects
            .filter(
                student=selected_student,
                academic_year=selected_year,
                term=selected_term,
                submission__school_class_curriculum=(
                    selected_class_curriculum
                ),
            )
            .select_related(
                "learning_area",
                "performance_level",
                "exam",
            )
        )

        assessment_map = {
            (
                assessment.learning_area_id,
                assessment.assessment_component,
            ): assessment
            for assessment in assessments
        }

        for learning_area in report_learning_areas:

            components = {}

            percentages = []
            points = []

            for component_code in ("CAT1", "MID", "END"):
                assessment = assessment_map.get(
                    (
                        learning_area.id,
                        component_code,
                    )
                )

                component_data = None

                if assessment:
                    component_data = {
                        "raw_score": assessment.raw_score,
                        "marks_out_of": assessment.marks_out_of,
                        "percentage": assessment.percentage_score,
                        "performance": (
                            assessment.performance_level.code
                            if assessment.performance_level
                            else ""
                        ),
                        "points": assessment.points,
                    }

                    if assessment.percentage_score is not None:
                        percentages.append(
                            Decimal(
                                str(
                                    assessment.percentage_score
                                )
                            )
                        )

                    if assessment.points is not None:
                        points.append(
                            Decimal(
                                str(assessment.points)
                            )
                        )

                components[component_code] = component_data

            # ----------------------------------------------------
            # Average Mark
            # ----------------------------------------------------

            average_mark = None

            if percentages:
                average_mark = (
                    sum(percentages)
                    / Decimal(len(percentages))
                ).quantize(
                    Decimal("0.01")
                )

            # ----------------------------------------------------
            # Average Points
            # ----------------------------------------------------

            average_points = None

            if points:
                average_points = (
                    sum(points)
                    / Decimal(len(points))
                ).quantize(
                    Decimal("0.01")
                )

            mark_rows.append(
                {
                    "learning_area": learning_area,
                    "cat1": components["CAT1"],
                    "mid": components["MID"],
                    "end": components["END"],
                    "average_mark": average_mark,
                    "average_points": average_points,
                }
            )

    # ============================================================
    # 15. CONTEXT
    # ============================================================

    context = {
        "academic_years": academic_years,
        "curriculum_grades": curriculum_grades,
        "pathways": pathways,
        "school_classes": school_classes,
        "learning_areas": learning_areas,
        "students": students,

        "selected_year": selected_year,
        "selected_term": selected_term,
        "selected_grade": selected_grade,
        "selected_pathway": selected_pathway,
        "selected_class_id": selected_class_id,
        "selected_learning_area_id": selected_learning_area_id,
        "selected_student_id": selected_student_id,

        "selected_class_curriculum": selected_class_curriculum,
        "selected_learning_area": selected_learning_area,
        "selected_student": selected_student,

        "mark_rows": mark_rows,
    }

    return render(
        request,
        "students/cbc_upper_secondary_mark_list.html",
        context,
    )
@login_required
@admin_required
def cbc_upper_secondary_mark_list_print(request):
    """
    Printable CBC Upper Secondary Mark List.

    Management-side only.
    Uses the same filters as cbc_upper_secondary_mark_list().
    """

    # ---------------------------------------------------------
    # Determine user's school
    # ---------------------------------------------------------
    if request.user.is_superuser:
        school = None

        school_id = request.GET.get("school_id", "").strip()

        if school_id:
            school = SchoolProfile.objects.filter(
                id=school_id
            ).first()

    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            messages.error(
                request,
                "Your account is not linked to a school.",
            )
            return redirect("students:home")

        school = school_user.school

    if school is None:
        messages.error(
            request,
            "Please select a school.",
        )
        return redirect("students:cbc_upper_secondary_mark_list")

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------
    selected_year = request.GET.get(
        "year",
        "",
    ).strip()

    selected_term = request.GET.get(
        "term",
        "",
    ).strip()

    selected_grade = request.GET.get(
        "grade",
        "",
    ).strip()

    selected_pathway = request.GET.get(
        "pathway",
        "",
    ).strip()

    selected_class_id = request.GET.get(
        "school_class",
        "",
    ).strip()

    selected_learning_area_id = request.GET.get(
        "learning_area",
        "",
    ).strip()

    selected_student_id = request.GET.get(
        "student",
        "",
    ).strip()

    # ---------------------------------------------------------
    # Required filters
    # ---------------------------------------------------------
    if not selected_year:
        messages.error(
            request,
            "Academic Year is required.",
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    if selected_term not in {"1", "2", "3"}:
        messages.error(
            request,
            "A valid term is required.",
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    if not selected_class_id:
        messages.error(
            request,
            "Class / Stream is required.",
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    if not selected_student_id:
        messages.error(
            request,
            "Student is required.",
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    # ---------------------------------------------------------
    # Upper-secondary grade codes
    # ---------------------------------------------------------
    upper_grade_codes = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "GRADE 10",
        "GRADE 11",
        "GRADE 12",
        "10",
        "11",
        "12",
    }

    # ---------------------------------------------------------
    # Selected class curriculum
    # ---------------------------------------------------------
    class_curriculum_qs = (
        SchoolClassCurriculum.objects
        .select_related(
            "school_class",
            "curriculum_version",
            "curriculum_grade",
            "pathway",
        )
        .filter(
            school_class_id=selected_class_id,
            academic_year=str(selected_year),
            school_class__school=school,
            curriculum_grade__grade__in=upper_grade_codes,
        )
    )

    selected_class_curriculum = (
        class_curriculum_qs.first()
    )

    if not selected_class_curriculum:
        messages.error(
            request,
            "The selected class curriculum could not be found."
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    # ---------------------------------------------------------
    # Validate selected grade
    # ---------------------------------------------------------
    curriculum_grade = (
        selected_class_curriculum.curriculum_grade
    )

    actual_grade = (
        curriculum_grade.grade
        if curriculum_grade
        else ""
    )

    if (
        selected_grade
        and actual_grade.upper() != selected_grade.upper()
    ):
        messages.error(
            request,
            "The selected grade does not match the class curriculum."
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    # ---------------------------------------------------------
    # Validate pathway
    # ---------------------------------------------------------
    pathway = selected_class_curriculum.pathway

    if selected_pathway:

        if not pathway:
            messages.error(
                request,
                "The selected class has no pathway."
            )
            return redirect(
                "students:cbc_upper_secondary_mark_list"
            )

        if pathway.name != selected_pathway:
            messages.error(
                request,
                "The selected pathway does not match the class curriculum."
            )
            return redirect(
                "students:cbc_upper_secondary_mark_list"
            )

    # ---------------------------------------------------------
    # Selected student
    #
    # IMPORTANT:
    # Student must belong to:
    #   school
    #   academic year
    #   term
    #   selected class
    # ---------------------------------------------------------
    students = (
        Student.objects
        .filter(
            school=school,
            academic_enrollments__academic_year=str(
                selected_year
            ),
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=selected_class_id,
        )
        .distinct()
        .order_by(
            "first_name",
            "last_name",
            "admission_number",
        )
    )

    selected_student = students.filter(
        id=selected_student_id
    ).first()

    if not selected_student:
        messages.error(
            request,
            "The selected student does not belong to the selected class, term and academic year."
        )
        return redirect(
            "students:cbc_upper_secondary_mark_list"
        )

    # ---------------------------------------------------------
    # Learning areas
    # ---------------------------------------------------------
    learning_areas = (
        CurriculumLearningArea.objects
        .filter(
            curriculum_grade=curriculum_grade,
            assessment_enabled=True,
        )
        .filter(
            Q(pathway__isnull=True)
            | Q(pathway=pathway)
        )
        .order_by(
            "order",
            "name",
        )
    )

    # ---------------------------------------------------------
    # Optional learning-area filter
    # ---------------------------------------------------------
    selected_learning_area = None

    if selected_learning_area_id:

        selected_learning_area = (
            learning_areas
            .filter(
                id=selected_learning_area_id
            )
            .first()
        )

        if not selected_learning_area:
            messages.error(
                request,
                "The selected learning area is not valid for this class."
            )
            return redirect(
                "students:cbc_upper_secondary_mark_list"
            )

        learning_areas = learning_areas.filter(
            id=selected_learning_area.id
        )

    # ---------------------------------------------------------
    # Load assessments
    # ---------------------------------------------------------
    assessments = (
        CBCUpperSecondaryAssessment.objects
        .filter(
            student=selected_student,
            academic_year=str(selected_year),
            term=selected_term,
            learning_area__in=learning_areas,
            submission__school_class_curriculum=(
                selected_class_curriculum
            ),
        )
        .select_related(
            "learning_area",
            "performance_level",
            "exam",
        )
        .order_by(
            "learning_area__order",
            "learning_area__name",
            "assessment_component",
        )
    )

    # ---------------------------------------------------------
    # Map:
    #
    # (learning_area_id, component)
    #
    # ---------------------------------------------------------
    assessment_map = {}

    for assessment in assessments:

        assessment_map[
            (
                assessment.learning_area_id,
                assessment.assessment_component,
            )
        ] = assessment

    # ---------------------------------------------------------
    # Build printable rows
    # ---------------------------------------------------------
    mark_rows = []

    for learning_area in learning_areas:

        row = {
            "learning_area": learning_area,
            "cat1": None,
            "mid": None,
            "end": None,
            "average_mark": None,
            "average_points": None,
        }

        percentages = []
        points = []

        # -----------------------------------------------------
        # CAT 1
        # -----------------------------------------------------
        cat1 = assessment_map.get(
            (
                learning_area.id,
                "CAT1",
            )
        )

        if cat1:

            row["cat1"] = {
                "raw_score": cat1.raw_score,
                "marks_out_of": cat1.marks_out_of,
                "percentage": cat1.percentage_score,
                "performance": (
                    cat1.performance_level.code
                    if cat1.performance_level
                    else ""
                ),
                "points": cat1.points,
            }

            if cat1.percentage_score is not None:
                percentages.append(
                    cat1.percentage_score
                )

            if cat1.points is not None:
                points.append(
                    cat1.points
                )

        # -----------------------------------------------------
        # MID TERM
        # -----------------------------------------------------
        mid = assessment_map.get(
            (
                learning_area.id,
                "MID",
            )
        )

        if mid:

            row["mid"] = {
                "raw_score": mid.raw_score,
                "marks_out_of": mid.marks_out_of,
                "percentage": mid.percentage_score,
                "performance": (
                    mid.performance_level.code
                    if mid.performance_level
                    else ""
                ),
                "points": mid.points,
            }

            if mid.percentage_score is not None:
                percentages.append(
                    mid.percentage_score
                )

            if mid.points is not None:
                points.append(
                    mid.points
                )

        # -----------------------------------------------------
        # END TERM
        # -----------------------------------------------------
        end = assessment_map.get(
            (
                learning_area.id,
                "END",
            )
        )

        if end:

            row["end"] = {
                "raw_score": end.raw_score,
                "marks_out_of": end.marks_out_of,
                "percentage": end.percentage_score,
                "performance": (
                    end.performance_level.code
                    if end.performance_level
                    else ""
                ),
                "points": end.points,
            }

            if end.percentage_score is not None:
                percentages.append(
                    end.percentage_score
                )

            if end.points is not None:
                points.append(
                    end.points
                )

        # -----------------------------------------------------
        # Average normalized percentage
        #
        # IMPORTANT:
        # Blank components are NOT treated as zero.
        # -----------------------------------------------------
        if percentages:

            row["average_mark"] = (
                sum(percentages)
                / len(percentages)
            )

        # -----------------------------------------------------
        # Average points
        # -----------------------------------------------------
        if points:

            row["average_points"] = (
                sum(points)
                / len(points)
            )

        mark_rows.append(row)

    # ---------------------------------------------------------
    # Render print template
    # ---------------------------------------------------------
    context = {
        "school": school,

        "academic_year": selected_year,
        "term": selected_term,

        "curriculum_grade": curriculum_grade,
        "curriculum_version": (
            selected_class_curriculum.curriculum_version
        ),

        "pathway": pathway,

        "school_class": (
            selected_class_curriculum.school_class
        ),

        "school_class_curriculum": (
            selected_class_curriculum
        ),

        "selected_learning_area": (
            selected_learning_area
        ),

        "selected_student": selected_student,

        "mark_rows": mark_rows,
    }

    return render(
        request,
        "students/cbc/upper_secondary_mark_list_print.html",
        context,
    )

@login_required
@admin_or_teacher
def cbc_upper_secondary_mark_entry(request, assignment_id):
    """
    Teacher mark entry for Grade 10-12.

    Teacher enters raw marks only.
    The system calculates:
        raw mark -> percentage -> performance level -> points

    Exam OPEN/CLOSED status is controlled by the existing Exam system.
    TeacherAssessmentAssignment is NOT term-specific.
    """

    # =====================================================
    # LOAD ASSIGNMENT
    # =====================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # =====================================================
    # SECURITY
    # =====================================================

    if not assignment_belongs_to_user(request, assignment):
        return HttpResponseForbidden(
            "You are not authorised to enter marks for this assignment."
        )

    if not curriculum_integrity_is_valid(assignment):
        return HttpResponseForbidden(
            "The curriculum configuration for this assignment is invalid."
        )

    # =====================================================
    # BASIC ASSIGNMENT DATA
    # =====================================================

    school_class_curriculum = assignment.school_class_curriculum
    school_class = school_class_curriculum.school_class
    curriculum_grade = school_class_curriculum.curriculum_grade
    curriculum_version = school_class_curriculum.curriculum_version
    pathway = school_class_curriculum.pathway
    learning_area = assignment.learning_area

    academic_year = str(assignment.academic_year)

    school = (
        school_class.school
        if school_class
        else None
    )

    if not school:
        return HttpResponseForbidden(
            "This class is not associated with a school."
        )

    # =====================================================
    # GRADE PROTECTION
    # =====================================================

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    upper_secondary_grades = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "GRADE 10",
        "GRADE 11",
        "GRADE 12",
        "10",
        "11",
        "12",
    }

    if grade_code not in upper_secondary_grades:
        return HttpResponseForbidden(
            "This mark-entry page is only available "
            "for Grade 10, Grade 11 and Grade 12."
        )

    # =====================================================
    # TERM
    # =====================================================

    selected_term = (
        request.GET.get("term")
        or request.POST.get("term")
        or "1"
    )

    if str(selected_term) not in {"1", "2", "3"}:
        selected_term = "1"

    selected_term = str(selected_term)

    # =====================================================
    # ASSESSMENT COMPONENT
    # =====================================================

    selected_component = (
        request.GET.get("assessment_component")
        or request.POST.get("assessment_component")
        or "CAT1"
    )

    selected_component = str(
        selected_component
    ).strip().upper()

    if selected_component not in {
        "CAT1",
        "MID",
        "END",
    }:
        selected_component = "CAT1"

    # =====================================================
    # GET THE EXISTING SCHOOL EXAM
    # =====================================================

    selected_exam = get_cbc_open_exam(
        school=school,
        academic_year=academic_year,
        term=selected_term,
        assessment_component=selected_component,
    )

    # =====================================================
    # STUDENTS
    # =====================================================

    students = list(
        Student.objects.filter(
            school_id=school.id,
            academic_enrollments__academic_year=academic_year,
            academic_enrollments__term=selected_term,
            academic_enrollments__school_class_id=school_class.id,
        )
        .distinct()
        .order_by(
            "first_name",
            "last_name",
            "admission_number",
        )
    )

    # =====================================================
    # EXISTING SUBMISSION
    # =====================================================

    existing_submission = (
        CBCAssessmentSubmission.objects.filter(
            school_class_curriculum=school_class_curriculum,
            learning_area=learning_area,
            academic_year=academic_year,
            term=selected_term,
            assessment_component=selected_component,
        )
        .first()
    )

    # =====================================================
    # VERIFY SUBMISSION OWNER
    # =====================================================

    if existing_submission:
        if (
            existing_submission.teacher_id
            != assignment.teacher_id
        ):
            return HttpResponseForbidden(
                "This assessment submission belongs to another teacher."
            )

    # =====================================================
    # EXISTING MARKS
    # =====================================================

    existing_assessments = (
        CBCUpperSecondaryAssessment.objects.filter(
            student__in=students,
            learning_area=learning_area,
            academic_year=academic_year,
            term=selected_term,
            assessment_component=selected_component,
        )
        .select_related(
            "performance_level",
            "exam",
            "submission",
        )
    )

    assessment_map = {
        assessment.student_id: assessment
        for assessment in existing_assessments
    }

    # =====================================================
    # POST - SAVE MARKS
    # =====================================================

    if request.method == "POST":

        # -------------------------------------------------
        # EXAM MUST BE OPEN
        # -------------------------------------------------

        if not selected_exam:
            messages.error(
                request,
                "This exam is not currently OPEN. "
                "Marks cannot be entered.",
            )

            return redirect(
                request.path
                + f"?assessment_component={selected_component}"
                + f"&term={selected_term}"
            )

        # -------------------------------------------------
        # EXISTING SUBMISSION STATUS
        # -------------------------------------------------

        if existing_submission:

            if existing_submission.status == "SUBMITTED":
                messages.error(
                    request,
                    "This assessment has already been submitted "
                    "and cannot be edited.",
                )

                return redirect(
                    request.path
                    + f"?assessment_component={selected_component}"
                    + f"&term={selected_term}"
                )

            if existing_submission.status == "APPROVED":
                messages.error(
                    request,
                    "This assessment has already been approved "
                    "and cannot be edited.",
                )

                return redirect(
                    request.path
                    + f"?assessment_component={selected_component}"
                    + f"&term={selected_term}"
                )

        # -------------------------------------------------
        # EXAM MARKS OUT OF
        # -------------------------------------------------

        marks_out_of = selected_exam.marks_out_of

        if marks_out_of is None:
            messages.error(
                request,
                "The selected exam does not have a marks-out-of value.",
            )

            return redirect(
                request.path
                + f"?assessment_component={selected_component}"
                + f"&term={selected_term}"
            )

        try:
            marks_out_of = Decimal(
                str(marks_out_of)
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            messages.error(
                request,
                "The exam marks-out-of value is invalid.",
            )

            return redirect(
                request.path
                + f"?assessment_component={selected_component}"
                + f"&term={selected_term}"
            )

        if marks_out_of <= 0:
            messages.error(
                request,
                "The exam marks-out-of value must be greater than zero.",
            )

            return redirect(
                request.path
                + f"?assessment_component={selected_component}"
                + f"&term={selected_term}"
            )

        # =================================================
        # SAVE ATOMICALLY
        # =================================================

        with transaction.atomic():

            # ---------------------------------------------
            # GET OR CREATE SUBMISSION
            # ---------------------------------------------

            submission, created = (
                CBCAssessmentSubmission.objects.get_or_create(
                    school_class_curriculum=school_class_curriculum,
                    learning_area=learning_area,
                    academic_year=academic_year,
                    term=selected_term,
                    assessment_component=selected_component,
                    defaults={
                        "teacher": assignment.teacher,
                        "status": "DRAFT",
                    },
                )
            )

            # ---------------------------------------------
            # VERIFY OWNER
            # ---------------------------------------------

            if (
                submission.teacher_id
                != assignment.teacher_id
            ):
                messages.error(
                    request,
                    "This assessment submission belongs "
                    "to another teacher.",
                )

                return redirect(
                    request.path
                    + f"?assessment_component={selected_component}"
                    + f"&term={selected_term}"
                )

            # ---------------------------------------------
            # SUBMISSION STATUS
            # ---------------------------------------------

            if submission.status in {
                "SUBMITTED",
                "APPROVED",
            }:
                messages.error(
                    request,
                    "This assessment can no longer be edited.",
                )

                return redirect(
                    request.path
                    + f"?assessment_component={selected_component}"
                    + f"&term={selected_term}"
                )

            # ---------------------------------------------
            # SAVE EACH STUDENT
            # ---------------------------------------------

            validation_error = None

            for student in students:

                field_name = f"score_{student.id}"

                raw_score = (
                    request.POST.get(
                        field_name,
                        "",
                    )
                    .strip()
                )

                # -----------------------------------------
                # EMPTY SCORE
                # -----------------------------------------

                if raw_score == "":

                    CBCUpperSecondaryAssessment.objects.filter(
                        student=student,
                        learning_area=learning_area,
                        academic_year=academic_year,
                        term=selected_term,
                        assessment_component=selected_component,
                    ).delete()

                    continue

                # -----------------------------------------
                # VALIDATE DECIMAL
                # -----------------------------------------

                try:
                    score = Decimal(raw_score)

                except (
                    InvalidOperation,
                    TypeError,
                    ValueError,
                ):

                    validation_error = (
                        f"Invalid mark for "
                        f"{student.first_name} "
                        f"{student.last_name}."
                    )

                    break

                # -----------------------------------------
                # VALIDATE RANGE
                # -----------------------------------------

                if score < 0 or score > marks_out_of:

                    validation_error = (
                        f"Mark for "
                        f"{student.first_name} "
                        f"{student.last_name} "
                        f"must be between 0 and "
                        f"{marks_out_of}."
                    )

                    break

                # -----------------------------------------
                # NORMALIZE TO PERCENTAGE
                # -----------------------------------------

                percentage_score = (
                    (score / marks_out_of)
                    * Decimal("100")
                ).quantize(
                    Decimal("0.01")
                )

                # -----------------------------------------
                # DERIVE PERFORMANCE + POINTS
                # -----------------------------------------

                performance_level, points = (
                    get_upper_secondary_performance(
                        curriculum_grade=curriculum_grade,
                        percentage=percentage_score,
                    )
                )

                # -----------------------------------------
                # PERFORMANCE LEVEL MUST EXIST
                # -----------------------------------------

                if performance_level is None:

                    validation_error = (
                        f"No configured CBC performance level "
                        f"covers {percentage_score}% for "
                        f"{student.first_name} "
                        f"{student.last_name}."
                    )

                    break

                # -----------------------------------------
                # SAVE
                # -----------------------------------------

                CBCUpperSecondaryAssessment.objects.update_or_create(
                    student=student,
                    learning_area=learning_area,
                    academic_year=academic_year,
                    term=selected_term,
                    assessment_component=selected_component,
                    defaults={
                        "submission": submission,
                        "exam": selected_exam,
                        "raw_score": score,
                        "marks_out_of": marks_out_of,
                        "percentage_score": percentage_score,
                        "performance_level": performance_level,
                        "points": points,
                        "entered_by": request.user,
                    },
                )

            # ---------------------------------------------
            # VALIDATION FAILURE
            # ---------------------------------------------

            if validation_error:

                transaction.set_rollback(True)

                messages.error(
                    request,
                    validation_error,
                )

                return redirect(
                    request.path
                    + f"?assessment_component={selected_component}"
                    + f"&term={selected_term}"
                )

            # ---------------------------------------------
            # SUBMIT FOR APPROVAL
            # ---------------------------------------------

            action = (
                request.POST.get("action", "save")
                .strip()
                .lower()
            )

            if action == "submit":

                saved_count = (
                    CBCUpperSecondaryAssessment.objects.filter(
                        submission=submission,
                        student__in=students,
                    ).count()
                )

                if saved_count == 0:

                    messages.error(
                        request,
                        "You cannot submit an assessment "
                        "without entering at least one mark.",
                    )

                    transaction.set_rollback(True)

                    return redirect(
                        request.path
                        + f"?assessment_component={selected_component}"
                        + f"&term={selected_term}"
                    )

                submission.status = "SUBMITTED"
                submission.submitted_at = timezone.now()
                submission.save(
                    update_fields=[
                        "status",
                        "submitted_at",
                    ]
                )

        # =================================================
        # SUCCESS
        # =================================================

        if action == "submit":

            messages.success(
                request,
                "Marks have been saved and submitted for approval.",
            )

        else:

            messages.success(
                request,
                "Marks have been saved as draft.",
            )

        return redirect(
            request.path
            + f"?assessment_component={selected_component}"
            + f"&term={selected_term}"
        )

    # =====================================================
    # BUILD TEMPLATE ROWS
    # =====================================================

    student_rows = []

    for student in students:

        assessment = assessment_map.get(
            student.id
        )

        student_rows.append(
            {
                "student": student,
                "assessment": assessment,
                "raw_score": (
                    assessment.raw_score
                    if assessment
                    else None
                ),
                "marks_out_of": (
                    assessment.marks_out_of
                    if assessment
                    else (
                        selected_exam.marks_out_of
                        if selected_exam
                        else None
                    )
                ),
                "percentage": (
                    assessment.percentage_score
                    if assessment
                    else None
                ),
                "performance": (
                    assessment.performance_level
                    if assessment
                    else None
                ),
                "points": (
                    assessment.points
                    if assessment
                    else None
                ),
            }
        )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        "assignment": assignment,
        "school": school,
        "school_class": school_class,
        "school_class_curriculum": school_class_curriculum,
        "curriculum_grade": curriculum_grade,
        "curriculum_version": curriculum_version,
        "pathway": pathway,
        "learning_area": learning_area,
        "academic_year": academic_year,
        "term": selected_term,
        "assessment_component": selected_component,
        "selected_exam": selected_exam,
        "students": student_rows,
        "submission": existing_submission,
        "assessment_components": [
            ("CAT1", "CAT 1"),
            ("MID", "MID TERM"),
            ("END", "END TERM"),
        ],
    }

    return render(
        request,

        "students/cbc/upper_secondary_mark_entry.html",
        context,
    )
# ============================================================
# CBC STUDENT RESULT / PRINT
# ============================================================

@login_required
@admin_or_teacher
def cbc_student_result(
    request,
    assignment_id,
    student_id,
):
    """
    Printable CBC result for ONE learner.

    PP1 - Grade 9:

        CAT1
            -> CAT 1 result only

        MID
            -> Mid-Term result only

        END
            -> CAT 1 + Mid-Term + End-Term
               compiled into the End-Term Summative Result.

    Grade 10-12 are intentionally excluded.
    """

    # =========================================================
    # GET ASSIGNMENT
    # =========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        ),
        pk=assignment_id,
    )

    # =========================================================
    # SECURITY
    # =========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorized to access this assessment."
        )

    if not curriculum_integrity_is_valid(
        assignment
    ):
        return HttpResponseForbidden(
            "Invalid curriculum assignment."
        )

    # =========================================================
    # CURRICULUM / CLASS / SCHOOL
    # =========================================================

    curriculum = assignment.school_class_curriculum
    school_class = curriculum.school_class
    school = school_class.school
    learning_area = assignment.learning_area

    curriculum_grade = curriculum.curriculum_grade

    grade_code = str(
        getattr(
            curriculum_grade,
            "grade",
            "",
        )
    ).strip().upper()

    # =========================================================
    # PP1 - GRADE 9 ONLY
    # =========================================================

    qualitative_grades = {
        "PP1",
        "PP2",
        "GRADE 1",
        "GRADE 2",
        "GRADE 3",
        "GRADE 4",
        "GRADE 5",
        "GRADE 6",
        "GRADE 7",
        "GRADE 8",
        "GRADE 9",
    }

    if grade_code not in qualitative_grades:
        return HttpResponseForbidden(
            "Grade 10 and above use the existing numerical "
            "assessment system."
        )
    # =========================================================
    # ASSESSMENT TERM
    # =========================================================

    valid_terms = {
        "1": "Term 1",
        "2": "Term 2",
        "3": "Term 3",
    }

    requested_term = (
        request.GET.get("term")
        or "1"
    )

    requested_term = str(
        requested_term
    ).strip()

    if requested_term not in valid_terms:
        requested_term = "1"

    selected_term = requested_term

    # =========================================================
    # ASSESSMENT COMPONENT
    # =========================================================

    assessment_component = (
        request.GET.get(
            "assessment_component"
        )
        or "CAT1"
    ).upper()

    valid_components = {
        "CAT1": "CAT 1",
        "MID": "Mid-Term",
        "END": "End-Term",
    }

    if assessment_component not in valid_components:
        assessment_component = "CAT1"

    # =========================================================
    # GET STUDENT
    # =========================================================

    student = get_object_or_404(
        Student.objects.select_related(
            "school",
            "school_class",
        ),
        pk=student_id,
    )

    # =========================================================
    # STUDENT SECURITY
    # =========================================================

    if student.school_id != school.id:
        return HttpResponseForbidden(
            "This learner does not belong to this school."
        )

    if student.school_class_id != school_class.id:
        return HttpResponseForbidden(
            "This learner does not belong to this class."
        )

    # =========================================================
    # LEARNING AREAS FOR THE LEARNER'S CLASS
    # =========================================================

    authorized_assignments = (
        get_teacher_assignments(request)
        .filter(
            school_class_curriculum=curriculum,
            academic_year=assignment.academic_year,
            
        )
        .select_related(
            "learning_area",
        )
    )

    valid_learning_areas = []

    seen_learning_area_ids = set()

    for item in authorized_assignments:

        if not curriculum_integrity_is_valid(
            item
        ):
            continue

        if item.learning_area_id in seen_learning_area_ids:
            continue

        valid_learning_areas.append(
            item.learning_area
        )

        seen_learning_area_ids.add(
            item.learning_area_id
        )

    valid_learning_areas.sort(
        key=lambda item: (
            item.name or "",
        )
    )

    # =========================================================
    # LOAD ALL THREE COMPONENTS
    # =========================================================

    records = (
        CBCSubjectAssessment.objects
        .filter(
            student=student,
            academic_year=str(
                assignment.academic_year
            ),
            term=str(
                selected_term
            ),
            assessment_component__in=[
                "CAT1",
                "MID",
                "END",
            ],
        )
        .select_related(
            "learning_area",
        )
    )

    # =========================================================
    # INDEX RECORDS
    # =========================================================

    records_by_area = {
        "CAT1": {},
        "MID": {},
        "END": {},
    }

    for record in records:

        records_by_area[
            record.assessment_component
        ][record.learning_area_id] = record

    # =========================================================
    # BUILD RESULT ROWS
    # =========================================================

    result_rows = []

    total_cat1 = Decimal("0")
    total_mid = Decimal("0")
    total_end = Decimal("0")

    cat1_count = 0
    mid_count = 0
    end_count = 0

    for area in valid_learning_areas:

        cat1_record = (
            records_by_area["CAT1"]
            .get(area.id)
        )

        mid_record = (
            records_by_area["MID"]
            .get(area.id)
        )

        end_record = (
            records_by_area["END"]
            .get(area.id)
        )

        cat1_score = (
            cat1_record.score
            if cat1_record
            and cat1_record.score is not None
            else None
        )

        mid_score = (
            mid_record.score
            if mid_record
            and mid_record.score is not None
            else None
        )

        end_score = (
            end_record.score
            if end_record
            and end_record.score is not None
            else None
        )

        # =====================================================
        # QUALITATIVE DISPLAY
        # =====================================================

        cat1_level = ""

        if cat1_record:
            cat1_level = (
                cbc_performance_level_label(
                    cat1_record.performance_level
                )
            )

        mid_level = ""

        if mid_record:
            mid_level = (
                cbc_performance_level_label(
                    mid_record.performance_level
                )
            )

        end_level = ""

        if end_record:
            end_level = (
                cbc_performance_level_label(
                    end_record.performance_level
                )
            )

        # =====================================================
        # INDIVIDUAL RESULT
        #
        # CAT1 -> CAT1 only
        # MID  -> MID only
        # END  -> all three
        # =====================================================

        average = None
        final_level = ""

        if assessment_component == "CAT1":

            display_level = cat1_level

            if cat1_score is not None:
                total_cat1 += cat1_score
                cat1_count += 1

        elif assessment_component == "MID":

            display_level = mid_level

            if mid_score is not None:
                total_mid += mid_score
                mid_count += 1

        else:

            display_level = end_level

            # -------------------------------------------------
            # FINAL END-TERM COMPILATION
            #
            # Only calculate when all three components exist.
            # -------------------------------------------------

            if (
                cat1_score is not None
                and mid_score is not None
                and end_score is not None
            ):

                average = (
                    (
                        cat1_score
                        + mid_score
                        + end_score
                    )
                    / Decimal("3")
                ).quantize(
                    Decimal("0.01")
                )

                final_level = (
                    cbc_performance_level_label(
                        get_cbc_subject_performance_level(
                            average
                        )
                    )
                )

            if cat1_score is not None:
                total_cat1 += cat1_score
                cat1_count += 1

            if mid_score is not None:
                total_mid += mid_score
                mid_count += 1

            if end_score is not None:
                total_end += end_score
                end_count += 1

            display_level = final_level

        result_rows.append(
            {
                "learning_area": area,

                # ---------------------------------------------
                # Individual component display
                # ---------------------------------------------

                "cat1_level": cat1_level,
                "mid_level": mid_level,
                "end_level": end_level,

                # ---------------------------------------------
                # Final compiled result
                # ---------------------------------------------

                "average": average,
                "performance_level": display_level,

                # ---------------------------------------------
                # Internal scores are available to template
                # only where needed.
                #
                # Learner-facing template should NOT display
                # them for PP1-Grade 9.
                # ---------------------------------------------

                "cat1_score": cat1_score,
                "mid_score": mid_score,
                "end_score": end_score,
            }
        )

    # =========================================================
    # RESULT TITLE
    # =========================================================

    result_title = valid_components[
        assessment_component
    ]

    if assessment_component == "END":
        result_title = "END-TERM SUMMATIVE ASSESSMENT"

    # =========================================================
    # TOTALS
    # =========================================================

    totals = {
        "cat1": total_cat1 if cat1_count else None,
        "mid": total_mid if mid_count else None,
        "end": total_end if end_count else None,
    }

    # =========================================================
    # RENDER
    # =========================================================

    return render(
        request,
        "students/cbc/student_result.html",
        {
            "assignment": assignment,

            "curriculum": curriculum,

            "school": school,

            "school_class": school_class,

            "student": student,

            "learning_area": learning_area,

            "academic_year": (
                assignment.academic_year
            ),

            "term": selected_term,
            "assessment_component": (
                assessment_component
            ),

            "assessment_component_label": (
                valid_components[
                    assessment_component
                ]
            ),

            "result_title": result_title,

            "result_rows": result_rows,

            "totals": totals,

            "is_end_term": (
                assessment_component == "END"
            ),
        },
    )

def get_cbc_open_exam(
    *,
    school,
    academic_year,
    term,
    assessment_component,
):
    """
    Return the existing OPEN exam corresponding to a CBC
    assessment component.

    Exams are created and controlled by school administrators.
    This helper must NEVER create or reopen an exam.
    """

    exam_names = {
        "CAT1": "CAT 1",
        "MID": "MID TERM",
        "END": "END TERM",
    }

    exam_name = exam_names.get(
        str(assessment_component).strip().upper()
    )

    if not exam_name:
        return None

    try:
        year = int(academic_year)
    except (TypeError, ValueError):
        return None

    if str(term) not in {"1", "2", "3"}:
        return None

    return Exam.objects.filter(
        school=school,
        year=year,
        term=str(term),
        name__iexact=exam_name,
        status="OPEN",
    ).first()

@login_required
@admin_required
def cbc_submission_review(request):
    """
    School-admin review of CBC subject assessment submissions.

    Filters:
    - Academic Year
    - Term
    - Class

    Administrators can review submissions belonging to their school.
    Superusers can review submissions across schools.
    """

    # -------------------------------------------------
    # Determine user's school
    # -------------------------------------------------
    if request.user.is_superuser:
        school = None
    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            messages.error(
                request,
                "Your account is not assigned to a school.",
            )
            return redirect("students:home")

        school = school_user.school

    # -------------------------------------------------
    # Filter values
    # -------------------------------------------------
    selected_year = (request.GET.get("year") or "").strip()
    selected_term = (request.GET.get("term") or "").strip()
    selected_class = (request.GET.get("school_class") or "").strip()

    # -------------------------------------------------
    # Academic years
    # Use configured SchoolAcademicYear records
    # -------------------------------------------------
    if school:
        academic_years = (
            SchoolAcademicYear.objects
            .filter(school=school)
            .order_by("-year")
        )
    else:
        academic_years = (
            SchoolAcademicYear.objects
            .all()
            .order_by("-year")
        )

    # -------------------------------------------------
    # Classes
    #
    # Classes come from SchoolClassCurriculum because
    # CBC submissions are tied to a curriculum assignment.
    # -------------------------------------------------
    if selected_year:

        class_curriculum_queryset = (
            SchoolClassCurriculum.objects
            .select_related(
                "school_class",
                "school_class__school",
                "curriculum_grade",
                "pathway",
            )
            .filter(
                academic_year=selected_year,
                school_class__curriculum="CBC",
            )
        )

        if school:
            class_curriculum_queryset = (
                class_curriculum_queryset.filter(
                    school_class__school=school,
                )
            )

        classes = (
            SchoolClass.objects
            .filter(
                id__in=class_curriculum_queryset.values_list(
                    "school_class_id",
                    flat=True,
                )
            )
            .distinct()
        )

        if school:
            classes = classes.order_by("name")
        else:
            classes = classes.select_related("school").order_by(
                "school__name",
                "name",
            )

    else:

        if school:
            classes = (
                SchoolClass.objects
                .filter(
                    school=school,
                    curriculum="CBC",
                )
                .order_by("name")
            )
        else:
            classes = (
                SchoolClass.objects
                .filter(curriculum="CBC")
                .select_related("school")
                .order_by(
                    "school__name",
                    "name",
                )
            )

    # -------------------------------------------------
    # Base submissions queryset
    # -------------------------------------------------
    submissions = (
        CBCAssessmentSubmission.objects
        .select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "learning_area",
        )
    )

    # -------------------------------------------------
    # School security
    # -------------------------------------------------
    if school:
        submissions = submissions.filter(
            school_class_curriculum__school_class__school=school,
        )

    # -------------------------------------------------
    # Academic Year filter
    # -------------------------------------------------
    if selected_year:
        submissions = submissions.filter(
            academic_year=selected_year,
        )

    # -------------------------------------------------
    # Term filter
    # -------------------------------------------------
    if selected_term in {"1", "2", "3"}:
        submissions = submissions.filter(
            term=selected_term,
        )

    # -------------------------------------------------
    # Class filter
    # -------------------------------------------------
    if selected_class:
        submissions = submissions.filter(
            school_class_curriculum__school_class_id=selected_class,
        )

    # -------------------------------------------------
    # Final ordering
    # -------------------------------------------------
    submissions = submissions.order_by(
        "-academic_year",
        "term",
        "school_class_curriculum__school_class__name",
        "learning_area__name",
        "-created_at",
    )

    # -------------------------------------------------
    # Render
    # -------------------------------------------------
    return render(
        request,
        "students/cbc_submission_review.html",
        {
            "submissions": submissions,
            "academic_years": academic_years,
            "classes": classes,
            "terms": ["1", "2", "3"],
            "selected_year": selected_year,
            "selected_term": selected_term,
            "selected_class": selected_class,
        },
    )

@login_required
@admin_required
def cbc_submission_approve(request, submission_id):
    """
    Approve a submitted CBC assessment.

    Only school administrators may approve submissions
    belonging to their school.
    """

    if request.method != "POST":
        return HttpResponseForbidden(
            "Approval must be submitted using POST."
        )

    submission = get_object_or_404(
        CBCAssessmentSubmission.objects.select_related(
            "school_class_curriculum",
            "school_class_curriculum__school_class",
        ),
        id=submission_id,
    )

    if request.user.is_superuser:
        allowed = True
    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            return HttpResponseForbidden(
                "Your account is not assigned to a school."
            )

        allowed = (
            submission.school_class_curriculum
            .school_class
            .school_id
            == school_user.school_id
        )

    if not allowed:
        return HttpResponseForbidden(
            "You are not authorized to approve this submission."
        )

    if submission.status != "SUBMITTED":
        messages.error(
            request,
            "Only submitted CBC assessments can be approved.",
        )
        return redirect("students:cbc_submission_review")

    submission.status = "APPROVED"
    submission.approved_at = timezone.now()
    submission.approved_by = request.user

    submission.save(
        update_fields=[
            "status",
            "approved_at",
            "approved_by",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "CBC assessment approved successfully.",
    )

    return redirect("students:cbc_submission_review")

@login_required
@admin_required
def cbc_submission_reject(request, submission_id):
    """
    Reject a submitted CBC assessment.

    Rejected assessments return to DRAFT so the teacher
    can correct the marks and submit again.
    """

    if request.method != "POST":
        return HttpResponseForbidden(
            "Rejection must be submitted using POST."
        )

    submission = get_object_or_404(
        CBCAssessmentSubmission.objects.select_related(
            "school_class_curriculum",
            "school_class_curriculum__school_class",
        ),
        id=submission_id,
    )

    if request.user.is_superuser:
        allowed = True
    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            return HttpResponseForbidden(
                "Your account is not assigned to a school."
            )

        allowed = (
            submission.school_class_curriculum
            .school_class
            .school_id
            == school_user.school_id
        )

    if not allowed:
        return HttpResponseForbidden(
            "You are not authorized to reject this submission."
        )

    if submission.status != "SUBMITTED":
        messages.error(
            request,
            "Only submitted CBC assessments can be rejected.",
        )
        return redirect("students:cbc_submission_review")

    rejection_reason = (
        request.POST.get("rejection_reason", "")
        .strip()
    )

    if not rejection_reason:
        messages.error(
            request,
            "Please provide a reason for rejecting this assessment.",
        )
        return redirect("students:cbc_submission_review")

    submission.status = "REJECTED"
    submission.rejection_reason = rejection_reason
    submission.submitted_at = None

    submission.save(
        update_fields=[
            "status",
            "rejection_reason",
            "submitted_at",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "CBC assessment rejected and returned to the teacher.",
    )

    return redirect("students:cbc_submission_review")


@login_required
@admin_required
def cbc_mark_edit(request, assessment_id):
    """
    Admin edit page for PP1–Grade 9 CBC Subject Assessments.

    One learning-area row represents:
        - CAT 1
        - Mid Term
        - End Term

    The assessment_id is used only to identify the student,
    learning area, academic year and term.

    The page then loads all three assessment components
    for that same assessment context.
    """

    # ============================================================
    # GET THE SELECTED ASSESSMENT
    # ============================================================

    assessment = get_object_or_404(
        CBCSubjectAssessment.objects.select_related(
            "student",
            "student__school",
            "student__school_class",
            "learning_area",
            "submission",
            "submission__school_class_curriculum",
            "submission__school_class_curriculum__school_class",
            "submission__school_class_curriculum__school_class__school",
        ),
        id=assessment_id,
    )

    # ============================================================
    # DETERMINE USER SCHOOL
    # ============================================================

    if request.user.is_superuser:
        school = None
    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            messages.error(
                request,
                "Your account is not assigned to a school.",
            )
            return redirect("students:home")

        school = school_user.school

    # ============================================================
    # SCHOOL SECURITY
    # ============================================================

    if school:

        if assessment.student.school_id != school.id:
            messages.error(
                request,
                "You are not authorized to edit this assessment.",
            )
            return redirect(
                "students:cbc_mark_list"
            )

        if (
            assessment.submission
            and assessment.submission.school_class_curriculum
            and assessment.submission.school_class_curriculum.school_class.school_id
            != school.id
        ):
            messages.error(
                request,
                "This assessment does not belong to your school.",
            )
            return redirect(
                "students:cbc_mark_list"
            )

    # ============================================================
    # SUBMISSION REQUIRED
    # ============================================================

    if not assessment.submission:
        messages.error(
            request,
            "This assessment is not linked to a submission.",
        )
        return redirect(
            "students:cbc_mark_list"
        )

    # ============================================================
    # IDENTIFY THE ASSESSMENT CONTEXT
    #
    # We deliberately use the selected assessment only as the
    # starting point. The actual edit page loads ALL THREE
    # components for the same:
    #
    # student
    # learning area
    # academic year
    # term
    # ============================================================

    student = assessment.student
    learning_area = assessment.learning_area
    academic_year = assessment.academic_year
    term = assessment.term

    school_class_curriculum = (
        assessment.submission.school_class_curriculum
    )

    if not school_class_curriculum:
        messages.error(
            request,
            "This assessment is not linked to a class curriculum.",
        )
        return redirect(
            "students:cbc_mark_list"
        )

    # ============================================================
    # LOAD CAT 1 / MID TERM / END TERM
    # ============================================================

    assessments = (
        CBCSubjectAssessment.objects
        .filter(
            student=student,
            learning_area=learning_area,
            academic_year=academic_year,
            term=term,
            submission__school_class_curriculum=school_class_curriculum,
            assessment_component__in=[
                "CAT1",
                "MID",
                "END",
            ],
        )
        .select_related(
            "submission",
            "submission__teacher",
        )
    )

    assessment_map = {
        item.assessment_component: item
        for item in assessments
    }

    cat1 = assessment_map.get("CAT1")
    mid = assessment_map.get("MID")
    end = assessment_map.get("END")

    # ============================================================
    # CHECK WHETHER ANY COMPONENT IS EDITABLE
    #
    # SUBMITTED = editable
    # APPROVED  = editable
    # DRAFT     = not editable
    # REJECTED  = not editable
    # ============================================================

    editable_statuses = {
        "SUBMITTED",
        "APPROVED",
    }

    editable_assessments = [
        item
        for item in (
            cat1,
            mid,
            end,
        )
        if (
            item is not None
            and item.submission is not None
            and item.submission.status in editable_statuses
        )
    ]

    if not editable_assessments:
        messages.error(
            request,
            "There are no submitted or approved assessments available for editing.",
        )
        return redirect(
            "students:cbc_mark_list"
        )

    # ============================================================
    # POST — SAVE ALL EDITABLE COMPONENTS
    # ============================================================

    if request.method == "POST":

        changed = False
        errors = []

        component_definitions = [
            ("CAT1", cat1, "cat1_score"),
            ("MID", mid, "mid_score"),
            ("END", end, "end_score"),
        ]

        for component, component_assessment, field_name in component_definitions:

            # ----------------------------------------------------
            # Assessment does not exist
            # ----------------------------------------------------

            if component_assessment is None:
                continue

            # ----------------------------------------------------
            # Only SUBMITTED / APPROVED may be edited
            # ----------------------------------------------------

            if (
                not component_assessment.submission
                or component_assessment.submission.status
                not in editable_statuses
            ):
                continue

            raw_score = request.POST.get(
                field_name,
                "",
            ).strip()

            # ----------------------------------------------------
            # Empty field
            #
            # Do not erase an existing mark accidentally.
            # ----------------------------------------------------

            if raw_score == "":
                errors.append(
                    f"{component} mark cannot be empty."
                )
                continue

            # ----------------------------------------------------
            # Validate score
            # ----------------------------------------------------

            try:

                score = Decimal(
                    raw_score
                ).quantize(
                    Decimal("0.01")
                )

                if score < Decimal("0"):
                    raise ValueError

            except (
                InvalidOperation,
                ValueError,
            ):
                errors.append(
                    f"Please enter a valid {component} mark."
                )
                continue

            # ----------------------------------------------------
            # Save score + recalculated performance level
            # ----------------------------------------------------

            component_assessment.score = score

            component_assessment.performance_level = (
                get_cbc_subject_performance_level(
                    score
                )
            )

            component_assessment.save(
                update_fields=[
                    "score",
                    "performance_level",
                    "updated_at",
                ]
            )

            changed = True

        # ========================================================
        # VALIDATION ERRORS
        # ========================================================

        if errors:

            for error in errors:
                messages.error(
                    request,
                    error,
                )

        elif changed:

            messages.success(
                request,
                "CBC assessment marks updated successfully.",
            )

            return redirect(
                "students:cbc_mark_list"
            )

        else:

            messages.warning(
                request,
                "No assessment marks were changed.",
            )

    # ============================================================
    # PERFORMANCE DISPLAY
    # ============================================================

    performance_labels = {
        4: "EE — Exceeding Expectations",
        3: "ME — Meeting Expectations",
        2: "AE — Approaching Expectations",
        1: "BE — Below Expectations",
    }

    def performance_display(assessment):
        if not assessment:
            return "—"

        value = getattr(
            assessment,
            "performance_level",
            None,
        )

        if value is None:
            return "—"

        code = getattr(
            value,
            "code",
            value,
        )

        return performance_labels.get(
            code,
            str(value),
        )

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "students/cbc_mark_edit.html",
        {
            "student": student,
            "learning_area": learning_area,
            "academic_year": academic_year,
            "term": term,
            "school_class_curriculum": school_class_curriculum,

            "assessment": assessment,

            "cat1": cat1,
            "mid": mid,
            "end": end,

            "cat1_performance": performance_display(cat1),
            "mid_performance": performance_display(mid),
            "end_performance": performance_display(end),

            "editable_statuses": editable_statuses,
        },
    )


@login_required
@admin_required
def cbc_upper_secondary_mark_edit(request, assessment_id):
    """
    Admin edit for one Grade 10–12 learning-area row.

    One page edits:
        - CAT 1
        - MID TERM
        - END TERM

    Editable when the individual assessment submission is:
        SUBMITTED
        APPROVED

    DRAFT and REJECTED assessments are displayed but cannot be edited.

    This does NOT modify:
        - marks_out_of
        - student
        - learning area
        - academic year
        - term
        - exam
        - submission status
    """

    # ============================================================
    # LOAD THE ANCHOR ASSESSMENT
    # ============================================================

    anchor = get_object_or_404(
        CBCUpperSecondaryAssessment.objects.select_related(
            "student",
            "student__school",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
            "submission",
            "submission__teacher",
            "exam",
        ),
        pk=assessment_id,
    )

    student = anchor.student
    learning_area = anchor.learning_area
    academic_year = str(anchor.academic_year)
    term = anchor.term

    # ============================================================
    # SCHOOL SECURITY
    # ============================================================

    if request.user.is_superuser:
        selected_school = student.school
    else:
        school_user = getattr(
            request.user,
            "school_user",
            None,
        )

        if not school_user or not school_user.school:
            messages.error(
                request,
                "Your account is not assigned to a school.",
            )
            return redirect("students:home")

        selected_school = school_user.school

        if student.school_id != selected_school.id:
            messages.error(
                request,
                "You are not authorized to edit this assessment.",
            )
            return redirect("students:cbc_mark_list")

    # ============================================================
    # VERIFY STUDENT ENROLLMENT FOR THIS YEAR + TERM
    # ============================================================

    enrollment = (
        student.academic_enrollments
        .filter(
            academic_year=academic_year,
            term=term,
        )
        .select_related(
            "school_class",
        )
        .first()
    )

    if not enrollment:
        messages.error(
            request,
            "No academic enrollment was found for this student "
            "for the selected academic year and term.",
        )
        return redirect("students:cbc_mark_list")

    school_class = enrollment.school_class

    # ============================================================
    # SCHOOL CLASS CURRICULUM
    # ============================================================

    school_class_curriculum = (
        SchoolClassCurriculum.objects
        .filter(
            school_class=school_class,
            academic_year=academic_year,
        )
        .select_related(
            "school_class",
            "curriculum_grade",
            "pathway",
        )
        .first()
    )

    if not school_class_curriculum:
        messages.error(
            request,
            "No CBC curriculum configuration was found for "
            "this class and academic year.",
        )
        return redirect("students:cbc_mark_list")

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    # ============================================================
    # MUST BE GRADE 10–12
    # ============================================================

    grade_code = (
        getattr(curriculum_grade, "code", None)
        or getattr(curriculum_grade, "name", "")
        or ""
    )

    grade_code = (
        str(grade_code)
        .upper()
        .replace(" ", "")
    )

    upper_secondary_grades = {
        "GRADE10",
        "GRADE11",
        "GRADE12",
        "10",
        "11",
        "12",
    }

    if grade_code not in upper_secondary_grades:
        messages.error(
            request,
            "This assessment is not a Grade 10–12 assessment.",
        )
        return redirect("students:cbc_mark_list")

    # ============================================================
    # PATHWAY / LEARNING AREA INTEGRITY
    # ============================================================

    expected_learning_area = (
        CurriculumLearningArea.objects
        .filter(
            id=learning_area.id,
            curriculum_grade=curriculum_grade,
            assessment_enabled=True,
        )
        .first()
    )

    if not expected_learning_area:
        messages.error(
            request,
            "The learning area does not belong to the "
            "student's Grade 10–12 curriculum.",
        )
        return redirect("students:cbc_mark_list")

    class_pathway = school_class_curriculum.pathway

    if class_pathway:
        if learning_area.pathway_id != class_pathway.id:
            messages.error(
                request,
                "The learning area does not belong to the "
                "student's selected pathway.",
            )
            return redirect("students:cbc_mark_list")
    else:
        if learning_area.pathway_id is not None:
            messages.error(
                request,
                "This class has no pathway configured, but the "
                "selected learning area is pathway-specific.",
            )
            return redirect("students:cbc_mark_list")

    # ============================================================
    # LOAD ALL THREE COMPONENTS
    # ============================================================

    assessments = (
        CBCUpperSecondaryAssessment.objects
        .filter(
            student=student,
            learning_area=learning_area,
            academic_year=academic_year,
            term=term,
        )
        .select_related(
            "submission",
            "exam",
            "performance_level",
        )
    )

    assessment_map = {
        assessment.assessment_component: assessment
        for assessment in assessments
    }

    cat1 = assessment_map.get("CAT1")
    mid = assessment_map.get("MID")
    end = assessment_map.get("END")

    components = [
        ("CAT1", "CAT 1", cat1),
        ("MID", "MID TERM", mid),
        ("END", "END TERM", end),
    ]

    # ============================================================
    # POST
    # ============================================================

    if request.method == "POST":

        updates = []

        for component_code, component_label, assessment in components:

            if not assessment:
                continue

            status = (
                assessment.submission.status
                if assessment.submission
                else None
            )

            # ----------------------------------------------------
            # Only SUBMITTED and APPROVED can be edited.
            # ----------------------------------------------------

            if status not in {"SUBMITTED", "APPROVED"}:
                continue

            raw_value = request.POST.get(
                f"{component_code.lower()}_score"
            )

            if raw_value is None:
                continue

            raw_value = raw_value.strip()

            if raw_value == "":
                messages.error(
                    request,
                    f"{component_label}: a mark is required.",
                )
                return render(
                    request,
                    "students/cbc/upper_secondary_mark_edit.html",
                    {
                        "student": student,
                        "school_class": school_class,
                        "school_class_curriculum": (
                            school_class_curriculum
                        ),
                        "curriculum_grade": curriculum_grade,
                        "learning_area": learning_area,
                        "academic_year": academic_year,
                        "term": term,
                        "components": components,
                        "cat1": cat1,
                        "mid": mid,
                        "end": end,
                    },
                )

            try:
                score = Decimal(raw_value)
            except (InvalidOperation, ValueError):
                messages.error(
                    request,
                    f"{component_label}: enter a valid numeric mark.",
                )
                return render(
                    request,
                    "students/cbc/upper_secondary_mark_edit.html",
                    {
                        "student": student,
                        "school_class": school_class,
                        "school_class_curriculum": (
                            school_class_curriculum
                        ),
                        "curriculum_grade": curriculum_grade,
                        "learning_area": learning_area,
                        "academic_year": academic_year,
                        "term": term,
                        "components": components,
                        "cat1": cat1,
                        "mid": mid,
                        "end": end,
                    },
                )

            marks_out_of = assessment.marks_out_of

            # ----------------------------------------------------
            # MARK RANGE
            # ----------------------------------------------------

            if score < 0 or score > marks_out_of:
                messages.error(
                    request,
                    f"{component_label}: mark must be between "
                    f"0 and {marks_out_of}.",
                )
                return render(
                    request,
                    "students/cbc/upper_secondary_mark_edit.html",
                    {
                        "student": student,
                        "school_class": school_class,
                        "school_class_curriculum": (
                            school_class_curriculum
                        ),
                        "curriculum_grade": curriculum_grade,
                        "learning_area": learning_area,
                        "academic_year": academic_year,
                        "term": term,
                        "components": components,
                        "cat1": cat1,
                        "mid": mid,
                        "end": end,
                    },
                )

            # ----------------------------------------------------
            # NORMALIZE TO PERCENTAGE
            # ----------------------------------------------------

            if marks_out_of <= 0:
                messages.error(
                    request,
                    f"{component_label}: marks out of must be "
                    f"greater than zero.",
                )
                return render(
                    request,
                    "students/cbc/upper_secondary_mark_edit.html",
                    {
                        "student": student,
                        "school_class": school_class,
                        "school_class_curriculum": (
                            school_class_curriculum
                        ),
                        "curriculum_grade": curriculum_grade,
                        "learning_area": learning_area,
                        "academic_year": academic_year,
                        "term": term,
                        "components": components,
                        "cat1": cat1,
                        "mid": mid,
                        "end": end,
                    },
                )

            percentage_score = (
                (score / marks_out_of)
                * Decimal("100")
            ).quantize(
                Decimal("0.01")
            )

            # ----------------------------------------------------
            # PERFORMANCE LEVEL + POINTS
            # ----------------------------------------------------

            performance_level, points = (
                get_upper_secondary_performance(
                    curriculum_grade=curriculum_grade,
                    percentage=percentage_score,
                )
            )

            if performance_level is None:
                messages.error(
                    request,
                    f"{component_label}: no configured CBC "
                    f"performance level covers "
                    f"{percentage_score}%.",
                )
                return render(
                    request,
                    "students/cbc/upper_secondary_mark_edit.html",
                    {
                        "student": student,
                        "school_class": school_class,
                        "school_class_curriculum": (
                            school_class_curriculum
                        ),
                        "curriculum_grade": curriculum_grade,
                        "learning_area": learning_area,
                        "academic_year": academic_year,
                        "term": term,
                        "components": components,
                        "cat1": cat1,
                        "mid": mid,
                        "end": end,
                    },
                )

            updates.append(
                (
                    assessment,
                    score,
                    percentage_score,
                    performance_level,
                    points,
                )
            )

        # --------------------------------------------------------
        # SAVE ALL COMPONENTS TOGETHER
        # --------------------------------------------------------

        if not updates:
            messages.warning(
                request,
                "There are no submitted or approved assessments "
                "available for editing.",
            )
            return redirect(
                "students:cbc_mark_list"
            )

        with transaction.atomic():

            for (
                assessment,
                score,
                percentage_score,
                performance_level,
                points,
            ) in updates:

                assessment.raw_score = score
                assessment.percentage_score = (
                    percentage_score
                )
                assessment.performance_level = (
                    performance_level
                )
                assessment.points = points

                # Keep marks_out_of, exam, submission,
                # student, learning area and entered_by unchanged.
                assessment.save(
                    update_fields=[
                        "raw_score",
                        "percentage_score",
                        "performance_level",
                        "points",
                        "updated_at",
                    ]
                )

        messages.success(
            request,
            "Upper-secondary assessment marks updated successfully.",
        )

        return redirect(
            "students:cbc_mark_list"
        )

    # ============================================================
    # GET
    # ============================================================

    return render(
        request,
        "students/cbc/upper_secondary_mark_edit.html",
        {
            "student": student,
            "school_class": school_class,
            "school_class_curriculum": (
                school_class_curriculum
            ),
            "curriculum_grade": curriculum_grade,
            "learning_area": learning_area,
            "academic_year": academic_year,
            "term": term,
            "components": components,
            "cat1": cat1,
            "mid": mid,
            "end": end,
        },
    )


@login_required
def cbc_subject_assessment_print(
    request,
    assignment_id,
    student_id,
):
    """
    Printable CBC Subject / Learning Area Assessment
    for one student.

    This is completely separate from the CBC
    strand/sub-strand assessment-book print.

    Data source:
        CBCSubjectAssessment

    Displays:
        CAT 1
        Mid-Term
        End-Term
        Average
        Performance Level
    """

    # ========================================================
    # TERM
    # ========================================================

    try:
        term = str(request.GET.get("term", "1"))
    except (TypeError, ValueError):
        term = "1"

    if term not in {"1", "2", "3"}:
        term = "1"

    # ========================================================
    # GET ASSIGNMENT
    # ========================================================

    assignment = get_object_or_404(
        TeacherAssessmentAssignment.objects.select_related(
            "teacher",
            "teacher__school",
            "school_class_curriculum",
            "school_class_curriculum__school_class",
            "school_class_curriculum__school_class__school",
            "school_class_curriculum__curriculum_grade",
            "school_class_curriculum__curriculum_version",
            "school_class_curriculum__pathway",
            "learning_area",
        ),
        id=assignment_id,
    )

    # ========================================================
    # SECURITY — ASSIGNMENT
    # ========================================================

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # CURRICULUM INTEGRITY
    # ========================================================

    if not curriculum_integrity_is_valid(
        assignment
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # SCHOOL / CLASS / LEARNING AREA
    # ========================================================

    curriculum = assignment.school_class_curriculum
    school_class = curriculum.school_class
    school = school_class.school
    learning_area = assignment.learning_area

    academic_year = str(assignment.academic_year)

    # ========================================================
    # END-TERM EXAM CONFIGURATION
    # ========================================================

    end_term_exam = get_cbc_open_exam(
        school=school,
        academic_year=academic_year,
        term=term,
        assessment_component="END",
    )

    end_marks_out_of = (
        end_term_exam.marks_out_of
        if end_term_exam
        else None
    )

    
    # ========================================================
    # GET STUDENT
    # ========================================================

    student = get_object_or_404(
        Student.objects.select_related(
            "school",
            "school_class",
        ),
        id=student_id,
    )

    # ========================================================
    # STUDENT SECURITY
    # ========================================================

    if student.school_id != school.id:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    if student.school_class_id != school_class.id:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ========================================================
    # GET SUBJECT ASSESSMENTS
    # ========================================================

    assessments = (
        CBCSubjectAssessment.objects.filter(
            student=student,
            learning_area=learning_area,
            academic_year=academic_year,
            term=term,
        )
        .select_related(
            "learning_area",
        )
        .order_by(
            "assessment_component",
        )
    )

    # ========================================================
    # COMPONENTS
    # ========================================================

    component_map = {
        "CAT1": None,
        "MID": None,
        "END": None,
    }

    for assessment in assessments:
        component_map[
            assessment.assessment_component
        ] = assessment

    cat1_assessment = component_map["CAT1"]
    mid_assessment = component_map["MID"]
    end_assessment = component_map["END"]

    # ========================================================
    # SCORES
    # ========================================================

    cat1_score = (
        cat1_assessment.score
        if cat1_assessment
        else None
    )

    mid_score = (
        mid_assessment.score
        if mid_assessment
        else None
    )

    end_score = (
        end_assessment.score
        if end_assessment
        else None
    )

    # ========================================================
    # END-TERM PERCENTAGE
    # ========================================================

    end_percentage = None

    if end_score is not None and end_marks_out_of:
        try:
            end_percentage = (
                Decimal(str(end_score))
                / Decimal(str(end_marks_out_of))
                * Decimal("100")
            ).quantize(Decimal("0.01"))
        except (TypeError, ValueError, ArithmeticError):
            end_percentage = None

    # ========================================================
    # AVERAGE
    # ========================================================

    scores = [
        score
        for score in (
            cat1_score,
            mid_score,
            end_score,
        )
        if score is not None
    ]

    average = None

    if scores:
        average = (
            sum(scores) / len(scores)
        ).quantize(
            Decimal("0.01")
        )

    # ========================================================
    # PERFORMANCE LEVEL
    # ========================================================

    performance_level = None

    # Prefer End-Term, then Mid-Term, then CAT1
    if end_assessment is not None:
        performance_level = (
            end_assessment.performance_level
        )

    elif mid_assessment is not None:
        performance_level = (
            mid_assessment.performance_level
        )

    elif cat1_assessment is not None:
        performance_level = (
            cat1_assessment.performance_level
        )

    performance_labels = {
        4: "EE — Exceeding Expectations",
        3: "ME — Meeting Expectations",
        2: "AE — Approaching Expectations",
        1: "BE — Below Expectations",
    }

    performance_label = (
        performance_labels.get(
            performance_level,
            "",
        )
        if performance_level
        else ""
    )

    # ========================================================
    # TEACHER COMMENT
    # ========================================================

    teacher_comment = ""

    if end_assessment is not None:
        teacher_comment = (
            end_assessment.teacher_comment
            or ""
        )

    elif mid_assessment is not None:
        teacher_comment = (
            mid_assessment.teacher_comment
            or ""
        )

    elif cat1_assessment is not None:
        teacher_comment = (
            cat1_assessment.teacher_comment
            or ""
        )

    # ========================================================
    # PRINT
    # ========================================================

    return render(
        request,
        "students/cbc/subject_assessment_print.html",
        {
            "assignment": assignment,
            "school": school,
            "school_class": school_class,
            "curriculum": curriculum,
            "learning_area": learning_area,
            "academic_year": academic_year,
            "term": term,
            "student": student,

            # Assessments
            "cat1_assessment": cat1_assessment,
            "mid_assessment": mid_assessment,
            "end_assessment": end_assessment,

            # Scores
            "cat1_score": cat1_score,
            "mid_score": mid_score,
            "end_score": end_score,

            # End-Term exam configuration
            "end_term_exam": end_term_exam,
            "end_marks_out_of": end_marks_out_of,
            "end_percentage": end_percentage,

            # Calculated result
            "average": average,
            "performance_level": performance_level,

            # Comment
            "teacher_comment": teacher_comment,
        },
    )

@login_required
@admin_or_teacher
def cbc_subject_assessment_book(
    request,
    student_id,
):
    """
    CBC Subject Assessment Book

    Displays one learner's complete CBC subject/learning-area
    assessment summary for a selected academic year and term.

    Components:
        CAT 1
        Mid-Term
        End-Term
        Average
        Performance Level

    CBCSubjectAssessment.score is already stored as a percentage,
    so the average is calculated directly from the stored values.

    This is completely separate from:
        - cbc_assessment_book
        - cbc_assessment_book_print
        - cbc_subject_assessment_print
        - cbc_subject_score_sheet
    """

    # =========================================================
    # DETERMINE SCHOOL
    # =========================================================

    if request.user.is_superuser:
        school = None
    else:
        school_user = (
            SchoolUser.objects
            .select_related("school")
            .filter(user=request.user)
            .first()
        )

        if not school_user or not school_user.school:
            return HttpResponseForbidden(
                "Your account is not associated with a school."
            )

        school = school_user.school

    # =========================================================
    # SELECTED YEAR / TERM
    # =========================================================

    selected_year = (
        request.GET.get("year")
        or request.POST.get("year")
        or str(date.today().year)
    ).strip()

    selected_term = (
        request.GET.get("term")
        or request.POST.get("term")
        or "1"
    ).strip()

    if selected_term not in {"1", "2", "3"}:
        selected_term = "1"

    # =========================================================
    # GET STUDENT
    # =========================================================

    student_queryset = (
        Student.objects
        .select_related(
            "school",
            "school_class",
        )
    )

    if school:
        student_queryset = student_queryset.filter(
            school=school,
        )

    student = get_object_or_404(
        student_queryset,
        id=student_id,
    )

    # =========================================================
    # STUDENT SCHOOL SECURITY
    # =========================================================

    if school and student.school_id != school.id:
        return HttpResponseForbidden(
            "You are not authorized to access this learner."
        )

    # =========================================================
    # STUDENT CLASS
    # =========================================================

    school_class = student.school_class

    if not school_class:
        return HttpResponseForbidden(
            "This learner is not assigned to a class."
        )

    # =========================================================
    # SCHOOL
    # =========================================================

    if school is None:
        school = student.school

    if not school:
        return HttpResponseForbidden(
            "This learner is not associated with a school."
        )

    # =========================================================
    # GET CBC CURRICULUM FOR THIS CLASS / YEAR
    # =========================================================

    school_class_curriculum = (
        SchoolClassCurriculum.objects
        .select_related(
            "school_class",
            "curriculum_grade",
            "curriculum_version",
            "pathway",
        )
        .filter(
            school_class=school_class,
            academic_year=selected_year,
        )
        .first()
    )

    if not school_class_curriculum:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # =========================================================
    # CURRICULUM INTEGRITY
    # =========================================================

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    curriculum_pathway = (
        school_class_curriculum.pathway
    )

    # =========================================================
    # ACTIVE CBC LEARNING AREAS
    # =========================================================

    learning_areas = (
        CurriculumLearningArea.objects
        .filter(
            curriculum_grade=curriculum_grade,
            assessment_enabled=True,
        )
        .filter(
            Q(pathway__isnull=True)
            | Q(pathway=curriculum_pathway)
        )
        .order_by("name")
    )

    # =========================================================
    # LOAD ASSESSMENTS
    # =========================================================

    assessments = (
        CBCSubjectAssessment.objects
        .select_related(
            "learning_area",
            "submission",
        )
        .filter(
            student=student,
            academic_year=selected_year,
            term=selected_term,
            assessment_component__in=[
                "CAT1",
                "MID",
                "END",
            ],
        )
    )

    # =========================================================
    # MAP ASSESSMENTS
    # =========================================================

    assessment_map = {}

    for assessment in assessments:

        learning_area_id = (
            assessment.learning_area_id
        )

        if learning_area_id not in assessment_map:
            assessment_map[learning_area_id] = {}

        assessment_map[
            learning_area_id
        ][
            assessment.assessment_component
        ] = assessment

    # =========================================================
    # BUILD BOOK ROWS
    # =========================================================

    result_rows = []

    for learning_area in learning_areas:

        component_map = assessment_map.get(
            learning_area.id,
            {},
        )

        cat1_assessment = (
            component_map.get("CAT1")
        )

        mid_assessment = (
            component_map.get("MID")
        )

        end_assessment = (
            component_map.get("END")
        )

        # -----------------------------------------------------
        # SCORES
        # -----------------------------------------------------

        cat1_score = (
            cat1_assessment.score
            if (
                cat1_assessment
                and cat1_assessment.score is not None
            )
            else None
        )

        mid_score = (
            mid_assessment.score
            if (
                mid_assessment
                and mid_assessment.score is not None
            )
            else None
        )

        end_score = (
            end_assessment.score
            if (
                end_assessment
                and end_assessment.score is not None
            )
            else None
        )

        # -----------------------------------------------------
        # AVERAGE
        #
        # Scores are already percentages.
        # -----------------------------------------------------

        average = None

        available_scores = [
            score
            for score in (
                cat1_score,
                mid_score,
                end_score,
            )
            if score is not None
        ]

        if available_scores:

            average = (
                sum(available_scores)
                / Decimal(str(len(available_scores)))
            ).quantize(
                Decimal("0.01")
            )

        # -----------------------------------------------------
        # PERFORMANCE LEVEL
        #
        # Use the calculated average when available.
        # -----------------------------------------------------

        performance_level = None
        performance_label = ""

        if average is not None:

            performance_level = (
                get_cbc_subject_performance_level(
                    average
                )
            )

            performance_label = (
                cbc_performance_level_label(
                    performance_level
                )
            )

        result_rows.append(
            {
                "learning_area": learning_area,

                "cat1_assessment": (
                    cat1_assessment
                ),

                "mid_assessment": (
                    mid_assessment
                ),

                "end_assessment": (
                    end_assessment
                ),

                "cat1_score": cat1_score,

                "mid_score": mid_score,

                "end_score": end_score,

                "average": average,

                "performance_level": (
                    performance_level
                ),

                "performance_label": (
                    performance_label
                ),
            }
        )

    # =========================================================
    # TOTAL SCORES
    # =========================================================

    total_cat1 = None
    total_mid = None
    total_end = None
    total_average = None
    total_performance_level = None
    total_performance_label = ""

    cat1_values = [
        row["cat1_score"]
        for row in result_rows
        if row["cat1_score"] is not None
    ]

    mid_values = [
        row["mid_score"]
        for row in result_rows
        if row["mid_score"] is not None
    ]

    end_values = [
        row["end_score"]
        for row in result_rows
        if row["end_score"] is not None
    ]

    average_values = [
        row["average"]
        for row in result_rows
        if row["average"] is not None
    ]

    if cat1_values:
        total_cat1 = (
            sum(cat1_values)
        ).quantize(
            Decimal("0.01")
        )

    if mid_values:
        total_mid = (
            sum(mid_values)
        ).quantize(
            Decimal("0.01")
        )

    if end_values:
        total_end = (
            sum(end_values)
        ).quantize(
            Decimal("0.01")
        )

    if average_values:
        total_average = (
            sum(average_values)
        ).quantize(
            Decimal("0.01")
        )

        # =========================================================
        # OVERALL PERFORMANCE LEVEL
        #
        # PP1–GRADE 9:
        # 4 = EE
        # 3 = ME
        # 2 = AE
        # 1 = BE
        #
        # Add the numerical level for each assessed learning area,
        # divide by the number of assessed learning areas,
        # round to the nearest whole level, then convert back
        # to the CBC performance label.
        # =========================================================

        performance_points = []

        for row in result_rows:

            performance_level = row.get(
                "performance_level"
            )

            if performance_level is None:
                continue

            # Get the numerical value stored on the
            # CBC performance-level record.
            level_value = getattr(
                performance_level,
                "code",
                None,
            )

            try:
                level_value = int(level_value)
            except (TypeError, ValueError):
                level_value = None

            if level_value in {1, 2, 3, 4}:
                performance_points.append(
                    level_value
                )

        if performance_points:

            average_level = (
                Decimal(
                    sum(performance_points)
                )
                / Decimal(
                    len(performance_points)
                )
            )

            # Round to the nearest whole CBC level.
            rounded_level = int(
                average_level.quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )

            # Keep safely within CBC levels 1–4.
            rounded_level = max(
                1,
                min(4, rounded_level),
            )

            total_performance_level = (
                rounded_level
            )

            total_performance_label = (
                {
                    4: "EE",
                    3: "ME",
                    2: "AE",
                    1: "BE",
                }
                .get(
                    rounded_level,
                    "",
                )
            )

    # =========================================================
    # DISPLAY
    # =========================================================

    return render(
        request,
        "students/cbc/subject_assessment_book.html",
        {
            "student": student,
            "school": school,
            "school_class": school_class,
            "school_class_curriculum": (
                school_class_curriculum
            ),

            "curriculum_grade": (
                curriculum_grade
            ),

            "curriculum_pathway": (
                curriculum_pathway
            ),

            "academic_year": selected_year,
            "term": selected_term,

            "result_rows": result_rows,

            "total_cat1": total_cat1,
            "total_mid": total_mid,
            "total_end": total_end,
            "total_average": total_average,
            "total_performance_level": total_performance_level,
            "total_performance_label": total_performance_label,
        },
    )
