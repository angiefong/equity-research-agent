import requests
from backend.schemas.evidence import EvidenceSpan
from backend.tools.source_ref import format_source_ref

EDGAR_BASE = "https://data.sec.gov"
HEADERS = {"User-Agent": "financial-research-agent contact@example.com"}


def get_cik(ticker: str) -> str:
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    for entry in resp.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"CIK not found for ticker: {ticker}")


def fetch_recent_filings(
    ticker: str,
    forms: list[str] | None = None,
    max_filings: int = 3,
) -> list[EvidenceSpan]:
    if forms is None:
        forms = ["10-K", "10-Q", "8-K"]
    cik = get_cik(ticker)
    url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    recent = resp.json().get("filings", {}).get("recent", {})

    form_list = recent.get("form", [])
    date_list = recent.get("filingDate", [])
    accession_list = recent.get("accessionNumber", [])

    spans = []
    for form, filing_date, accession in zip(form_list, date_list, accession_list):
        if len(spans) >= max_filings:
            break
        if form not in forms:
            continue
        spans.append(EvidenceSpan(
            text=f"{ticker} {form} filed {filing_date} (accession: {accession})",
            source_ref=format_source_ref("sec", f"{ticker}-{form}-{filing_date}", "filing-index"),
            agent_origin="filings",
        ))
    return spans
