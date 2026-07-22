# Apex Bank — Loan Processing Standard Operating Procedure
**Version:** 2.4  |  **Effective:** January 2026  |  **Owner:** Credit Risk

---

## Section 1 — Eligibility Criteria by Applicant Type

### Section 1.1 — Credit Score Requirements

All loan applicants must meet the following minimum credit score thresholds before
a loan can proceed to sanction:

| Applicant Type    | Minimum Credit Score |
|-------------------|----------------------|
| Salaried          | 680                  |
| Self-Employed     | 700                  |
| Government Employee| 680                 |

A credit score below the applicable minimum is grounds for automatic decline.
If the credit bureau is temporarily unavailable, the application must be referred
to the Credit Committee — not declined. See Section 4.1.

### Section 1.2 — Income and Employment Verification

Salaried applicants must provide last 3 months' salary slips and Form 16.
Self-employed applicants must provide 2 years' ITR with CA certification.
Government employees must provide latest pay slip and employment certificate.
Minimum net monthly income: INR 25,000 for all applicant types.

---

## Section 2 — Loan Amount and DTI Thresholds

### Section 2.1 — Debt-to-Income (DTI) Ratio Limits

DTI is calculated as: (all existing EMIs + estimated new EMI) / gross monthly income.

| Applicant Type    | Maximum DTI |
|-------------------|-------------|
| Salaried          | 40%         |
| Self-Employed     | 35%         |
| Government Employee| 45%        |

Applications exceeding the DTI limit must be declined.
Applications within 5% of the DTI limit (borderline) may be referred to committee.

### Section 2.2 — Large Loan Threshold (Committee Review)

Any loan application for an amount exceeding INR 5,000,000 (fifty lakhs) must be
referred to the Credit Committee regardless of credit score or DTI ratio.
The committee meets every Tuesday and Thursday; decisions are issued within 3 working days.

---

## Section 3 — Documentation Requirements

### Section 3.1 — Mandatory Documents for All Applicants

Every applicant must submit valid copies of:
1. PAN card (mandatory, no expiry)
2. Aadhaar card (mandatory, must be linked to mobile)
3. Proof of residence (utility bill, rental agreement, or bank statement, not older than 3 months)

If any mandatory document is invalid or expired, the application must be declined pending
resubmission. The applicant may reapply with valid documents within 90 days.

### Section 3.2 — Property Documents (Home Loans Only)

For home loan applications, the following additional documents are required:
- Sale agreement or property registration copy
- Latest property tax receipt
- Builder NOC (for under-construction properties)

---

## Section 4 — Credit Bureau Integration

### Section 4.1 — Bureau Unavailability Protocol

If the credit bureau (CIBIL or Experian) returns an error or timeout:
- Do NOT decline the application
- Mark credit_score as null and document_bureau_error in the application record
- Set preliminary_decision to "refer_to_committee"
- Include in policy_basis: "Credit bureau temporarily unavailable per Section 4.1"
- The committee will commission a manual bureau check within 2 working days

This protocol applies only to temporary outages. Persistent bureau failures for the
same customer (>2 failed attempts) indicate a potential data issue and require
Branch Manager approval before proceeding.

### Section 4.2 — Interpreting Bureau Results

Credit scores from 300–549: High risk — ineligible (decline per Section 1.1)
Credit scores from 550–679: Medium risk — below threshold for salaried/government
Credit scores from 680–749: Standard — eligible if DTI within limits
Credit scores from 750–900: Low risk — eligible; fast-track processing available

---

## Section 5 — Disbursement and Processing Timelines

### Section 5.1 — Processing SLAs

| Decision Type         | SLA               |
|-----------------------|-------------------|
| Proceed (auto-sanction)| 2 working days   |
| Refer to Committee    | 5 working days    |
| Decline               | Same day          |

All SLA breaches must be reported to the Branch Manager and logged in the
Loan Operations System under the "SLA Breach" queue.

---

## Section 6 — Appeals and Escalation

### Section 6.1 — Customer Appeals

A declined applicant may appeal within 30 days of the decision date.
Appeals are reviewed by the Regional Credit Manager.
The appeal outcome is final and no further escalation is permitted within 90 days.

### Section 6.2 — Internal Escalation

Branch staff may escalate borderline cases to the Zonal Credit Manager if they
believe the auto-decision does not reflect the customer's true creditworthiness.
Supporting documentation must accompany all escalation requests.
