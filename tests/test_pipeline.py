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

def test_budget_table_headers_extract_project_amount_and_explicit_sector():
    doc = DocumentResult(
        "FY 2023/24 ADP",
        "upload://adp.pdf",
        tables=[[
            ["Project Name", "Sector", "Allocated Budget (KES)", "Financial Year"],
            ["Borehole construction", "Water", "1,250,000", "FY 2023/24"],
        ]],
    )
    records = parse_document(doc, make_classifier({"water": ["borehole"]}))
    assert len(records) == 1
    assert records[0].project == "Borehole construction"
    assert records[0].amount == 1250000
    assert records[0].sector == "Water"
    assert records[0].provenance == ["explicit_sector_column"]

def test_multiple_financial_year_documents_aggregate_together():
    classifier = make_classifier({"roads": ["road"], "health": ["clinic"]})
    docs = [
        DocumentResult("ADP FY 2022/23", "upload://adp-2022.pdf",
                       tables=[[["Project Name", "Sector", "Allocated", "FY"],
                                ["Road upgrade", "Roads", "1000000", "FY 2022/23"]]]),
        DocumentResult("ADP FY 2023/24", "upload://adp-2023.pdf",
                       tables=[[["Project Name", "Sector", "Allocated", "FY"],
                                ["Clinic build", "Health", "2000000", "FY 2023/24"]]]),
    ]
    records = [parse_document(doc, classifier)[0] for doc in docs]
    _, summary = aggregate(records)
    assert set(summary.financial_year) == {2022, 2023}
    assert summary.amount.sum() == 3000000
