from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

from students.utils import get_user_school
from django.shortcuts import render, redirect, get_object_or_404
from students.models import(Student, 
                            FeePayment, 
                            Mark, 
                            Attendance,
                            FeeStructure,
                            Homework, 
                            Subject, 
                            SchoolClass, 
                            Teacher,
                            HomeworkSubmission,
                            CBCSubjectAssessment,
                            CBCUpperSecondaryAssessment,
                            CBCPerformanceLevel,
                            CBCSubStrandAssessment,
                            CBCStrandSummativeAssessment,
                            CurriculumLearningArea,
                            CurriculumStrand,
                            SchoolClassCurriculum,
                                                
)


from django.http import HttpResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from ..models import Homework, Subject, SchoolClass, Teacher

CBCPerformanceLevel,



@login_required
def parent_dashboard(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    ).order_by(
        "first_name",
        "last_name",
    )

    if request.method == "GET":

        child_id = request.GET.get("child")

        if child_id:
            request.session["selected_child"] = child_id

    selected_child = None

    if "selected_child" in request.session:

        selected_child = children.filter(
            id=request.session["selected_child"]
        ).first()

    if selected_child is None and children.exists():

        selected_child = children.first()

        request.session["selected_child"] = selected_child.id

    return render(
        request,
        "parents/dashboard.html",
        {
            "children": children,
            "selected_child": selected_child,
        },
    )
@login_required
def parent_students(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    ).order_by(
        "school_class",
        "first_name",
    )

    return render(
        request,
        "parents/parent_students.html",
        {
            "children": children,
        },
    )


@login_required
def parent_student_profile(request, student_id):

    school = request.user.school_user.school

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        parent_user=request.user,
    )

    marks = Mark.objects.filter(
        student=student,
        student__school=school,
    )

    fee_payments = FeePayment.objects.filter(
        student=student,
        student__school=school,
    )

    context = {
        "student": student,
        "marks": marks,
        "fee_payments": fee_payments,
    }

    return render(
        request,
        "parents/student_profile.html",
        context,
    )

@login_required
def parent_attendance(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    )

    attendance = Attendance.objects.filter(
        school=school,
        student__in=children,
    ).order_by("-date")

    return render(
        request,
        "parents/attendance.html",
        {
            "attendance": attendance,
        },
    )

