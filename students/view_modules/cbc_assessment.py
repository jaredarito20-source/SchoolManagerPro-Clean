from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from students.models import (
    Teacher,
    
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
            "term",
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
        "term",
        "school_class_curriculum__school_class__name",
        "learning_area__name",
    )


def assignment_belongs_to_user(request, assignment):
    """
    Final authorization check.

    Never trust an assignment ID supplied in a URL.
    """

    if request.user.is_superuser:
        return True

    teacher = get_cbc_teacher(request)

    if not teacher or not teacher.school:
        return False

    if assignment.teacher_id != teacher.id:
        return False

    if assignment.teacher.school_id != teacher.school_id:
        return False

    curriculum = assignment.school_class_curriculum

    if curriculum.school_class.school_id != teacher.school_id:
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

    Security:
        - Ordinary teachers only see their own assignments.
        - Ordinary teachers are restricted to their own school.
        - Superusers may see all valid assignments.
        - Invalid curriculum configurations are excluded.
        - Classes are grouped by curriculum + academic year + term.
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
            "term",
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
        # One entry per:
        #
        # curriculum + academic year + term
        # --------------------------------------------------------

        key = (
            curriculum.id,
            assignment.academic_year,
            assignment.term,
        )

        if key not in class_entries:

            class_entries[key] = {
                "curriculum": curriculum,
                "school_class": school_class,
                "academic_year": assignment.academic_year,
                "term": assignment.term,
            }

    # ============================================================
    # SORT CLASSES
    # ============================================================

    classes = sorted(
        class_entries.values(),
        key=lambda item: (
            str(item["academic_year"]),
            str(item["term"]),
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
            "| TERM:",
            item["term"],
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
    Show only Learning Areas assigned to the teacher for
    this exact CBC class curriculum, year and term.
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

        assignments = TeacherAssessmentAssignment.objects.filter(
            teacher=teacher,
            teacher__school=teacher.school,
            school_class_curriculum=curriculum,
            academic_year=curriculum.academic_year,
            term=term,
        ).select_related(
            "teacher",
            "teacher__school",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        )

    else:

        assignments = TeacherAssessmentAssignment.objects.filter(
            school_class_curriculum=curriculum,
            academic_year=curriculum.academic_year,
            term=term,
        ).select_related(
            "teacher",
            "teacher__school",
            "learning_area",
            "learning_area__curriculum_grade",
            "learning_area__pathway",
        )

    # --------------------------------------------------------
    # Remove any internally invalid assignments.
    # --------------------------------------------------------

    valid_assignments = []

    for assignment in assignments:

        if assignment.academic_year != curriculum.academic_year:
            continue

        if assignment.term != term:
            continue

        if not curriculum_integrity_is_valid(assignment):
            continue

        # Ordinary teacher gets another explicit school check.
        if not request.user.is_superuser:

            teacher = get_cbc_teacher(request)

            if (
                assignment.teacher_id != teacher.id
                or assignment.teacher.school_id != teacher.school_id
            ):
                continue

        valid_assignments.append(assignment)

    return render(
        request,
        "students/cbc/learning_areas.html",
        {
            "curriculum": curriculum,
            "assignments": valid_assignments,
            "term": term,
        },
    )


@login_required
def cbc_assessment_book(
    request,
    assignment_id,
):
    """
    Teacher-facing CBC Assessment Book.

    Workflow:

        Class
            ↓
        Learning Area
            ↓
        Strand
            ↓
        Sub-Strand
            ↓
        Whole Class
            ↓
        Enter Marks
            ↓
        System derives Performance Level + Points

    Teacher enters MARKS ONLY.
    """

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

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return HttpResponseForbidden(
            "You are not authorized to access this assessment assignment."
        )

    if not curriculum_integrity_is_valid(
        assignment,
    ):
        messages.error(
            request,
            "This assessment assignment has invalid curriculum configuration.",
        )
        return redirect("students:cbc_my_classes")

    school_class_curriculum = assignment.school_class_curriculum
    school_class = school_class_curriculum.school_class
    school = school_class.school
    learning_area = assignment.learning_area

    try:
        academic_year = int(
            assignment.academic_year
        )
    except (TypeError, ValueError):
        messages.error(
            request,
            "Invalid academic year on this assessment assignment.",
        )
        return redirect("students:cbc_my_classes")

    # ---------------------------------------------------------
    # ASSESSMENT COMPONENT
    # ---------------------------------------------------------

    valid_components = {
        value
        for value, label
        in CBCSubStrandAssessment.ASSESSMENT_COMPONENT_CHOICES
    }

    assessment_component = (
        request.POST.get("assessment_component")
        or request.GET.get("assessment_component")
        or "CAT1"
    )

    if assessment_component not in valid_components:
        assessment_component = "CAT1"

    # ---------------------------------------------------------
    # AUTHORIZED CLASSES FOR THIS TEACHER / LEARNING AREA
    # ---------------------------------------------------------

    authorized_assignments = (
        get_teacher_assignments(request)
        .filter(
            academic_year=assignment.academic_year,
            term=assignment.term,
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
        if curriculum_integrity_is_valid(candidate):
            valid_authorized_assignments.append(candidate)

    authorized_classes = []
    seen_class_ids = set()

    for candidate in valid_authorized_assignments:

        candidate_class = (
            candidate.school_class_curriculum.school_class
        )

        if candidate_class.id not in seen_class_ids:

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

    # ---------------------------------------------------------
    # SELECT CLASS
    # ---------------------------------------------------------

    requested_class_id = (
        request.POST.get("class_id")
        or request.GET.get("class_id")
    )

    if requested_class_id:

        try:
            requested_class_id = int(
                requested_class_id
            )
        except (TypeError, ValueError):
            requested_class_id = None

    selected_assignment = assignment

    if requested_class_id:

        matching_assignments = [
            candidate
            for candidate in valid_authorized_assignments
            if (
                candidate.school_class_curriculum
                .school_class
                .id
                == requested_class_id
            )
        ]

        if matching_assignments:

            selected_assignment = (
                matching_assignments[0]
            )

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

            try:
                academic_year = int(
                    selected_assignment.academic_year
                )
            except (TypeError, ValueError):

                messages.error(
                    request,
                    "Invalid academic year on this assessment assignment.",
                )

                return redirect(
                    "students:cbc_my_classes"
                )

        else:

            messages.error(
                request,
                "You are not authorized to assess that class.",
            )

    # ---------------------------------------------------------
    # CURRICULUM GRADE
    # ---------------------------------------------------------

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    # ---------------------------------------------------------
    # STRANDS
    # ---------------------------------------------------------

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
        except (TypeError, ValueError):
            requested_strand_id = None

    selected_strand = None

    if requested_strand_id:

        selected_strand = next(
            (
                strand
                for strand in strands
                if strand.id == requested_strand_id
            ),
            None,
        )

    if selected_strand is None and strands:

        selected_strand = strands[0]

    # ---------------------------------------------------------
    # SUB-STRANDS
    # ---------------------------------------------------------

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
        except (TypeError, ValueError):
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

    # ---------------------------------------------------------
    # STUDENTS
    # ---------------------------------------------------------

    students = list(
        Student.objects.filter(
            school_id=school.id,
            school_class_id=school_class.id,
        ).order_by(
            "admission_number",
            "first_name",
            "last_name",
        )
    )

    # ---------------------------------------------------------
    # PERFORMANCE LEVELS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # SUBMIT ASSESSMENT
    # ---------------------------------------------------------

    if request.method == "POST":

        if selected_strand is None:

            messages.error(
                request,
                "Please select a strand.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        if selected_sub_strand is None:

            messages.error(
                request,
                "Please select a sub-strand.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

        if not assignment_belongs_to_user(
            request,
            selected_assignment,
        ):

            return HttpResponseForbidden(
                "You are not authorized to access this assessment assignment."
            )

        if not curriculum_integrity_is_valid(
            selected_assignment,
        ):

            messages.error(
                request,
                "This assessment assignment has invalid curriculum configuration.",
            )

            return redirect(
                "students:cbc_my_classes"
            )

        # -----------------------------------------------------
        # SUBMISSION
        # -----------------------------------------------------

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
                term=selected_assignment.term,
                defaults={
                    "teacher": selected_assignment.teacher,
                    "status": "DRAFT",
                },
            )
        )

        if submission.status == "APPROVED":

            messages.error(
                request,
                "This assessment has already been approved and cannot be edited.",
            )

            return redirect(
                "students:cbc_assessment_book",
                assignment_id=selected_assignment.id,
            )

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

        # -----------------------------------------------------
        # VALIDATE ALL CLASS MARKS FIRST
        # -----------------------------------------------------

        values_to_save = []

        for student in students:

            mark_value = request.POST.get(
                f"mark_{student.id}",
                "",
            ).strip()

            teacher_comment = request.POST.get(
                f"comment_{student.id}",
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

                if mark < 0 or mark > 100:

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
                    "teacher_comment": (
                        teacher_comment
                    ),
                }
            )

        # -----------------------------------------------------
        # SAVE ATOMICALLY
        # -----------------------------------------------------

        with transaction.atomic():

            for item in values_to_save:

                student = item["student"]
                mark = item["mark"]
                performance_level = (
                    item["performance_level"]
                )
                teacher_comment = (
                    item["teacher_comment"]
                )

                existing_filter = {
                    "student": student,
                    "sub_strand": selected_sub_strand,
                    "academic_year": academic_year,
                    "term": selected_assignment.term,
                    "assessment_component": (
                        assessment_component
                    ),
                    "submission": submission,
                }

                if (
                    mark is None
                    and not teacher_comment
                ):

                    CBCSubStrandAssessment.objects.filter(
                        **existing_filter
                    ).delete()

                    continue

                CBCSubStrandAssessment.objects.update_or_create(
                    **existing_filter,
                    defaults={
                        "performance_level": (
                            performance_level
                        ),
                        "mark": mark,
                        "points": (
                            performance_level.points
                            if performance_level
                            else None
                        ),
                        "teacher_comment": (
                            teacher_comment
                        ),
                        "entered_by": request.user,
                        "legacy_performance_level": "",
                    },
                )

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

    # ---------------------------------------------------------
    # EXISTING RECORDS
    # ---------------------------------------------------------

    existing_records = {}

    if (
        selected_sub_strand
        and students
    ):

        records = (
            CBCSubStrandAssessment.objects.filter(
                student__in=students,
                sub_strand=selected_sub_strand,
                academic_year=academic_year,
                term=selected_assignment.term,
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

    # ---------------------------------------------------------
    # CLASS LIST
    # ---------------------------------------------------------

    student_rows = []

    for index, student in enumerate(
        students,
        start=1,
    ):

        record = existing_records.get(
            student.id
        )

        student_rows.append(
            {
                "number": index,
                "student": student,
                "record": record,
            }
        )

    # ---------------------------------------------------------
    # PREVIOUS / NEXT SUB-STRAND
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    context = {
        "assignment": selected_assignment,

        "curriculum": (
            school_class_curriculum
        ),

        "school": school,

        "school_class": school_class,

        "learning_area": learning_area,

        "academic_year": academic_year,

        "term": selected_assignment.term,

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
def cbc_assessment_book_print(request):
    """
    Printable CBC Assessment Book.

    The teacher may only print an assessment book for a CBC
    teacher assignment they are authorized to access.
    """

    assignment_id = request.GET.get("assignment")
    assessment_component = request.GET.get(
        "assessment_component",
        "CAT1",
    )

    if not assignment_id:
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

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

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    if not assignment_belongs_to_user(
        request,
        assignment,
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    # ---------------------------------------------------------
    # CURRICULUM INTEGRITY
    # ---------------------------------------------------------

    if not curriculum_integrity_is_valid(
        assignment
    ):
        return render(
            request,
            "students/cbc/access_denied.html",
            status=403,
        )

    curriculum = (
        assignment.school_class_curriculum
    )

    school_class = (
        curriculum.school_class
    )

    school = school_class.school

    academic_year = assignment.academic_year
    term = assignment.term

    # ---------------------------------------------------------
    # STRANDS / SUB-STRANDS
    # ---------------------------------------------------------

    strands = CurriculumStrand.objects.filter(
        learning_area=assignment.learning_area,
        curriculum_grade=curriculum.curriculum_grade,
        curriculum_version=curriculum.curriculum_version,
    ).order_by(
        "order",
        "id",
    )

    # ---------------------------------------------------------
    # STUDENTS
    # ---------------------------------------------------------

    students = Student.objects.filter(
        school=school,
        school_class=school_class,
    ).order_by(
        "admission_number",
        "first_name",
        "last_name",
    )

    # ---------------------------------------------------------
    # PERFORMANCE LEVELS
    # ---------------------------------------------------------

    performance_levels = CBCPerformanceLevel.objects.filter(
        curriculum_grade=curriculum.curriculum_grade,
    ).order_by(
        "order",
        "minimum_mark",
    )

    def get_performance_level(mark):
        if mark is None:
            return None

        try:
            mark = Decimal(str(mark))
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            return None

        return performance_levels.filter(
            minimum_mark__lte=mark,
            maximum_mark__gte=mark,
        ).first()

    # ---------------------------------------------------------
    # BUILD PRINTABLE ASSESSMENT DATA
    # ---------------------------------------------------------

    printable_strands = []

    for strand in strands:

        sub_strands = CurriculumSubStrand.objects.filter(
            strand=strand,
        ).order_by(
            "order",
            "id",
        )

        printable_sub_strands = []

        for sub_strand in sub_strands:

            rows = []

            for student in students:

                assessment = (
                    CBCSubStrandAssessment.objects.filter(
                        student=student,
                        teacher_assessment_assignment=assignment,
                        sub_strand=sub_strand,
                        academic_year=academic_year,
                        term=term,
                        assessment_component=assessment_component,
                    ).first()
                )

                mark = (
                    assessment.mark
                    if assessment
                    else None
                )

                performance_level = (
                    get_performance_level(mark)
                    if mark is not None
                    else None
                )

                rows.append(
                    {
                        "student": student,
                        "assessment": assessment,
                        "mark": mark,
                        "performance_level": performance_level,
                        "points": (
                            performance_level.points
                            if performance_level
                            else None
                        ),
                        "comment": (
                            assessment.teacher_comment
                            if assessment
                            else ""
                        ),
                    }
                )

            printable_sub_strands.append(
                {
                    "sub_strand": sub_strand,
                    "rows": rows,
                }
            )

        printable_strands.append(
            {
                "strand": strand,
                "sub_strands": printable_sub_strands,
            }
        )

    # ---------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------

    return render(
        request,
        "students/cbc/assessment_book_print.html",
        {
            "assignment": assignment,
            "curriculum": curriculum,
            "school": school,
            "school_class": school_class,
            "learning_area": assignment.learning_area,
            "academic_year": academic_year,
            "term": term,
            "assessment_component": assessment_component,
            "students": students,
            "strands": printable_strands,
            "performance_levels": performance_levels,
        },
    )