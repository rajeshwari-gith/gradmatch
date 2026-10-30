"""Week 6 - Data-flow testing.

We follow each variable from where it gets a value (def) to where that value is used (use).
The def-use table for find_programs() and chance() is in docs/control-and-data-flow.md.
These tests cover every def-use pair in it (the "all-uses" criterion).
"""
from gradmatch.fit import MATCH, REACH, SAFETY, chance
from gradmatch.search import find_programs
from helpers import make_program, make_student


# ---- chance(): diff is defined at node 2 and used at nodes 3 and 5 ----

def test_diff_def_2_use_3():
    # diff = 0.30 reaches the check at node 3, which is true.
    assert chance(3.8, 3.5) == SAFETY


def test_diff_def_2_use_5_true():
    # diff = 0.10 passes node 3 (false) and reaches node 5, which is true.
    assert chance(3.6, 3.5) == MATCH


def test_diff_def_2_use_5_false():
    # diff = -0.30 reaches node 5, which is false.
    assert chance(3.2, 3.5) == REACH


# ---- find_programs(): cost is defined at node 6 ----

def test_cost_def_6_use_7_over_budget():
    # The cost (35,000) is used in the budget check at node 7 and the program is dropped.
    assert find_programs([make_program(living_cost=25000)], make_student(budget=34999)) == []


def test_cost_def_6_use_8_stored_in_result():
    # The same cost value must reach the Result made at node 8.
    result = find_programs([make_program(living_cost=25000)], make_student(budget=35000))[0]
    assert result.cost == 35000


# ---- find_programs(): student is defined at the start ----

def test_student_home_state_used_at_node_6():
    # home_state changes the cost: in-state 25,000 vs out-of-state 35,000.
    in_state = find_programs([make_program()], make_student(home_state="MI"))[0]
    out_of_state = find_programs([make_program()], make_student(home_state="OH"))[0]
    assert (in_state.cost, out_of_state.cost) == (25000, 35000)


def test_student_gpa_used_at_node_8():
    # The student's GPA reaches chance() when the result is made.
    result = find_programs([make_program(avg_gpa=3.0)], make_student(gpa=3.9))[0]
    assert result.chance == SAFETY


# ---- find_programs(): results is defined at node 3, added to at node 8, used at node 9 ----

def test_results_def_3_use_9_empty():
    # Nothing is added, so the empty list from node 3 is what gets returned.
    assert find_programs([make_program(field="Data Science")], make_student()) == []


def test_results_def_8_use_9_sorted():
    # Values added at node 8 are sorted at node 9, cheapest first.
    programs = [make_program(university="Dear", living_cost=20000),
                make_program(university="Cheap", living_cost=5000)]
    results = find_programs(programs, make_student())
    assert [r.program.university for r in results] == ["Cheap", "Dear"]
