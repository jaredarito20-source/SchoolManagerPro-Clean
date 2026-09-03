from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from students.models import (
    FeeLedgerEntry,
    FeePayment,
    Student,
    FeeStructure,
    StudentAcademicEnrollment,
)



ZERO = Decimal("0.00")


# ============================================================
# BASIC HELPERS
# ============================================================

def get_student_school(student):
    """
    Return the school that owns the student.

    Every finance transaction must belong to the same
    school as the student.
    """

    if not student.school_id:
        raise ValueError(
            f"Student {student.id} is not linked to a school."
        )

    return student.school


def get_current_period(school):
    """
    Return the school's configured academic year and term.
    """

    academic_year = (
        school.academic_year or ""
    ).strip()

    term = (
        school.current_term or ""
    ).strip()

    if not academic_year:
        raise ValueError(
            "The school's academic year is not configured."
        )

    if not term:
        raise ValueError(
            "The school's current term is not configured."
        )

    return academic_year, term


def _decimal(value):
    """
    Safely convert a value to Decimal.
    """

    if value is None:
        return ZERO

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(
            f"Invalid monetary value: {value}"
        )


def _validate_amounts(debit, credit):
    """
    Validate ledger debit/credit amounts.

    A ledger entry must contain either:
        debit
    OR:
        credit

    Never both.
    """

    debit = _decimal(debit)
    credit = _decimal(credit)

    if debit < ZERO:
        raise ValueError(
            "Debit cannot be negative."
        )

    if credit < ZERO:
        raise ValueError(
            "Credit cannot be negative."
        )

    if debit > ZERO and credit > ZERO:
        raise ValueError(
            "A ledger entry cannot contain both debit and credit."
        )

    if debit == ZERO and credit == ZERO:
        raise ValueError(
            "A ledger entry must contain a debit or credit amount."
        )

    return debit, credit


# ============================================================
# LEDGER REBUILD
# ============================================================

@transaction.atomic
def rebuild_student_ledger(student):
    """
    Recalculate the student's continuous ledger balance.

    Accounting rules:

        debit  = increases amount owed
        credit = reduces amount owed

    Positive balance:
        Student owes the school.

    Zero:
        Account is settled.

    Negative balance:
        Student has a credit / overpayment.

    Terms within the same academic year are continuous:

        Term 1 closing
            ↓
        Term 2 opening
            ↓
        Term 2 closing
            ↓
        Term 3 opening
            ↓
        Term 3 closing

    No CARRY_FORWARD transaction is required for normal
    Term 1 → Term 2 → Term 3 movement.

    An academic year is a separate accounting period.
    """

    if not student.school_id:
        return ZERO

    entries = (
        FeeLedgerEntry.objects
        .select_for_update()
        .filter(
            student=student,
            school_id=student.school_id,
        )
        .order_by(
            "academic_year",
            "term",
            "transaction_date",
            "id",
        )
    )

    running_balance = ZERO
    current_academic_year = None

    for entry in entries:

        academic_year = str(
            entry.academic_year
        ).strip()

        # --------------------------------------------------
        # NEW ACADEMIC YEAR
        # --------------------------------------------------
        #
        # Terms within an academic year remain continuous.
        # A new academic year starts a new accounting period.
        #
        if current_academic_year != academic_year:
            running_balance = ZERO
            current_academic_year = academic_year

        debit = (
            entry.debit
            if entry.debit is not None
            else ZERO
        )

        credit = (
            entry.credit
            if entry.credit is not None
            else ZERO
        )

        running_balance += (
            debit - credit
        )

        if entry.balance != running_balance:

            FeeLedgerEntry.objects.filter(
                pk=entry.pk
            ).update(
                balance=running_balance
            )

        entry.balance = running_balance

    return running_balance

# ============================================================
# CREATE LEDGER ENTRY
# ============================================================

