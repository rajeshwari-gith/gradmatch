from gradmatch.cost import tuition_for, yearly_cost
from helpers import make_program


def test_req3_tuition():
    assert tuition_for(make_program(state="MI"), "MI") == 10000
    assert tuition_for(make_program(state="MI"), "OH") == 20000


def test_req3_yearly_cost():
    assert yearly_cost(make_program(), "MI") == 10000 + 15000
