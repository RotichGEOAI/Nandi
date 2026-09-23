import pandas as pd

def records_frame(records):
    return pd.DataFrame([{
        "project": r.project, "amount": r.amount, "financial_year": r.financial_year,
        "sector": r.sector, "source": r.source, "source_url": r.source_url,
        "confidence": r.confidence, "provenance": "; ".join(r.provenance),
        "review_flags": "; ".join(r.review_flags),
        "development_earmarked": r.development_earmarked
    } for r in records])

def aggregate(records, start=2013, end=2026):
    frame = records_frame(records)
    if frame.empty:
        return frame, pd.DataFrame(columns=["financial_year", "sector", "amount"])
    valid = frame[
        frame.amount.notna()
        & frame.financial_year.between(start, end)
        & frame.development_earmarked.ne(False)
    ]
    summary = (valid.groupby(["financial_year", "sector"], as_index=False)["amount"].sum()
               .sort_values(["financial_year", "sector"]))
    return frame, summary
