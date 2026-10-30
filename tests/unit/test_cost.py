from tests.helpers import make_program
from programs import yearly_cost


def test_yearly_cost():
    assert yearly_cost(make_program(state="MI"), "MI") == 10000 + 15000
    assert yearly_cost(make_program(state="MI"), "OH") == 20000 + 15000
