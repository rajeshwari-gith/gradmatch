"""Week 11 - Acceptance testing.

Each test is one user story, written as Given / When / Then, and run on the full app.
"""
from test_system import open_app, search


def test_story_1_michigan_student_finds_affordable_cs_programs():
    """As a Michigan student with $40,000 a year, I want to see the CS programs
    I can afford, so I know where I can apply."""
    # Given a Michigan student with a 3.5 GPA and a $40,000 budget
    at = open_app()
    # When they search for Computer Science
    search(at, field="Computer Science", gpa=3.5, home_state="MI", budget=40000)
    # Then they see GVSU and Wayne State, cheapest first, and nothing over budget
    table = at.dataframe[0].value
    assert list(table["University"]) == ["Grand Valley State University", "Wayne State University"]


def test_story_2_student_sees_their_chance_of_getting_in():
    """As a student, I want to see if a program is a Safety, Match or Reach for my GPA,
    so I can apply to a good mix."""
    # Given a student with a 3.5 GPA and a big budget
    at = open_app()
    # When they search for Computer Science
    search(at, gpa=3.5, budget=100000)
    table = at.dataframe[0].value
    chances = dict(zip(table["University"], table["Chance"]))
    # Then GVSU (avg 3.3) is Safety, Ohio State (avg 3.5) is Match, Stanford (avg 3.8) is Reach
    assert chances["Grand Valley State University"] == "Safety"
    assert chances["Ohio State University"] == "Match"
    assert chances["Stanford University"] == "Reach"


def test_story_3_student_with_a_small_budget_gets_a_clear_message():
    """As a student with a small budget, I want to be told when nothing fits,
    instead of seeing an empty page."""
    # Given a student with only $10,000 a year
    at = open_app()
    # When they search
    search(at, budget=10000)
    # Then they see a message telling them to try a bigger budget
    assert "Try a bigger budget" in at.info[0].value
