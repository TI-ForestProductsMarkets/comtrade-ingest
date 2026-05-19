"""
HS commodity reference sets for Comtrade downloads.

Use these as tokens in configs/comtrade.yaml, e.g.
    cmdCode: "WOOD_PANEL"
"""

from __future__ import annotations
from comtrade_ingest.reference.cmdCode_dict import HS_VALID_YEARS as DEFAULT_HS_VALID_YEARS

# Optional local override.
# If you define LOCAL_HS_VALID_YEARS below, it will be used instead of the imported DEFAULT_HS_VALID_YEARS.
# If you want to use the DEFAULT_HS_VALID_YEARS, simply leave LOCAL_HS_VALID_YEARS undefined or empty.

LOCAL_HS_VALID_YEARS: dict[str, tuple[int, int]] = {
    "440112": (2021, 2023),  # Example: Wood panels cmdCode with valid year range
}

try:
    HS_VALID_YEARS = LOCAL_HS_VALID_YEARS
except NameError:
    HS_VALID_YEARS = DEFAULT_HS_VALID_YEARS

# Single wood-sector code.
WOOD_PANEL = [key for key in HS_VALID_YEARS]  

# Multi wood-sector codes.
WOOD_ALL: list[str] = []

def get_hs_valid_year_range(
    cmd_code: str,
    fallback_start: int,
    fallback_end: int,
) -> tuple[int, int]:
    """
    Look up the valid year range for a commodity code.
    
    Returns the year range from LOCAL_HS_VALID_YEARS or fallback.
    Does NOT validate—pipeline.py handles validation with full config context.
    
    Args:
        cmd_code: Commodity code to look up
        fallback_start: Default start year if cmd_code not found
        fallback_end: Default end year if cmd_code not found
    
    Returns:
        Tuple of (start_year, end_year)
    """
    cmd_code = str(cmd_code).strip()

    if cmd_code in LOCAL_HS_VALID_YEARS:
        start_year, end_year = LOCAL_HS_VALID_YEARS[cmd_code]
    else:
        start_year, end_year = fallback_start, fallback_end

    return int(start_year), int(end_year)