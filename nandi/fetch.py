from functools import lru_cache
import requests
from .sources import normalize_url

@lru_cache(maxsize=64)
def download(url: str, timeout: int = 30):
    url = normalize_url(url)
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "NandiResearch/1.0"})
    response.raise_for_status()
    return response.content, response.headers.get("content-type", ""), response.url

def safe_download(url, timeout=30):
    try:
        body, content_type, final_url = download(url, timeout)
        return body, content_type, final_url, None
    except Exception as exc:
        return b"", "", url, str(exc)

def discover_document_links(data: bytes, base_url: str):
    """Return absolute document links found in an HTML landing page."""
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(data, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        if any(href.lower().split("?")[0].endswith(ext)
               for ext in (".pdf", ".docx", ".txt", ".csv", ".xlsx")):
            if href not in links:
                links.append(href)
    return links