@login_required
def parent_results(request, student_id):

    # =========================================================
    # SCHOOL / PARENT SECURITY
    # =========================================================

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
        school=school,
    )

    # =========================================================
    # CURRENT SCHOOL ACADEMIC PERIOD
    # =========================================================

    academic_year = str(school.academic_year)

    selected_term = str(school.current_term)

    # Handle installations where current_term may be stored
    # as "Term 1", "Term 2", or "Term 3".
    if selected_term.lower().startswith("term "):
        selected_term = selected_term.split()[-1]

    elif selected_term.upper().startswith("T"):
        selected_term = selected_term[1:]

    # =========================================================
    # LEGACY EXAMINATION RESULTS
    #
    # Keep the existing Mark workflow untouched.
    # =========================================================

    marks = (
        Mark.objects
        .filter(
            student=student,
            student__school=school,
        )
        .select_related(
            "subject",
            "exam",
        )
        .order_by(
            "exam__name",
            "subject__name",
        )
    )

    total = sum(
        mark.marks
        for mark in marks
    )

    count = marks.count()

    average = (
        round(total / count, 2)
        if count
        else 0
    )

    # =========================================================
    # FIND THE STUDENT'S CBC CURRICULUM FOR THIS YEAR
    # =========================================================

    school_class_curriculum = None

    if student.school_class_id:

        school_class_curriculum = (
            student.school_class.curriculum_assignments
            .filter(
                academic_year=academic_year,
            )
            .select_related(
                "curriculum_grade",
                "pathway",
            )
            .first()
        )

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
        if school_class_curriculum
        else None
    )

    grade_code = ""

    if curriculum_grade:

        grade_code = (
            getattr(curriculum_grade, "grade", None)
            or getattr(curriculum_grade, "display_name", "")
            or ""
        )

        grade_code = (
            str(grade_code)
            .upper()
            .replace(" ", "")
        )

    # =========================================================
    # PP1 – GRADE 9 CBC SUBJECT RESULTS
    #
    # Learner-facing values are ONLY:
    # EE / ME / AE / BE
    #
    # Internal numerical scores are never displayed.
    # =========================================================

    cbc_subject_rows = []

    lower_assessments = (
        CBCSubjectAssessment.objects
        .filter(
            student=student,
            academic_year=academic_year,
            term=selected_term,
        )
        .select_related(
            "learning_area",
            "submission",
        )
        .order_by(
            "learning_area__name",
            "assessment_component",
        )
    )

    lower_by_learning_area = {}

    for assessment in lower_assessments:

        learning_area_id = assessment.learning_area_id

        if learning_area_id not in lower_by_learning_area:

            lower_by_learning_area[learning_area_id] = {
                "learning_area": assessment.learning_area,
                "CAT1": None,
                "MID": None,
                "END": None,
            }

        lower_by_learning_area[
            learning_area_id
        ][assessment.assessment_component] = assessment

    performance_labels = {
        1: "BE",
        2: "AE",
        3: "ME",
        4: "EE",
    }

    for row in lower_by_learning_area.values():

        cat1 = row["CAT1"]
        mid = row["MID"]
        end = row["END"]

        row["cat1_level"] = (
            performance_labels.get(cat1.performance_level)
            if cat1 and cat1.performance_level
            else None
        )

        row["mid_level"] = (
            performance_labels.get(mid.performance_level)
            if mid and mid.performance_level
            else None
        )

        row["end_level"] = (
            performance_labels.get(end.performance_level)
            if end and end.performance_level
            else None
        )

        cbc_subject_rows.append(row)

    # =========================================================
    # GRADE 10 – 12 CBC RESULTS
    #
    # Uses:
    #   raw_score
    #   marks_out_of
    #   percentage_score
    #   calculated average
    #   CBC performance level
    #   points
    # =========================================================

    cbc_upper_rows = []

    if grade_code in {"GRADE10", "GRADE11", "GRADE12"}:

        upper_assessments = (
            CBCUpperSecondaryAssessment.objects
            .filter(
                student=student,
                academic_year=academic_year,
                term=selected_term,
            )
            .select_related(
                "learning_area",
                "performance_level",
                "submission",
            )
            .order_by(
                "learning_area__name",
                "assessment_component",
            )
        )

        upper_by_learning_area = {}

        for assessment in upper_assessments:

            learning_area_id = assessment.learning_area_id

            if learning_area_id not in upper_by_learning_area:

                upper_by_learning_area[learning_area_id] = {
                    "learning_area": assessment.learning_area,
                    "CAT1": None,
                    "MID": None,
                    "END": None,
                }

            upper_by_learning_area[
                learning_area_id
            ][assessment.assessment_component] = assessment

        for row in upper_by_learning_area.values():

            cat1 = row["CAT1"]
            mid = row["MID"]
            end = row["END"]

            scores = []

            for assessment in (cat1, mid, end):

                if (
                    assessment
                    and assessment.percentage_score is not None
                ):
                    scores.append(
                        Decimal(
                            str(
                                assessment.percentage_score
                            )
                        )
                    )

            row_average = None

            if scores:

                row_average = (
                    sum(scores) / len(scores)
                ).quantize(
                    Decimal("0.01")
                )

            performance_level = None
            points = None

            # Use the same rule as the existing
            # Grade 10–12 examination workflow.
            if (
                cat1
                and mid
                and end
                and row_average is not None
                and curriculum_grade
            ):

                performance_level = (
                    CBCPerformanceLevel.objects
                    .filter(
                        curriculum_grade=curriculum_grade,
                        minimum_mark__lte=row_average,
                        maximum_mark__gte=row_average,
                    )
                    .order_by("order")
                    .first()
                )

                if performance_level:

                    points = getattr(
                        performance_level,
                        "points",
                        None,
                    )

            row["average"] = row_average
            row["performance_level"] = performance_level
            row["points"] = points

            cbc_upper_rows.append(row)

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        # Student
        "student": student,

        # Current CBC period
        "academic_year": academic_year,
        "selected_term": selected_term,

        # Curriculum
        "school_class_curriculum": school_class_curriculum,
        "curriculum_grade": curriculum_grade,
        "grade_code": grade_code,

        # Legacy results
        "marks": marks,
        "total": total,
        "average": average,

        # CBC PP1–Grade 9
        "cbc_subject_rows": cbc_subject_rows,

        # CBC Grade 10–12
        "cbc_upper_rows": cbc_upper_rows,
    }

    return render(
        request,
        "parents/results.html",
        context,
    )
