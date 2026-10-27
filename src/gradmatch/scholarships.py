"""Find the scholarships a student is eligible for.

Eligibility rule (CONTRIBUTING.md) - ALL of these must hold:
  1. profile.degree_sought is in scholarship.degree_levels
  2. profile.field is in scholarship.fields, or fields contains "Any"
  3. profile.gpa >= scholarship.min_gpa
  4. profile.citizenship is in scholarship.citizenship, or it contains "Any"
  5. profile.home_state is in scholarship.states, or it contains "Any"
  6. every item in scholarship.special is in profile.special
"""
# In plain words: a student should only see scholarships they can actually apply for. This
# file checks a student's profile against each scholarship's rules and lists the matches, the
# ones that close soonest first, so the student does not miss a deadline.

from gradmatch.models import Scholarship, StudentProfile

# "Any" in a list means there is no limit on that rule (any field, any state, ...).
ANY = "Any"


# True only when the student meets EVERY rule of the scholarship. Why ALL and not "most":
# a scholarship's rules are hard limits. A US-citizens-only award is still closed to an
# international student with a perfect GPA, and showing it would waste the student's time.
# The tests use a decision table that turns each rule false on its own to prove each one counts.
def is_eligible(profile: StudentProfile, scholarship: Scholarship) -> bool:
    # The rules in the same order as the list at the top of this file.
    # The GPA rule is >=, so meeting the minimum exactly is enough.
    # For "special" (first-gen, women in STEM, ...), the student must have every listed group;
    # having extra groups never hurts.
    return (
        profile.degree_sought in scholarship.degree_levels
        and _allows(scholarship.fields, profile.field)
        and profile.gpa >= scholarship.min_gpa
        and _allows(scholarship.citizenship, profile.citizenship)
        and _allows(scholarship.states, profile.home_state)
        and all(item in profile.special for item in scholarship.special)
    )


# Keep the scholarships the student qualifies for, then sort them: soonest deadline first
# (the most urgent to act on), and for the same deadline the biggest award first.
# Closed scholarships are kept here on purpose; the app hides them using the deadline status.
def eligible_scholarships(profile: StudentProfile,
                          scholarships: list[Scholarship]) -> list[Scholarship]:
    """Return the eligible scholarships, earliest deadline first.

    Scholarships with the same deadline are ordered by amount, highest first.
    """
    matches = [s for s in scholarships if is_eligible(profile, s)]
    # Sort key is (deadline, -amount): the minus sign puts bigger amounts first.
    return sorted(matches, key=lambda s: (s.deadline, -s.amount))


# Small helper shared by the field, citizenship and state rules, so "Any" works the same in all three.
def _allows(allowed: tuple[str, ...], value: str) -> bool:
    """True if the list says "Any" or contains the value."""
    return ANY in allowed or value in allowed
