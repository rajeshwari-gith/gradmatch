from gradmatch.models import Scholarship, Student


def qualifies(scholarship: Scholarship, student: Student) -> bool:
    if student.degree not in scholarship.degrees:
        return False
    if "Any" not in scholarship.fields and student.field not in scholarship.fields:
        return False
    if "Any" not in scholarship.citizenship and student.citizenship not in scholarship.citizenship:
        return False
    return student.gpa >= scholarship.min_gpa


def find_scholarships(scholarships: list[Scholarship], student: Student) -> list[Scholarship]:
    found = [s for s in scholarships if qualifies(s, student)]
    found.sort(key=lambda s: s.amount, reverse=True)
    return found
