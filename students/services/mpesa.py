import base64
import requests

from datetime import datetime
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from django.conf import settings


def get_mpesa_access_token():
    """
    Get an OAuth access token from Safaricom Daraja.
    """

    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    credentials = f"{consumer_key}:{consumer_secret}"

    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]




def get_mpesa_access_token():
    """
    Get an OAuth access token from Safaricom Daraja.
    """

    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    credentials = f"{consumer_key}:{consumer_secret}"

    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    url = (
        "https://sandbox.safaricom.co.ke/"
        "oauth/v1/generate?grant_type=client_credentials"
    )

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["access_token"]


def send_stk_push(
    phone_number,
    amount,
    account_reference,
    transaction_description,
):
    """
    Initiate an M-Pesa STK Push.
    """

    access_token = get_mpesa_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_string = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        password_string.encode("utf-8")
    ).decode("utf-8")

    url = (
        "https://sandbox.safaricom.co.ke/"
        "mpesa/stkpush/v1/processrequest"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_description,
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()




@csrf_exempt
def mpesa_callback(request):
    if request.method == "POST":
        data = json.loads(request.body)

        print("M-Pesa Callback Received:")
        print(json.dumps(data, indent=4))

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Callback received successfully"
        })

    return JsonResponse({
        "ResultCode": 1,
        "ResultDesc": "Only POST requests are allowed"
    }, status=405)