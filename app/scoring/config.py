"""Time windows, bands and thresholds shared by the scorer and the synthetic generator.

Every threshold lives here so it can be shown, questioned and tuned in one place.
"""
from datetime import datetime, timedelta, timezone

EDT = timezone(timedelta(hours=-4))
HIST_START = datetime(2026, 4, 15, tzinfo=EDT)
WIN_START = datetime(2026, 9, 15, tzinfo=EDT)   # current window = last 30 days
WIN_END = datetime(2026, 10, 15, tzinfo=EDT)    # exclusive
MONTH_STARTS = [datetime(2026, m, 15, tzinfo=EDT) for m in (4, 5, 6, 7, 8, 9, 10)]
HIST_MONTHS = 5

# Band midpoints (annual CAD) used as estimated income. Derived from the band, not personal data.
INCOME_MIDPOINT = {"<20k": 15_000, "20-50k": 35_000, "50-100k": 75_000, "100-200k": 150_000, "200k+": 250_000}

BAND_HIGH, BAND_MEDIUM = 50, 25

# Check thresholds (team spec IN-07 section 5).
INCOME_FIT_FLOOR, INCOME_FIT_SPAN = 0.25, 0.75
HISTORY_FLOOR, HISTORY_SPAN, HISTORY_MIN_BASE = 2.0, 8.0, 50.0
PEER_P95, PEER_P99 = 0.95, 0.99
LOCATION_CITIES, LOCATION_HOURS = 3, 24

# Labels (no points).
STRUCTURING_LOW, STRUCTURING_HIGH, STRUCTURING_MIN = 9_000, 9_999.99, 2
MINIMAL_PLAY_RATIO = 0.10
ESCALATING_MONTHS = 4
NIGHT_SHARE, NIGHT_START_H, NIGHT_END_H, NIGHT_MIN_SESSIONS = 0.60, 0, 4, 3

# Version 1.0 stand-in: a simplified single-deposit threshold rule. Not OLG's actual rule.
V1_THRESHOLD = 10_000

SOURCES = {
    "income": "OLG brief: spend inconsistent with occupation or income",
    "history": "OLG brief: significant behaviour change over time",
    "peer": "OLG brief: activity unlike comparable demographic groups",
    "location": "OLG brief: transactions from unexpected locations; FINTRAC-2024-SB001",
    "structuring": "FINTRAC ML/TF indicators, casinos: multiple transactions just below a reporting threshold",
    "minimal_play": "FINTRAC-2024-SB001: little play before withdrawal",
    "shared": "FINTRAC-2024-SB001: one card or account used by several players",
    "third_party": "FINTRAC ML/TF indicators, casinos: winnings sent to another person's account",
    "safer": "OLG brief: player protection",
}

# Peer check needs enough peers for a percentile to mean anything (amendment to team spec IN-07).
PEER_MIN_GROUP = 20  # owner decision 2026-10-14 19:55 EDT (BUILD-LOG D-2026-10-14-12)
