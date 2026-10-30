# Unit test for admission chance
from programs import chance


def test_chance():
    assert chance(3.5, 0.40) == "Match"
