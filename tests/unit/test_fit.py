from gradmatch.fit import MATCH, chance


def test_chance():
    assert chance(3.5, 0.40) == MATCH
