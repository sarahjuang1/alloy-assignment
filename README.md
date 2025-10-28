# Alloy TAM Assignment – API Integration Script

This project is a Python script that connects to Alloy’s sandbox API to simulate an applicant evaluation flow. It collects user inputs, validates based on the key fields, and submits the data to Alloy to return a simulated decision (allow, review or deny). 

---

## Overview

The goal is to create a script that demonstrates how a client could send applicant data to Alloy, process the API response, and handle different outcomes — Approved, Manual Review, or Denied while minimizing the number of applications that are sent to manual review. 

The script:
1. Collects and validates applicant details  
2. Submits the applicant to Alloy’s sandbox endpoint  
3. Interprets the JSON response and shows a clear decision message

---

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sarahjuang1/alloy-assignment.git
   cd alloy-assignment
