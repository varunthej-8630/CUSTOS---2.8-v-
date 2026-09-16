# core/constants.py — CUSTOS Global Constants & Enums
from enum import Enum

class SystemMode(str, Enum):
    DAY = "DAY"
    NIGHT = "NIGHT"
    ARMED = "ARMED"
    DISARMED = "DISARMED"

class ZoneType(str, Enum):
    EXCLUSION = "EXCLUSION"
    RESTRICTED = "RESTRICTED"
    CRITICAL = "CRITICAL"
    PERIMETER = "PERIMETER"
    WATCH = "WATCH"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"

class SubjectStatus(str, Enum):
    NORMAL = "NORMAL"
    WATCHLIST = "WATCHLIST"
    SUSPICIOUS = "SUSPICIOUS"
    AUTHORIZED = "AUTHORIZED"
    UNKNOWN = "UNKNOWN"
