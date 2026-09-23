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

def _row_record(row, doc, classify, start=2013, end=2026):
    values = [str(x).strip() for x in row if x is not None]
    joined = " | ".join(values)
    fy = parse_fy(joined)
    amount = parse_amount(joined)
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
    sector, confidence, provenance = classify(project + " " + joined)
    if confidence < 0.6: flags.append("low_sector_confidence")
    return ProjectRecord(project or "Unidentified project", amount, fy, sector, doc.source, doc.url,
                         confidence, provenance, flags, {"values": values}, development_earmarked)

def parse_document(doc: DocumentResult, classify, start=2013, end=2026):
    records = []
    for table in doc.tables:
        for row in table:
            if row: records.append(_row_record(row, doc, classify, start, end))
    if not records:
        for line in doc.text.splitlines():
            if parse_amount(line) is not None or parse_fy(line) is not None:
                records.append(_row_record([line], doc, classify, start, end))
    return records
