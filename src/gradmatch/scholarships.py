"""Find the scholarships a student is eligible for.

Eligibility rule (CONTRIBUTING.md) - ALL of these must hold:
  1. profile.degree_sought is in scholarship.degree_levels
  2. profile.field is in scholarship.fields, or fields contains "Any"
  3. profile.gpa >= scholarship.min_gpa
  4. profile.citizenship is in scholarship.citizenship, or it contains "Any"
  5. profile.home_state is in scholarship.states, or it contains "Any"
  6. every item in scholarship.special is in profile.special
"""
from gradmatch.models import Scholarship, StudentProfile

ANY = "Any"


def is_eligible(profile: StudentProfile, scholarship: Scholarship) -> bool:
    return (
        profile.degree_sought in scholarship.degree_levels
        and _allows(scholarship.fields, profile.field)
        and profile.gpa >= scholarship.min_gpa
        and _allows(scholarship.citizenship, profile.citizenship)
        and _allows(scholarship.states, profile.home_state)
        and all(item in profile.special for item in scholarship.special)
    )


def eligible_scholarships(profile: StudentProfile,
                          scholarships: list[Scholarship]) -> list[Scholarship]:
    """Return the eligible scholarships, earliest deadline first.

    Scholarships with the same deadline are ordered by amount, highest first.
    """
    matches = [s for s in scholarships if is_eligible(profile, s)]
    # Sort key is (deadline, -amount): the minus sign puts bigger amounts first.
    return sorted(matches, key=lambda s: (s.deadline, -s.amount))


def _allows(allowed: tuple[str, ...], value: str) -> bool:
    """True if the list says "Any" or contains the value."""
    return ANY in allowed or value in allowed
