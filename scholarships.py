from datetime import date

SOON_DAYS = 14


def qualifies(scholarship, student):
    if student["degree"] not in scholarship["degrees"].split(";"):
        return False
    fields = scholarship["fields"].split(";")
    if "Any" not in fields and student["field"] not in fields:
        return False
    return student["gpa"] >= scholarship["min_gpa"]


def find_scholarships(scholarships, student):
    found = [s for s in scholarships if qualifies(s, student)]
    # biggest amount first; same amount goes A-Z by name
    found.sort(key=lambda s: (-s["amount"], s["name"]))
    return found


def today():
    return date.today()


def upcoming(deadlines, today):
    # deadlines is a list of (name, "YYYY-MM-DD") pairs
    coming = []
    for name, day in deadlines:
        days_left = (date.fromisoformat(day) - today).days
        if days_left < 0:
            continue
        coming.append({"name": name, "date": day, "days_left": days_left,
                       "soon": days_left <= SOON_DAYS})
    coming.sort(key=lambda d: d["date"])
    return coming
