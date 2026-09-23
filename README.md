# Nandi Development-Earmarked Intelligence

A transparent Streamlit pipeline for discovering public documents, extracting tables/text, normalizing project records, classifying sectors, and aggregating development-earmarked amounts by sector and financial year (FY 2013–FY 2026).

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Use **Add URLs** for public PDFs/DOCX/text files or **Upload files** for local documents. The application never marks a document as successfully extracted when the parser returns no usable text; review flags and source provenance remain attached to every record. Rows with explicit recurrent/operational wording are excluded from development totals, while ambiguous rows remain included and retain review metadata.

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit source URLs, sector rules, and fiscal-year bounds. YAML is optional; JSON is also accepted. The default catalog is intentionally small and safe to extend.

## Testing

```bash
pytest -q
python -m py_compile app.py nandi/*.py tests/*.py
```

## Pipeline

`nandi.sources` loads configurable catalogs; `nandi.fetch` downloads with timeouts and caching; `nandi.extract` handles PDF, DOCX, HTML, CSV and text; `nandi.parse` identifies project/amount/FY rows and normalizes currencies, including a development/recurrent review signal; `nandi.classify` assigns sector with confidence and rule provenance; `nandi.aggregate` produces FY/sector summaries. Failed or ambiguous steps are surfaced in the dashboard instead of silently discarded.