@transaction.atomic
def create_ledger_entry(
    *,
    student,
    transaction_type,
    description,
    debit=ZERO,
    credit=ZERO,
    transaction_date=None,
    academic_year=None,
    term=None,
    reference="",
    fee_payment=None,
    recorded_by=None,
):
    """
    Create one authoritative ledger transaction.

    All finance transactions should eventually pass through
    this function.

    Debit:
        increases amount owed.

    Credit:
        decreases amount owed.
    """

    school = get_student_school(student)

    debit, credit = _validate_amounts(
        debit,
        credit,
    )

    if not description:
        raise ValueError(
            "Ledger transaction description is required."
        )

    if transaction_date is None:
        transaction_date = date.today()

    if academic_year is None or term is None:

        current_year, current_term = (
            get_current_period(school)
        )

        if academic_year is None:
            academic_year = current_year

        if term is None:
            term = current_term

    if fee_payment is not None:

        if fee_payment.student_id != student.id:
            raise ValueError(
                "Fee payment does not belong to this student."
            )

        if student.school_id != fee_payment.student.school_id:
            raise ValueError(
                "Fee payment belongs to a different school."
            )

    entry = FeeLedgerEntry.objects.create(
        student=student,
        school=school,
        academic_year=str(academic_year),
        term=str(term),
        transaction_date=transaction_date,
        transaction_type=transaction_type,
        description=description,
        debit=debit,
        credit=credit,
        balance=ZERO,
        reference=reference or "",
        fee_payment=fee_payment,
        recorded_by=recorded_by,
    )

    rebuild_student_ledger(student)

    entry.refresh_from_db()

    return entry


# ============================================================
# FEE CHARGES
# ============================================================

def record_fee_charge(
    *,
    student,
    amount,
    description="Fee Charge",
    transaction_date=None,
    academic_year=None,
    term=None,
    reference="",
    recorded_by=None,
):
    """
    Record a fee charge as a debit.
    """

    amount = _decimal(amount)

    if amount <= ZERO:
        raise ValueError(
            "Fee charge amount must be greater than zero."
        )

    return create_ledger_entry(
        student=student,
        transaction_type="FEE_CHARGE",
        description=description,
        debit=amount,
        credit=ZERO,
        transaction_date=transaction_date,
        academic_year=academic_year,
        term=term,
        reference=reference,
        recorded_by=recorded_by,
    )

# ============================================================
# TERM FEE CHARGES
# ============================================================

@transaction.atomic
def record_term_fee_charge(
    *,
    student,
    fee_structure,
    transaction_date=None,
    recorded_by=None,
):
    """
    Create or synchronize the student's fee charge
    for a specific academic year and term.

    The FeeStructure is the charge definition.

    The student's ledger contains the actual accounting
    transaction.

    One student + one class + one academic year + one term
    must have one FEE_CHARGE entry for this fee structure.

    If the fee structure amount changes, the existing
    FEE_CHARGE is adjusted rather than creating a duplicate.
    """

    if student is None:
        raise ValueError(
            "Student is required."
        )

    if fee_structure is None:
        raise ValueError(
            "Fee structure is required."
        )

    if not student.school_id:
        raise ValueError(
            "Student is not linked to a school."
        )

    if (
        fee_structure.school_class_id
        != student.school_class_id
    ):
        raise ValueError(
            "Fee structure does not belong to the student's class."
        )

    if (
        fee_structure.school_class.school_id
        != student.school_id
    ):
        raise ValueError(
            "Fee structure belongs to a different school."
        )

    amount = _decimal(
        fee_structure.total_fee
    )

    if amount <= ZERO:
        raise ValueError(
            "Fee structure total must be greater than zero."
        )

    academic_year = str(
        fee_structure.academic_year
    ).strip()

    term = str(
        fee_structure.term
    ).strip()

    if not academic_year:
        raise ValueError(
            "Fee structure academic year is required."
        )

    if not term:
        raise ValueError(
            "Fee structure term is required."
        )

    if transaction_date is None:
        transaction_date = date.today()

    reference = (
        f"FEE-{student.id}-"
        f"{academic_year}-T{term}"
    )

    existing = (
        FeeLedgerEntry.objects
        .select_for_update()
        .filter(
            student=student,
            school_id=student.school_id,
            academic_year=academic_year,
            term=term,
            transaction_type="FEE_CHARGE",
            reference=reference,
        )
        .order_by("id")
        .first()
    )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if existing is None:

        return create_ledger_entry(
            student=student,
            transaction_type="FEE_CHARGE",
            description=(
                f"Term {term} Fee Charge"
            ),
            debit=amount,
            credit=ZERO,
            transaction_date=transaction_date,
            academic_year=academic_year,
            term=term,
            reference=reference,
            recorded_by=recorded_by,
        )

    # --------------------------------------------------------
    # SYNCHRONIZE EXISTING CHARGE
    # --------------------------------------------------------

    if existing.credit != ZERO:
        raise ValueError(
            "Invalid FEE_CHARGE ledger entry: "
            "a fee charge cannot contain credit."
        )

    if existing.debit == amount:
        return existing

    existing.debit = amount
    existing.description = (
        f"Term {term} Fee Charge"
    )

    existing.save(
        update_fields=[
            "debit",
            "description",
        ]
    )

    rebuild_student_ledger(student)

    existing.refresh_from_db()

    return existing

