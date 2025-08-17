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

    def _longest_common_subsequence(self, s1: str, s2: str) -> int:
        """
        Calculate the length of the longest common subsequence between two strings.
        This is useful for fuzzy matching of registration numbers that might have slight variations.
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]

    def _normalize_registration_number(self, hrb: str) -> str:
        """Normalize registration number by removing spaces and converting to uppercase."""
        if not hrb:
            return ""
        return re.sub(r'\s+', '', hrb.upper())

    def _calculate_registration_similarity(self, target_registration: str, company_registration: str) -> float:
        """
        Calculate similarity between two registration numbers using multiple strategies.
        Returns a score between 0.0 and 1.0.
        Supports ALL German commercial register formats: HRB, HRA, PR, GnR, VR, GüR, EWIV, SE, SCE, SPE, etc.
        """
        if not target_registration or not company_registration:
            return 0.0
        
        # Normalize both numbers
        target_norm = self._normalize_registration_number(target_registration)
        company_norm = self._normalize_registration_number(company_registration)
        
        # Define all possible German commercial register prefixes
        ALL_REGISTRATION_PREFIXES = [
            'HRB', 'HRA', 'PR', 'GNR', 'VR', 'GÜR', 'EWIV', 'SE', 'SCE', 'SPE'
        ]
        
        # Extract prefix and number parts for all registration types
        prefix_pattern = '|'.join(ALL_REGISTRATION_PREFIXES)
        target_parts = re.match(rf'^({prefix_pattern})\s*(\d+[A-Z]?)$', target_registration.upper())
        company_parts = re.match(rf'^({prefix_pattern})\s*(\d+[A-Z]?)$', company_registration.upper())
        
        if target_parts and company_parts:
            target_prefix = target_parts.group(1)
            target_num = target_parts.group(2)
            company_prefix = company_parts.group(1)
            company_num = company_parts.group(2)
            
            # Check prefix compatibility
            prefix_match = target_prefix == company_prefix
            
            # Exact match (highest priority)
            if target_norm == company_norm:
                return 1.0
            
            # Same prefix, check number similarity
            if prefix_match:
                # Check if one is contained in the other
                if target_num in company_num or company_num in target_num:
                    return 0.9
                
                # Calculate longest common subsequence similarity for numbers
                lcs_length = self._longest_common_subsequence(target_num, company_num)
                max_length = max(len(target_num), len(company_num))
                lcs_similarity = lcs_length / max_length if max_length > 0 else 0.0
                
                # Check for common patterns (e.g., "123 456" vs "123456")
                target_digits = re.sub(r'[^0-9]', '', target_num)
                company_digits = re.sub(r'[^0-9]', '', company_num)
                
                if target_digits == company_digits:
                    # Same digits, different formatting
                    return 0.95
                
                # Calculate digit similarity
                digit_lcs = self._longest_common_subsequence(target_digits, company_digits)
                max_digits = max(len(target_digits), len(company_digits))
                digit_similarity = digit_lcs / max_digits if max_digits > 0 else 0.0
                
                # Return the best similarity score
                return max(lcs_similarity, digit_similarity)
            else:
                # Different prefixes, but check if numbers are similar
                lcs_length = self._longest_common_subsequence(target_num, company_num)
                max_length = max(len(target_num), len(company_num))
                lcs_similarity = lcs_length / max_length if max_length > 0 else 0.0
                
                # Lower score for different prefixes
                return lcs_similarity * 0.7
        
        # Fallback to general string similarity
        lcs_length = self._longest_common_subsequence(target_norm, company_norm)
        max_length = max(len(target_norm), len(company_norm))
        lcs_similarity = lcs_length / max_length if max_length > 0 else 0.0
        
        return lcs_similarity

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
            
            # Enhanced registration number scoring
            registration_bonus = 0
            if target_registration and company.hrb:
                # Calculate similarity using LCS algorithm
                similarity = self._calculate_registration_similarity(target_registration, company.hrb)
                
                if similarity >= 0.95:  # Very high similarity
                    registration_bonus = 1000
                elif similarity >= 0.8:   # High similarity
                    registration_bonus = 800
                elif similarity >= 0.6:   # Medium similarity
                    registration_bonus = 500
                elif similarity >= 0.4:   # Low similarity
                    registration_bonus = 200
                else:
                    registration_bonus = 50  # Minimal bonus for any similarity
                
                logger.debug(f"Registration similarity: {target_registration} vs {company.hrb} = {similarity:.3f} (bonus: {registration_bonus})")
            elif company.hrb:
                # Has registration but no target specified
                registration_bonus = 100
            else:
                # No registration - penalty
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
