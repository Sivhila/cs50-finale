import logging
from flask import Flask, redirect, render_template, session, request, jsonify, make_response, flash, url_for
import secrets
from flask_session import Session
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import os
from datetime import datetime, timezone
import uuid
from uuid import uuid4
from google.cloud.firestore import FieldFilter
from helpers import login_required, zmw, initiate_payment, verify_payment, initialize_paystack, verify_paystack_payment,normalize_phone
from dotenv import load_dotenv

load_dotenv()



app = Flask(__name__)

app.jinja_env.filters["ZMW"] = zmw

app.secret_key = os.getenv("SECRET_KEY")
app.paystack_secret_key = os.getenv("PAYSTACK_SECRET_KEY")

app.AUTH_ID = os.getenv("MONEYUNIFY_AUTH_ID")


cred = credentials.Certificate("firebase-auth.json")
firebase_admin.initialize_app(cred, {
    "storageBucket": "dbowy-8aa9c.firebasestorage.app"
    })

db = firestore.client()
bucket = storage.bucket()


app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

logging.basicConfig(level=logging.INFO)

WRITER_COMMISSION = 0.5
PROOFREADER_COMMISSION = 1/6

@app.after_request
def add_header(response):
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-crop'
    return response


@app.route("/auth", methods=["POST"])
def authorize():

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return "Missing or invalid Authorization header", 401

    id_token = auth_header.split(" ", 1)[1].strip()
    if not id_token:
        return "Missing ID token", 401

    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)

        session["user_id"] = decoded_token.get("uid")

        session["user"] = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name")
                }
        logging.info("User logged in: %s", session["user"].get("email"))
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logging.exception("Token verification failed")
        return f"Unauthorized: {str(e)}", 401



@app.route("/login", methods=["GET"])
def login():
    if "user" in session:
        return redirect("/")

    return render_template("login.html")


@app.route("/signup", methods=["GET"])
def signup():

        if "user" in session:
            return redirect("/")

        return render_template("signup.html")


@app.route("/reset_password")
def reset_password():
    if "user" in session:
        return redirect("/")
    else:
       return render_template("forgot_password.html")



@app.route("/logout")
def logout():

    session.clear()
    response = make_response(redirect("/login"))
    response.set_cookie("session", '', expires=0)
    return response



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    user = session["user"]
    uid = user["uid"]


    if request.method == "POST":
        
        role = request.form.get("role")
        university = request.form.get("university")
        program = request.form.get("program")
        major = request.form.get("major")
        minor = request.form.get("minor")
        certificate = request.files.get("certificate")

        if not role or not university or not program:
            return "Missing required fields", 400


        profile_info = {
                    "role": role,
                    "university": university,
                    "program": program,
                    "major": major,
                    "minor": minor,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                    }

        if role == "writer":
            if not certificate or certificate.filename == "":
                flash("No certificate selected", "error")
                return redirect("/profile")

            filename = f"certificates/{uid}_{uuid4()}"
            blob = bucket.blob(filename)
            blob.upload_from_file(certificate)
            blob.make_public()

            profile_info["certificate_url"] = blob.public_url

        db.collection("users").document(uid).set(profile_info, merge=True)

        session["role"] = role

        flash("Profile updated successfully.", "success")
        return redirect("/")

    user_doc = db.collection("users").document(uid).get()
    current_data = user_doc.to_dict() if user_doc.exists else {} 

    return render_template("profile.html", user=current_data)



@app.route("/history")
@login_required
def history():
    user = session["user"]
    user_id = user["uid"]


    assignments_info = (
             db.collection("quotes")
             .where(filter=FieldFilter(
                 "status",
                 "in",
                 [
                     "pending",
                     "in_progress",
                     "waiting_proofread",
                     "correction_required",
                     "approved_work",
                     ]
                 )
                 )
             .order_by("created_at", direction=firestore.Query.DESCENDING)
             .stream()
             )

    assignments = []

    for doc in assignments_info:
        data = doc.to_dict()
        data["id"] = doc.id

        if (
                data.get("user_id") != user_id and 
                data.get("writer_id") != user_id and 
                data.get("proofreader_id") != user_id
                ):
            continue

        if data.get("created_at"):
            data["created_at"] = data["created_at"].strftime("%Y-%m-%d %H:%M:%S")

            assignments.append(data)

    return render_template("history.html", assignments=assignments)



