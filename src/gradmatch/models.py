from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    university: str
    program: str
    field: str
    state: str
    tuition_in_state: int
    tuition_out_state: int
    living_cost: int
    avg_gpa: float
    website: str


@dataclass(frozen=True)
class Student:
    gpa: float
    field: str
    home_state: str
    budget: int
