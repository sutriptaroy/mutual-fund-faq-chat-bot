"""Detect PII in questions before they hit the LLM.

Opinion / advice detection is handled by the LLM via the system prompt,
which can judge intent far better than keyword matching.
"""

import re

PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",            # PAN
    r"\b\d{4}\s?\d{4}\s?\d{4}\b",            # Aadhaar
    r"\b\d{9,18}\b",                          # Bank acct / long numeric
    r"\b\d{6}\b",                             # OTP
    r"[\w\.-]+@[\w\.-]+\.\w+",                # email
    r"\+?\d[\d\s\-]{8,}\d",                   # phone
]


def contains_pii(question: str) -> bool:
    return any(re.search(p, question) for p in PII_PATTERNS)
