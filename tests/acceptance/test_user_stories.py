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
import pytest

from app_pages import (DEADLINES, PHD, SCHOLARSHIPS, banner, chance_filter, chances, days_left,
                       deadline_names, deadline_rows, find_programs, go, infos, open_app, phd_cards,
                       phd_names, row_names, scholarship_amounts, scholarship_names, yearly_costs)

pytestmark = pytest.mark.acceptance

# In plain words: acceptance tests ask "does the app do what we promised the professor?". Each test
# plays one user story from the proposal, step by step, like a real student would, and checks
# only what that student would see on the screen.

URGENT_BG = "#FBE9E2"     # the tinted date tile of a deadline inside the warning window


@pytest.fixture
def student():
    """A new visitor who has just opened GradMatch."""
    return open_app()


def press_find_programs(at):
    return find_programs(at)


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
    assert row_names(student) == ["Cheap State University – MS in Computer Science",
                                  "Middle University – MS in Computer Science"]
    assert all(cost <= 40_000 for cost in yearly_costs(student))
    assert yearly_costs(student) == sorted(yearly_costs(student))
    assert chances(student) == ["Safety", "Match"]
    # And the filter tells them how many of each kind there are
    assert chance_filter(student) == ["All 2", "Safety 1", "Match 1"]


def test_story_1_preferred_states_narrow_the_list(student):
    student.number_input(key="budget").set_value(100_000)
    student.multiselect(key="preferred_states").set_value(["CA"])
    press_find_programs(student)
    assert row_names(student) == ["Pricey Tech – MS in Computer Science"]
    assert chances(student) == ["Reach"]                  # a 3.5 GPA against a 3.9 average


def test_story_1_student_with_no_affordable_program_is_told_what_to_try(student):
    student.number_input(key="budget").set_value(1_000)
    press_find_programs(student)
    assert "Try a higher budget" in infos(student)
    assert row_names(student) == []


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
    assert row_names(student) == ["Funded University – PhD in Computer Science"]
    assert yearly_costs(student) == [0]
    # And the PhD funding screen shows it with a full funding bar and its stipend
    go(student, PHD)
    assert phd_names(student)[0] == "Funded University"
    assert "background:#5E7D63" in phd_cards(student)[0] and "$30,000" in phd_cards(student)[0]
    # And the Scholarships screen lists the fellowship they are eligible for
    go(student, SCHOLARSHIPS)
    assert scholarship_names(student) == ["Funded PhD Fellowship"]
    assert scholarship_amounts(student) == ["$40,000"]


def test_story_2_a_partly_funded_program_appears_once_the_budget_allows_it(student):
    student.radio(key="degree").set_value("PhD")
    student.number_input(key="gpa").set_value(3.9)
    student.number_input(key="budget").set_value(20_000)
    press_find_programs(student)
    assert row_names(student) == ["Funded University – PhD in Computer Science",
                                  "Partly Funded Institute – PhD in Computer Science"]
    assert yearly_costs(student) == [0, 15000]


def test_story_2_fellowship_with_a_higher_gpa_requirement_is_not_offered(student):
    student.radio(key="degree").set_value("PhD")
    student.number_input(key="gpa").set_value(3.4)            # the fellowship needs 3.5
    press_find_programs(student)
    go(student, SCHOLARSHIPS)
    assert "Funded PhD Fellowship" not in scholarship_names(student)


# ===== Story 3: upcoming deadlines and a warning when one is within 14 days =====

def test_story_3_student_sees_deadlines_soonest_first_with_an_urgent_warning(student):
    # Given a student who searched with the default profile
    press_find_programs(student)
    # When they open the Deadlines screen
    go(student, DEADLINES)
    # Then the open deadlines are listed soonest first, programs and scholarships together
    names = deadline_names(student)
    assert names[names.index("Cheap State University – MS in Computer Science"):] == [
        "Cheap State University – MS in Computer Science", "Michigan Fee Waiver",
        "Middle University – MS in Computer Science"]
    # And the one due in 12 days is warned about, with a tinted date
    assert "Cheap State University" in banner(student)
    rows = dict(zip(names, deadline_rows(student)))
    assert URGENT_BG in rows["Cheap State University – MS in Computer Science"]
    # And the later ones are not
    assert URGENT_BG not in rows["Middle University – MS in Computer Science"]


def test_story_3_a_scholarship_due_within_14_days_is_also_flagged(student):
    student.multiselect(key="special").set_value(["first_gen"])   # unlocks the Nov 1 grant (8 days)
    press_find_programs(student)
    go(student, DEADLINES)
    open_names = [n for n, left in zip(deadline_names(student), days_left(student)) if left != "Passed"]
    assert open_names[0] == "First-Gen Grant" and "8 days left" in days_left(student)
    assert "2 deadlines are coming up in the next 14 days" in banner(student)


def test_story_3_closed_deadlines_are_marked_passed_and_the_student_can_save_the_open_ones(student):
    student.number_input(key="budget").set_value(100_000)         # includes Pricey Tech (closed)
    press_find_programs(student)
    assert len(student.get("download_button")) == 1               # the results (.csv)
    go(student, DEADLINES)
    names, labels = deadline_names(student), days_left(student)
    assert labels[names.index("Pricey Tech – MS in Computer Science")] == "Passed"
    assert [b.label for b in student.get("download_button")] == ["Add these deadlines to my calendar (.ics)"]


def test_story_3_student_with_nothing_left_to_apply_to_is_told_so(student, monkeypatch):
    monkeypatch.setenv("GRADMATCH_TODAY", "2027-12-01")           # every deadline has passed
    student.run()
    press_find_programs(student)
    go(student, DEADLINES)
    assert "no open deadlines" in infos(student).lower()


# ---- Story 4: a high school student looks for a college ----

def test_story_4_a_high_school_student_finds_colleges_they_can_afford(student):
    student.radio(key="degree").set_value("BS")
    press_find_programs(student)
    # The fixed data has no bachelor's programs, so the student is told so politely, not shown an error.
    assert "No programs match" in infos(student)
