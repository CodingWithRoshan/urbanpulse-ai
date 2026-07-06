from enum import Enum


class Role(str, Enum):
    CITIZEN = "citizen"
    AUTHORITY = "authority"
    ADMIN = "admin"


class ReportStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class Intent(str, Enum):
    FLOOD_RISK = "flood_risk"
    OUTDOOR_SAFETY = "outdoor_safety"
    COMMUTE_DECISION = "commute_decision"


class ComplaintCategory(str, Enum):
    POTHOLE = "Pothole"
    GARBAGE_OVERFLOW = "Garbage Overflow"
    WATERLOGGING = "Waterlogging"
    BROKEN_STREETLIGHT = "Broken Streetlight"
    OTHER = "Other"
