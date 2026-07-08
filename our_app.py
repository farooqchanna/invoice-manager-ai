from flask import Flask , render_template, sessions,url_for,redirect, request, session
from apscheduler.schedulers.background import BackgroundScheduler
from google import genai
from google.genai import types
from datetime import datetime , date
import smtplib
from email.message import EmailMessage
import csv
import os
import json
import pandas as pd
from api import api_key
from prom import prt


app = Flask(__name__)
app.secret_key = "change-this-to-a-real-secret-key"  

def auto_mail():
    try:
        df = pd.read_csv("invoice.csv")
        df["due_date"] = pd.to_datetime(df["due_date"])

        today = date.today()
        invoice = df[df["due_date"].dt.date == today]

        if invoice.empty:
            return None

        sender = "farooquechanna18@gmail.com"
        recipient = "farooquechanna18@gmail.com"
        password = "YOUR_APP_PASSWORD"

        msg = EmailMessage()
        msg["Subject"] = "Bill to be paid"
        msg["From"] = sender
        msg["To"] = recipient
        msg.set_content(invoice.to_string(index=False))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

        return "Email sent"

    except Exception as e:
        print(f"Auto mail error: {e}")  
        return None


scheduler =BackgroundScheduler()
scheduler.add_job(auto_mail,trigger="cron",hour = 9 , minute = 0)
scheduler.start()

@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        if name == "admin" and password == "123":
            session["user"] = name          
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user", None)               
    return redirect(url_for("login"))       


CSV_PATH = "invoice.csv"
CSV_HEADERS = ["company_name", "service", "total_payment", "due_date"]

def append_invoice_row(info):
    file_exists = os.path.isfile(CSV_PATH) and os.path.getsize(CSV_PATH) > 0
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADERS)
        writer.writerow([
            info.get("company_name"),
            info.get("service"),
            info.get("total_payment"),
            info.get("due_date"),
        ])

@app.route("/home", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        client = genai.Client()
        file = request.files["file"]
        file_bytes = file.read()
        prompt = prt()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Part.from_bytes(data=file_bytes, mime_type=file.mimetype), prompt]
        )

        data = response.text.strip()
        if data.startswith("```"):
            data = data.strip("`")
            if data.lower().startswith("json"):
                data = data[4:]
            data = data.strip()

        info = json.loads(data)
        append_invoice_row(info)
        return redirect(url_for("view"))

    return render_template("upload.html")

@app.route("/view", methods = ["POST","GET"])
def view():
    df = pd.read_csv("invoice.csv")
    num = request.form.get("number")
    if num is not None and num != "":
        try:
            num = int(num)
        except Exception as e:
            num = None
    else:
        num = None
    
    if num is not None and num in df.index:
        df = df.drop(num)
        df = df.reset_index(drop=True)
        df.to_csv("invoice.csv", index=False)
    
    df.total_amount = pd.to_numeric(df.total_amount, errors= "coerce")
    total = df.total_amount.sum()
    if not df.empty:
        data = df.to_html()
        found = True
    else:
        data = None
        found = False
    return render_template("view.html",data = data, found = found, total = total)

   





