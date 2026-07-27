"""
Smart CSV parser with encoding detection and structure identification.
"""

import pandas as pd
import re
from typing import Tuple, List, Optional


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


def is_year_column(col_name: str, values: pd.Series) -> bool:
    """
    Check if a column name looks like a year (e.g., '2023', '2023年', 'year_2023').
    """
    name = str(col_name).strip()
    # Match 4-digit year patterns in the column name
    if re.match(r'^.*(?:19|20)\d{2}.*$', name):
        return True
    return False


def looks_like_year_value(val) -> bool:
    """Check if a value looks like a year number."""
    try:
        v = int(float(val))
        return 1900 <= v <= 2100
    except (ValueError, TypeError):
        return False


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
        if is_year_column(col_str, col_values):
            year_cols.append(col_str)
            continue

        # Check if this column contains mostly region name strings
        str_count = 0
        total = min(20, len(col_values))
        sample = col_values.head(total)

        for val in sample:
            try:
                float(val)
            except (ValueError, TypeError):
                str_count += 1

        # If majority of non-null values are strings, it's likely a region column
        str_ratio = str_count / total if total > 0 else 0
        if str_ratio > 0.6:
            region_col = col_str
        else:
            # It's a numeric data column
            data_cols.append(col_str)

    # If we have data_cols but no year_cols, treat data_cols as year columns
    # if their names look like years
    if not year_cols and data_cols:
        potential_years = [c for c in data_cols if is_year_column(c, df[c])]
        if potential_years:
            year_cols = potential_years
            data_cols = [c for c in data_cols if c not in year_cols]
        else:
            # Single data column case - no year dimension
            pass

    # If still no region_col found, use the first non-numeric column
    if region_col is None:
        for col in df.columns:
            col_values = df[col].dropna()
            if len(col_values) == 0:
                continue
            try:
                float(col_values.iloc[0])
            except (ValueError, TypeError):
                region_col = str(col).strip()
                break

    return region_col, year_cols, data_cols


def parse_csv(file_bytes: bytes) -> Tuple[pd.DataFrame, str, Optional[str], List[str]]:
    """
    Parse a CSV file with automatic encoding detection and structure analysis.

    Args:
        file_bytes: Raw bytes of the CSV file

    Returns:
        (dataframe, encoding_used, region_column, year_columns)
    """
    encoding = detect_encoding(file_bytes)

    # Try reading with detected encoding
    for delimiter in [",", ";", "\t"]:
        try:
            df = pd.read_csv(
                pd.io.common.BytesIO(file_bytes),
                encoding=encoding,
                delimiter=delimiter,
                dtype=str,
            )
            if df.shape[1] >= 2:
                break
        except Exception:
            continue
    else:
        # Last resort
        df = pd.read_csv(
            pd.io.common.BytesIO(file_bytes),
            encoding=encoding,
            dtype=str,
        )

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.match(r'^Unnamed')]

    # Identify structure
    region_col, year_cols, data_cols = identify_columns(df)

    # If only one data column and it's not a year, treat it as a generic data column
    if not year_cols and data_cols:
        year_cols = data_cols

    # Clean region names
    if region_col:
        df[region_col] = df[region_col].astype(str).str.strip()
        # Remove rows with empty region names
        df = df[df[region_col] != ""]
        df = df[df[region_col] != "nan"]

    return df, encoding, region_col, year_cols
