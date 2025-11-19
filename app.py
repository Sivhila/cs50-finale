from flask import Flask, redirect, render_template, request, session
from flask_session import session
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

cred = credentials.certificate("firebase-auth.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/login" methods=["GET", "POST"])
def login():
    // To do


@app.route("/logout" methods=["GET", "POST"])
def logout():
    // To do


@app.route("/register" methods=["GET", "POST"])
def register():
    // To do



@app.route("/status" methods=["GET", "POST"])
def status():
    // To do



@app.route("/payment" methods=["GET", "POST"])
def payment():
    // To do


@app.route("/index" methods=["GET", "POST"])
def index():
    // To do



@app.route("/quote" methods=["GET", "POST"])
def quote():
    // To do