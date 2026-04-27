from backend.schemas.evidence import EvidenceSpan


def format_evidence(spans: list[EvidenceSpan], max_spans: int = 30) -> str:
    lines = []
    for i, span in enumerate(spans[:max_spans]):
        lines.append(f"[{i+1}] ({span.source_ref}) {span.text}")
    return "\n".join(lines)