@transaction.atomic
def record_term_fee_charges_for_class(
    *,
    school_class,
    academic_year,
    term,
    transaction_date=None,
    recorded_by=None,
):
    """
    Apply the term fee structure to every student
    in a class.

    Returns the number of students charged.
    """

    if school_class is None:
        raise ValueError(
            "School class is required."
        )

    fee_structure = (
        FeeStructure.objects
        .select_related(
            "school_class",
            "school_class__school",
        )
        .filter(
            school_class=school_class,
            academic_year=str(academic_year),
            term=str(term),
        )
        .first()
    )

    if fee_structure is None:
        raise ValueError(
            f"No fee structure exists for "
            f"{school_class.name}, "
            f"{academic_year}, Term {term}."
        )

    students = (
        Student.objects
        .filter(
            school=school_class.school,
            school_class=school_class,
        )
        .order_by(
            "admission_number",
            "id",
        )
    )

    count = 0

    for student in students:

        if not student_is_eligible_for_term(
            student=student,
            academic_year=academic_year,
            term=term,
        ):
            continue

        record_term_fee_charge(
            student=student,
            fee_structure=fee_structure,
            transaction_date=transaction_date,
            recorded_by=recorded_by,
        )

        count += 1

        

    return count


# ============================================================
# PAYMENTS
# ============================================================

@transaction.atomic
def record_payment(
    *,
    student,
    payment,
    academic_year=None,
    term=None,
    recorded_by=None,
):
    """
    Record one FeePayment as one ledger credit.

    Safe to call repeatedly for the same payment.

    One FeePayment must never create multiple PAYMENT
    ledger entries.
    """

    if payment is None:
        raise ValueError(
            "A FeePayment is required."
        )

    if payment.student_id != student.id:
        raise ValueError(
            "Payment does not belong to this student."
        )

    existing = (
        FeeLedgerEntry.objects
        .filter(
            fee_payment=payment,
            transaction_type="PAYMENT",
        )
        .order_by("id")
        .first()
    )

    if existing:
        return existing

    amount = _decimal(
        payment.amount
    )

    if amount <= ZERO:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    return create_ledger_entry(
        student=student,
        transaction_type="PAYMENT",
        description=(
            f"Payment - {payment.payment_method}"
        ),
        debit=ZERO,
        credit=amount,
        transaction_date=payment.payment_date,
        academic_year=(
            academic_year
            if academic_year is not None
            else payment.academic_year
        ),
        term=(
            term
            if term is not None
            else payment.term
        ),
        reference=(
            payment.reference
            or payment.receipt_number
        ),
        fee_payment=payment,
        recorded_by=(
            recorded_by
            or payment.recorded_by
        ),
    )

