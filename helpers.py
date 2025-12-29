import requests
import os
from flask import redirect, render_template, session
from functools import wraps

AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsproject.com/en/latest/patterns/viewdecorators
    
    """
    
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        
        if "user" not in session:
            return redirect("/login") 
        return f(*args, **kwargs)
    
    return decorated_function


def zmw(value):
    """Format value as Zambian Kwacha (ZMW)."""
    try:
        return f"K {float(value):,.2f}"
    except (ValueError, TypeError):
        return f"K {value}"


def initiate_payment(phone, amount, quote_id):
    url = "https://api.moneyunify.one/payments/request"

    payload = {
            "from_payer": str(phone),
            "amount": str(amount),
            "auth_id": AUTH_ID,
            "webhook_url": f"http://127.0.0.1:5000/webhook/moneyunify/{quote_id}"
            }

    headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
            }

    try:
        response = requests.post(url, data=payload, headers=headers)

        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            return {
                    "isError": False, 
                    "transaction_id": data.get("transaction_id"), 
                    "data": data
                    }

        return {
                "isError": True,
                "message": data.get("message", "Payment request failed")
                }

    except Exception as e:
        return {
                "isError": True, 
                "message": f"Connection error: {str(e)}"
                }



def verify_payment(transaction_id):
    url = "https://api.moneyunify.one/payments/verify"

    payload = {
            "transaction_id": transaction_id, 
            "auth_id": Auth_ID
            }

    headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
            }
    try:
        response = requests.post(
                url, 
                data=payload, 
                headers=headers,
                timeout=15
                )
        
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
                "isError": True,
                "message": f"Verification failed: {str(e)}"
                }


def normalize_phone(phone):
    phone = phone.replace(" ", "").strip()

    if phone.startswith("0") and len(phone) == 10:
        return phone
    
    return None



def initialize_paystack(email, amount):

    """
    Initialize a Paystack payment (REST API).
    Amount must be sent in ngwee => ZMW 10 = 100
    """

    PAYSTACK_BASE_URL = "https://api.paystack.co/transaction"

    try:
        amount_smallest = int(float(amount) * 100)

        headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
                }

        payload = {
                "email": email,
                "amount": amount_smallest,
                "currency": "ZAR"
                }
        response = requests.post(
                f"{PAYSTACK_BASE_URL}/initialize",
                json=payload,
                headers=headers
                ).json()

        if not response.get("status"):
            return {"isError": True, "message": response.get("message", "Paystack initialization failed")}

        data = response["data"]
        return {
                "isError": False,
                "authorization_url": data["authorization_url"],
                "reference": data["reference"]
                }
    except Exception as e:
        return {"isError": True, "message": str(e)}




def verify_paystack_payment(reference):
    """
    Verify a Paystack payment using REST API.
    """
    PAYSTACK_BASE_URL = "https://api.paystack.co/transaction"

    try:
        headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                }

        response = requests.get(
                f"{PAYSTACK_BASE_URL}/verify/{reference}",
                headers=headers
                ).json()

        if not response.get("status"):
            return {"isError": True, "message": response.get("message", "Verification failed")}

        data = response["data"]

        return {
                "isError": False,
                "status": data["status"],
                "amount": data["amount"] / 100,
                "gateway_response": data["gateway_response"]
                }
    except Exception as e:
        return {"isError": True, "message": str(e)}


