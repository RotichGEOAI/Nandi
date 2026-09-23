import io
from pathlib import Path
import pandas as pd
import streamlit as st
from nandi.config import load_config, source_catalog
from nandi.sources import documents_from_urls, discover_urls
from nandi.fetch import safe_download, discover_document_links
from nandi.extract import extract_bytes
from nandi.classify import make_classifier
from nandi.parse import parse_document
from nandi.aggregate import aggregate

st.set_page_config(page_title="Nandi Development Intelligence", layout="wide")
st.title("Nandi Development-Earmarked Intelligence")
st.caption("Evidence-first document discovery, extraction, classification and FY 2013–2026 aggregation.")

try:
    config = load_config(st.sidebar.text_input("Config path", "config.yaml"))
except ValueError as exc:
    st.error(str(exc)); st.stop()
start, end = int(config["fiscal_year_start"]), int(config["fiscal_year_end"])
classifier = make_classifier(config.get("sector_rules"))

if "records" not in st.session_state:
    st.session_state.records, st.session_state.docs = [], []

with st.sidebar:
    st.header("Sources")
    pasted = st.text_area("URLs (one per line or pasted text)")
    uploaded = st.file_uploader("Upload PDF, DOCX, HTML or text", accept_multiple_files=True,
                                type=["pdf", "docx", "txt", "csv", "html", "htm"])
    discover = st.button("Process sources", type="primary")

if discover:
    docs = []
    docs.extend(documents_from_urls([line.strip() for line in pasted.splitlines() if line.strip()] + discover_urls(pasted)))
    for item in source_catalog(config):
        if item.url not in {d.url for d in docs}: docs.append(item)
    status = st.status("Processing sources...", expanded=True)
    index = 0
    seen = set()
    while index < len(docs):
        source = docs[index]
        index += 1
        if source.url in seen:
            continue
        seen.add(source.url)
        body, ctype, final_url, error = safe_download(source.url, config["request_timeout_seconds"])
        if error:
            st.session_state.docs.append({"source": source.name, "url": source.url, "status": "error", "error": error})
            status.write(f"❌ {source.url}: {error}"); continue
        result = extract_bytes(body, source.name or final_url, final_url, ctype)
        st.session_state.docs.append(result)
        if "html" in ctype.lower() and not source.url.lower().split("?")[0].endswith((".html", ".htm")):
            for link in discover_document_links(body, final_url):
                docs.append(type(source)(link, link, source.sector_hint))
            if docs:
                status.write(f"🔎 Discovered {len(docs) - index} linked document candidate(s)")
        if result.status == "extracted":
            st.session_state.records.extend(parse_document(result, classifier, start, end))
        status.write(f"{'✅' if result.status == 'extracted' else '⚠️'} {source.name}: {result.status}")
    for file in uploaded or []:
        result = extract_bytes(file.getvalue(), file.name, f"upload://{file.name}", file.type or "")
        st.session_state.docs.append(result)
        if result.status == "extracted":
            st.session_state.records.extend(parse_document(result, classifier, start, end))
    status.update(label="Processing complete", state="complete")

frame, summary = aggregate(st.session_state.records, start, end)
if frame.empty:
    st.info("Add URLs or upload documents to begin. Download and extraction failures will remain visible in status.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Records", len(frame)); c2.metric("Valid amounts", int(frame.amount.notna().sum()))
    c3.metric("Needs review", int((frame.review_flags != "").sum()))
    st.subheader("Development-earmarked totals by sector and FY")
    st.dataframe(summary, use_container_width=True)
    if not summary.empty:
        st.bar_chart(summary.pivot(index="financial_year", columns="sector", values="amount").fillna(0))
    st.subheader("Project records and transparent review flags")
    st.dataframe(frame, use_container_width=True)
    csv = frame.to_csv(index=False).encode()
    st.download_button("Download records CSV", csv, "nandi_records.csv", "text/csv")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="records")
        summary.to_excel(writer, index=False, sheet_name="summary")
    st.download_button("Download workbook", output.getvalue(), "nandi_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with st.expander("Document status and errors"):
    for item in st.session_state.docs:
        if isinstance(item, dict):
            st.error(f"{item['source']}: {item['error']}")
        else:
            st.write({"source": item.source, "status": item.status, "flags": item.review_flags, "error": item.error})
