"""Shared data models used by every part of GradMatch.

Change this file only when both team members agree (see CONTRIBUTING.md).
"""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class StudentProfile:
    degree_sought: str            # "BS", "MS" or "PhD"
    gpa: float                    # 0.0 - 4.0
    field: str                    # e.g. "Computer Science"
    home_state: str               # 2-letter code, e.g. "MI"
    citizenship: str              # "US", "PR" (permanent resident), "International"
    annual_budget: float          # USD per year, >= 0
    preferred_states: tuple[str, ...] = ()   # empty = any state
    gre: int | None = None        # 260 - 340
    toefl: int | None = None      # 0 - 120
    special: tuple[str, ...] = () # e.g. ("first_gen", "women_stem")
    sat: int | None = None        # 400 - 1600 (bachelor's search)
    act: int | None = None        # 1 - 36 (bachelor's search)


@dataclass(frozen=True)
class Program:
    program_id: str
    university: str
    program_name: str
    field: str
    degree: str                   # "BS", "MS" or "PhD"
    state: str
    tuition_in_state: float       # USD per year
    tuition_out_state: float
    duration_years: float
    avg_gpa: float | None         # None = not published
    avg_gre: int | None
    acceptance_rate: float | None  # 0.0 - 1.0, None = not published
    stipend: float | None         # USD per year, 0 = none, None = not published
    min_toefl: int | None
    application_deadline: date | None  # None = not published, check the program page
    website: str
    source: str = "estimate"      # where the row comes from: "estimate", "official-page" or "ipeds"
    sat_25: int | None = None     # SAT total (reading + math) of the 25th and 75th percentile of enrolled students
    sat_75: int | None = None
    act_25: int | None = None     # ACT composite, 25th and 75th percentile
    act_75: int | None = None


@dataclass(frozen=True)
class Scholarship:
    scholarship_id: str
    name: str
    type: str                     # scholarship | fellowship | assistantship | research | fee_waiver
    amount: float                 # USD (0 if non-monetary)
    degree_levels: tuple[str, ...]  # any of "BS", "MS", "PhD"
    fields: tuple[str, ...]       # ("Any",) or list of fields
    min_gpa: float
    citizenship: tuple[str, ...]  # ("Any",) or subset of US/PR/International
    states: tuple[str, ...]       # ("Any",) or list of state codes
    special: tuple[str, ...]      # () = no special requirement; else ALL listed required
    deadline: date
    website: str
