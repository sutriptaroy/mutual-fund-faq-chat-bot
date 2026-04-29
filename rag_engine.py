"""RAG engine: loads official URLs, builds FAISS index, answers via OpenAI."""

import os
import socket
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("USER_AGENT", "mf-faq-bot/0.1")

# Some networks (NAT64 / broken IPv6) hang on OpenAI's IPv6 endpoints.
# Force IPv4-only DNS resolution for this process.
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, *args, **kwargs):
    return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)
socket.getaddrinfo = _ipv4_only_getaddrinfo

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA

from prompts import SYSTEM_PROMPT
from sources import URLS

INDEX_DIR = Path(__file__).parent / ".faiss_index"


def _load_documents():
    """Fetch each URL with an explicit HTTP 200 check, then parse with
    WebBaseLoader. Pages that return non-200 are skipped so the corpus
    isn't polluted with 'Page Not Found' boilerplate."""
    import requests

    docs = []
    for url in URLS:
        try:
            head = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (mf-faq-bot)"},
                timeout=15,
                allow_redirects=True,
            )
            if head.status_code != 200:
                print(f"[skip {head.status_code}] {url}")
                continue

            loader = WebBaseLoader(url)
            loader.requests_kwargs = {"timeout": 20}
            loaded = loader.load()
            for d in loaded:
                d.metadata["source"] = url
            docs.extend(loaded)
            print(f"[ok]  {url}")
        except Exception as e:
            print(f"[skip] {url} — {e}")
    return docs


def _make_embeddings():
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    dim_env = os.getenv("OPENAI_EMBEDDING_DIMENSION")
    kwargs = {"model": model}
    if dim_env:
        kwargs["dimensions"] = int(dim_env)
    return OpenAIEmbeddings(**kwargs)


def build_or_load_index():
    embeddings = _make_embeddings()

    if INDEX_DIR.exists():
        print("[index] loading existing FAISS index from disk")
        return FAISS.load_local(
            str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
        )

    print("[index] fetching documents…")
    docs = _load_documents()
    if not docs:
        raise RuntimeError("No documents loaded — check URLs / network.")

    print(f"[index] splitting {len(docs)} documents…")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"[index] {len(chunks)} chunks; embedding via OpenAI…")

    db = FAISS.from_documents(chunks, embeddings)
    print("[index] saving FAISS index to disk")
    db.save_local(str(INDEX_DIR))
    return db


def make_qa_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example → .env and fill it.")

    db = build_or_load_index()
    retriever = db.as_retriever(search_kwargs={"k": 4})

    prompt = PromptTemplate(
        template=SYSTEM_PROMPT,
        input_variables=["context", "question"],
        partial_variables={"today": date.today().isoformat()},
    )

    model_name = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )


import re as _re

# When the question names a specific scheme, prefer that scheme's official
# page as the citation (provided it was actually retrieved). The retriever
# can rank generic pages above scheme pages when scheme pages are JS-heavy
# and have less plain text — this map fixes that for the named-scheme case.
SCHEME_URL_HINTS = [
    (("bluechip", "blue chip", "blue-chip"),
     "https://www.sbimf.com/en-us/equity-schemes/sbi-blue-chip-fund"),
    (("flexicap", "flexi cap", "flexi-cap"),
     "https://www.sbimf.com/en-us/equity-schemes/sbi-flexicap-fund"),
    (("elss", "tax saver", "long term equity", "long-term equity"),
     "https://www.sbimf.com/en-us/equity-schemes/sbi-long-term-equity-fund"),
    (("smallcap", "small cap", "small-cap"),
     "https://www.sbimf.com/en-us/equity-schemes/sbi-small-cap-fund"),
]


def _preferred_source(question: str, retrieved: list[str]) -> str | None:
    """If the question names a specific scheme, prefer that scheme's URL.
    First try the retrieved set; if missing there, fall back to the URL
    list in sources.py — that page is still authoritative for the named
    scheme even when the retriever picked richer-text neighbours instead."""
    q = question.lower()
    for keywords, url in SCHEME_URL_HINTS:
        if any(k in q for k in keywords):
            if url in retrieved:
                return url
            if url in URLS:
                return url
    return None


def _force_real_source(text: str, top_source: str) -> str:
    """Strip any 'Source: ...' and 'Last updated from sources: ...' that the
    LLM may have inlined inside a bullet or paragraph, then re-append them
    as their own clean lines separated by blank lines so Streamlit / Markdown
    renders them as distinct paragraphs."""
    from datetime import date

    today = date.today().isoformat()

    # Remove every occurrence of "Source: <url>" — handles markdown links too.
    text = _re.sub(
        r"Source:\s*(?:\[[^\]]*\]\([^)]+\)|<[^>]+>|\S+)",
        "",
        text,
        flags=_re.IGNORECASE,
    )
    # Remove every occurrence of "Last updated from sources: ..."
    text = _re.sub(
        r"Last updated from sources:\s*[^\n]*",
        "",
        text,
        flags=_re.IGNORECASE,
    )
    # Collapse trailing whitespace per line and shrink runs of blank lines.
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = "\n".join(lines).rstrip()
    cleaned = _re.sub(r"\n{3,}", "\n\n", cleaned)

    src_line = f"Source: {top_source}" if top_source else ""
    suffix_parts = [p for p in (src_line, f"Last updated from sources: {today}") if p]
    suffix = "\n".join(suffix_parts)

    return f"{cleaned}\n\n{suffix}"


def answer(qa_chain, question: str) -> dict:
    result = qa_chain.invoke({"query": question})
    sources = []
    for d in result.get("source_documents", []):
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(src)

    from datetime import date

    chosen = _preferred_source(question, sources) or (sources[0] if sources else "")
    raw = result["result"]
    body = _strip_source_and_date(raw)
    return {
        "answer": _force_real_source(raw, chosen),
        "body": body,
        "source": chosen,
        "last_updated": date.today().isoformat(),
        "sources": sources,
    }


def _strip_source_and_date(text: str) -> str:
    """Return the answer text with any 'Source:' / 'Last updated…' fragments
    removed — used by the UI when rendering the body separately from the
    citation."""
    text = _re.sub(
        r"Source:\s*(?:\[[^\]]*\]\([^)]+\)|<[^>]+>|\S+)",
        "",
        text,
        flags=_re.IGNORECASE,
    )
    text = _re.sub(
        r"Last updated from sources:\s*[^\n]*",
        "",
        text,
        flags=_re.IGNORECASE,
    )
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = "\n".join(lines).rstrip()
    cleaned = _re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


if __name__ == "__main__":
    chain = make_qa_chain()
    out = answer(chain, "What is the ELSS lock-in period?")
    print(out["answer"])
    print("Sources:", out["sources"])
