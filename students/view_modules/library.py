from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.lib import colors
from django.db.models import Count
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.pdfgen import canvas

from students.models import *

from students.decorators import (
    admin_or_bursar,
    in_group,
)

from students.utils import (
    draw_school_header,
    draw_school_footer,
    get_user_school,
)

@login_required
@in_group(
    "Administrators",
    "Librarian",
    "Head Teacher",
)
def library_list(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    books = Book.objects.filter(
        school=school
    ).order_by("title")

    return render(
        request,
        "library/library_list.html",
        {
            "books": books,
        },
    )
@login_required
@in_group(
    "Administrators",
    "Librarian",
    "Head Teacher",
)
def add_book(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    if request.method == "POST":

        copies = int(request.POST["copies"])

        Book.objects.create(

            school=school,

            title=request.POST["title"],

            author=request.POST["author"],

            isbn=request.POST["isbn"],

            category=request.POST["category"],

            publisher=request.POST["publisher"],

            publication_year=request.POST["publication_year"] or None,

            copies=copies,

            available_copies=copies,

            shelf=request.POST["shelf"],
        )

        messages.success(
            request,
            "Book added successfully."
        )

        return redirect("students:library_list")

    return render(
        request,
        "library/add_book.html",
    )
@login_required
@in_group("Administrators", "Librarian", "Head Teacher")
def edit_book(request, id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    book = get_object_or_404(
        Book,
        id=id,
        school=school,
    )

    if request.method == "POST":

        book.title = request.POST["title"]
        book.author = request.POST["author"]
        book.isbn = request.POST["isbn"]
        book.category = request.POST["category"]
        book.publisher = request.POST["publisher"]
        book.publication_year = (
            request.POST["publication_year"] or None
        )

        copies = int(request.POST["copies"])

        difference = copies - book.copies

        book.copies = copies
        book.available_copies += difference

        book.shelf = request.POST["shelf"]

        book.save()

        messages.success(
            request,
            "Book updated successfully."
        )

        return redirect("students:library_list")

    return render(
        request,
        "library/edit_book.html",
        {
            "book": book,
        },
    )

@login_required
@in_group("Administrators", "Librarian")
def delete_book(request, id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    book = get_object_or_404(
        Book,
        id=id,
        school=school,
    )

    if request.method == "POST":

        book.delete()

        messages.success(
            request,
            "Book deleted successfully."
        )

        return redirect("students:library_list")

    return render(
        request,
        "library/delete_book.html",
        {
            "book": book,
        },
    )

@login_required
@admin_or_bursar
def borrow_book(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    students = Student.objects.filter(
        school=school
    ).order_by(
        "admission_number"
    )

    books = Book.objects.filter(
        school=school,
        copies__gt=0,
    ).order_by(
        "title"
    )

    if request.method == "POST":

        student = get_object_or_404(
            Student,
            id=request.POST["student"],
            school=school,
        )

        book = get_object_or_404(
            Book,
            id=request.POST["book"],
            school=school,
        )

        if book.copies <= 0:

            messages.error(
                request,
                "This book is out of stock."
            )

            return redirect(
                "students:borrow_book"
            )

        BorrowBook.objects.create(
            school=school,
            student=student,
            book=book,
            borrow_date=request.POST["borrow_date"],
            due_date=request.POST["due_date"],
            issued_by=request.user,
        )

        book.copies -= 1
        book.save(
            update_fields=["copies"]
        )

        messages.success(
            request,
            "Book borrowed successfully."
        )

        return redirect(
            "students:borrow_list"
        )

    return render(
        request,
        "students/borrow_book.html",
        {
            "students": students,
            "books": books,
            "today": date.today(),
        },
    )
@login_required
@admin_or_bursar
def borrow_list(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    borrowed_books = (
        BorrowBook.objects
        .filter(
            school=school
        )
        .select_related(
            "student",
            "book",
        )
        .order_by(
            "-borrow_date"
        )
    )

    return render(
        request,
        "students/borrow_list.html",
        {
            "borrowed_books": borrowed_books,
        },
    )
@login_required
@admin_or_bursar
def return_book(request, id):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    borrow = get_object_or_404(
        BorrowBook,
        id=id,
        school=school,
    )

    if borrow.status == "Returned":

        messages.warning(
            request,
            "This book has already been returned."
        )

        return redirect(
            "students:borrow_list"
        )

    borrow.status = "Returned"
    borrow.return_date = date.today()

    borrow.save(
        update_fields=[
            "status",
            "return_date",
        ]
    )

    book = borrow.book

    book.copies += 1

    book.save(
        update_fields=["copies"]
    )

    messages.success(
        request,
        "Book returned successfully."
    )

    return redirect(
        "students:borrow_list"
    )
from datetime import date
from django.db.models import Sum

@login_required
@admin_or_bursar
def library_dashboard(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    total_books = Book.objects.filter(
        school=school
    ).count()

    borrowed_books = BorrowBook.objects.filter(
        school=school,
        status="Borrowed",
    ).count()

    available_books = Book.objects.filter(
        school=school
    ).aggregate(
        total=Sum("available_copies")
    )["total"] or 0

    overdue_books = BorrowBook.objects.filter(
        school=school,
        status="Borrowed",
        due_date__lt=date.today(),
    ).count()

    active_borrowers = BorrowBook.objects.filter(
        school=school,
        status="Borrowed",
    ).values(
        "student"
    ).distinct().count()

    recent_borrowings = BorrowBook.objects.filter(
        school=school
    ).select_related(
        "student",
        "book"
    ).order_by(
        "-borrow_date"
    )[:10]

    context = {
        "total_books": total_books,
        "borrowed_books": borrowed_books,
        "available_books": available_books,
        "overdue_books": overdue_books,
        "active_borrowers": active_borrowers,
        "recent_borrowings": recent_borrowings,
    }

    return render(
        request,
        "students/library_dashboard.html",
        context,
    )
@login_required
@admin_or_bursar
def library_reports(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    borrowed_books = BorrowBook.objects.filter(
        school=school,
        status="Borrowed",
    ).select_related(
        "student",
        "book",
    ).order_by(
        "-borrow_date"
    )

    returned_books = BorrowBook.objects.filter(
        school=school,
        status="Returned",
    ).select_related(
        "student",
        "book",
    ).order_by(
        "-return_date"
    )

    overdue_books = BorrowBook.objects.filter(
        school=school,
        status="Borrowed",
        due_date__lt=date.today(),
    ).select_related(
        "student",
        "book",
    ).order_by(
        "due_date"
    )

    context = {
        "borrowed_books": borrowed_books,
        "returned_books": returned_books,
        "overdue_books": overdue_books,
    }

    return render(
        request,
        "students/library_reports.html",
        context,
    )
@login_required
@admin_or_bursar
def print_library_report(request):

    school = get_user_school(request.user)

    if not school:
        messages.error(
            request,
            "Your account is not associated with a school."
        )
        return redirect("home")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="library_report.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            f"<b>{school.name}</b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "<b>Library Report</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    borrowed = BorrowBook.objects.filter(
        school=school
    ).select_related(
        "student",
        "book",
    ).order_by(
        "-borrow_date"
    )

    data = [
        [
            "Student",
            "Book",
            "Borrow Date",
            "Due Date",
            "Status",
        ]
    ]

    for item in borrowed:

        data.append([
            str(item.student),
            item.book.title,
            str(item.borrow_date),
            str(item.due_date),
            item.status,
        ])

    table = Table(data)

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.darkblue,
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            ),

            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.beige,
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
        ])
    )

    elements.append(table)

    doc.build(elements)

    return response