@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():

    user = session["user"]
    customer_id = user["uid"]
    email = user.get("email", "customer@example.com")


    if request.method == "GET":
        quote_id = request.args.get("id")

        if not quote_id:
            return "No assignment selected", 400
        
        quote_doc = db.collection("quotes").document(quote_id).get()

        if not quote_doc.exists:
            return "Assignment not found", 404

        quote_data = quote_doc.to_dict()
        price = quote_data.get("price")

        return render_template(
                "payment.html",
                price=price,
                quote_id=quote_id
                )

    
    if request.method == "POST":
        quote_id = request.form.get("quote_id")
        method = request.form.get("method")

        if not quote_id or not method:
            return "Invalid request: Missing ID or Method", 400

        quote_doc = db.collection("quotes").document(quote_id).get()

        if not quote_doc.exists:
            return "Quote not found", 400

        quote_data = quote_doc.to_dict()
        price = quote_data.get("price")
        amount = str(int(price))


        if method == "mobile":
            provider = request.form.get("provider")
            phone = normalize_phone(request.form.get("phone"))

            if not phone or not provider:
                return "Mobile payment details required", 400


            result = initiate_payment(phone, amount, quote_id)
            print("PAYMENT API RESULT:", result)
            
            if result["isError"]:
                flash(result["message"], "error")
                return redirect(f"/payment?id={quote_id}")

            transaction_id = result["data"].get("transaction_id")
            payment_status = "pending"


        elif method == "card":
            card_number = request.form.get("card_number")
            expiry = request.form.get("expiry")
            cvv = request.form.get("cvv")
            
            if not card_number or not expiry or not cvv:
                return "Card details required", 400

            result = initialize_paystack(email, amount)

            if result["isError"]:
                flash(result["message"], "error")
                return redirect(f"Payment?id={quote_id}")

            reference = result["reference"]


        else:
            return "Invalid payment method", 400


        db.collection("quotes").document(quote_id).update({
            "payment_status": payment_status,
            "Payment_reference": reference | transacton_id,
            "payment_provider": "moneyunify" | "paystack",
            "payment_method": method,
            "paid_amount": int(amount),
            "payment_requested_at": firestore.SERVER_TIMESTAMP
            })

        flash("Payment request sent. Please approve the payment on your phone.", "info")
        return redirect(f"/payment/verify?id={quote_id}")



@app.route("/payment/verify", methods=["GET"])
@login_required
def verify_payment():
    quote_id = request.args.get("id")

    if not quote_id:
        return "Missing quote ID", 400

    quote_doc = db.collection("quotes").document(quote_id).get()

    if not quote_doc.exists:
        return "Quote not found", 404

    quote_data = quote_doc.to_dict()

    provider = quote_data.get("payment_provider")
    reference = quote_data.get("payment_reference")

    if not provider or not reference:
        return "No transaction to verify", 400

    if provider == "moneyunify":
        result = verify_payment(transacton_id)
        payment_status = result.get("status")

    elif provider == "paystack":
        result = verify_paystack_payment(reference)
        payment_status = result.get("status")

    else:
        return "Unknown payment provider", 400

    print("VERIFY API RESULT:", result)

    if result.get("isError"):
        flash(result.get("message", "Verification failed"), "error")
        return redirect(f"payment?id={quote_id}")

    if payment_status == "success":
        db.collection("quotes").document(quote_id).update({
            "status": "paid",
            "payment_staus": "success",
            "verifed_at": firestore.SERVER_TIMESTAMP
            })

        flash(
                "Payment confirmed successfully. Your assignment will be ready in 72 hours.", "success"
                )
        return redirect("/")

    elif payment_status == "pending":
        flash(
            "Payment s still pending. Please approve it on your phone.", "warning"
            )
        return redirect(f"/payment?id={quote_id}")

    else:
        db.collection("quotes").document(quote_id).update({
            "payment_status": "failed",
            "failed_at": firestore.SERVER_TIMESTAMP
            })

        flash(
            "Payment failed or was cancelled.Please try again.", "error"
            )
        return redirect(f"/payment?id={quote_id}")


@app.route("/")
@login_required
def index():
    user = session["user"]
    user_id = user["uid"]


    assignments_info = (
                db.collection("quotes")
                .where(filter=FieldFilter("status", "==", "pending"))
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .stream()
                )
    
    assignments = []
    has_approved = False
    has_rejected = False

    for doc in assignments_info:
        data = doc.to_dict()
        data["id"] = doc.id
   
        assignments.append(data)

        if data.get("writer_id") == user_id:
            if data.get("status") == "approved_work":
                has_approved = True
            elif data.get("status") == "correction_required":
                has_rejected = True

    if has_approved:
        flash("Assignment task approved. You have earned income!", "success")

    if has_rejected:
        flash("Assignment task rejected. Correct your assignment.", "error")


    return render_template(
            "index.html",
            assignments=assignments
            )




