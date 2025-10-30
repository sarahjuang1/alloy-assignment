#!/usr/bin/env python3
"""
Alloy Script Overview
  1) We are asking the applicant for their info
  2) Calls Alloy's Sandbox API
  3) Returns a decision based on response.summary.outcome.

How to run:
  - Add credentials to a local `.env`
  - Run: python app.py
"""

import re
import sys
import json
import base64
from datetime import datetime
from typing import Tuple

import requests
from dotenv import load_dotenv
import os


# --- validation ---

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STATE_RE = re.compile(r"^[A-Z]{2}$")
SSN_RE = re.compile(r"^\d{9}$")
DATE_FMT = "%Y-%m-%d"

def prompt(prompt_text: str, required: bool = True) -> str:
    while True:
        val = input(prompt_text).strip()
        if val or not required:
            return val
        print("This field is required. Please enter a value.")

def validate_dob(dob: str) -> bool:
    try:
        datetime.strptime(dob, DATE_FMT)
        return True
    except ValueError:
        return False

def validate_age_realistic(dob: str) -> bool:
    """
    Validation that the date of birth is realistic. Applicant is between 18 and 120 years old.
    Returns True if valid, False is invalid. We want to reject any unrealistic ages to reduce manual review.
    """
    try:
        dob_dt = datetime.strptime(dob.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False  # invalid or wrongly formatted date

    today = datetime.utcnow().date()
    age = (today.year - dob_dt.year) - ((today.month, today.day) < (dob_dt.month, dob_dt.day))

    return 18 <= age <= 120

def validate_email(email: str) -> bool:
    return EMAIL_RE.match(email) is not None

def validate_state(state: str) -> bool:
    return STATE_RE.match(state) is not None

def validate_ssn(ssn: str) -> bool:
    return SSN_RE.match(ssn) is not None

def ask_yes_no(message: str) -> bool:
    while True:
        ans = input(f"{message} [y/n]: ").strip().lower()
        if ans in ("y","yes"): return True
        if ans in ("n","no"): return False
        print("Please answer y or n.")

# Valid U.S. States
VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

def validate_state_code(state: str) -> bool:
    """
    Returns True if the state is a valid 2-letter US State. Rejects non-valid 2-letter values.
    """
    return state.upper() in VALID_STATES


# Connecting to Alloy’s sandbox API with credentials
# get_parameters() asks Alloy what the field names are
# post_evaluation() sends our applicant info and gets the decision back


def load_credentials() -> Tuple[str, str, str]:
    load_dotenv()
    base_url = os.getenv("ALLOY_BASE_URL", "https://sandbox.alloy.co/v1").rstrip("/")
    token = os.getenv("ALLOY_WORKFLOW_TOKEN")
    secret = os.getenv("ALLOY_WORKFLOW_SECRET")
    if not token or not secret:
        print("ERROR: Missing ALLOY_WORKFLOW_TOKEN or ALLOY_WORKFLOW_SECRET in .env", file=sys.stderr)
        sys.exit(1)
    return base_url, token, secret

def get_parameters(base_url: str, auth: Tuple[str,str]) -> dict:
    url = f"{base_url}/parameters"
    resp = requests.get(url, auth=auth, timeout=20)
    resp.raise_for_status()
    return resp.json()

def post_evaluation(base_url: str, auth: Tuple[str,str], payload: dict) -> requests.Response:
    url = f"{base_url}/evaluations"
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, auth=auth, headers=headers, json=payload, timeout=30)
    return resp

# Main section - running the script
# Includes the welcome message, adds credentials and gets parameters
# Asks for applicant information
# Builds the payload and calls post_evaluation to send data


def main():
    print("\n--- Alloy Sandbox Integration (Python) ---\n")

    base_url, token, secret = load_credentials()
    auth = (token, secret)

    if ask_yes_no("Show parameters from /parameters first? (helpful for debugging)"):
        try:
            params = get_parameters(base_url, auth)
            # print a trimmed view
            print(json.dumps(params, indent=2)[:2000])  # avoid overly long output
            print("(truncated above for brevity)\n")
        except requests.HTTPError as e:
            print(f"Failed to fetch parameters: {e}")

    print("Enter Applicant Details")

# --- Applicant info ---

    name_first = prompt("First Name: ")
    name_last  = prompt("Last Name: ")

    # Date of Birth: require valid format and realistic age (18–120)
    while True:
        birth_date = prompt("Date of Birth (YYYY-MM-DD): ")
        if not validate_dob(birth_date):
            print("Invalid date format. Use YYYY-MM-DD.")
            continue
        if not validate_age_realistic(birth_date):
            print("Date of birth must represent an age between 18 and 120 years old.")
            continue
        break

    # SSN: exactly 9 digits, numbers only
    while True:
        ssn = prompt("SSN (9 digits, no dashes): ")
        if validate_ssn(ssn):
            break
        print("Invalid SSN. Enter exactly 9 digits, numbers only.")

    # Email: basic shape like name@example.com
    while True:
        email = prompt("Email Address: ")
        if validate_email(email):
            break
        print("Invalid email format (e.g., name@example.com).")

    print("\nAddress")
    address_line1 = prompt("Line 1: ")
    address_line2 = prompt("Line 2 (optional): ", required=False)
    address_city  = prompt("City: ")

    # State: must be a real US code
    while True:
        address_state = prompt("State (2-letter code like NY): ").upper()
        if validate_state_code(address_state):
            break
        print("Invalid state. Use a valid two-letter abbreviation (e.g., NY, CA, TX).")

    address_postal_code   = prompt("Zip/Postal Code: ")
    address_country_code  = "US"  # per assignment


    # Construct payload
    payload = {
        "name_first": name_first,
        "name_last": name_last,
        "birth_date": birth_date,
        "document_ssn": ssn,
        "email_address": email,
        "address_line_1": address_line1,
        "address_line_2": address_line2 or None,
        "address_city": address_city,
        "address_state": address_state,
        "address_postal_code": address_postal_code,
        "address_country_code": address_country_code,
    }


    print("\nSubmitting to Alloy Sandbox ...")
    try:
        resp = post_evaluation(base_url, auth, payload)
        # If API returns non-2xx, show the body to help debugging
        if not resp.ok:
            print(f"HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        
        data = resp.json()

        # We accept "Deny" or "Denied"
        raw_outcome = ((data.get("summary") or {}).get("outcome") or "")
        outcome = raw_outcome.strip().lower()

        if outcome in ("approved", "approve"):
            print("Congratulations! You are approved.")
        elif outcome in ("manual review", "manual_review", "review"):
            print("Your application is under review. Please wait for further updates.")
        elif outcome in ("deny", "denied", "rejected", "declined"):
            print("Unfortunately, we cannot approve your application at this time.")
        else:
            print("Received an unexpected response shape (unmapped outcome):", raw_outcome)
            print(json.dumps(data, indent=2))

        if ask_yes_no("\nPrint full JSON response for review?"):
            print(json.dumps(data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Network or request error: {e}")
        print("Tip: Double-check your credentials, network/VPN, and payload fields.")
        sys.exit(2)

if __name__ == "__main__":
    main()
