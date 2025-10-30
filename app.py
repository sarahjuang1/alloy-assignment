#!/usr/bin/env python3
"""
  1) Collects applicant info from a frontend form
  2) Sends data to Alloy’s Sandbox API
  3) Returns a decision message from Alloy’s response

How to run:
  - Add credentials to a local `.env`
  - Run: python app.py
"""

import os
import sys
import re
import json
from datetime import datetime, date
from typing import Tuple

from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

# --- Flask Setup ---
app = Flask(__name__, template_folder="templates", static_folder="static")

# --- Load API Credentials ---
def load_credentials() -> Tuple[str, str, str]:
    load_dotenv()
    base_url = os.getenv("ALLOY_BASE_URL", "https://sandbox.alloy.co/v1").rstrip("/")
    token = os.getenv("ALLOY_WORKFLOW_TOKEN")
    secret = os.getenv("ALLOY_WORKFLOW_SECRET")
    if not token or not secret:
        raise RuntimeError("Missing ALLOY_WORKFLOW_TOKEN or ALLOY_WORKFLOW_SECRET in .env")
    return base_url, token, secret


# --- Helper: Post Applicant Evaluation to Alloy ---
def post_evaluation(base_url: str, auth: Tuple[str, str], payload: dict):
    """Send applicant data to Alloy’s sandbox API"""
    url = f"{base_url}/evaluations"
    headers = {"Content-Type": "application/json"}
    return requests.post(url, auth=auth, headers=headers, json=payload, timeout=30)


# --- Validation Helpers ---
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

def validate_age_realistic(dob: str) -> bool:
    """Ensure DOB is valid and applicant age is between 18 and 120."""
    try:
        dob_dt = datetime.strptime(dob.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False
    today = date.today()
    age = (today.year - dob_dt.year) - ((today.month, today.day) < (dob_dt.month, dob_dt.day))
    return 18 <= age <= 120

def validate_state_code(state: str) -> bool:
    return state.upper() in VALID_STATES

def validate_email(email: str) -> bool:
    return EMAIL_RE.match(email) is not None

def validate_ssn(ssn: str) -> bool:
    return ssn.isdigit() and len(ssn) == 9


# --- Routes ---
@app.get("/")
def index():
    return render_template("index.html")


@app.post("/evaluate")
def evaluate():
    try:
        # Load credentials
        base_url, token, secret = load_credentials()
        auth = (token, secret)
        form = request.form

        # --- Validate Inputs ---
        birth_date = form.get("birth_date", "").strip()
        state = form.get("address_state", "").strip().upper()
        email = form.get("email", "").strip()
        ssn = form.get("ssn", "").strip()

        errors = []
        if not validate_age_realistic(birth_date):
            errors.append("Applicant must be between 18 and 120 years old.")
        if not validate_state_code(state):
            errors.append("Invalid state code. Please use a valid 2-letter abbreviation.")
        if not validate_email(email):
            errors.append("Please enter a valid email address.")
        if not validate_ssn(ssn):
            errors.append("SSN must be exactly 9 digits (numbers only).")

        if errors:
            return jsonify({"ok": False, "errors": errors}), 400

        # --- Build Payload for Alloy API ---
        payload = {
            "name_first": form.get("name_first"),
            "name_last": form.get("name_last"),
            "birth_date": birth_date,
            "document_ssn": ssn,
            "email_address": email,
            "address_line_1": form.get("address_line1"),
            "address_line_2": form.get("address_line2"),
            "address_city": form.get("address_city"),
            "address_state": state,
            "address_postal_code": form.get("address_postal_code"),
            "address_country_code": "US"
        }

        # --- Send Request to Alloy ---
        resp = post_evaluation(base_url, auth, payload)
        data = resp.json()

        summary = (data.get("summary") or {})
        outcome = (summary.get("outcome") or "").strip().lower()

        if outcome in ("approved", "approve"):
            message = "Congratulations! You are approved."
        elif outcome in ("manual review", "manual_review", "review"):
            message = "Your application is under review. Please wait for further updates."
        elif outcome in ("deny", "denied", "rejected", "declined"):
            message = "Unfortunately, we cannot approve your application at this time."
        else:
            message = "Unexpected or missing outcome."

        return jsonify({
            "ok": True,
            "outcome": outcome.title() if outcome else "Unknown",
            "message": message,
            "evaluation_token": data.get("evaluation_token"),
            "summary": summary
        })

    except Exception as e:
        return jsonify({"ok": False, "errors": [str(e)]}), 500


# --- Run Flask App ---
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
