"""
We are using a Flask backend for the Alloy demo:
- Serves an HTML form at GET /
- Gets credentials from .env
"""

import os
import json
from typing import Tuple
from datetime import datetime, date

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import requests
import app as alloy_api


app = Flask(__name__)

# ------------------ helpers ------------------

VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

def load_credentials() -> Tuple[str, str, str]:
    load_dotenv()
    base_url = os.getenv("ALLOY_BASE_URL", "https://sandbox.alloy.co/v1").rstrip("/")
    token    = os.getenv("ALLOY_WORKFLOW_TOKEN")
    secret   = os.getenv("ALLOY_WORKFLOW_SECRET")
    if not token or not secret:
        raise RuntimeError("Missing ALLOY_WORKFLOW_TOKEN or ALLOY_WORKFLOW_SECRET in .env")
    return base_url, token, secret

def validate_age_18_120(dob_iso: str) -> bool:
    try:
        dob = datetime.strptime(dob_iso.strip(), "%Y-%m-%d").date()
    except Exception:
        return False
    today = date.today()
    age = (today.year - dob.year) - ((today.month, today.day) < (dob.month, dob.day))
    return 18 <= age <= 120

def build_payload(f) -> dict:
    """Build Alloy payload """
    payload = {
        "name_first":        (f.get("name_first") or "").strip(),
        "name_last":         (f.get("name_last") or "").strip(),
        "birth_date":        (f.get("birth_date") or "").strip(),
        "document_ssn":      (f.get("ssn") or "").strip(),
        "email_address":     (f.get("email") or "").strip().lower(),
        "address_line_1":    (f.get("address_line1") or "").strip(),
        "address_line_2":    (f.get("address_line2") or "").strip() or None,
        "address_city":      (f.get("address_city") or "").strip(),
        "address_state":     (f.get("address_state") or "").strip().upper(),
        "address_postal_code": (f.get("address_postal_code") or "").strip(),
        "address_country_code": "US",
    }
    # drop empty/None
    return {k: v for k, v in payload.items() if v not in ("", None)}

def post_evaluation(base_url: str, auth: Tuple[str,str], payload: dict) -> requests.Response:
    url = f"{base_url}/evaluations"
    headers = {"Content-Type": "application/json"}
    return requests.post(url, auth=auth, headers=headers, json=payload, timeout=30)

def pretty_outcome(summary: dict) -> str:
    raw = (summary.get("outcome") or "").strip().lower()
    if raw in {"approve", "approved"}:
        return "Approved"
    if raw in {"manual review", "manual_review", "review"}:
        return "Manual Review"
    if raw in {"deny", "denied", "declined", "rejected"}:
        return "Denied"
    return summary.get("outcome") or "Unknown"

# ------------------ routes ------------------

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/evaluate")
def evaluate():
    # Validate required fields so we can reduce manual review
    data = request.form
    issues = []

    name_first = (data.get("name_first") or "").strip()
    name_last  = (data.get("name_last") or "").strip()
    birth_date = (data.get("birth_date") or "").strip()
    ssn        = (data.get("ssn") or "").strip()
    email      = (data.get("email") or "").strip()
    state      = (data.get("address_state") or "").strip().upper()
    addr1      = (data.get("address_line1") or "").strip()
    city       = (data.get("address_city") or "").strip()
    postal     = (data.get("address_postal_code") or "").strip()

    if not name_first: issues.append("First name is required.")
    if not name_last:  issues.append("Last name is required.")
    if not validate_age_18_120(birth_date):
        issues.append("DOB must be YYYY-MM-DD and age between 18–120.")
    if not (len(ssn) == 9 and ssn.isdigit()):
        issues.append("SSN must be exactly 9 digits (numbers only).")
    if "@" not in email or "." not in email.split("@")[-1]:
        issues.append("Email must look like name@example.com.")
    if not addr1: issues.append("Address Line 1 is required.")
    if not city:  issues.append("City is required.")
    if state not in VALID_STATES:
        issues.append("State must be a valid 2-letter US code (e.g., NY, CA).")
    if not postal: issues.append("Zip/Postal Code is required.")

    if issues:
        return jsonify({"ok": False, "errors": issues}), 400

    payload = build_payload(data)

    try:
        base_url, token, secret = load_credentials()
        auth = (token, secret)
    except Exception as e:
        return jsonify({"ok": False, "errors": [str(e)]}), 500

    try:
        resp = post_evaluation(base_url, auth, payload)
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "errors": ["Request to Alloy timed out. Try again."]}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"ok": False, "errors": ["Could not connect to Alloy API. Check internet."]}), 503

    if not resp.ok:
        # Return Alloy's error
        try:
            return jsonify({"ok": False, "errors": [resp.json()]}), resp.status_code
        except Exception:
            return jsonify({"ok": False, "errors": [resp.text]}), resp.status_code

    try:
        data = resp.json()
    except ValueError:
        return jsonify({"ok": False, "errors": ["Non-JSON response from Alloy.", resp.text]}), 502

    summary = data.get("summary", {})
    outcome = pretty_outcome(summary)

    # Messages displayed dependent on outcome
    if outcome == "Approved":
        message = "Congratulations! You are approved."
    elif outcome == "Manual Review":
        message = "Your application is under review. Please wait for further updates."
    elif outcome == "Denied":
        message = "Unfortunately, we cannot approve your application at this time."
    else:
        message = f"Unexpected outcome: {outcome}"

    return jsonify({
        "ok": True,
        "outcome": outcome,
        "message": message,
        "evaluation_token": data.get("evaluation_token"),
        "summary": {k: summary.get(k) for k in ("outcome", "score", "tags", "services", "outcome_reasons")}
    })
    
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
