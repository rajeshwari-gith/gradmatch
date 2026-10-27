"""Shared test helpers.

Tests never use the real CSV files. They build small, fixed objects with
the helpers below so results never change when the real data changes.
"""
from datetime import date

import pytest

from gradmatch.models import Program, Scholarship, StudentProfile


# Why a helper: almost every test needs "a normal program". make_program() gives one, and a test
# changes only the field it cares about, so the test shows exactly what it is about.
def make_program(**changes) -> Program:
    """Return a valid Program; pass keyword arguments to change any field."""
    values = dict(
        program_id="P1",
        university="Test University",
        program_name="MS in Computer Science",
        field="Computer Science",
        degree="MS",
        state="MI",
        tuition_in_state=15000.0,
        tuition_out_state=30000.0,
        duration_years=2.0,
        avg_gpa=3.40,
        avg_gre=315,
        acceptance_rate=0.40,
        stipend=0.0,
        min_toefl=80,
        application_deadline=date(2027, 1, 15),
        website="https://example.edu/ms-cs",
    )
    values.update(changes)
    return Program(**values)


def make_profile(**changes) -> StudentProfile:
    """Return a valid StudentProfile; pass keyword arguments to change any field."""
    values = dict(
        degree_sought="MS",
        gpa=3.50,
        field="Computer Science",
        home_state="MI",
        citizenship="US",
        annual_budget=40000.0,
    )
    values.update(changes)
    return StudentProfile(**values)


def make_scholarship(**changes) -> Scholarship:
    """Return a valid Scholarship; pass keyword arguments to change any field."""
    values = dict(
        scholarship_id="S1",
        name="Test Fellowship",
        type="fellowship",
        amount=30000.0,
        degree_levels=("PhD",),
        fields=("Any",),
        min_gpa=3.0,
        citizenship=("US", "PR"),
        states=("Any",),
        special=(),
        deadline=date(2026, 12, 5),
        website="https://example.org/fellowship",
    )
    values.update(changes)
    return Scholarship(**values)


# Fixtures: pytest hands these helpers to a test that asks for them by name.
@pytest.fixture
def program_factory():
    return make_program


@pytest.fixture
def profile_factory():
    return make_profile
