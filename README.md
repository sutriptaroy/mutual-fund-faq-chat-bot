# 📊 Mutual Fund FAQ Chatbot (RAG)

A facts-only FAQ assistant for **SBI Mutual Fund** schemes. Every answer cites
**one official source** from AMC / AMFI / SEBI. No investment advice.

## Scope

- **AMC:** SBI Mutual Fund
- **Schemes:**
  - SBI Bluechip Fund (Large Cap)
  - SBI Flexicap Fund
  - SBI Long Term Equity Fund (ELSS)
  - SBI Small Cap Fund
- **Sources:** ~20 official URLs (AMC, AMFI, SEBI) — see `sources.md`.

## Setup

```bash
# 1. Clone and enter the project
cd "new project"

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your OpenAI key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...

# 5. Run the app
streamlit run app.py
```

The first run downloads the official pages, splits them into chunks, embeds them
with `text-embedding-3-small`, and saves a FAISS index to `.faiss_index/`.
Subsequent runs reuse that index.

## Project Layout

```
new project/
├── app.py              # Streamlit UI
├── rag_engine.py       # Loader, splitter, FAISS index, RetrievalQA chain
├── prompts.py          # System prompt + refusal template
├── refusal.py          # Opinion / PII detection
├── sources.py          # List of official URLs
├── sources.md          # Deliverable: human-readable source list
├── sample_qa.md        # Deliverable: sample Q&A
├── requirements.txt
├── .env.example
└── PROJECT_PLAN.md     # Original plan
```

## Rules Enforced

- ✅ Answers are factual, ≤3 sentences, with one source link.
- ✅ Every answer ends with `Last updated from sources: <date>`.
- ❌ Opinion questions ("should I buy?") → polite refusal + educational link.
- ❌ PII (PAN / Aadhaar / OTP / email / phone) is detected and blocked client-side.
- ❌ No return calculations or scheme comparisons.

## Known Limits

- Small corpus (~20 official pages). Anything outside that won't be answered.
- Page contents change; rebuild the index by deleting `.faiss_index/`.
- LLM calls require an OpenAI API key and outbound network access.
- Web pages may render client-side JS that `WebBaseLoader` cannot execute —
  some content may be missing on first load.

## Disclaimer

> Facts-only. No investment advice.