@login_required
def parent_fee_statement(request, student_id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    student = get_object_or_404(
        Student,
        id=student_id,
        parent_user=request.user,
        school=school,
    )

    fee_structure = FeeStructure.objects.filter(
        school_class=student.school_class,
        school_class__school=school,
    ).first()

    payments = FeePayment.objects.filter(
        student=student,
        student__school=school,
    ).order_by("-payment_date")

    total_paid = sum(
        payment.amount_paid
        for payment in payments
    )

    total_fee = (
        fee_structure.total_fee
        if fee_structure
        else 0
    )

    balance = total_fee - total_paid

    context = {
        "student": student,
        "fee_structure": fee_structure,
        "payments": payments,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "balance": balance,
    }

    return render(
        request,
        "parents/fee_statement.html",
        context,
    )
@login_required
def parent_assessment_book(request, student_id):
    """
    Parent-facing FINAL CBC Assessment Book.

    Security:
        - Student must belong to the parent's school.
        - Student must be linked to the logged-in parent.

    This view is completely separate from the teacher CBC
    assessment-book views.

    PP1 - Grade 9:
        - Uses the student's exact CBC curriculum.
        - Displays all applicable learning areas.
        - Displays strands and sub-strands.
        - Uses END TERM as the final assessment component.
        - Displays only EE / ME / AE / BE.
        - Displays strand summative.
        - Displays teacher comments.

    Grade 10 - 12:
        - Uses exact Grade + Pathway.
        - Displays all applicable learning areas.
        - Displays CAT 1 / MID / END.
        - Displays percentage, performance level and points.
        - Read-only.
    """

    # =========================================================
    # 1. SCHOOL / PARENT SECURITY
    # =========================================================

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        parent_user=request.user,
    )

    # =========================================================
    # 2. CURRENT SCHOOL ACADEMIC PERIOD
    # =========================================================

    academic_year = str(school.academic_year)

    selected_term = str(school.current_term)

    if selected_term.lower().startswith("term "):
        selected_term = selected_term.split()[-1]

    elif selected_term.upper().startswith("T"):
        selected_term = selected_term[1:]

    if selected_term not in {"1", "2", "3"}:
        selected_term = "1"

    # =========================================================
    # 3. STUDENT CLASS / CURRICULUM
    # =========================================================

    school_class_curriculum = None

    if student.school_class_id:

        school_class_curriculum = (
            SchoolClassCurriculum.objects
            .filter(
                school_class_id=student.school_class_id,
                academic_year=academic_year,
            )
            .select_related(
                "school_class",
                "school_class__school",
                "curriculum_version",
                "curriculum_grade",
                "pathway",
            )
            .first()
        )

    if not school_class_curriculum:

        return render(
            request,
            "parents/assessment_book.html",
            {
                "student": student,
                "school": school,
                "academic_year": academic_year,
                "selected_term": selected_term,
                "school_class_curriculum": None,
                "curriculum_grade": None,
                "pathway": None,
                "is_upper_secondary": False,
                "learning_area_sections": [],
                "upper_learning_area_rows": [],
                "message": (
                    "No CBC curriculum is configured for "
                    f"{student.first_name} {student.last_name} "
                    f"for academic year {academic_year}."
                ),
            },
        )

    curriculum_grade = (
        school_class_curriculum.curriculum_grade
    )

    pathway = (
        school_class_curriculum.pathway
    )

    school_class = (
        school_class_curriculum.school_class
    )

    grade_code = str(
        curriculum_grade.grade
    ).upper()

    is_upper_secondary = (
        grade_code in {
            "GRADE10",
            "GRADE11",
            "GRADE12",
        }
    )

    # =========================================================
    # 4. PP1 - GRADE 9
    # =========================================================

    learning_area_sections = []

    if not is_upper_secondary:

        learning_areas = (
            CurriculumLearningArea.objects
            .filter(
                curriculum_grade=curriculum_grade,
                pathway__isnull=True,
                assessment_enabled=True,
            )
            .prefetch_related(
                "strands__sub_strands",
            )
            .order_by(
                "name",
                "id",
            )
        )

        # -----------------------------------------------------
        # FINAL COMPONENT
        #
        # For the parent final book we use END TERM.
        # -----------------------------------------------------

        final_component = "END"

        assessments = (
            CBCSubStrandAssessment.objects
            .filter(
                student=student,
                academic_year=academic_year,
                term=selected_term,
                assessment_component=final_component,
                submission__school_class_curriculum=(
                    school_class_curriculum
                ),
                submission__learning_area__curriculum_grade=(
                    curriculum_grade
                ),
                submission__status="APPROVED",
            )
            .select_related(
                "sub_strand",
                "sub_strand__strand",
                "submission",
            )
        )

        assessment_map = {}

        for assessment in assessments:

            assessment_map[
                assessment.sub_strand_id
            ] = assessment

        # -----------------------------------------------------
        # STRAND SUMMATIVES
        # -----------------------------------------------------

        summatives = (
            CBCStrandSummativeAssessment.objects
            .filter(
                student=student,
                academic_year=academic_year,
                term=selected_term,
                assessment_component=final_component,
                strand__learning_area__curriculum_grade=(
                    curriculum_grade
                ),
                submission__school_class_curriculum=(
                    school_class_curriculum
                ),
                submission__status="APPROVED",
            )
            .select_related(
                "strand",
                "submission",
            )
        )

        summative_map = {}

        for summative in summatives:

            summative_map[
                summative.strand_id
            ] = summative

        # -----------------------------------------------------
        # PERFORMANCE LEVEL DISPLAY
        # -----------------------------------------------------

        performance_labels = {
            1: "BE",
            2: "AE",
            3: "ME",
            4: "EE",
        }

        # -----------------------------------------------------
        # BUILD COMPLETE LEARNING AREA BOOK
        # -----------------------------------------------------

        for learning_area in learning_areas:

            strand_rows = []

            strands = (
                learning_area.strands
                .all()
                .order_by(
                    "order",
                    "id",
                )
            )

            for strand in strands:

                sub_strand_rows = []

                sub_strands = (
                    strand.sub_strands
                    .all()
                    .order_by(
                        "order",
                        "id",
                    )
                )

                for sub_strand in sub_strands:

                    assessment = (
                        assessment_map.get(
                            sub_strand.id
                        )
                    )

                    qualitative_level = None
                    comment = ""

                    if assessment:

                        qualitative_level = (
                            performance_labels.get(
                                assessment.performance_level
                            )
                        )

                        comment = (
                            assessment.teacher_comment
                            or ""
                        )

                    sub_strand_rows.append(
                        {
                            "sub_strand": sub_strand,
                            "qualitative_level": (
                                qualitative_level
                            ),
                            "comment": comment,
                        }
                    )

                summative = (
                    summative_map.get(
                        strand.id
                    )
                )

                summative_label = None

                if summative:

                    summative_label = (
                        performance_labels.get(
                            summative.performance_level
                        )
                    )

                strand_rows.append(
                    {
                        "strand": strand,
                        "sub_strands": sub_strand_rows,
                        "summative_label": (
                            summative_label
                        ),
                        "summative_comment": (
                            summative.teacher_comment
                            if summative
                            else ""
                        ),
                    }
                )

            learning_area_sections.append(
                {
                    "learning_area": learning_area,
                    "strands": strand_rows,
                }
            )

    # =========================================================
    # 5. GRADE 10 - 12
    # =========================================================

    upper_learning_area_rows = []

    if is_upper_secondary:

        learning_areas = (
            CurriculumLearningArea.objects
            .filter(
                curriculum_grade=curriculum_grade,
                assessment_enabled=True,
                pathway=pathway,
            )
            .order_by(
                "name",
                "id",
            )
        )

        upper_assessments = (
            CBCUpperSecondaryAssessment.objects
            .filter(
                student=student,
                academic_year=academic_year,
                term=selected_term,
                learning_area__in=learning_areas,
                submission__school_class_curriculum=(
                    school_class_curriculum
                ),
                submission__status="APPROVED",
            )
            .select_related(
                "learning_area",
                "performance_level",
                "submission",
            )
            .order_by(
                "learning_area__name",
                "assessment_component",
            )
        )

        assessment_map = {}

        for assessment in upper_assessments:

            assessment_map[
                (
                    assessment.learning_area_id,
                    assessment.assessment_component,
                )
            ] = assessment

        total_percentages = []
        total_points_list = []

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

                percentage = None
                performance = None
                points = None
                teacher_comment = ""

                if assessment:

                    if (
                        assessment.percentage_score
                        is not None
                    ):
                        percentage = Decimal(
                            str(
                                assessment.percentage_score
                            )
                        )

                    performance = (
                        assessment.performance_level
                    )

                    points = (
                        assessment.points
                    )

                    teacher_comment = (
                        assessment.teacher_comment
                        or ""
                    )

                components[component] = {
                    "assessment": assessment,
                    "percentage": percentage,
                    "performance": performance,
                    "points": points,
                    "teacher_comment": (
                        teacher_comment
                    ),
                }

            # -------------------------------------------------
            # AVERAGE PERCENTAGE
            # -------------------------------------------------

            percentage_values = [
                components[component]["percentage"]
                for component in (
                    "CAT1",
                    "MID",
                    "END",
                )
                if components[component]["percentage"]
                is not None
            ]

            average_percentage = None

            if percentage_values:

                average_percentage = (
                    sum(percentage_values)
                    / len(percentage_values)
                ).quantize(
                    Decimal("0.01")
                )

                total_percentages.append(
                    average_percentage
                )

            # -------------------------------------------------
            # AVERAGE POINTS
            # -------------------------------------------------

            point_values = [
                Decimal(
                    str(
                        components[component]["points"]
                    )
                )
                for component in (
                    "CAT1",
                    "MID",
                    "END",
                )
                if components[component]["points"]
                is not None
            ]

            average_points = None

            if point_values:

                average_points = (
                    sum(point_values)
                    / len(point_values)
                ).quantize(
                    Decimal("0.01")
                )

                total_points_list.append(
                    average_points
                )

            # -------------------------------------------------
            # FINAL PERFORMANCE LEVEL
            #
            # Use the stored performance level from the
            # completed components. If all three are present,
            # calculate from the average, matching the existing
            # Grade 10-12 workflow.
            # -------------------------------------------------

            final_performance = None

            if (
                len(percentage_values) == 3
                and average_percentage is not None
            ):

                final_performance = (
                    CBCPerformanceLevel.objects
                    .filter(
                        curriculum_grade=curriculum_grade,
                        minimum_mark__lte=(
                            average_percentage
                        ),
                        maximum_mark__gte=(
                            average_percentage
                        ),
                    )
                    .order_by("order")
                    .first()
                )

            upper_learning_area_rows.append(
                {
                    "learning_area": learning_area,
                    "components": components,
                    "average_percentage": (
                        average_percentage
                    ),
                    "average_points": (
                        average_points
                    ),
                    "final_performance": (
                        final_performance
                    ),
                }
            )

        # -----------------------------------------------------
        # OVERALL FINAL VALUES
        # -----------------------------------------------------

        total_marks = None
        total_points = None

        if total_percentages:

            total_marks = (
                sum(total_percentages)
                / len(total_percentages)
            ).quantize(
                Decimal("0.01")
            )

        if total_points_list:

            total_points = (
                sum(total_points_list)
                / len(total_points_list)
            ).quantize(
                Decimal("0.01")
            )

    else:

        total_marks = None
        total_points = None

    # =========================================================
    # 6. CONTEXT
    # =========================================================

    context = {
        "school": school,
        "student": student,
        "school_class": school_class,
        "school_class_curriculum": (
            school_class_curriculum
        ),
        "curriculum_grade": curriculum_grade,
        "curriculum_version": (
            school_class_curriculum.curriculum_version
        ),
        "pathway": pathway,
        "academic_year": academic_year,
        "selected_term": selected_term,
        "grade_code": grade_code,
        "is_upper_secondary": is_upper_secondary,

        # PP1 - Grade 9
        "learning_area_sections": (
            learning_area_sections
        ),

        # Grade 10 - 12
        "upper_learning_area_rows": (
            upper_learning_area_rows
        ),
        "total_marks": total_marks,
        "total_points": total_points,

        "message": None,
    }

    return render(
        request,
        "parents/assessment_book.html",
        context,
    )


