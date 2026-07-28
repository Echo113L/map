"""
Auto-detect which pyecharts map type matches the user's data.
"""

from typing import List, Tuple
from . import mappings


def detect_map_type(region_names: List[str]) -> Tuple[str, str, float]:
    """
    Detect the best matching pyecharts map type for a list of region names.

    Strategy:
    1. Try China province names (Chinese → map='china')
    2. Try world country names in Chinese (translate → map='world')
    3. Try world country names in English (normalize → map='world')

    Returns:
        (map_type, map_label, confidence)
        map_type: the pyecharts maptype parameter (e.g. 'china', 'world')
        map_label: human-readable label (e.g. '中国地图')
        confidence: 0.0 - 1.0 match rate
    """
    if not region_names:
        return "world", "世界地图", 0.0

    clean_names = [n.strip() for n in region_names if n and str(n).strip()]

    # ── Try China provinces ──
    china_hits = 0
    for name in clean_names:
        if name in mappings.CN_PROVINCE_MAP:
            china_hits += 1
    china_confidence = china_hits / len(clean_names)

    if china_confidence >= 0.3:
        return "china", "中国地图 (China)", china_confidence

    # ── Try Chinese → English country names (world map) ──
    cn_en_hits = 0
    for name in clean_names:
        if name in mappings.CN_TO_EN_COUNTRY:
            cn_en_hits += 1
    cn_en_confidence = cn_en_hits / len(clean_names)

    if cn_en_confidence >= 0.3:
        return "world", "世界地图 (World)", cn_en_confidence

    # ── Try English country names directly ──
    en_hits = 0
    for name in clean_names:
        # Check if it matches a standard English country name or a known variation
        if name in mappings.EN_COUNTRY_STANDARD:
            en_hits += 1
        else:
            # Check against the values of CN_TO_EN_COUNTRY (standard English names)
            for std_name in mappings.CN_TO_EN_COUNTRY.values():
                if name.lower() == std_name.lower():
                    en_hits += 1
                    break
    en_confidence = en_hits / len(clean_names)

    if en_confidence >= 0.3:
        return "world", "世界地图 (World)", en_confidence

    # ── Fallback: try world with lower confidence ──
    return "world", "世界地图 (World)", max(cn_en_confidence, en_confidence, 0.0)