@transaction.atomic
def void_payment(
    *,
    payment,
    voided_by=None,
    void_reason="",
    transaction_date=None,
):
    """
    Void a FeePayment without deleting its accounting history.

    The original PAYMENT ledger entry remains untouched.
    A REVERSAL entry offsets the original payment.

    A payment can only be voided once.
    """

    if payment is None:
        raise ValueError(
            "A FeePayment is required."
        )

    payment = (
        FeePayment.objects
        .select_for_update()
        .select_related("student")
        .get(pk=payment.pk)
    )

    if payment.is_voided:
        raise ValueError(
            "This payment has already been voided."
        )

    payment_entry = (
        FeeLedgerEntry.objects
        .select_for_update()
        .filter(
            fee_payment=payment,
            transaction_type="PAYMENT",
        )
        .order_by("id")
        .first()
    )

    if payment_entry is None:
        raise ValueError(
            "No PAYMENT ledger entry exists for this payment."
        )

    if transaction_date is None:
        transaction_date = date.today()

    reversal = reverse_ledger_entry(
        entry=payment_entry,
        description=(
            f"Void payment - "
            f"{payment.receipt_number}"
        ),
        transaction_date=transaction_date,
        recorded_by=voided_by,
    )

    payment.is_voided = True
    payment.voided_at = timezone.now()
    payment.voided_by = voided_by
    payment.void_reason = (
        void_reason or ""
    )
    payment.save(
        update_fields=[
            "is_voided",
            "voided_at",
            "voided_by",
            "void_reason",
        ]
    )

    return reversal


# ============================================================
# STUDENT CREDITS
# ============================================================

def record_credit(
    *,
    student,
    amount,
    description="Student Credit",
    transaction_date=None,
    academic_year=None,
    term=None,
    reference="",
    recorded_by=None,
):
    """
    Record a credit belonging to the student.

    Examples:

        Scholarship
        Fee waiver
        Approved credit
        Previous overpayment adjustment

    Credit reduces the amount owed.
    """

    amount = _decimal(amount)

    if amount <= ZERO:
        raise ValueError(
            "Credit amount must be greater than zero."
        )

    return create_ledger_entry(
        student=student,
        transaction_type="CREDIT",
        description=description,
        debit=ZERO,
        credit=amount,
        transaction_date=transaction_date,
        academic_year=academic_year,
        term=term,
        reference=reference,
        recorded_by=recorded_by,
    )


# ============================================================
# ADJUSTMENTS
# ============================================================

def record_adjustment(
    *,
    student,
    amount,
    description="Fee Adjustment",
    transaction_date=None,
    academic_year=None,
    term=None,
    reference="",
    recorded_by=None,
):
    """
    Record a positive fee adjustment as a debit.

    An adjustment increases the amount owed.
    """

    amount = _decimal(amount)

    if amount <= ZERO:
        raise ValueError(
            "Adjustment amount must be greater than zero."
        )

    return create_ledger_entry(
        student=student,
        transaction_type="ADJUSTMENT",
        description=description,
        debit=amount,
        credit=ZERO,
        transaction_date=transaction_date,
        academic_year=academic_year,
        term=term,
        reference=reference,
        recorded_by=recorded_by,
    )


# ============================================================
# OPENING BALANCE
# ============================================================

def record_opening_balance(
    *,
    student,
    amount,
    description="Opening Balance",
    transaction_date=None,
    academic_year=None,
    term=None,
    reference="",
    recorded_by=None,
):
    """
    Record an opening balance for a student.

    Positive amount:
        Student owes the school.

    Negative amount:
        Student has a credit.

    Example:

        amount = 5000
            -> debit 5000

        amount = -2000
            -> credit 2000
    """

    amount = _decimal(amount)

    if amount == ZERO:
        return None

    if amount > ZERO:

        return create_ledger_entry(
            student=student,
            transaction_type="OPENING_BALANCE",
            description=description,
            debit=amount,
            credit=ZERO,
            transaction_date=transaction_date,
            academic_year=academic_year,
            term=term,
            reference=reference,
            recorded_by=recorded_by,
        )

    return create_ledger_entry(
        student=student,
        transaction_type="OPENING_BALANCE",
        description=description,
        debit=ZERO,
        credit=abs(amount),
        transaction_date=transaction_date,
        academic_year=academic_year,
        term=term,
        reference=reference,
        recorded_by=recorded_by,
    )


