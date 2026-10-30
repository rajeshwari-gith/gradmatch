from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Program:
    university: str
    program: str
    degree: str
    field: str
    state: str
    tuition_in_state: int
    tuition_out_state: int
    living_cost: int
    acceptance_rate: float
    stipend: int
    avg_gre: int
    deadline: date
    website: str


@dataclass(frozen=True)
class Scholarship:
    name: str
    amount: int
    degrees: tuple[str, ...]
    fields: tuple[str, ...]
    min_gpa: float
    citizenship: tuple[str, ...]
    deadline: date
    website: str


@dataclass(frozen=True)
class Student:
    degree: str
    field: str
    gpa: float
    home_state: str
    budget: int
    citizenship: str
    states: tuple[str, ...] = ()
    gre: int | None = None
