import base64
import json
from datetime import datetime

import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from students.models import (
    Student,
    MpesaTransaction,
    FeePayment,
)

from students.utils import get_user_school


@login_required
def mpesa_stk_push(request):

    school = get_user_school(request.user)

    # Superuser can see all schools.
    # Other users only see students from their school.
    students = Student.objects.select_related(
        "school_class"
    ).order_by(
        "admission_number"
    )

    if school:
        students = students.filter(
            school=school
        )

    # -----------------------------
    # DISPLAY PAYMENT PAGE
    # -----------------------------
    if request.method == "GET":

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
            },
        )

    # -----------------------------
    # GET FORM DATA
    # -----------------------------
    student_id = request.POST.get(
        "student_id",
        ""
    ).strip()

    phone = request.POST.get(
        "phone",
        ""
    ).strip()

    amount = request.POST.get(
        "amount",
        ""
    ).strip()

    # -----------------------------
    # VALIDATE REQUIRED FIELDS
    # -----------------------------
    if not student_id or not phone or not amount:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Student, phone number and "
                    "amount are required."
                ),
            },
        )

    # -----------------------------
    # GET STUDENT
    # -----------------------------
    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Selected student does not exist."
                ),
            },
        )

    # -----------------------------
    # SECURITY:
    # MAKE SURE STUDENT BELONGS
    # TO LOGGED-IN USER'S SCHOOL
    # -----------------------------
    if school and student.school_id != school.id:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "You cannot make a payment "
                    "for a student from another school."
                ),
            },
        )

    # -----------------------------
    # NORMALIZE PHONE NUMBER
    # -----------------------------
    if phone.startswith("0"):

        phone = "254" + phone[1:]

    elif phone.startswith("+254"):

        phone = phone[1:]

    elif phone.startswith("7") or phone.startswith("1"):

        phone = "254" + phone

    # -----------------------------
    # VALIDATE PHONE
    # -----------------------------
    if (
        not phone.isdigit()
        or len(phone) != 12
        or not phone.startswith("254")
    ):

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Enter a valid Kenyan phone "
                    "number, for example 0712345678."
                ),
            },
        )

    # -----------------------------
    # CONVERT AMOUNT
    # -----------------------------
    try:

        amount = int(float(amount))

    except (ValueError, TypeError):

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Enter a valid payment amount."
                ),
            },
        )

    if amount < 1:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Amount must be at least KES 1."
                ),
            },
        )

    # -----------------------------
    # GET M-PESA ACCESS TOKEN
    # -----------------------------
    auth_url = (
        "https://sandbox.safaricom.co.ke/"
        "oauth/v1/generate"
        "?grant_type=client_credentials"
    )

    try:

        auth_response = requests.get(
            auth_url,
            auth=(
                settings.MPESA_CONSUMER_KEY,
                settings.MPESA_CONSUMER_SECRET,
            ),
            timeout=30,
        )

    except requests.RequestException as e:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Could not connect to "
                    "M-PESA."
                ),
                "details": str(e),
            },
        )

    if auth_response.status_code != 200:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Could not authenticate "
                    "with M-PESA."
                ),
                "details": auth_response.text,
            },
        )

    try:

        access_token = (
            auth_response.json()
            .get("access_token")
        )

    except ValueError:

        access_token = None

    if not access_token:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "M-PESA did not return "
                    "an access token."
                ),
            },
        )

    # -----------------------------
    # GENERATE TIMESTAMP
    # -----------------------------
    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    # -----------------------------
    # GENERATE PASSWORD
    # -----------------------------
    password_string = (
        settings.MPESA_SHORTCODE
        + settings.MPESA_PASSKEY
        + timestamp
    )

    password = base64.b64encode(
        password_string.encode()
    ).decode()

    # -----------------------------
    # STK PUSH URL
    # -----------------------------
    stk_url = (
        "https://sandbox.safaricom.co.ke/"
        "mpesa/stkpush/v1/processrequest"
    )

    # -----------------------------
    # STK PUSH PAYLOAD
    # -----------------------------
    payload = {

        "BusinessShortCode":
            settings.MPESA_SHORTCODE,

        "Password":
            password,

        "Timestamp":
            timestamp,

        "TransactionType":
            "CustomerPayBillOnline",

        "Amount":
            amount,

        "PartyA":
            phone,

        "PartyB":
            settings.MPESA_SHORTCODE,

        "PhoneNumber":
            phone,

        "CallBackURL":
            settings.MPESA_CALLBACK_URL,

        # IMPORTANT:
        # Used by callback to identify
        # the student.
        "AccountReference":
            f"STUDENT-{student.id}",

        "TransactionDesc":
            (
                "School fee payment - "
                f"{student.admission_number}"
            ),
    }

    headers = {

        "Authorization":
            f"Bearer {access_token}",

        "Content-Type":
            "application/json",
    }

    # -----------------------------
    # SEND STK PUSH
    # -----------------------------
    try:

        stk_response = requests.post(
            stk_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

    except requests.RequestException as e:

        return render(
            request,
            "students/mpesa_payment.html",
            {
                "students": students,
                "error": (
                    "Could not connect to "
                    "M-PESA STK service."
                ),
                "details": str(e),
            },
        )

    try:

        result = stk_response.json()

    except ValueError:

        result = {
            "error": (
                "M-PESA returned an invalid response."
            ),
            "raw_response": stk_response.text,
        }

    print(
        "\n========== M-PESA STK PUSH RESPONSE =========="
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print(
        "===============================================\n"
    )

    # -----------------------------
    # SAVE PENDING TRANSACTION
    # -----------------------------
    checkout_request_id = result.get(
        "CheckoutRequestID"
    )

    merchant_request_id = result.get(
        "MerchantRequestID",
        ""
    )

    response_code = result.get(
        "ResponseCode"
    )

    if checkout_request_id:

        MpesaTransaction.objects.create(

            student=student,

            phone_number=phone,

            amount=amount,

            merchant_request_id=(
                merchant_request_id
            ),

            checkout_request_id=(
                checkout_request_id
            ),

            status="Pending",

            result_code=(
                int(response_code)
                if response_code is not None
                and str(response_code).isdigit()
                else None
            ),

            result_description=(
                result.get(
                    "ResponseDescription",
                    ""
                )
            ),
        )

    # -----------------------------
    # DISPLAY RESULT
    # -----------------------------
    return render(
        request,
        "students/mpesa_payment.html",
        {
            "students": students,
            "result": result,
        },
    )


# =====================================================
# M-PESA CALLBACK
# =====================================================

@csrf_exempt
def mpesa_callback(request):

    print(
        "\n========== M-PESA CALLBACK HIT =========="
    )

    print(
        "METHOD:",
        request.method
    )

    print(
        "RAW BODY:",
        request.body.decode(
            "utf-8",
            errors="replace"
        )
    )

    print(
        "=========================================\n"
    )

    # --------------------------------
    # ONLY ACCEPT POST
    # --------------------------------

    if request.method != "POST":

        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc":
                    "Only POST requests are allowed",
            },
            status=405,
        )

    # --------------------------------
    # READ JSON
    # --------------------------------

    try:

        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        print(
            "INVALID JSON RECEIVED"
        )

        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc":
                    "Invalid JSON",
            },
            status=400,
        )

    print(
        "\nM-PESA CALLBACK JSON:"
    )

    print(
        json.dumps(
            data,
            indent=4
        )
    )

    # --------------------------------
    # GET STK CALLBACK
    # --------------------------------

    stk_callback = (
        data
        .get("Body", {})
        .get("stkCallback", {})
    )

    checkout_request_id = (
        stk_callback.get(
            "CheckoutRequestID"
        )
    )

    merchant_request_id = (
        stk_callback.get(
            "MerchantRequestID",
            ""
        )
    )

    result_code = stk_callback.get(
        "ResultCode"
    )

    result_description = (
        stk_callback.get(
            "ResultDesc",
            ""
        )
    )

    # --------------------------------
    # NO CHECKOUT REQUEST ID
    # --------------------------------

    if not checkout_request_id:

        print(
            "No CheckoutRequestID received."
        )

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc":
                    "Callback received",
            }
        )

    # --------------------------------
    # FIND OUR TRANSACTION
    # --------------------------------

    try:

        transaction = (
            MpesaTransaction.objects
            .select_related("student")
            .get(
                checkout_request_id=(
                    checkout_request_id
                )
            )
        )

    except MpesaTransaction.DoesNotExist:

        print(
            "Transaction not found:",
            checkout_request_id
        )

        return JsonResponse(
            {
                "ResultCode": 0,
                "ResultDesc":
                    "Callback received",
            }
        )

    # --------------------------------
    # SAVE CALLBACK INFORMATION
    # --------------------------------

    transaction.merchant_request_id = (
        merchant_request_id
    )

    transaction.result_code = (
        result_code
    )

    transaction.result_description = (
        result_description
    )

    # --------------------------------
    # SUCCESSFUL PAYMENT
    # --------------------------------

    if result_code == 0:

        callback_metadata = (
            stk_callback
            .get(
                "CallbackMetadata",
                {}
            )
            .get(
                "Item",
                []
            )
        )

        metadata = {}

        for item in callback_metadata:

            name = item.get(
                "Name"
            )

            value = item.get(
                "Value"
            )

            if name:

                metadata[name] = value

        # --------------------------------
        # GET PAYMENT INFORMATION
        # --------------------------------

        mpesa_receipt = (
            metadata.get(
                "MpesaReceiptNumber",
                ""
            )
        )

        transaction_date = (
            metadata.get(
                "TransactionDate"
            )
        )

        phone_number = (
            metadata.get(
                "PhoneNumber"
            )
        )

        amount = (
            metadata.get(
                "Amount"
            )
        )

        print(
            "\n========== PAYMENT METADATA =========="
        )

        print(
            "Amount:",
            amount
        )

        print(
            "M-Pesa Receipt:",
            mpesa_receipt
        )

        print(
            "Phone:",
            phone_number
        )

        print(
            "Transaction Date:",
            transaction_date
        )

        print(
            "======================================\n"
        )

        # --------------------------------
        # SAVE M-PESA INFORMATION
        # --------------------------------

        transaction.mpesa_receipt_number = (
            mpesa_receipt
        )

        transaction.transaction_date = (
            str(transaction_date)
            if transaction_date
            else ""
        )

        # --------------------------------
        # VERIFY AMOUNT
        # --------------------------------

        try:

            received_amount = float(
                amount
            )

        except (
            TypeError,
            ValueError
        ):

            received_amount = None

        requested_amount = float(
            transaction.amount
        )

        # --------------------------------
        # INVALID AMOUNT
        # --------------------------------

        if received_amount is None:

            transaction.status = (
                "Failed"
            )

            transaction.result_description = (
                "M-Pesa callback did not "
                "contain a valid payment amount."
            )

            transaction.save()

            print(
                "M-Pesa payment rejected:"
                " invalid amount."
            )

        # --------------------------------
        # AMOUNT MISMATCH
        # --------------------------------

        elif received_amount != requested_amount:

            transaction.status = (
                "Failed"
            )

            transaction.result_description = (
                "Payment amount mismatch. "
                f"Expected KES "
                f"{requested_amount:.2f}, "
                f"received KES "
                f"{received_amount:.2f}."
            )

            transaction.save()

            print(
                "M-Pesa payment rejected:"
                " amount mismatch."
            )

            print(
                f"Expected: "
                f"KES {requested_amount:.2f}"
            )

            print(
                f"Received: "
                f"KES {received_amount:.2f}"
            )

        # --------------------------------
        # AMOUNT IS CORRECT
        # --------------------------------

        else:

            transaction.status = (
                "Completed"
            )

            transaction.save()

            print(
                "M-Pesa amount verified."
            )

            # --------------------------------
            # PREVENT DUPLICATE PAYMENT
            # --------------------------------

            existing_payment = (
                FeePayment.objects
                .filter(
                    reference=mpesa_receipt
                )
                .first()
            )

            if not existing_payment:

                # --------------------------------
                # PAYMENT DATE
                # --------------------------------

                payment_date = (
                    timezone.localdate()
                )

                # Safaricom format:
                # YYYYMMDDHHMMSS

                if transaction_date:

                    try:

                        payment_date = (
                            datetime.strptime(
                                str(
                                    transaction_date
                                ),
                                "%Y%m%d%H%M%S"
                            ).date()
                        )

                    except ValueError:

                        pass

                # --------------------------------
                # CREATE FEE PAYMENT
                # --------------------------------

                FeePayment.objects.create(

                    student=(
                        transaction.student
                    ),

                    amount=(
                        received_amount
                    ),

                    payment_date=(
                        payment_date
                    ),

                    payment_method=(
                        "M-Pesa"
                    ),

                    receipt_number=(
                        "RCPT-"
                        + mpesa_receipt
                    ),

                    reference=(
                        mpesa_receipt
                    ),

                    remarks=(
                        "M-Pesa STK payment"
                    ),

                    recorded_by=None,
                )

                print(
                    "FeePayment created successfully."
                )

            else:

                print(
                    "FeePayment already exists."
                )

    # --------------------------------
    # FAILED / CANCELLED PAYMENT
    # --------------------------------

    else:

        transaction.status = (
            "Failed"
        )

        transaction.save()

        print(
            "M-Pesa payment failed:"
        )

        print(
            result_code,
            result_description
        )

    # --------------------------------
    # CALLBACK COMPLETE
    # --------------------------------

    print(
        "\n========== CALLBACK PROCESSED ==========\n"
    )

    return JsonResponse(
        {
            "ResultCode": 0,
            "ResultDesc":
                "Callback received successfully",
        }
    )