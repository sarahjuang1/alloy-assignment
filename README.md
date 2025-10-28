# Alloy Sandbox Integration (Python)

This repo contains a Python script that:
1) Collects applicant details from the console,
2) Submits them to Alloy's **Sandbox** API,
3) Prints an approval/deny/manual-review decision based on the API response,
4) Demonstrates *Sandbox Personas* by changing the applicant's last name.

> **Security:** Credentials are loaded from a local `.env` file and **never** committed. The repo includes `.gitignore` that ignores `.env`.

---

## Prerequisites

- **Python 3.9+** installed
- Your **Alloy Sandbox** credentials (workflow token & secret) from the secure email

## Quick Start

```bash
# 1) Clone the repo (after you push it to your GitHub)
git clone <your-repo-url>
cd alloy_tam_assignment

# 2) (Recommended) Create & activate a virtual environment
python3 -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install -r requirements.txt

# 4) Create your .env file from the example and add your credentials
cp .env.example .env
# then edit .env and set ALLOY_WORKFLOW_TOKEN and ALLOY_WORKFLOW_SECRET

# 5) Run the app
python app.py
```

When prompted, enter the applicant details. To trigger **Sandbox Personas**:

- Use any last name normally → default is `"Approved"`
- Use last name **`Review`** → returns `"Manual Review"`
- Use last name **`Deny`** → returns `"Deny"`

## Demo Flow (what to show live)

1. Run `python app.py`
2. Enter a standard applicant (e.g., last name `Smith`) → observe `"Approved"`
3. Run again with last name **`Review`** → observe `"Manual Review"`
4. Run again with last name **`Deny`** → observe `"Deny"`
5. (Optional) Show `GET /parameters` output to discuss payload fields & validations

## Code Walkthrough

- **`app.py`** handles:
  - Input & basic validation (DOB, SSN, email, state code, country)
  - Loading credentials from `.env` (never hard-coded)
  - Calling `GET /parameters` (optional helper to introspect expected fields)
  - Posting the evaluation to `POST /evaluations`
  - Reading `response.json()["summary"]["outcome"]` and printing a message

## Git Hygiene

- `.env` is ignored by git (see `.gitignore`).
- Provide a **`.env.example`** so others know what to set, without leaking secrets.
- Never paste your token/secret into code or README.

## Troubleshooting

- **401/403**: Check your token/secret in `.env` and that you used the **Sandbox** host.
- **400**: Look at the error response; a field may be missing or misnamed. Use `--debug` or select `Show parameters?` to see the API's parameter names.
- **Networking**: Corporate VPN or proxy might block requests; try off VPN or configure proxy.

---
