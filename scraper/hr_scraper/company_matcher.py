import re
from typing import List, Optional
from .models import Company
from .logger import get_logger

logger = get_logger(__name__)

class CompanyMatcher:
    def __init__(self):
        self.legal_form_mappings = {
            'aktien': 'ag',
            'gesellschaft mit beschränkter haftung': 'gmbh',
            'gesellschaft mit beschraenkter haftung': 'gmbh',
            'offene handelsgesellschaft': 'ohg',
            'kommanditgesellschaft': 'kg',
            'eingetragener verein': 'ev',
            'eingetragene genossenschaft': 'eg',
            'gesellschaft bürgerlichen rechts': 'gbr',
            'gesellschaft buergerlichen rechts': 'gbr',
            'partnerschaftsgesellschaft': 'partg',
            'europäische wirtschaftliche interessenvereinigung': 'ewiv',
            'europaeische wirtschaftliche interessenvereinigung': 'ewiv',
            'europäische aktiengesellschaft': 'se',
            'europaeische aktiengesellschaft': 'se',
        }
        self.legal_forms = set(self.legal_form_mappings.values())
        self.noise_words = ['hrb', 'amtsgericht', 'register', 'handelsregister', 'commercial register']

    def normalize_company_name(self, name: str) -> str:
        name_lower = name.lower().strip()
        for full_form, abbrev in self.legal_form_mappings.items():
            name_lower = name_lower.replace(full_form, abbrev)
        for noise in self.noise_words:
            name_lower = name_lower.replace(noise, '')
        name_lower = re.sub(r'[^\w\s]', ' ', name_lower)
        name_lower = re.sub(r'\s+', ' ', name_lower).strip()
        return name_lower

    def find_best_match(self, search_name: str, companies: List[Company], target_registration: Optional[str] = None) -> Optional[Company]:
        logger.info(f"Finding best match for '{search_name}' with registration '{target_registration}'")
        search_name_normalized = self.normalize_company_name(search_name)
        search_words = set(search_name_normalized.split())
        core_search_words = [word for word in search_words if word not in self.legal_forms]

        best_match = None
        best_score = -1

        for company in companies:
            if not company.name:
                continue

            company_normalized = self.normalize_company_name(company.name)
            company_words = set(company_normalized.split())
            
            name_score = 0
            # Exact match
            if search_name_normalized == company_normalized:
                name_score = 100
            # All core words match
            elif core_search_words and all(word in company_normalized for word in core_search_words):
                name_score = 95 + len(core_search_words)
            # Search name in company name
            elif search_name_normalized in company_normalized:
                name_score = 90 + (len(search_name_normalized) / len(company_normalized) * 5)
            # Company name in search name
            elif company_normalized in search_name_normalized:
                name_score = 80 + (len(company_normalized) / len(search_name_normalized) * 5)
            # Common words
            else:
                common_words = search_words.intersection(company_words)
                if common_words:
                    name_score = len(common_words) / max(len(search_words), len(company_words)) * 60
            
            registration_bonus = 0
            if company.hrb:
                if target_registration and company.hrb == target_registration:
                    registration_bonus = 1000
                else:
                    registration_bonus = 100
            else:
                registration_bonus = -50

            final_score = registration_bonus + (name_score * 0.1)
            
            logger.debug(f"Scoring for '{company.name} (HRB: {company.hrb})': name_score={name_score:.1f}, registration_bonus={registration_bonus}, final_score={final_score:.1f}")

            if final_score > best_score:
                best_score = final_score
                best_match = company
        
        if best_match:
            logger.info(f"Best match found: '{best_match.name} (HRB: {best_match.hrb})' with score {best_score:.1f}")
        else:
            logger.warning("No suitable company match found.")
            
        return best_match
