import base64
import io
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from backend.schemas.evidence import EvidenceSpan
from backend.tools.source_ref import format_source_ref


def compute_returns(ticker: str) -> EvidenceSpan:
    hist = yf.Ticker(ticker).history(period="90d")
    ret = (hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100
    return EvidenceSpan(
        text=f"{ticker} 90-day return: {ret:+.2f}%",
        source_ref=format_source_ref("quant", f"{ticker}-returns", "90d"),
        agent_origin="quant_data",
    )


def compute_volatility(ticker: str) -> EvidenceSpan:
    hist = yf.Ticker(ticker).history(period="30d")
    vol = hist["Close"].pct_change().std() * (252 ** 0.5) * 100
    return EvidenceSpan(
        text=f"{ticker} annualized 30-day volatility: {vol:.1f}%",
        source_ref=format_source_ref("quant", f"{ticker}-volatility", "30d"),
        agent_origin="quant_data",
    )


def fetch_peer_comps(ticker: str, peers: list[str]) -> list[EvidenceSpan]:
    spans = []
    for peer in peers[:3]:
        pe = yf.Ticker(peer).info.get("trailingPE", "N/A")
        spans.append(EvidenceSpan(
            text=f"Peer {peer} trailing P/E: {pe}",
            source_ref=format_source_ref("quant", f"{peer}-peer-comp", "pe-ratio"),
            agent_origin="quant_data",
            confidence=0.9,
        ))
    return spans


def compute_pe_ratio(ticker: str) -> EvidenceSpan:
    pe = yf.Ticker(ticker).info.get("trailingPE", "N/A")
    return EvidenceSpan(
        text=f"{ticker} trailing P/E: {pe}",
        source_ref=format_source_ref("quant", f"{ticker}-ratios", "pe-ratio"),
        agent_origin="quant_interpretation",
    )


def compute_ev_ebitda(ticker: str) -> EvidenceSpan:
    ev_ebitda = yf.Ticker(ticker).info.get("enterpriseToEbitda", "N/A")
    return EvidenceSpan(
        text=f"{ticker} EV/EBITDA: {ev_ebitda}",
        source_ref=format_source_ref("quant", f"{ticker}-ratios", "ev-ebitda"),
        agent_origin="quant_interpretation",
    )


def generate_price_chart(ticker: str) -> EvidenceSpan:
    hist = yf.Ticker(ticker).history(period="90d")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hist.index, hist["Close"], linewidth=1.5, color="#2563eb")
    ax.set_title(f"{ticker} — 90-Day Price", fontsize=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode("utf-8")
    return EvidenceSpan(
        text=f"{ticker} 90-day price chart",
        source_ref=format_source_ref("quant", f"{ticker}-chart", "90d-price"),
        agent_origin="quant_interpretation",
        chart_data=chart_b64,
    )
