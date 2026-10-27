"""Acceptance tests: the three user stories from the project specification.

Each test plays one story the way a student would, through the real app, and
checks what the student sees. They use the small fixed data in
tests/data_fixtures.py, so "today" is Oct 24, 2026 and every number is stable.

Story 1  As an undergraduate, I can enter my GPA, budget and preferred states
         and see affordable Master's programs labeled Reach / Match / Safety.
Story 2  As a graduate student, I can find fully funded PhD programs in my
         field and the fellowships I am eligible for.
Story 3  As a student, I can see the upcoming deadlines for my programs and
         scholarships and am warned when one is due within 14 days.
Story 4  As a high school student, I can choose Bachelor's and see colleges I can afford.
"""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.acceptance

# In plain words: acceptance tests ask "does the app do what we promised the professor?". Each test
# plays one user story from the proposal, step by step, like a real student would, and checks
# only what that student would see on the screen.

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")
PROGRAMS, SCHOLARSHIPS, DEADLINES = 0, 1, 2
CORAL, YELLOW = "#F0705F", "#F5C469"


@pytest.fixture
def student():
    """A new visitor who has just opened GradMatch."""
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def press_find_programs(at):
    at.button[0].click().run()
    assert not at.exception
    return at


def cards(at, tab):
    blocks = [m.value for m in at.tabs[tab].markdown if 'class="gm-card"' in m.value]
    return blocks[0] if blocks else ""


def titles(at, tab):
    return re.findall(r'class="gm-title"[^>]*>([^<]+)<', cards(at, tab))


def yearly_costs(at):
    return [int(c.replace(",", "")) for c in
            re.findall(r'gm-stat-value">\$([\d,]+)</div><div class="gm-stat-label">per year',
                       cards(at, PROGRAMS))]


# ===== Story 1: affordable Master's programs labeled Reach / Match / Safety =====

def test_story_1_undergraduate_sees_affordable_masters_programs_with_fit_labels(student):
    # Given an undergraduate from Michigan with a 3.5 GPA and a $40,000 yearly budget
    student.radio(key="degree").set_value("MS")
    student.selectbox(key="field").set_value("Computer Science")
    student.number_input(key="gpa").set_value(3.5)
    student.number_input(key="budget").set_value(40_000)
    # When they press "Find programs"
    press_find_programs(student)
    # Then they see the programs they can afford, cheapest first, each with a fit label
    assert titles(student, PROGRAMS) == ["Cheap State University – MS in Computer Science",
                                         "Middle University – MS in Computer Science"]
    assert all(cost <= 40_000 for cost in yearly_costs(student))
    assert yearly_costs(student) == sorted(yearly_costs(student))
    html = cards(student, PROGRAMS)
    assert ">Safety<" in html and ">Match<" in html
    # And the summary tells them how many of each kind there are
    assert {m.label: m.value for m in student.metric}["Safety / Match / Reach"] == "1 / 1 / 0"


def test_story_1_preferred_states_narrow_the_list(student):
    student.number_input(key="budget").set_value(100_000)
    student.multiselect(key="preferred_states").set_value(["CA"])
    press_find_programs(student)
    assert titles(student, PROGRAMS) == ["Pricey Tech – MS in Computer Science"]
    assert ">Reach<" in cards(student, PROGRAMS)          # a 3.5 GPA against a 3.9 average


def test_story_1_student_with_no_affordable_program_is_told_what_to_try(student):
    student.number_input(key="budget").set_value(1_000)
    press_find_programs(student)
    assert "Try a higher budget" in student.tabs[PROGRAMS].info[0].value
    assert titles(student, PROGRAMS) == []


# ===== Story 2: fully funded PhD programs and fellowships =====

def test_story_2_phd_student_finds_funded_programs_and_a_fellowship(student):
    # Given a PhD applicant in Computer Science with a 3.9 GPA who can pay nothing
    student.radio(key="degree").set_value("PhD")
    student.selectbox(key="field").set_value("Computer Science")
    student.number_input(key="gpa").set_value(3.9)
    student.number_input(key="budget").set_value(0)
    # When they press "Find programs"
    press_find_programs(student)
    # Then they see the fully funded PhD program at no cost
    assert titles(student, PROGRAMS) == ["Funded University – PhD in Computer Science"]
    assert yearly_costs(student) == [0]
    assert "Fully Funded" in cards(student, PROGRAMS)
    # And the Scholarships tab lists the fellowship they are eligible for
    assert titles(student, SCHOLARSHIPS) == ["Funded PhD Fellowship"]
    assert "$40,000" in cards(student, SCHOLARSHIPS)


def test_story_2_a_partly_funded_program_appears_once_the_budget_allows_it(student):
    student.radio(key="degree").set_value("PhD")
    student.number_input(key="gpa").set_value(3.9)
    student.number_input(key="budget").set_value(20_000)
    press_find_programs(student)
    assert titles(student, PROGRAMS) == ["Funded University – PhD in Computer Science",
                                         "Partly Funded Institute – PhD in Computer Science"]
    assert "Partially Funded" in cards(student, PROGRAMS)


def test_story_2_fellowship_with_a_higher_gpa_requirement_is_not_offered(student):
    student.radio(key="degree").set_value("PhD")
    student.number_input(key="gpa").set_value(3.4)            # the fellowship needs 3.5
    press_find_programs(student)
    assert "Funded PhD Fellowship" not in cards(student, SCHOLARSHIPS)


# ===== Story 3: upcoming deadlines and a warning when one is within 14 days =====

def test_story_3_student_sees_deadlines_soonest_first_with_an_urgent_warning(student):
    # Given a student who searched with the default profile
    press_find_programs(student)
    # When they open the Deadlines tab
    html = cards(student, DEADLINES)
    # Then the deadlines are listed soonest first, programs and scholarships together
    assert titles(student, DEADLINES) == ["Cheap State University – MS in Computer Science",
                                          "Michigan Fee Waiver",
                                          "Middle University – MS in Computer Science"]
    # And the one due in 12 days carries a coral warning
    assert f'--chip:{CORAL}">Nov 5, 2026 · 12 days left' in html
    # And the later ones do not
    assert f'--chip:{CORAL}">Jan' not in html


def test_story_3_a_scholarship_due_within_14_days_is_also_flagged(student):
    student.multiselect(key="special").set_value(["first_gen"])   # unlocks the Nov 1 grant (8 days)
    press_find_programs(student)
    html = cards(student, DEADLINES)
    assert f'--chip:{CORAL}">Nov 1, 2026 · 8 days left' in html
    assert titles(student, DEADLINES)[0] == "First-Gen Grant"


def test_story_3_closed_deadlines_are_not_shown_and_the_student_can_save_the_open_ones(student):
    student.number_input(key="budget").set_value(100_000)         # includes Pricey Tech (closed)
    press_find_programs(student)
    assert "Pricey Tech" not in cards(student, DEADLINES)
    assert len(student.get("download_button")) == 2               # results (.csv) and calendar (.ics)


def test_story_3_student_with_nothing_left_to_apply_to_is_told_so(student, monkeypatch):
    monkeypatch.setenv("GRADMATCH_TODAY", "2027-12-01")           # every deadline has passed
    student.run()
    press_find_programs(student)
    assert "no open deadlines" in student.tabs[DEADLINES].info[0].value.lower()


# ---- Story 4: a high school student looks for a college ----

def test_story_4_a_high_school_student_finds_colleges_they_can_afford(student):
    student.radio(key="degree").set_value("BS")
    press_find_programs(student)
    # The fixed data has no bachelor's programs, so the student is told so politely, not shown an error.
    assert any("No programs match" in i.value for i in student.info)
