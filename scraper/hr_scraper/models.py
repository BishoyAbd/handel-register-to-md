from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Document:
    id: str
    text: str
    doc_type: str
    company_name: str
    link_id: str

@dataclass
class Company:
    name: str
    hrb: Optional[str] = None

@dataclass
class EnrichedCompany:
    name: str
    documents: List[Document]
    hrb: Optional[str] = None
