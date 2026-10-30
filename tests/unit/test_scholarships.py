# Unit test for scholarships
from scholarships import find_scholarships
from tests.helpers import make_scholarship, make_student


def test_find_scholarships():
    found = find_scholarships([make_scholarship(name="Small", amount=1000),
                               make_scholarship(name="Zeta"), make_scholarship(name="Alpha"),
                               make_scholarship(name="PhD only", degrees="PhD")], make_student())
    assert [s["name"] for s in found] == ["Alpha", "Zeta", "Small"]
