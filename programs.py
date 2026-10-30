SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"


def yearly_cost(program, home_state):
    if home_state == program["state"]:
        tuition = program["tuition_in_state"]
    else:
        tuition = program["tuition_out_state"]
    return tuition + program["living_cost"]


def check_gpa(gpa):
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def chance(gpa, acceptance_rate):
    if acceptance_rate < 0.10:
        return REACH

    points = 0
    if acceptance_rate >= 0.60:
        points += 2
    elif acceptance_rate >= 0.25:
        points += 1

    if gpa >= 3.7:
        points += 1
    elif gpa < 3.0:
        points -= 1

    if points >= 2:
        return SAFETY
    if points == 1:
        return MATCH
    return REACH


def find_programs(programs, student):
    check_gpa(student["gpa"])
    if student["budget"] < 0:
        raise ValueError("budget can't be negative")

    results = []
    for program in programs:
        if program["degree"] != student["degree"] or program["field"] != student["field"]:
            continue
        if student["states"] and program["state"] not in student["states"]:
            continue
        cost = yearly_cost(program, student["home_state"])
        if cost > student["budget"]:
            continue
        results.append({"program": program, "cost": cost,
                        "chance": chance(student["gpa"], program["acceptance_rate"])})

    # cheapest first; same cost goes A-Z by university
    results.sort(key=lambda result: (result["cost"], result["program"]["university"]))
    return results