# ============================================================
# REVERSALS
# ============================================================

@transaction.atomic
def reverse_ledger_entry(
    *,
    entry,
    description=None,
    transaction_date=None,
    recorded_by=None,
):
    """
    Reverse an existing ledger entry.

    The original transaction remains untouched.

    A new REVERSAL entry is created with the opposite
    debit/credit.

    This preserves the accounting audit trail.
    """

    if entry is None:
        raise ValueError(
            "Ledger entry is required."
        )

    entry = (
        FeeLedgerEntry.objects
        .select_for_update()
        .select_related("student")
        .get(pk=entry.pk)
    )

    if entry.transaction_type == "REVERSAL":
        raise ValueError(
            "A reversal cannot itself be reversed."
        )

    reversal_reference = (
        f"REV-{entry.id}"
    )

    existing = (
        FeeLedgerEntry.objects
        .filter(
            transaction_type="REVERSAL",
            reference=reversal_reference,
        )
        .first()
    )

    if existing:
        return existing

    if transaction_date is None:
        transaction_date = date.today()

    if description is None:
        description = (
            f"Reversal - {entry.description}"
        )

    return create_ledger_entry(
        student=entry.student,
        transaction_type="REVERSAL",
        description=description,
        debit=entry.credit,
        credit=entry.debit,
        transaction_date=transaction_date,
        academic_year=entry.academic_year,
        term=entry.term,
        reference=reversal_reference,
        recorded_by=recorded_by,
    )


# ============================================================
# BALANCES
# ============================================================

def get_student_balance(student):
    """
    Return the student's complete current ledger balance.

    Positive:
        Amount owed.

    Zero:
        Settled.

    Negative:
        Student credit.
    """

    if not student.school_id:
        return ZERO

    latest = (
        FeeLedgerEntry.objects
        .filter(
            student=student,
            school_id=student.school_id,
        )
        .order_by(
            "-transaction_date",
            "-id",
        )
        .first()
    )

    if latest:
        return latest.balance

    return ZERO


def get_term_balance(
    *,
    student,
    academic_year,
    term,
):
    """
    Return the student's closing balance at the end of
    the requested term.

    Terms within the same academic year are continuous.

    Therefore:

        Term 1 balance
            = Term 1 transactions

        Term 2 balance
            = Term 1 + Term 2 transactions

        Term 3 balance
            = Term 1 + Term 2 + Term 3 transactions

    Positive:
        Student owes the school.

    Zero:
        Account is settled.

    Negative:
        Student has a credit / overpayment.
    """

    if not student.school_id:
        return ZERO

    academic_year = str(
        academic_year
    ).strip()

    term = str(
        term
    ).strip()

    if not academic_year:
        raise ValueError(
            "Academic year is required."
        )

    if term not in {"1", "2", "3"}:
        raise ValueError(
            f"Invalid term: {term}. "
            "The school operates three terms."
        )

    entries = (
        FeeLedgerEntry.objects
        .filter(
            student=student,
            school_id=student.school_id,
            academic_year=academic_year,
            term__in=["1", "2", "3"],
        )
        .order_by(
            "term",
            "transaction_date",
            "id",
        )
    )

    balance = ZERO

    for entry in entries:

        # Only process transactions up to the
        # requested term.
        if int(str(entry.term)) > int(term):
            continue

        debit = (
            entry.debit
            if entry.debit is not None
            else ZERO
        )

        credit = (
            entry.credit
            if entry.credit is not None
            else ZERO
        )

        balance += (
            debit - credit
        )

    return balance

