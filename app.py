"""Streamlit UI for the Mutual Fund FAQ Bot (facts-only)."""

import streamlit as st

from rag_engine import answer, make_qa_chain
from refusal import contains_pii

st.set_page_config(page_title="Mutual Fund FAQ Bot", page_icon="📊")

st.title("📊 Mutual Fund FAQ Bot")
st.caption("Facts-only. No investment advice.")

with st.expander("Scope & limits", expanded=False):
    st.markdown(
        "- **AMC:** SBI Mutual Fund\n"
        "- **Schemes:** Bluechip, Flexicap, Long Term Equity (ELSS), Small Cap\n"
        "- **Sources:** Official AMC, AMFI, SEBI pages only\n"
        "- **No PII:** Don't share PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers."
    )

st.markdown("**Example questions:**")
st.markdown(
    "- What is the exit load on SBI Flexicap?\n"
    "- Steps to invest in a mutual fund?\n"
    "- What is the ELSS lock-in period?"
)


@st.cache_resource(show_spinner="Building knowledge base from official sources…")
def get_chain():
    return make_qa_chain()


query = st.text_input("Ask a factual question:")

if query:
    if contains_pii(query):
        st.error(
            "Please don't share personal data (PAN, Aadhaar, account number, "
            "OTP, email, phone). I cannot accept or store PII."
        )
    else:
        try:
            chain = get_chain()
            with st.spinner("Looking up official sources…"):
                result = answer(chain, query)

            body = result["body"].lower()
            is_refusal = "not investment advice" in body or "outside my scope" in body
            if is_refusal:
                st.warning(result["body"])
            else:
                st.success(result["body"])

            if result["source"]:
                st.markdown(f"**Source:** [{result['source']}]({result['source']})")
            st.caption(f"Last updated from sources: {result['last_updated']}")

            if result["sources"]:
                with st.expander("Retrieved from (top matches)", expanded=False):
                    for s in result["sources"]:
                        st.markdown(f"- {s}")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.divider()
st.caption("Disclaimer: Facts-only. No investment advice.")
