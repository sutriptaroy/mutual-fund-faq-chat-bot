"""Official public sources only — AMC (SBI MF), AMFI, SEBI.

Every URL here is verified to return HTTP 200 from the public web. The loader
in rag_engine.py also re-checks status before embedding, so any URL that goes
404 in the future will simply be skipped instead of polluting the index with
'Page Not Found' boilerplate.
"""

URLS = [
    # ---------- SBI Mutual Fund — scheme pages ----------
    "https://www.sbimf.com/en-us/equity-schemes/sbi-blue-chip-fund",
    "https://www.sbimf.com/en-us/equity-schemes/sbi-flexicap-fund",
    "https://www.sbimf.com/en-us/equity-schemes/sbi-long-term-equity-fund",
    "https://www.sbimf.com/en-us/equity-schemes/sbi-small-cap-fund",

    # ---------- SBI MF — investor services / docs ----------
    "https://www.sbimf.com/en-us/factsheet",
    "https://www.sbimf.com/en-us/downloads/forms-and-downloads",
    "https://www.sbimf.com/en-us/investor-services/account-statement",
    "https://www.sbimf.com/en-us/investor-services/tax-information",
    "https://www.sbimf.com/en-us/investor-services/sip",
    "https://www.sbimf.com/en-us/investor-services/exit-load",

    # ---------- AMFI — investor education ----------
    "https://www.amfiindia.com/investor-corner/investor-center/investor-faqs.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/what-are-mutual-funds-new.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/sip-new.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/Riskometer.html",
    "https://www.amfiindia.com/research-information/other-data/categorization-of-mutual-fund-schemes",
    "https://www.amfiindia.com/investor-corner/investor-center/elss-new.html",

    # ---------- SEBI ----------
    "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&type=mutual_funds",
    "https://www.sebi.gov.in/sebi_data/faqfiles/jan-2017/1485345372625.html",
    "https://investor.sebi.gov.in/mf.html",
    "https://investor.sebi.gov.in/mfprocess.html",
    "https://investor.sebi.gov.in/elss.html",
]
