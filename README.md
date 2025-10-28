# Alloy TAM Assignment

For this assignment, I've created a script that connects to Alloy’s sandbox API to simulate an applicant flow. The script demonstrates how a client could send applicant data to Alloy, process the API response, and show the outcomes — Approved, Manual Review, or Denied. All while minimizing the number of applications that are sent to manual review. 

The script:
1. Collects and validates applicant details  
2. Submits the applicant to Alloy’s sandbox endpoint  
3. Interprets the response and shows a decision message

---

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sarahjuang1/alloy-assignment.git
   cd alloy-assignment
