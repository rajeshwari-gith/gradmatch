from scholarships import find_scholarships
from helpers import make_scholarship, make_student


def test_find_scholarships():
    found = find_scholarships([make_scholarship(name="Small", amount=1000),
                               make_scholarship(name="Big", amount=9000)], make_student())
    assert [s.name for s in found] == ["Big", "Small"]
    same = find_scholarships([make_scholarship(name="Zeta"), make_scholarship(name="Alpha")],
                             make_student())
    assert [s.name for s in same] == ["Alpha", "Zeta"]
