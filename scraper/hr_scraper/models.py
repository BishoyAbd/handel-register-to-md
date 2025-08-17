from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class DocumentType(Enum):
    """Enum for document types available in the Handelsregister"""
    AD = "AD"      # Aktueller Abdruck (Current Extract)
    CD = "CD"      # Chronologischer Abdruck (Chronological Extract)
    HD = "HD"      # Handelsregister (Commercial Register)
    DK = "DK"      # Dokument (Document)
    UT = "UT"      # Unternehmensregister (Company Register)
    VÖ = "VÖ"      # Veröffentlichungen (Publications)
    SI = "SI"      # Sonstige Informationen (Other Information)

@dataclass
class Document:
    id: str
    text: str
    doc_type: DocumentType
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
