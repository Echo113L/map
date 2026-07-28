"""
Smart CSV parser with encoding detection, structure identification,
and automatic header-row discovery.
"""

import csv
import io
import re
from typing import Tuple, List, Optional
import pandas as pd


def detect_encoding(file_bytes: bytes) -> str:
    """Try common encodings and return the one that works."""
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "latin-1"]
    for enc in encodings:
        try:
            file_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"  # fallback


# ── Header row auto-detection ──────────────────────────────────────────
# Keywords that suggest a column is a *region name* column
REGION_KEYWORDS = [
    "area", "region", "country", "province", "state", "city", "district",
    "nation", "地区", "省份", "国家", "城市", "区域", "省", "市", "县", "区",
    "name", "名称", "地名", "国名",
    "country name", "province name",
]

# Patterns that suggest a column holds a *year*
YEAR_PATTERN = re.compile(r"^(?:.*[^0-9])?(?:19\d{2}|20\d{2})(?:[^0-9].*)?$")

# Row types
_HEADER = 1
_DATA = 2
_METADATA = 3


def _classify_row(row: List[str]) -> int:
    """Classify a CSV row as HEADER, DATA, or METADATA."""
    if not row:
        return _METADATA

    # Blank / empty row → metadata
    cleaned = [c.strip() for c in row]
    if all(c == "" for c in cleaned):
        return _METADATA

    # ── Heuristic 1: header row has year-pattern column names ──
    year_hits = sum(1 for c in cleaned if YEAR_PATTERN.match(c))
    if year_hits >= 2:
        return _HEADER
    if year_hits == 1 and len(cleaned) >= 2:
        return _HEADER

    # ── Heuristic 2: header row has region-like keywords ──
    region_hits = sum(
        1 for c in cleaned for kw in REGION_KEYWORDS if kw.lower() in c.lower()
    )
    if region_hits >= 1 and len(cleaned) >= 2:
        return _HEADER

    # ── Heuristic 3: data rows have mostly numeric cells ──
    numeric = 0
    for c in cleaned:
        c = c.strip().replace(",", "").replace("%", "")
        try:
            float(c)
            numeric += 1
        except (ValueError, TypeError):
            pass

    # If ≥50% of cells are numeric (and ≥2 numeric cells), it's a data row
    if numeric >= 2 and numeric / max(len(cleaned), 1) >= 0.5:
        return _DATA

    # ── Heuristic 4: rows with few cells = metadata ──
    if len(cleaned) == 1:
        return _METADATA

    # ── Heuristic 5: a row with many string cells that DON'T look numeric
    #    could still be a header (e.g., "北京", "天津" → chinese region names)
    string_cells = 0
    for c in cleaned:
        if not c.strip():
            continue
        stripped = c.strip().replace(",", "").replace("%", "")
        try:
            float(stripped)
        except (ValueError, TypeError):
            string_cells += 1
    if string_cells >= 1 and len(cleaned) >= 3 and "年" in "".join(cleaned):
        return _HEADER

    # Default: uncertain → metadata
    return _METADATA


def _score_header_row(row: List[str], row_idx: int) -> int:
    """
    Score how likely this row is the real header.
    Higher score = more likely header.
    """
    score = 0
    cleaned = [c.strip() for c in row]

    # Year columns → strong signal
    year_count = sum(1 for c in cleaned if YEAR_PATTERN.match(c))
    score += year_count * 30

    # Region keywords → signal
    region_hits = sum(
        1 for c in cleaned for kw in REGION_KEYWORDS if kw.lower() in c.lower()
    )
    score += region_hits * 25

    # String-heavy (not numeric) → header-ish
    string_count = 0
    for c in cleaned:
        c2 = c.replace(",", "").replace("%", "").replace("-", "")
        if c2.strip() == "":
            continue
        try:
            float(c2)
        except ValueError:
            string_count += 1
    if string_count >= 2:
        score += 15 * min(string_count, 4)

    # Prefer rows with ≥2 non-empty cells
    non_empty = sum(1 for c in cleaned if c != "")
    score += non_empty * 5

    # Prefer rows later than row 0 slightly (metadata is often at the very top)
    if row_idx > 0:
        score += 10

    # Rows ONLY containing numbers → NOT headers (strong penalty)
    all_numeric = True
    for c in cleaned:
        c2 = c.replace(",", "").replace("%", "").replace("-", "")
        if c2.strip() == "":
            continue
        try:
            float(c2)
        except ValueError:
            all_numeric = False
            break
    if all_numeric:
        score -= 100

    return score


def find_header_row(file_bytes: bytes, encoding: str) -> int:
    """
    Scan a CSV file and find the index (0-based) of the actual header row.

    Handles CSVs with metadata rows before the header, e.g.:
        Row 0: "数据库："
        Row 1: "数据来源：国家统计局"
        Row 2: "地区,2025年,2024年,..."  ← real header
    """
    text = file_bytes.decode(encoding, errors="replace")

    # Split into lines, skip empty lines
    lines = text.splitlines()
    # Filter out completely blank lines but keep their indices
    non_empty_indices = []
    non_empty_lines = []
    for i, line in enumerate(lines):
        if line.strip():
            non_empty_indices.append(i)
            non_empty_lines.append(line)

    if not non_empty_lines:
        return 0

    # Try common delimiters: comma, tab, semicolon
    parsed_rows = []
    for line in non_empty_lines:
        parsed = _try_parse_csv_line(line)
        if parsed is not None:
            parsed_rows.append(parsed)
        else:
            parsed_rows.append(None)

    if not any(parsed_rows):
        return 0

    # Score each row
    best_score = -1
    best_idx = 0
    for i, (orig_idx, parsed) in enumerate(zip(non_empty_indices, parsed_rows)):
        if parsed is None:
            continue
        s = _score_header_row(parsed, i)
        if s > best_score:
            best_score = s
            best_idx = orig_idx

    # Safety: if best score is too low, fall back to row 0
    if best_score < 20:
        return 0

    return best_idx


