import json
from pathlib import Path
from .models import SourceDocument

DEFAULT_RULES = {
    "agriculture": ["agriculture", "irrigation", "livestock", "food security"],
    "education": ["school", "education", "classroom", "bursary"],
    "health": ["hospital", "clinic", "health", "medical"],
    "water": ["water", "borehole", "sanitation", "sewer"],
    "roads": ["road", "bridge", "transport", "access road"],
}

def load_config(path="config.yaml"):
    p = Path(path)
    if not p.exists():
        return {"fiscal_year_start": 2013, "fiscal_year_end": 2026, "request_timeout_seconds": 30,
                "sources": [], "sector_rules": DEFAULT_RULES}
    try:
        if p.suffix.lower() == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            import yaml
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"Could not load configuration: {exc}") from exc
    data.setdefault("sector_rules", DEFAULT_RULES)
    data.setdefault("sources", [])
    data.setdefault("fiscal_year_start", 2013)
    data.setdefault("fiscal_year_end", 2026)
    data.setdefault("request_timeout_seconds", 30)
    return data

def source_catalog(config):
    return [SourceDocument(str(x.get("name", x.get("url", "Unnamed source"))),
                           str(x.get("url", "")), x.get("sector_hint"))
            for x in config.get("sources", []) if x.get("url")]
