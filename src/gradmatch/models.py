"""The two kinds of data the app works with."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    university: str
    program: str          # e.g. "MS in Computer Science"
    field: str            # "Computer Science" or "Data Science"
    state: str            # 2-letter code, e.g. "MI"
    tuition_in_state: int  # dollars per year
    tuition_out_state: int
    living_cost: int      # dollars per year for rent, food, etc.
    avg_gpa: float        # average GPA of admitted students
    website: str


@dataclass(frozen=True)
class Student:
    gpa: float            # 0.0 to 4.0
    field: str
    home_state: str
    budget: int           # dollars the student can spend per year