@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    customer = session["user"]
    customer_id = customer["uid"]

    if request.method == "POST":

        task = request.form.get("task")
        title = request.form.get("title")
        pages = request.form.get("pages")
        reference = request.form.get("reference")
        instruction = request.form.get("instruction")
        file_data = request.files.get("data")

        data = []

        if not task:
            return "Missing required fields", 400

        if task == "research":
            flash(f"Contact research team.", "error")
            return redirect("/quote")


        if task == "assignment":
            if not title:
                return "Please provide assignment title", 400
            
            if not pages:
                return "Please enter number of pages", 400

            if not reference:
                return "Please provide referencing style", 400

            if not instruction:
                return "Please provide special instructions", 400
            if not file_data or file_data.filename == "":
                return "Please upload file", 400

            try:
                pages = int(pages)
            except ValueError:   
                return "pages must be an integer", 400

            if pages < 1 or pages > 15:
                return "Pages must be between 1 and 15", 400

            if pages < 5:
                price = 100
            elif pages < 8:
                price = 150
            elif pages < 12:
                price = 200
            else:
                price = 250
            
            filename = f"quote_files/{customer_id}_{uuid4()}"
            blob = bucket.blob(filename)
            blob.upload_from_file(
                    file_data,
                    content_type=file_data.content_type
                    )
            blob.make_public()
            file_url = blob.public_url

            data.append({
                "task": task,
                "title": title,
                "pages": pages,
                "reference": reference,
                "instruction": instruction,
                "file": file_url
                })

            _, doc_ref = db.collection("quotes").add({
                "user_id": customer_id,
                "task": task,
                "title": title,
                "pages": pages,
                "reference": reference,
                "instruction": instruction,
                "file_url": file_url,
                "price": price,
                "status": "pending",
                "created_at": firestore.SERVER_TIMESTAMP
                })


            return render_template(
                    "quoted.html",
                    data=data,
                    price=price,
                    quote_id=doc_ref.id
                    )

    return render_template("quote.html")


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    if "user" not in session:
        return redirect("/login")
    
    writer = session["user"]
    writer_id = writer["uid"]


    tasks_data = (
            db.collection("quotes")
            .where(filter=FieldFilter("status", "in", ["pending", "waiting_proofread"]))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
            )

    tasks = []
    
    for doc in tasks_data:
        data = doc.to_dict()
        data["id"] = doc.id
        status = data.get("status")

        if status == "pending":
            data["task_type"] = "Writing Task"
        elif status == "waiting_proofread":
            data["task_type"] = "Proofreading Task"
        else:
            continue

        try:
            price = float(data.get("price", 0))
        except (ValueError, TypeError):
            price = 0.0

        data["writer_earnings"] = round(price * WRITER_COMMISSION, 2)
        data["proofreader_earnings"] = round(price * PROOFREADER_COMMISSION, 2)


        if status == "waiting_proofread":
            if data.get("writer_id") == writer_id or data.get("proofreader_id") == writer_id:
                continue


        tasks.append(data)

    return render_template(
            "tasks.html",
            tasks=tasks
            )



@app.route("/accept_task/<task_id>", methods=["GET", "POST"])
@login_required
def accept_task(task_id):
    writer = session["user"]
    writer_id = writer["uid"]

    task_ref = db.collection("quotes").document(task_id)

    @firestore.transactional
    def accept_task_txn(transaction):
        task_doc = task_ref.get(transaction=transaction)

        if not task_doc.exists:
            return False, "Sorry, this task not found"

        current_status = task_doc.to_dict().get("status")
        if current_status != "pending":
            return False, "Sorry, this task was just taken by someone else!"

        transaction.update(task_ref, {
            "status": "in_progress",
            "writer_id": writer_id,
            "accepted_at": firestore.SERVER_TIMESTAMP
        })

        return True, None

    transaction = db.transaction()
    success, error = accept_task_txn(transaction)

    if not success:
        flash(error, "error")
        return redirect("/tasks")

    flash("Task accepted! you have 24 hrs to complete task.", "success")
    return redirect(f"/complete_task/{task_id}")


