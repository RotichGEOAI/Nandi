from urllib.parse import urlparse
from .models import SourceDocument

def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError("URL is empty")
    parsed = urlparse(value if "://" in value else "https://" + value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Unsupported URL: {value}")
    return parsed.geturl()

def discover_urls(text: str) -> list[str]:
    import re
    candidates = re.findall(r"https?://[^\s<>\"]+", text or "")
    out = []
    for item in candidates:
        try:
            url = normalize_url(item.rstrip(".,);]"))
            if url not in out:
                out.append(url)
        except ValueError:
            pass
    return out

def documents_from_urls(urls):
    docs = []
    for url in urls:
        try:
            norm = normalize_url(url)
            docs.append(SourceDocument(norm, norm))
        except ValueError:
            continue
    return docs