@login_required
def print_fee_statement(request, student_id):

    school = request.user.school_user.school

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        parent_user=request.user,
    )

    fee_structure = (
        FeeStructure.objects
        .filter(
            school=school,
            school_class=student.school_class,
        )
        .first()
    )

    payments = (
        FeePayment.objects
        .filter(
            school=school,
            student=student,
        )
        .order_by("-payment_date")
    )

    total_paid = sum(
        payment.amount_paid
        for payment in payments
    )

    total_fee = (
        fee_structure.total_fee
        if fee_structure
        else 0
    )

    balance = total_fee - total_paid

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="Fee_Statement_'
        f'{student.admission_number}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>FEE STATEMENT</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            f"Student: {student.first_name} "
            f"{student.last_name}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Admission No: {student.admission_number}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Class: {student.school_class}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "<br/>",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Fees: Ksh {total_fee}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Paid: Ksh {total_paid}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Balance: Ksh {balance}",
            styles["Normal"],
        )
    )

    doc.build(story)

    return response
@login_required
def parent_fee_balance(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    children = Student.objects.filter(
        parent_user=request.user,
        school=school,
    ).select_related(
        "school_class",
    )

    fee_data = []

    for child in children:

        fee_structure = FeeStructure.objects.filter(
            school_class=child.school_class,
            school_class__school=school,
        ).first()

        total_fee = (
            fee_structure.total_fee
            if fee_structure
            else 0
        )

        payments = FeePayment.objects.filter(
            student=child,
            student__school=school,
        )

        total_paid = sum(
            payment.amount_paid
            for payment in payments
        )

        balance = total_fee - total_paid

        fee_data.append({
            "student": child,
            "total_fee": total_fee,
            "total_paid": total_paid,
            "balance": balance,
        })

    return render(
        request,
        "parents/fee_balance.html",
        {
            "fee_data": fee_data,
        },
    )


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def parent_attendance(request):

    school = request.user.school_user.school

    children = Student.objects.filter(
        school=school,
        parent_user=request.user,
    )

    if not children.exists():
        return render(
            request,
            "parents/attendance.html",
            {
                "student": None,
                "attendance": [],
            },
        )

    child_id = request.session.get("selected_child")

    student = children.filter(
        id=child_id
    ).first()

    if student is None:
        student = children.first()
        request.session["selected_child"] = student.id

    attendance = Attendance.objects.filter(
        school=school,
        student=student,
    ).order_by("-date")

    return render(
        request,
        "parents/attendance.html",
        {
            "student": student,
            "attendance": attendance,
        },
    )
@login_required
def homework_list(request):

    user = request.user
    school = get_user_school(user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )

        return redirect("students:home")

    # Administrator
    if (
        user.is_superuser
        or user.groups.filter(
            name="Administrators"
        ).exists()
    ):

        homework = Homework.objects.filter(
            school=school
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by(
            "-date_given"
        )

    # Teacher
    elif user.groups.filter(
        name="Teachers"
    ).exists():

        teacher = Teacher.objects.filter(
            user=user,
            school=school,
        ).first()

        if teacher:

            homework = Homework.objects.filter(
                school=school,
                teacher=teacher,
            ).select_related(
                "subject",
                "school_class",
                "teacher",
            ).order_by(
                "-date_given"
            )

        else:
            homework = Homework.objects.none()

    # Parent
    elif user.groups.filter(
        name="Parents"
    ).exists():

        children = Student.objects.filter(
            parent_user=user,
            school=school,
        )

        classes = children.values_list(
            "school_class_id",
            flat=True,
        )

        homework = Homework.objects.filter(
            school=school,
            school_class_id__in=classes,
        ).select_related(
            "subject",
            "school_class",
            "teacher",
        ).order_by(
            "-date_given"
        )

    # Student
    else:

        student = Student.objects.filter(
            user=user,
            school=school,
        ).first()

        if student:

            homework = Homework.objects.filter(
                school=school,
                school_class=student.school_class,
            ).select_related(
                "subject",
                "school_class",
                "teacher",
            ).order_by(
                "-date_given"
            )

        else:
            homework = Homework.objects.none()

    return render(
        request,
        "homework/homework_list.html",
        {
            "homework": homework,
        },
    )
@login_required
def add_homework(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    subjects = Subject.objects.filter(
        school=school
    ).select_related(
        "school_class",
        "teacher",
    )

    classes = SchoolClass.objects.filter(
        school=school
    )

    teachers = Teacher.objects.filter(
        school=school
    )

    if request.method == "POST":

        try:

            subject = Subject.objects.get(
                id=request.POST["subject"],
                school=school,
            )

            school_class = SchoolClass.objects.get(
                id=request.POST["school_class"],
                school=school,
            )

            teacher = Teacher.objects.get(
                id=request.POST["teacher"],
                school=school,
            )

        except (
            Subject.DoesNotExist,
            SchoolClass.DoesNotExist,
            Teacher.DoesNotExist,
        ):

            messages.error(
                request,
                "Invalid subject, class, or teacher."
            )

            return render(
                request,
                "homework/add_homework.html",
                {
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        # If the subject is assigned to a specific class,
        # make sure it matches the selected class.
        if (
            subject.school_class
            and subject.school_class_id != school_class.id
        ):

            messages.error(
                request,
                "The selected subject does not belong to the selected class."
            )

            return render(
                request,
                "homework/add_homework.html",
                {
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        Homework.objects.create(
            school=school,
            subject=subject,
            school_class=school_class,
            teacher=teacher,
            title=request.POST["title"],
            description=request.POST["description"],
            due_date=request.POST["due_date"],
            attachment=request.FILES.get("attachment"),
        )

        messages.success(
            request,
            "Homework added successfully."
        )

        return redirect("students:homework_list")

    return render(
        request,
        "homework/add_homework.html",
        {
            "subjects": subjects,
            "classes": classes,
            "teachers": teachers,
        },
    )

@login_required
def edit_homework(request, pk):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "subject",
            "school_class",
            "teacher",
        ),
        pk=pk,
        school=school,
    )

    subjects = Subject.objects.filter(
        school=school
    )

    classes = SchoolClass.objects.filter(
        school=school
    )

    teachers = Teacher.objects.filter(
        school=school
    )

    if request.method == "POST":

        try:

            subject = Subject.objects.get(
                id=request.POST["subject"],
                school=school,
            )

            school_class = SchoolClass.objects.get(
                id=request.POST["school_class"],
                school=school,
            )

            teacher = Teacher.objects.get(
                id=request.POST["teacher"],
                school=school,
            )

        except (
            Subject.DoesNotExist,
            SchoolClass.DoesNotExist,
            Teacher.DoesNotExist,
        ):

            messages.error(
                request,
                "Invalid subject, class, or teacher."
            )

            return render(
                request,
                "homework/edit_homework.html",
                {
                    "homework": homework,
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        if (
            subject.school_class
            and subject.school_class_id != school_class.id
        ):

            messages.error(
                request,
                "The selected subject does not belong to the selected class."
            )

            return render(
                request,
                "homework/edit_homework.html",
                {
                    "homework": homework,
                    "subjects": subjects,
                    "classes": classes,
                    "teachers": teachers,
                },
            )

        homework.subject = subject
        homework.school_class = school_class
        homework.teacher = teacher
        homework.title = request.POST["title"]
        homework.description = request.POST["description"]
        homework.due_date = request.POST["due_date"]

        if request.FILES.get("attachment"):
            homework.attachment = request.FILES["attachment"]

        homework.save()

        messages.success(
            request,
            "Homework updated successfully."
        )

        return redirect("students:homework_list")

    return render(
        request,
        "homework/edit_homework.html",
        {
            "homework": homework,
            "subjects": subjects,
            "classes": classes,
            "teachers": teachers,
        },
    )

@login_required
def delete_homework(request, pk):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    homework = get_object_or_404(
        Homework,
        pk=pk,
        school=school,
    )

    if request.method == "POST":

        homework.delete()

        messages.success(
            request,
            "Homework deleted successfully."
        )

        return redirect("students:homework_list")

    return render(
        request,
        "homework/delete_homework.html",
        {
            "homework": homework,
        },
    )

@login_required
def parent_homework(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    children = Student.objects.filter(
        parent_user=request.user,
        school=school,
    ).select_related(
        "school_class"
    )

    classes = children.values_list(
        "school_class_id",
        flat=True,
    )

    homework = Homework.objects.filter(
        school=school,
        school_class_id__in=classes,
    ).select_related(
        "subject",
        "school_class",
        "teacher",
    ).order_by(
        "-date_given"
    )

    return render(
        request,
        "parents/homework.html",
        {
            "children": children,
            "homework": homework,
        },
    )

@login_required
def submit_homework(request, homework_id):

    student = Student.objects.filter(
        user=request.user
    ).select_related(
        "school",
        "school_class",
    ).first()

    if not student:
        messages.error(
            request,
            "Student profile not found."
        )
        return redirect("students:home")

    if not student.school:
        messages.error(
            request,
            "Your student account is not associated with a school."
        )
        return redirect("students:home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "school",
            "school_class",
            "subject",
            "teacher",
        ),
        id=homework_id,
        school=student.school,
        school_class=student.school_class,
    )

    submission = HomeworkSubmission.objects.filter(
        homework=homework,
        student=student,
    ).first()

    if request.method == "POST":

        file = request.FILES.get(
            "submission_file"
        )

        if submission:

            if file:
                submission.submission_file = file

            submission.save()

            messages.success(
                request,
                "Homework updated successfully."
            )

        else:

            if not file:
                messages.error(
                    request,
                    "Please select a file to submit."
                )

                return render(
                    request,
                    "students/submit_homework.html",
                    {
                        "homework": homework,
                        "submission": submission,
                    },
                )

            HomeworkSubmission.objects.create(
                homework=homework,
                student=student,
                submission_file=file,
            )

            messages.success(
                request,
                "Homework submitted successfully."
            )

        return redirect(
            "student_homework"
        )

    return render(
        request,
        "students/submit_homework.html",
        {
            "homework": homework,
            "submission": submission,
        },
    )

@login_required
def homework_submissions(request, homework_id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")

    homework = get_object_or_404(
        Homework.objects.select_related(
            "school",
            "teacher",
            "school_class",
            "subject",
        ),
        id=homework_id,
        school=school,
    )

    user = request.user

    # Teachers can only view submissions
    # for their own homework.
    if user.groups.filter(
        name="Teachers"
    ).exists():

        teacher = Teacher.objects.filter(
            user=user,
            school=school,
        ).first()

        if not teacher or homework.teacher_id != teacher.id:
            messages.error(
                request,
                "You are not allowed to view these submissions."
            )
            return redirect("students:homework_list")

    submissions = HomeworkSubmission.objects.filter(
        homework=homework,
        student__school=school,
    ).select_related(
        "student",
        "graded_by",
    ).order_by(
        "-submitted_at"
    )

    return render(
        request,
        "homework/homework_submissions.html",
        {
            "homework": homework,
            "submissions": submissions,
        },
    )

@login_required
def mark_homework(request, submission_id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("students:home")
    
    submission = get_object_or_404(
        HomeworkSubmission.objects.select_related(
            "homework",
            "homework__teacher",
            "homework__school",
            "student",
            "student__school",
        ),
        id=submission_id,
        homework__school=school,
        student__school=school,
    )

    user = request.user

    # Find teacher
    teacher = Teacher.objects.filter(
        user=user,
        school=school,
    ).first()

    # Teacher permission
    if user.groups.filter(
        name="Teachers"
    ).exists():

        if not teacher:
            messages.error(
                request,
                "Teacher profile not found."
            )
            return redirect("students:homework_list")

        if submission.homework.teacher_id != teacher.id:
            messages.error(
                request,
                "You are not allowed to mark this homework."
            )
            return redirect(
                "homework_submissions",
                submission.homework.id,
            )

    # Administrator or authorized teacher
    if request.method == "POST":

        marks_value = request.POST.get(
            "marks"
        )

        teacher_comment = request.POST.get(
            "teacher_comment",
            "",
        )

        if marks_value:
            try:
                marks = float(marks_value)

            except (TypeError, ValueError):

                messages.error(
                    request,
                    "Please enter valid marks."
                )

                return render(
                    request,
                    "homework/mark_homework.html",
                    {
                        "submission": submission,
                    },
                )

            if marks < 0 or marks > 100:

                messages.error(
                    request,
                    "Marks must be between 0 and 100."
                )

                return render(
                    request,
                    "homework/mark_homework.html",
                    {
                        "submission": submission,
                    },
                )

            submission.marks = marks

        else:
            submission.marks = None

        submission.teacher_comment = teacher_comment
        submission.graded_by = teacher
        submission.graded_at = timezone.now()

        submission.save()

        messages.success(
            request,
            "Homework marked successfully."
        )

        return redirect(
            "homework_submissions",
            submission.homework.id,
        )

    return render(
        request,
        "homework/mark_homework.html",
        {
            "submission": submission,
        },
    )