from nandi.classify import make_classifier
from nandi.parse import parse_amount, parse_fy, parse_document
from nandi.aggregate import aggregate
from nandi.models import DocumentResult

def test_amount_and_fy():
    assert parse_amount("KES 1.5 million") == 1500000
    assert parse_amount("FY 2024/25 - KES 2m") == 2000000
    assert parse_fy("FY 2024/25") == 2024

def test_classification_provenance():
    classifier = make_classifier({"health": ["clinic", "hospital"], "roads": ["road"]})
    sector, confidence, provenance = classifier("New clinic and hospital")
    assert sector == "health" and confidence == 1.0 and provenance

def test_parse_and_aggregate():
    doc = DocumentResult("x", "https://x", text="", tables=[[["Road upgrade", "KES 2,000,000", "FY 2024/25"]]])
    records = parse_document(doc, make_classifier({"roads": ["road"]}))
    frame, summary = aggregate(records)
    assert len(frame) == 1 and summary.iloc[0]["amount"] == 2000000

def test_recurrent_rows_are_not_in_development_summary():
    doc = DocumentResult("x", "https://x", tables=[[["Routine administration", "KES 500,000", "FY 2024/25"]]])
    records = parse_document(doc, make_classifier({"general": ["administration"]}))
    frame, summary = aggregate(records)
    assert frame.iloc[0]["development_earmarked"] == False
    assert summary.empty
