"""
Fuzzy matching engine for region names → pyecharts standard names.
"""

from typing import List, Dict, Tuple, Optional
from rapidfuzz import process, fuzz

from . import mappings


def standardize_region_name(name: str, map_type: str) -> Tuple[str, float]:
    """
    Convert a single region name to pyecharts standard name.

    Args:
        name: Raw region name from CSV
        map_type: pyecharts map type ('china' or 'world')

    Returns:
        (standardized_name, confidence)
        confidence: 0.0 - 100.0 (rapidfuzz score)
    """
    name = str(name).strip()
    if not name:
        return name, 0.0

    if map_type == "china":
        return _match_china(name)
    elif map_type == "world":
        return _match_world(name)
    else:
        return name, 100.0


def _match_china(name: str) -> Tuple[str, float]:
    """Match a name to China province standard name."""
    # 1. Exact match in variant map
    if name in mappings.CN_PROVINCE_MAP:
        return mappings.CN_PROVINCE_MAP[name], 100.0

    # 2. Case-insensitive exact match
    name_lower = name.lower()
    for variant, standard in mappings.CN_PROVINCE_MAP.items():
        if variant.lower() == name_lower:
            return standard, 100.0

    # 3. Check if name already is a standard name (after removing suffix)
    for standard in mappings.CHINA_STANDARD_NAMES:
        if name == standard:
            return standard, 100.0
        # e.g., "北京省" → if stripped suffix matches standard name
        for suffix in ["省", "市", "自治区", "特别行政区"]:
            if name.endswith(suffix):
                stripped = name[:-len(suffix)]
                if stripped in mappings.CHINA_STANDARD_NAMES:
                    return stripped, 95.0

    # 4. Fuzzy match against variant keys
    variants = list(mappings.CN_PROVINCE_MAP.keys())
    result = process.extractOne(name, variants, scorer=fuzz.ratio, score_cutoff=50)
    if result:
        matched_variant, score, _ = result
        return mappings.CN_PROVINCE_MAP[matched_variant], score

    # 5. Fuzzy match against standard names directly
    result = process.extractOne(name, mappings.CHINA_STANDARD_NAMES, scorer=fuzz.ratio, score_cutoff=50)
    if result:
        matched, score, _ = result
        return matched, score

    return name, 0.0


def _match_world(name: str) -> Tuple[str, float]:
    """Match a name to world country standard English name."""
    # 1. Exact match in Chinese→English map
    if name in mappings.CN_TO_EN_COUNTRY:
        return mappings.CN_TO_EN_COUNTRY[name], 100.0

    # 2. Exact match in English standard map
    if name in mappings.EN_COUNTRY_STANDARD:
        return mappings.EN_COUNTRY_STANDARD[name], 100.0

    # 3. Case-insensitive match against Chinese→English values
    name_lower = name.lower()
    for standard_en in mappings.CN_TO_EN_COUNTRY.values():
        if standard_en.lower() == name_lower:
            return standard_en, 100.0

    # 4. Case-insensitive match against English standard values
    for standard_en in mappings.EN_COUNTRY_STANDARD.values():
        if standard_en.lower() == name_lower:
            return standard_en, 100.0

    # 5. Case-insensitive match against Chinese→English keys
    for cn_name, en_name in mappings.CN_TO_EN_COUNTRY.items():
        if cn_name.lower() == name_lower:
            return en_name, 100.0

    # 6. Fuzzy match against Chinese→English keys
    cn_keys = list(mappings.CN_TO_EN_COUNTRY.keys())
    result = process.extractOne(name, cn_keys, scorer=fuzz.ratio, score_cutoff=55)
    if result:
        matched, score, _ = result
        return mappings.CN_TO_EN_COUNTRY[matched], score

    # 7. Fuzzy match against English standard values (for already-English names)
    en_standards = list(set(mappings.CN_TO_EN_COUNTRY.values()))
    result = process.extractOne(name, en_standards, scorer=fuzz.ratio, score_cutoff=60)
    if result:
        matched, score, _ = result
        return matched, score

    # 8. Fuzzy match against English standard keys
    en_keys = list(mappings.EN_COUNTRY_STANDARD.keys())
    result = process.extractOne(name, en_keys, scorer=fuzz.ratio, score_cutoff=60)
    if result:
        matched, score, _ = result
        return mappings.EN_COUNTRY_STANDARD[matched], score

    return name, 0.0


def match_all(
    region_names: List[str],
    map_type: str,
    confidence_threshold: float = 80.0,
) -> Tuple[Dict[str, str], List[Dict]]:
    """
    Match all region names to pyecharts standard names.

    Args:
        region_names: List of raw region names
        map_type: pyecharts map type
        confidence_threshold: below this, the match is considered "uncertain"

    Returns:
        (matched_dict, uncertain_list)
        matched_dict: {original_name: standard_name}
        uncertain_list: [{original, suggested, confidence, alternatives}, ...]
    """
    matched = {}
    uncertain = []

    for name in region_names:
        name = str(name).strip()
        if not name or name.lower() == "nan":
            continue

        std_name, confidence = standardize_region_name(name, map_type)
        matched[name] = std_name

        if confidence < confidence_threshold:
            # Get top alternatives for user to pick from
            alternatives = get_alternatives(name, map_type, top_n=5)
            uncertain.append({
                "original": name,
                "suggested": std_name,
                "confidence": round(confidence, 1),
                "alternatives": alternatives,
            })

    return matched, uncertain


def get_alternatives(name: str, map_type: str, top_n: int = 5) -> List[Tuple[str, float]]:
    """Get top-N alternative matches for a region name."""
    name = str(name).strip()

    if map_type == "china":
        candidates = list(mappings.CN_PROVINCE_MAP.items())
        # (display_name, standard_name) pairs, unique by standard_name
        seen = set()
        unique = []
        for variant, standard in candidates:
            if standard not in seen:
                seen.add(standard)
                unique.append((variant, standard))
        choices = [standard for _, standard in unique]
        results = process.extract(name, choices, scorer=fuzz.ratio, limit=top_n)
        return [(match, score) for match, score, _ in results]

    elif map_type == "world":
        choices = list(set(mappings.CN_TO_EN_COUNTRY.values()))
        results = process.extract(name, choices, scorer=fuzz.ratio, limit=top_n)
        return [(match, score) for match, score, _ in results]

    else:
        return []