@app.route("/complete_task/<task_id>", methods=["GET", "POST"])
@login_required
def complete_task(task_id):
    writer = session["user"]
    writer_id = writer["uid"]

    task_ref = db.collection("quotes").document(task_id)
    task_doc = task_ref.get()


    if not task_doc.exists:
        flash("Task not found.", "error")
        return redirect("/tasks")

    task_data = task_doc.to_dict()

    if task_data.get("writer_id") != writer_id:
        flash("Unauthorized access", "error")
        return redirect("/tasks")

    if task_data.get("status") != "in_progress":
        flash("This task has already been submitted.", "warning")
        return redirect("/tasks")


    accepted_at = task_data.get("accepted_at")
    if not accepted_at:
        flash("Task acceptance time missing", "error")
        return redirect("/tasks")

    current_time = datetime.now(timezone.utc)
    elapsed_time = (current_time - accepted_at).total_seconds()

    TOTAL_TIME = 24 * 60 * 60
    remaining_seconds = max(0, int(TOTAL_TIME - elapsed_time))

    if remaining_seconds <= 0:
        flash("Submission time expired.", "error")
        return redirect("/tasks")
    
    if request.method == "POST":

        assignment_file = request.files.get("assignment_file")

        if not assignment_file or assignment_file.filename == "":
             flash("Please upload the completed assignment file.", "error")

        else:
             try:
                 customer_id = task_data.get("user_id")
                 filename = f"quote_files/{customer_id}_{uuid4()}"
                 blob = bucket.blob(filename)
                 blob.upload_from_file(
                         assignment_file,
                         content_type=assignment_file.content_type
                         )
                 blob.make_public()
                 file_url = blob.public_url

                 task_ref.update({
                     "status": "waiting_proofread",
                     "submitted_at": firestore.SERVER_TIMESTAMP,
                     "completed_file_url": file_url,
                     })

                 flash("Assignment submitted successfully. You be notified after review.", "success")
                 return redirect("/tasks")

             except Exception as e:
                 print(f"Error: {e}")
                 flash("An error occurred during submission. Please try again.", "error")

    return render_template(
            "complete_task.html",
            task_id=task_id,
            remaining_seconds=remaining_seconds
            )



@app.route("/accept_proofread/<task_id>", methods=["GET", "POST"])
@login_required
def accept_proofread(task_id):
    proofreader = session["user"]
    proofreader_id = proofreader["uid"]

    task_ref = db.collection("quotes").document(task_id)

    @firestore.transactional
    def accept_proofread_tx(transaction):
        task_doc = task_ref.get(transaction=transaction)

    if not task_doc.exists:
        return False, "Task not found"

    task_data = task_doc.to_dict()
    current_status = task_data.get("status")

    if current_status != "waiting_proofread":
        return False, "Sorry, this task has already been claimed or processed!"

    if task_data.get("writer_id") == proofreader_id:
        return False, "You cannot proofread your own submitted work!"

    transaction.update(task_ref, {
            "status": "proofread_in_progress",
            "proofreader_id": proofreader_id,
            "proofreader_at": firestore.SERVER_TIMESTAMP
            })

    return True, None

    transaction = db.transaction()
    success, error = accept_proofread_tx(transaction)

    if not success:
        flash(error, "error")
        return redirect("/tasks")

    flash("Proofreading task accepted! You have 4 hours to review the assignment.", "success")
    return redirect(f"/submit_proofread/{task_id}")


@app.route("/submit_proofread/<task_id>", methods=["GET", "POST"])
@login_required
def submit_proofread(task_id):
    proofreader = session["user"]
    proofreader_id = proofreader["uid"]

    task_ref = db.collection("quotes").document(task_id)
    task_doc = task_ref.get()

    if not task_doc.exists:
        flash("Task not found.", "error")
        return redirect("/tasks")

    task_data = task_doc.to_dict()

    if task_data.get("proofreader_id") != proofreader_id:
        flash("You are not the assigned proofreader.", "error")
        return redirect("/tasks")

    accepted_at = task_data.get("accepted_at")
    if not accepted_at:
        flash("Task acceptance time missing", "error")
        return redirect("/tasks")

    current_time = datetime.now(timezone.utc)
    elapsed_time = (current_time - accepted_at).total_seconds()

    TOTAL_SECONDS = 4 * 60 * 60
    remaining_seconds = max(0, int(TOTAL_SECONDS - elapsed_time))

    if remaining_seconds <= 0:
        task_ref.update({
            "status": "waiting_proofread",
            "proofreader_id": firestore.DELETE_FIELD,
            "proofread_at": firestore.DELETE_FIELD
            })

        flash("Proofreading time limit expired. Task released.", "error")
        return redirect("/tasks")

    if request.method == "GET":
         return render_template(
                 "proofread.html",
                 task_data=task_data,
                 remaining_seconds=remaining_seconds
                 )

    if request.method == "POST":
        action = request.form.get("action")
        comment = request.form.get("comment", "")

        try:
            task_price = float(task_data.get("price", 0))
        except (ValueError, TypeError):
            task_price = 0.0

        if action == "approve":
            task_ref.update({
                "status": "approved_work",
                "proofreader_comment": comment,
                "proofread_submitted_at": firestore.SERVER_TIMESTAMP,
                "writer_payout": round(task_price * WRITER_COMMISSION, 2),
                "proofreader_payout": round(task_price * PROOFREADER_COMMISSION, 2)
                })

            flash("Assignment approved. Tasks completed.", "success")


        elif action == "reject":
            task_ref.update({
                "status": "correction_required",
                "proofreader_comment": comment,
                "proofread_submitted_at": firestore.SERVER_TIMESTAMP,
                "proofreader_id": firestore.DELETE_FIELD,
                "proofreader_at": firestore.DELETE_FIELD
                })

            flash(f"Assignment rejected. Writer notified.", "warning")

        else:
            flash("Invalid action.", "error")
            return redirect(f"/submit_proofread/{task_id}")
        
        return redirect("/")
                

    
