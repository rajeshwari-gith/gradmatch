"""Check that a StudentProfile has valid values before it is used.

validate_profile() returns a list of error messages. An empty list means
the profile is valid. Returning all errors at once lets the UI show the
student everything they need to fix.
"""
from gradmatch.models import StudentProfile

DEGREES = ("BS", "MS", "PhD")
CITIZENSHIP = ("US", "PR", "International")

US_STATES = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
    "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY",
)

GPA_MIN, GPA_MAX = 0.0, 4.0
GRE_MIN, GRE_MAX = 260, 340
TOEFL_MIN, TOEFL_MAX = 0, 120
SAT_MIN, SAT_MAX = 400, 1600
ACT_MIN, ACT_MAX = 1, 36


def validate_profile(profile: StudentProfile) -> list[str]:
    errors = []

    if profile.degree_sought not in DEGREES:
        errors.append("Degree must be BS, MS or PhD.")

    if not GPA_MIN <= profile.gpa <= GPA_MAX:
        errors.append("GPA must be between 0.0 and 4.0.")

    if not profile.field.strip():
        errors.append("Field of study is required.")

    if profile.home_state not in US_STATES:
        errors.append("Home state must be a valid U.S. state code.")

    for state in profile.preferred_states:
        if state not in US_STATES:
            errors.append(f"Preferred state '{state}' is not a valid U.S. state code.")

    if profile.citizenship not in CITIZENSHIP:
        errors.append("Citizenship must be US, PR or International.")

    if profile.annual_budget < 0:
        errors.append("Budget cannot be negative.")

    if profile.gre is not None and not GRE_MIN <= profile.gre <= GRE_MAX:
        errors.append("GRE score must be between 260 and 340.")

    if profile.toefl is not None and not TOEFL_MIN <= profile.toefl <= TOEFL_MAX:
        errors.append("TOEFL score must be between 0 and 120.")

    if profile.sat is not None and not SAT_MIN <= profile.sat <= SAT_MAX:
        errors.append("SAT score must be between 400 and 1600.")

    if profile.act is not None and not ACT_MIN <= profile.act <= ACT_MAX:
        errors.append("ACT score must be between 1 and 36.")

    if profile.citizenship == "International" and profile.toefl is None:
        errors.append("TOEFL score is required for international students.")

    return errors


def is_valid(profile: StudentProfile) -> bool:
    return validate_profile(profile) == []
