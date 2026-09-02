import pytest

from app.services.derived_products import (
    calculate_current_direction,
    calculate_current_speed,
)


def test_current_speed_calculation():
    assert calculate_current_speed(3, 4) == pytest.approx(5)


def test_current_direction_calculation():
    assert calculate_current_direction(1, 0) == pytest.approx(0)
    assert calculate_current_direction(0, 1) == pytest.approx(90)
    assert calculate_current_direction(-1, 0) == pytest.approx(180)
    assert calculate_current_direction(0, -1) == pytest.approx(270)


def test_derived_calculations_preserve_missing_components():
    assert calculate_current_speed(None, 1) is None
    assert calculate_current_direction(1, None) is None