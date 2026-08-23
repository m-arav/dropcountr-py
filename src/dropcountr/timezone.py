"""Premise timezone inference and API timestamp correction.

Dropcountr series payloads use the premise's local wall clock but label
instants as UTC (``Z`` / ``+00:00``). This module infers an IANA zone from
the premise address and rewrites those timestamps with the real offset.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, TYPE_CHECKING

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.8
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef, import-not-found]

if TYPE_CHECKING:
    from .models import Address

# Date-only values have no false UTC marker to fix.
_HAS_CLOCK = re.compile(r"T\d{2}:\d{2}")
_OFFSET = re.compile(r"(Z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)

# Single-zone US states / territories. Multi-zone states are refined with
# coordinates when available.
_STATE_TZ = {
    "AL": "America/Chicago",
    "AK": "America/Anchorage",
    "AZ": "America/Phoenix",
    "AR": "America/Chicago",
    "CA": "America/Los_Angeles",
    "CO": "America/Denver",
    "CT": "America/New_York",
    "DE": "America/New_York",
    "DC": "America/New_York",
    "FL": "America/New_York",
    "GA": "America/New_York",
    "HI": "Pacific/Honolulu",
    "ID": "America/Boise",
    "IL": "America/Chicago",
    "IN": "America/Indiana/Indianapolis",
    "IA": "America/Chicago",
    "KS": "America/Chicago",
    "KY": "America/New_York",
    "LA": "America/Chicago",
    "ME": "America/New_York",
    "MD": "America/New_York",
    "MA": "America/New_York",
    "MI": "America/Detroit",
    "MN": "America/Chicago",
    "MS": "America/Chicago",
    "MO": "America/Chicago",
    "MT": "America/Denver",
    "NE": "America/Chicago",
    "NV": "America/Los_Angeles",
    "NH": "America/New_York",
    "NJ": "America/New_York",
    "NM": "America/Denver",
    "NY": "America/New_York",
    "NC": "America/New_York",
    "ND": "America/Chicago",
    "OH": "America/New_York",
    "OK": "America/Chicago",
    "OR": "America/Los_Angeles",
    "PA": "America/New_York",
    "RI": "America/New_York",
    "SC": "America/New_York",
    "SD": "America/Chicago",
    "TN": "America/Chicago",
    "TX": "America/Chicago",
    "UT": "America/Denver",
    "VT": "America/New_York",
    "VA": "America/New_York",
    "WA": "America/Los_Angeles",
    "WV": "America/New_York",
    "WI": "America/Chicago",
    "WY": "America/Denver",
    "PR": "America/Puerto_Rico",
    "VI": "America/St_Thomas",
    "GU": "Pacific/Guam",
    "AS": "Pacific/Pago_Pago",
}

_STATE_NAMES = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "puerto rico": "PR",
}


def _normalize_state(state: Optional[str]) -> Optional[str]:
    if not state:
        return None
    key = state.strip()
    if not key:
        return None
    upper = key.upper()
    if upper in _STATE_TZ:
        return upper
    return _STATE_NAMES.get(key.lower())


def _tz_from_coords(lat: float, lng: float) -> Optional[str]:
    if 18.5 <= lat <= 22.8 and -161.0 <= lng <= -154.0:
        return "Pacific/Honolulu"
    if 51.0 <= lat <= 72.0 and -180.0 <= lng <= -129.0:
        return "America/Anchorage"
    if 17.5 <= lat <= 18.6 and -68.2 <= lng <= -64.4:
        return "America/Puerto_Rico"
    if 31.3 <= lat <= 37.1 and -115.0 <= lng <= -109.0:
        return "America/Phoenix"
    if not (24.0 <= lat <= 49.5 and -125.0 <= lng <= -66.0):
        return None
    if lng <= -114.0:
        return "America/Los_Angeles"
    if lng <= -102.0:
        return "America/Denver"
    if lng <= -87.0:
        return "America/Chicago"
    return "America/New_York"


def _tz_from_state(state: str, lat: Optional[float], lng: Optional[float]) -> Optional[str]:
    if lat is None or lng is None:
        return _STATE_TZ.get(state)
    if state == "FL" and lng <= -87.1:
        return "America/Chicago"
    if state == "ID" and lng <= -116.0 and lat >= 45.5:
        return "America/Los_Angeles"
    if state == "OR" and lng >= -117.0 and lat <= 44.6:
        return "America/Boise"
    if state == "TX" and lng <= -104.5:
        return "America/Denver"
    if state == "KS" and lng <= -101.5:
        return "America/Denver"
    if state in {"NE", "SD", "ND"} and lng <= -101.0:
        return "America/Denver"
    if state == "TN" and lng >= -85.0:
        return "America/New_York"
    if state == "KY" and lng <= -85.5:
        return "America/Chicago"
    if state == "IN" and lng <= -86.9 and lat <= 38.9:
        return "America/Chicago"
    return _STATE_TZ.get(state)


def timezone_for_address(address: Optional[Address]) -> Optional[str]:
    """IANA timezone for a premise address (coords, then US state)."""
    if address is None:
        return None
    state = _normalize_state(address.state)
    if state:
        return _tz_from_state(state, address.lat, address.lng)
    if address.lat is not None and address.lng is not None:
        return _tz_from_coords(address.lat, address.lng)
    return None


def localize_api_time(value: Optional[str], timezone: Optional[str]) -> Optional[str]:
    """Treat an API timestamp's wall clock as ``timezone``, ignoring its offset.

    Intervals (``start/end``) are rewritten on both sides. Date-only values
    are left unchanged.
    """
    if value is None or not timezone:
        return value
    if "/" in value:
        start, end = value.split("/", 1)
        return f"{localize_api_time(start, timezone)}/{localize_api_time(end, timezone)}"
    if not _HAS_CLOCK.search(value):
        return value
    wall = _OFFSET.sub("", value)
    try:
        dt = datetime.fromisoformat(wall)
        aware = dt.replace(tzinfo=ZoneInfo(timezone))
        return aware.isoformat(timespec="seconds")
    except (ValueError, TypeError):
        return value