def get_term_opening_balance(
    *,
    student,
    academic_year,
    term,
):
    """
    Return the student's opening account position for a term.

    Term 1:
        Uses an explicitly recorded OPENING_BALANCE, if one exists.

        If no explicit opening balance exists and the student
        had an academic enrollment in the previous academic
        year, the previous year's Term 3 closing balance becomes
        the new year's Term 1 opening balance.

        A genuinely new student starts with zero.

    Term 2:
        Uses the closing balance of Term 1.

    Term 3:
        Uses the closing balance of Term 2.

    Normal term-to-term movement does NOT require a
    CARRY_FORWARD ledger transaction.
    """

    if not student.school_id:
        return ZERO

    academic_year = str(
        academic_year
    ).strip()

    term = str(
        term
    ).strip()

    if not academic_year:
        raise ValueError(
            "Academic year is required."
        )

    if term not in {"1", "2", "3"}:
        raise ValueError(
            f"Invalid term: {term}. "
            "The school operates three terms."
        )

    # --------------------------------------------------
    # TERM 1
    # --------------------------------------------------
    #
    # Term 1 may have an explicitly recorded opening
    # balance. An explicit opening balance always takes
    # precedence over an automatically derived balance.
    #
    if term == "1":

        entries = (
            FeeLedgerEntry.objects
            .filter(
                student=student,
                school_id=student.school_id,
                academic_year=academic_year,
                term="1",
                transaction_type="OPENING_BALANCE",
            )
            .order_by(
                "transaction_date",
                "id",
            )
        )

        balance = ZERO

        for entry in entries:

            balance += (
                (entry.debit or ZERO)
                - (entry.credit or ZERO)
            )

        # --------------------------------------------------
        # EXPLICIT OPENING BALANCE EXISTS
        # --------------------------------------------------

        if entries.exists():
            return balance

        # --------------------------------------------------
        # YEAR CROSSOVER
        # --------------------------------------------------
        #
        # Only a student with enrollment history in the
        # previous academic year carries the previous
        # year's Term 3 closing balance forward.
        #
        try:
            previous_academic_year = str(
                int(academic_year) - 1
            )
        except ValueError:
            # Non-numeric academic years cannot be safely
            # crossed automatically.
            return ZERO

        previous_year_enrollment_exists = (
            StudentAcademicEnrollment.objects
            .filter(
                student=student,
                academic_year=previous_academic_year,
            )
            .exists()
        )

        if not previous_year_enrollment_exists:
            return ZERO

        return get_term_balance(
            student=student,
            academic_year=previous_academic_year,
            term="3",
        )

    # --------------------------------------------------
    # TERM 2
    # --------------------------------------------------
    #
    # Opening = Term 1 closing.
    #
    if term == "2":

        return get_term_balance(
            student=student,
            academic_year=academic_year,
            term="1",
        )

    # --------------------------------------------------
    # TERM 3
    # --------------------------------------------------
    #
    # Opening = Term 2 closing.
    #

    return get_term_balance(
        student=student,
        academic_year=academic_year,
        term="2",
    )
# ============================================================
# LEDGER QUERY
# ============================================================

def get_student_ledger(student):
    """
    Return the student's complete financial ledger.

    The ledger is isolated to the student's school.
    """

    if not student.school_id:
        return FeeLedgerEntry.objects.none()

    return (
        FeeLedgerEntry.objects
        .filter(
            student=student,
            school_id=student.school_id,
        )
        .select_related(
            "student",
            "school",
            "fee_payment",
            "recorded_by",
        )
        .order_by(
            "transaction_date",
            "id",
        )
    )


# ============================================================
# TERM CARRY FORWARD
# ============================================================

