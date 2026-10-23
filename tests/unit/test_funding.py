"""Unit tests for funding.py.

Techniques: equivalence partitioning (no stipend / partial / full) and
boundary-value analysis around 0 and around the living cost.
"""
import pytest

from conftest import make_program
from gradmatch.funding import (FULLY_FUNDED, PARTIALLY_FUNDED, SELF_FUNDED,
                               funding_label)

pytestmark = pytest.mark.unit

LIVING_COST = 20000


@pytest.mark.parametrize("stipend, expected", [
    (0, SELF_FUNDED),              # no stipend
    (1, PARTIALLY_FUNDED),         # just above 0
    (19999, PARTIALLY_FUNDED),     # just below living cost
    (20000, FULLY_FUNDED),         # exactly living cost
    (20001, FULLY_FUNDED),         # just above living cost
    (35000, FULLY_FUNDED),
])
def test_funding_label_boundaries(stipend, expected):
    assert funding_label(make_program(stipend=stipend), LIVING_COST) == expected
