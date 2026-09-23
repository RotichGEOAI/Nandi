from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class SourceDocument:
    name: str
    url: str
    sector_hint: Optional[str] = None

@dataclass
class DocumentResult:
    source: str
    url: str
    content_type: str = ""
    text: str = ""
    tables: list[list[list[str]]] = field(default_factory=list)
    status: str = "pending"
    error: Optional[str] = None
    review_flags: list[str] = field(default_factory=list)

@dataclass
class ProjectRecord:
    project: str
    amount: Optional[float]
    financial_year: Optional[int]
    sector: str
    source: str
    source_url: str
    confidence: float
    provenance: list[str] = field(default_factory=list)
    review_flags: list[str] = field(default_factory=list)
    raw_row: dict[str, Any] = field(default_factory=dict)
    development_earmarked: Optional[bool] = None
