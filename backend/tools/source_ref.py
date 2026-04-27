from dataclasses import dataclass

VALID_SOURCE_TYPES = {"sec", "news", "market", "quant"}


@dataclass
class ParsedSourceRef:
    source_type: str
    identifier: str
    section: str


def format_source_ref(source_type: str, identifier: str, section: str) -> str:
    for part in [source_type, identifier, section]:
        if ":" in part:
            raise ValueError(f"source_ref parts cannot contain ':': '{part}'")
    return f"{source_type}:{identifier}:{section}"


def parse_source_ref(ref: str) -> ParsedSourceRef:
    parts = ref.split(":")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid source_ref '{ref}': expected <type>:<identifier>:<section>"
        )
    return ParsedSourceRef(source_type=parts[0], identifier=parts[1], section=parts[2])


def validate_source_ref(ref: str) -> bool:
    try:
        parsed = parse_source_ref(ref)
        return parsed.source_type in VALID_SOURCE_TYPES
    except ValueError:
        return False


def render_source_ref(ref: str) -> str:
    parsed = parse_source_ref(ref)
    labels = {
        "sec": f"SEC Filing ({parsed.identifier}) — {parsed.section}",
        "news": f"News ({parsed.identifier}) [{parsed.section}]",
        "market": f"Market Data ({parsed.identifier}) — {parsed.section}",
        "quant": f"Computed ({parsed.identifier}) — {parsed.section}",
    }
    return labels.get(parsed.source_type, ref)
