"""
Load sample HR policy documents into the ChromaDB vector store.
Run once before starting the server:

    python -m scripts.ingest
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logger import get_logger
from app.db.vector_store import add_documents

logger = get_logger(__name__)

POLICY_DOCS = [
    {
        "id": "leave_001",
        "policy_name": "Leave Policy",
        "section": "Annual Leave",
        "content": (
            "Annual Leave Policy: Full-time employees earn annual leave based on tenure. "
            "Under 2 years: 12 days/year. 2–5 years: 15 days/year. Over 5 years: 18 days/year. "
            "Applications must be submitted at least 3 working days in advance. "
            "Up to 5 unused days may be carried forward to the next calendar year."
        ),
    },
    {
        "id": "leave_002",
        "policy_name": "Leave Policy",
        "section": "Sick Leave",
        "content": (
            "Sick Leave Policy: Employees receive 10 sick leave days per calendar year. "
            "Sick leave covers personal illness or care for an immediate family member. "
            "A medical certificate is required for sick leave exceeding 3 consecutive days. "
            "Sick leave does not carry forward and cannot be combined with annual leave without HR approval."
        ),
    },
    {
        "id": "leave_003",
        "policy_name": "Leave Policy",
        "section": "Casual Leave",
        "content": (
            "Casual Leave Policy: Employees receive 5 casual leave days per year for personal matters. "
            "Apply at least 1 day in advance when possible. "
            "Cannot exceed 2 consecutive days. Unused casual leave lapses at year end and cannot be encashed."
        ),
    },
    {
        "id": "leave_004",
        "policy_name": "Leave Policy",
        "section": "Maternity and Paternity Leave",
        "content": (
            "Maternity Leave: 26 weeks paid leave for the first two children; 12 weeks for subsequent children. "
            "Paternity Leave: 15 days paid leave within 6 months of childbirth. "
            "Adoption Leave: 12 weeks for primary caregivers adopting a child under 3 months. "
            "These are separate from annual, sick, and casual leave balances."
        ),
    },
    {
        "id": "wfh_001",
        "policy_name": "Work From Home Policy",
        "section": "Eligibility and Process",
        "content": (
            "WFH Policy: Employees who have completed the 6-month probation period are eligible. "
            "Up to 2 WFH days per week subject to manager approval. "
            "Requests must be submitted at least 24 hours in advance. "
            "Employees must be reachable on all official channels and may not WFH on days with mandatory in-office meetings."
        ),
    },
    {
        "id": "wfh_002",
        "policy_name": "Work From Home Policy",
        "section": "Equipment and Security",
        "content": (
            "WFH Equipment: The company provides a laptop. Employees must use a secure, stable internet connection. "
            "Company data must not be stored on personal devices. VPN is mandatory for accessing internal systems remotely. "
            "Any company equipment damaged during WFH must be reported to IT immediately."
        ),
    },
    {
        "id": "conduct_001",
        "policy_name": "Code of Conduct",
        "section": "Workplace Behavior",
        "content": (
            "All employees must treat colleagues, clients, and vendors with respect. "
            "Harassment, discrimination, or bullying of any kind is grounds for immediate termination. "
            "Employees must maintain confidentiality of company and client information. "
            "Conflicts of interest must be disclosed to HR immediately. "
            "Unethical behavior should be reported via the official whistleblower channel."
        ),
    },
    {
        "id": "conduct_002",
        "policy_name": "Code of Conduct",
        "section": "Social Media Policy",
        "content": (
            "Employees must not share confidential company information on social media. "
            "Content that damages the company's reputation is prohibited. "
            "Official company statements may only be issued by authorized communications personnel. "
            "Personal social media use during work hours must not interfere with productivity."
        ),
    },
    {
        "id": "benefits_001",
        "policy_name": "Compensation and Benefits",
        "section": "Health Insurance",
        "content": (
            "Health Insurance: Comprehensive coverage for employee and immediate family (spouse + up to 2 children). "
            "Includes hospitalization, outpatient, dental, and vision. Annual sum insured: INR 5,00,000 per family. "
            "Top-up coverage is available at employee expense. Pre-existing conditions covered after 12-month waiting period. "
            "Claims must be submitted within 30 days of treatment."
        ),
    },
    {
        "id": "benefits_002",
        "policy_name": "Compensation and Benefits",
        "section": "Provident Fund and Gratuity",
        "content": (
            "Provident Fund: Company contributes 12% of basic salary; employee contributes 12%. "
            "Gratuity: Payable after 5 years of continuous service at 15 days salary per year of service. "
            "Both are statutory benefits under Indian labor law."
        ),
    },
    {
        "id": "benefits_003",
        "policy_name": "Compensation and Benefits",
        "section": "Performance Bonus",
        "content": (
            "Annual performance bonus ranges from 0–20% of CTC based on individual and company performance. "
            "Bonus cycle: April–March. Payout in May. "
            "Employees must be on rolls as of March 31 to be eligible. "
            "Employees who resign before March 31 forfeit the annual bonus."
        ),
    },
    {
        "id": "perf_001",
        "policy_name": "Performance Review Policy",
        "section": "Review Cycle and Ratings",
        "content": (
            "Annual performance reviews cover April 1–March 31. Mid-year check-ins occur in October. "
            "Ratings (5-point scale): Exceptional, Exceeds Expectations, Meets Expectations, Below Expectations, Unsatisfactory. "
            "Ratings below Meets Expectations trigger a Performance Improvement Plan (PIP)."
        ),
    },
    {
        "id": "perf_002",
        "policy_name": "Performance Review Policy",
        "section": "Promotion Policy",
        "content": (
            "Promotions require 'Exceeds Expectations' rating for two consecutive years and are subject to business need. "
            "Recommendations are made during the annual review cycle and approved by the department head and HR. "
            "Off-cycle promotions require CHRO approval."
        ),
    },
]


def ingest():
    documents = [d["content"] for d in POLICY_DOCS]
    metadatas = [{"policy_name": d["policy_name"], "section": d["section"]} for d in POLICY_DOCS]
    ids = [d["id"] for d in POLICY_DOCS]
    add_documents(documents, metadatas, ids)
    print(f"Ingested {len(POLICY_DOCS)} HR policy documents.")


if __name__ == "__main__":
    ingest()