@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    user = session["user"]
    user_id = user["uid"]

    payout_tasks_stream = db.collection("quotes").where(
            filter=firestore.FieldFilter("status", "==", "approved_work")).stream()
    total_earnings = 0.0
    
    for doc in payout_tasks_stream:
        task_data = doc.to_dict()
        try:
            if task_data.get("writer_id") == user_id:
                total_earnings += float(task_data.get("writer_payout", 0.0))

            if task_data.get("proofreader_id") == user_id:
                total_earnings += float(task_data.get("proofreader_payout", 0.0))
        except (ValueError, TypeError):
            continue

    withdrawals_stream = db.collection("withdrawals").where(
            filter=firestore.FieldFilter("user_id", "==", user_id)).stream()

    total_withdraw = 0.0

    for doc in withdrawals_stream:
        try:
            total_withdraw += float(doc.to_dict().get("amount", 0.0))
        except (ValueError, TypeError):
            continue

    available_balance = total_earnings - total_withdraw

    if request.method == "GET":
        return render_template(
                "withdraw.html",
                available_balance=available_balance
                )

    if request.method == "POST":
        amount = request.form.get("amount")
        withdraw_method = request.form.get("withdraw_method")

        if not amount or not withdraw_method:
            flash("All required fields must be filled.", "error")
            return redirect("/withdraw")

        try:
            withdrawal_amount = float(amount)
        except ValueError:
            flash("Invalid amount entered.", "error")
            return redirect("/withdraw")

        if withdrawal_amount <= 0:
            flash("Withdrawal amount must be postive.", "error")
            return redirect("/withdraw")

        if withdrawal_amount > available_balance:
            flash("Insufficient balance for this withdrawal.", "error")
            return redirect("/withdraw")

        if withdrawal_amount < 10:
            flash("Minimum withdrawal amount is 10 ZMW.", "error")
            return redirect("/withdraw")

        if withdraw_method == "mobile":
            provider = request.form.get("provider")
            phone = request.form.get("phone")

            if not provider or not phone:
                flash("Mobile provider and phone number are required.", "error")
                return redirect("/withdraw")

            result = initiate_withdraw(withdrawal_amount)

            if result.get("isError"):
                flash(f"Withdraw failed: {result.get('message')}", "error")
                return redirect("withdraw")

        elif withdraw_method == "card":
                 card_number = request.form.get("card_number")
                 expiry = request.form.get("expiry")
                 cvv = request.form.get("cvv")

                 if not card_number or not expiry or not cvv:
                     flash("ALL card fields required,", "error")
                     return redirect("withdraw")

                 result = initialize_paystack(email, withdrwal_amount)

                 if result.get("isError"):
                     flash(f"Withdraw initialization failed: {result.get('message')}", "error")
                     return redirect("/withdraw")

                 withdraw_status = "success"
                 account_details = f"Card ending {card_number[-4:]}"

        else:

            flash("Invalid withdrawal method selected", "error")
            return redirect("/withdraw")

        if withdrawal_status == "success":
            db.collection("withdrawals").add({
                "user_id": user_id,
                "amount": withdrawal_amount,
                "withdraw_method": account_details,
                "status": "withdrawn",
                "requested_at": firestore.SERVER_TIMESTAMP
                })

            flash("Withdrawal request successful! Processing takes up 72 hours.", "success")
            return redirect("/withdraw")
        
        flash("Withdrawal failed. Please try again.", "error")
        return redirect("/withdraw")
                            



























if __name__== "__main__":
    app.run(debug=True)