@transaction.atomic
def carry_forward_term_balance(
    *,
    student,
    academic_year,
    from_term,
    to_term,
    transaction_date=None,
    recorded_by=None,
):
    """
    Carry the closing balance of one term into the next term.

    Positive previous balance:
        Student owes money.
        Carry forward is a DEBIT.

    Negative previous balance:
        Student has a credit/overpayment.
        Carry forward is a CREDIT.

    Example:

        Term 1:
            Fee       30,000
            Payment   25,000
            Balance    5,000 owed

        Term 2:
            Carry      5,000 debit
            Fee       30,000 debit
            Payment   20,000 credit
            Balance   15,000 owed
    """

    academic_year = str(academic_year)
    from_term = str(from_term)
    to_term = str(to_term)

    # Cannot carry a term into itself.
    if from_term == to_term:
        return None

    # Get closing balance of previous term.
    previous_balance = get_term_balance(
        student=student,
        academic_year=academic_year,
        term=from_term,
    )

    previous_balance = _decimal(
        previous_balance
    )

    # Nothing to carry.
    if previous_balance == ZERO:
        return None

    reference = (
        f"CF-{academic_year}-"
        f"T{from_term}-T{to_term}"
    )

    # Prevent duplicate carry-forward.
    existing = (
        FeeLedgerEntry.objects
        .filter(
            student=student,
            school_id=student.school_id,
            academic_year=academic_year,
            term=to_term,
            transaction_type="CARRY_FORWARD",
            reference=reference,
        )
        .first()
    )

    if existing:
        return existing

    if transaction_date is None:
        transaction_date = date.today()

    # --------------------------------------------------
    # POSITIVE BALANCE
    # Student owes money.
    # Carry forward as DEBIT.
    # --------------------------------------------------

    if previous_balance > ZERO:

        return create_ledger_entry(
            student=student,
            transaction_type="CARRY_FORWARD",
            description=(
                f"Balance brought forward "
                f"from Term {from_term}: "
                f"KSh {previous_balance:,.2f}"
            ),
            debit=previous_balance,
            credit=ZERO,
            transaction_date=transaction_date,
            academic_year=academic_year,
            term=to_term,
            reference=reference,
            recorded_by=recorded_by,
        )

    # --------------------------------------------------
    # NEGATIVE BALANCE
    # Student has an overpayment/credit.
    # Carry forward as CREDIT.
    # --------------------------------------------------

    credit_amount = abs(previous_balance)

    return create_ledger_entry(
        student=student,
        transaction_type="CARRY_FORWARD",
        description=(
            f"Credit brought forward "
            f"from Term {from_term}: "
            f"KSh {credit_amount:,.2f}"
        ),
        debit=ZERO,
        credit=credit_amount,
        transaction_date=transaction_date,
        academic_year=academic_year,
        term=to_term,
        reference=reference,
        recorded_by=recorded_by,
    )
# ============================================================
# CARRY FORWARD ALL STUDENTS
# ============================================================

@transaction.atomic
def carry_forward_all_students(
    *,
    school,
    academic_year,
    from_term,
    to_term,
    transaction_date,
    recorded_by=None,
):
    """
    Carry balances for every student in a school.

    Example:

        Term 1 -> Term 2

    The transaction date must be supplied by the caller
    and should represent the opening date of the destination
    term.

    Returns:

        created
        skipped
    """

    if school is None:
        raise ValueError(
            "School is required."
        )

    students = (
        Student.objects
        .filter(
            school=school,
        )
        .order_by(
            "id",
        )
    )

    created_count = 0
    skipped_count = 0

    for student in students:

        entry = carry_forward_term_balance(
            student=student,
            academic_year=academic_year,
            from_term=from_term,
            to_term=to_term,
            transaction_date=transaction_date,
            recorded_by=recorded_by,
        )

        if entry:
            created_count += 1
        else:
            skipped_count += 1

    return {
        "created": created_count,
        "skipped": skipped_count,
    }


# ============================================================
# SYNCHRONIZE EXISTING PAYMENTS
# ============================================================

