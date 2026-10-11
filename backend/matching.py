"""Compatibility and priority scheduling rules used by the allocator."""

# Donor-to-recipient compatibility for ABO and Rh blood groups. This is a teaching
# simulation; clinical tissue typing and jurisdictional allocation policy are out of scope.
COMPATIBLE = {
    "O-": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
    "O+": {"O+", "A+", "B+", "AB+"},
    "A-": {"A-", "A+", "AB-", "AB+"},
    "A+": {"A+", "AB+"},
    "B-": {"B-", "B+", "AB-", "AB+"},
    "B+": {"B+", "AB+"},
    "AB-": {"AB-", "AB+"},
    "AB+": {"AB+"},
}


def is_compatible(donor_type: str, recipient_type: str) -> bool:
    return recipient_type in COMPATIBLE.get(donor_type.upper(), set())


def priority_score(urgency_score: int, waiting_days: int, distance_km: float) -> float:
    """Urgency dominates; waiting time is rewarded and transport distance penalized."""
    return urgency_score * 10.0 + waiting_days * 2.0 - distance_km