def _try_parse_csv_line(line: str) -> Optional[List[str]]:
    """Try to parse a line as CSV. Returns list of fields, or None."""
    for delimiter in [",", "\t", ";"]:
        if delimiter in line:
            try:
                reader = csv.reader([line], delimiter=delimiter)
                for row in reader:
                    if row:
                        return row
            except Exception:
                continue

    # No delimiter found — might be a single-column line (metadata)
    if line.strip():
        return [line.strip()]
    return None


# ── Column identification ──────────────────────────────────────────────


def is_year_column(col_name: str) -> bool:
    """Check if a column name looks like a year (e.g. '2023', '2023年', 'year_2023')."""
    name = str(col_name).strip()
    return bool(YEAR_PATTERN.match(name))


def identify_columns(df: pd.DataFrame) -> Tuple[Optional[str], List[str], List[str]]:
    """
    Analyze DataFrame columns and identify:
    - region_col: the column with region/area names
    - year_cols: columns that represent years (multi-year data)
    - data_cols: other numeric data columns

    Returns: (region_col, year_cols, data_cols)
    """
    region_col = None
    year_cols = []
    data_cols = []

    for col in df.columns:
        col_str = str(col).strip()
        col_values = df[col].dropna()

        if len(col_values) == 0:
            continue

        # Check if column name looks like a year
        if is_year_column(col_str):
            year_cols.append(col_str)
            continue

        # Also check if the VALUES in this column look like years
        # (handle case where column name is not a year but values are)
        if is_year_column(str(col_values.iloc[0]) if len(col_values) > 0 else ""):
            year_cols.append(col_str)
            continue

        # Check if this column contains mostly region name strings
        str_count = 0
        total = min(20, len(col_values))
        sample = col_values.head(total)

        for val in sample:
            try:
                float(str(val).replace(",", "").replace("%", ""))
            except (ValueError, TypeError):
                str_count += 1

        str_ratio = str_count / total if total > 0 else 0
        if str_ratio > 0.6:
            region_col = col_str
        else:
            data_cols.append(col_str)

    # If no explicit region column found, use first non-numeric column
    if region_col is None:
        for col in df.columns:
            col_values = df[col].dropna()
            if len(col_values) == 0:
                continue
            try:
                float(str(col_values.iloc[0]).replace(",", "").replace("%", ""))
            except (ValueError, TypeError):
                region_col = str(col).strip()
                break

    # If data_cols have no year cols, treat data_cols as year cols
    if not year_cols and data_cols:
        potential_years = [c for c in data_cols if is_year_column(c)]
        if potential_years:
            year_cols = potential_years
            data_cols = [c for c in data_cols if c not in year_cols]

    return region_col, year_cols, data_cols


# ── Main entry ──────────────────────────────────────────────────────────


def parse_csv(file_bytes: bytes) -> Tuple[pd.DataFrame, str, Optional[str], List[str]]:
    """
    Parse a CSV file with:
    - Automatic encoding detection
    - Automatic header row discovery (handles metadata prefixes)
    - Structure identification (region column, year columns)

    Returns:
        (dataframe, encoding_used, region_column, year_columns)
    """
    encoding = detect_encoding(file_bytes)

    # Find the real header row
    header_row = find_header_row(file_bytes, encoding)

    # Try reading with the detected header position
    for delimiter in [",", ";", "\t"]:
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                delimiter=delimiter,
                dtype=str,
                skiprows=header_row,
                header=0,
            )
            if df.shape[1] >= 2:
                break
        except Exception:
            continue
    else:
        # Last resort: auto-detect delimiter
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                dtype=str,
                skiprows=header_row,
                header=0,
                sep=None,
                engine="python",
            )
        except Exception:
            # Absolute fallback
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=encoding,
                dtype=str,
                header=0,
            )

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Remove unnamed / empty columns
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    df = df.loc[:, df.columns != ""]

    # Drop rows where ALL columns are NaN or empty
    df = df.dropna(how="all")
    df = df[~(df.astype(str).apply(lambda row: row.str.strip().eq("").all(), axis=1))]

    # Identify structure
    region_col, year_cols, data_cols = identify_columns(df)

    # If only one data column and no year col, treat it as the sole data column
    if not year_cols and data_cols:
        year_cols = data_cols

    # Clean region names: strip, remove empty rows
    if region_col:
        df[region_col] = df[region_col].astype(str).str.strip()
        df = df[df[region_col] != ""]
        df = df[df[region_col] != "nan"]
        df = df[df[region_col] != "NaN"]

    return df, encoding, region_col, year_cols