@transaction.atomic
def sync_existing_fee_payments():
    """
    Ensure every existing FeePayment has exactly one
    corresponding PAYMENT ledger entry.

    Safe to run repeatedly.

    Existing ledger entries are not duplicated.
    """

    created_count = 0
    skipped_count = 0
    skipped_no_school = 0

    payments = (
        FeePayment.objects
        .select_related(
            "student",
            "student__school",
        )
        .order_by(
            "payment_date",
            "id",
        )
    )

    for payment in payments:

        student = payment.student

        if not student.school_id:
            skipped_no_school += 1
            continue

        existing = (
            FeeLedgerEntry.objects
            .filter(
                fee_payment=payment,
                transaction_type="PAYMENT",
            )
            .order_by("id")
            .first()
        )

        if existing:
            skipped_count += 1
            continue

        record_payment(
            student=student,
            payment=payment,
            recorded_by=payment.recorded_by,
        )

        created_count += 1

    return {
        "created": created_count,
        "skipped": skipped_count,
        "skipped_no_school": skipped_no_school,
    }

def get_previous_term_closing_balance(
    *,
    student,
    academic_year,
    term,
):
    """
    Return the closing balance from the term immediately
    preceding the selected term.

    Same academic year:

        Term 1 -> 0
        Term 2 -> Term 1 closing
        Term 3 -> Term 2 closing

    The returned value keeps the accounting sign:

        Positive = student owes money
        Negative = student has credit

    This function is intended for reports and calculations
    that need to display the previous term's balance as
    the current term's carry forward.
    """

    academic_year = str(
        academic_year
    ).strip()

    term = str(
        term
    ).strip()

    if term == "1":
        return ZERO

    if term == "2":
        previous_term = "1"

    elif term == "3":
        previous_term = "2"

    else:
        raise ValueError(
            f"Invalid term: {term}"
        )

    return get_term_balance(
        student=student,
        academic_year=academic_year,
        term=previous_term,
    )

def student_is_eligible_for_term(
    *,
    student,
    academic_year,
    term,
):
    """
    Determine whether a student should receive
    a fee charge for the specified academic year
    and term.

    Rules:

        Earlier academic year:
            eligible

        Same academic year:
            enrollment term <= charge term

        Later academic year:
            not eligible

    Legacy students with no enrollment period are
    treated as eligible for backward compatibility.
    """

    charge_year = str(
        academic_year
    ).strip()

    charge_term = str(
        term
    ).strip()

    enrollment_year = str(
        student.enrollment_academic_year or ""
    ).strip()

    enrollment_term = str(
        student.enrollment_term or ""
    ).strip()

    # --------------------------------------------------------
    # Legacy student
    # --------------------------------------------------------
    #
    # Existing students created before enrollment tracking
    # may have blank enrollment fields.
    #
    # Do not accidentally remove their fee charges.
    #
    if not enrollment_year or not enrollment_term:
        return True

    # --------------------------------------------------------
    # Validate values
    # --------------------------------------------------------

    try:
        charge_year_int = int(charge_year)
        enrollment_year_int = int(enrollment_year)
        charge_term_int = int(charge_term)
        enrollment_term_int = int(enrollment_term)

    except (TypeError, ValueError):
        raise ValueError(
            "Invalid academic year or term in "
            "student enrollment or fee structure."
        )

    if charge_term_int not in [1, 2, 3]:
        raise ValueError(
            f"Invalid charge term: {charge_term}"
        )

    if enrollment_term_int not in [1, 2, 3]:
        raise ValueError(
            f"Invalid student enrollment term: "
            f"{enrollment_term}"
        )

    # --------------------------------------------------------
    # Enrollment before the charge academic year
    # --------------------------------------------------------

    if enrollment_year_int < charge_year_int:
        return True

    # --------------------------------------------------------
    # Student enrolled after the charge academic year
    # --------------------------------------------------------

    if enrollment_year_int > charge_year_int:
        return False

    # --------------------------------------------------------
    # Same academic year
    # --------------------------------------------------------

    return enrollment_term_int <= charge_term_int