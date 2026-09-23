import re
from .models import DocumentResult, ProjectRecord

FY_RE = re.compile(r"\b(?:FY\s*)?(20(?:1[3-9]|2[0-6]))(?:\s*/\s*(?:20)?\d{2})?\b", re.I)
AMOUNT_RE = re.compile(r"(?:KES|KSH|KSh|Sh|€|\$)?\s*([\d,]+(?:\.\d+)?)\s*(million|billion|m|bn|k)?", re.I)

def parse_amount(value):
    if value is None: return None
    text = str(value).replace(",", "").strip()
    # Ignore fiscal-year tokens so "FY 2024/25 - KES 2m" yields 2,000,000.
    text = re.sub(r"\bFY\s*20\d{2}\s*/\s*(?:20)?\d{2}\b", "", text, flags=re.I)
    match = re.search(r"(?<!\d)([\d]+(?:\.\d+)?)\s*(million|billion|m|bn|k)?", text, re.I)
    if not match: return None
    amount = float(match.group(1))
    multiplier = {"k": 1e3, "m": 1e6, "million": 1e6, "bn": 1e9, "billion": 1e9}
    return amount * multiplier.get((match.group(2) or "").lower(), 1)

def parse_fy(value):
    match = FY_RE.search(str(value or ""))
    return int(match.group(1)) if match else None

def _header_map(row):
    aliases = {
        "project": ("project", "programme", "program", "activity", "description", "intervention"),
        "amount": ("allocation", "allocated", "budget", "amount", "cost", "estimate", "provision"),
        "sector": ("sector", "department", "directorate", "sub-sector", "subsector"),
        "fy": ("financial year", "fiscal year", "fy", "year"),
    }
    mapped = {}
    for index, value in enumerate(row):
        label = re.sub(r"[^a-z0-9 ]", " ", str(value or "").lower())
        label = re.sub(r"\s+", " ", label).strip()
        for field, names in aliases.items():
            if any(name == label or name in label for name in names):
                mapped[field] = index
                break
    return mapped

def _row_record(row, doc, classify, start=2013, end=2026, columns=None):
    values = [str(x).strip() for x in row if x is not None]
    joined = " | ".join(values)
    columns = columns or {}
    project = values[columns["project"]] if "project" in columns and columns["project"] < len(values) else ""
    amount_cell = values[columns["amount"]] if "amount" in columns and columns["amount"] < len(values) else ""
    fy_cell = values[columns["fy"]] if "fy" in columns and columns["fy"] < len(values) else ""
    sector_cell = values[columns["sector"]] if "sector" in columns and columns["sector"] < len(values) else ""
    fy = parse_fy(fy_cell or joined) or parse_fy(doc.source)
    amount = parse_amount(amount_cell) if amount_cell else None
    if amount is None:
        # Prefer currency/unit-marked cells, then the largest numeric cell.
        candidates = [parse_amount(x) for x in values if re.search(
            r"(?:kes|ksh|million|billion|\b(?:bn|m|k)\b)", x, re.I)]
        if candidates:
            amount = candidates[0]
        else:
            numeric = [parse_amount(x) for x in values if parse_amount(x) is not None and not parse_fy(x)]
            amount = max(numeric) if numeric else None
    if not project:
        project = next((x for x in values if len(x) > 4 and not parse_fy(x) and parse_amount(x) is None), "")
    flags = []
    if not project: flags.append("missing_project_name")
    if amount is None: flags.append("missing_or_unparseable_amount")
    if fy is None or not start <= fy <= end: flags.append("missing_or_out_of_range_fy")
    lowered = joined.lower()
    development_earmarked = None
    if re.search(r"\b(recurrent|operations?|administration|personnel)\b", lowered):
        development_earmarked = False
        flags.append("recurrent_or_operational_wording")
    elif re.search(r"\b(development|capital|infrastructure|project)\b", lowered):
        development_earmarked = True
    if sector_cell and sector_cell.lower() not in {"sector", "n/a", "na", "-"}:
        sector, confidence, provenance = sector_cell, 1.0, ["explicit_sector_column"]
    else:
        sector, confidence, provenance = classify(project + " " + joined)
    if confidence < 0.6: flags.append("low_sector_confidence")
    return ProjectRecord(project or "Unidentified project", amount, fy, sector, doc.source, doc.url,
                         confidence, provenance, flags, {"values": values}, development_earmarked)

def parse_document(doc: DocumentResult, classify, start=2013, end=2026):
    records = []
    for table in doc.tables:
        columns = _header_map(table[0]) if table else {}
        start_row = 1 if len(columns) >= 2 else 0
        for row in table[start_row:]:
            if row: records.append(_row_record(row, doc, classify, start, end, columns))
    if not records:
        for line in doc.text.splitlines():
            if parse_amount(line) is not None or parse_fy(line) is not None:
                records.append(_row_record([line], doc, classify, start, end))
    return records
