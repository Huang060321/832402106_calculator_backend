import math

import pytest

from app.services.calculator import CalculationError, calculate


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("12+8", 20),
        ("1+2*3", 7),
        ("(1+2)*3", 9),
        ("10/2+7", 12),
        ("8-3*2", 2),
        ("-5+8", 3),
        ("3*-2", -6),
        ("0.1+0.2", 0.3),
        ("2^3^2", 512),
        ("sqrt(81)", 9),
        ("abs(-4)", 4),
    ],
)
def test_valid_expressions(expression, expected):
    assert calculate(expression) == pytest.approx(expected)


def test_constants_and_functions():
    assert calculate("sin(pi/2)") == pytest.approx(1)
    assert calculate("ln(e)") == pytest.approx(1)


@pytest.mark.parametrize(
    "expression",
    ["", "1/0", "1++", "(1+2", "1+2)", "__import__(x)", "sqrt(-1)"],
)
def test_invalid_expressions(expression):
    with pytest.raises(CalculationError):
        calculate(expression)


def test_never_executes_arbitrary_code(tmp_path):
    marker = tmp_path / "should-not-exist"
    with pytest.raises(CalculationError):
        calculate(f"open({marker})")
    assert not marker.exists()


def test_large_result_is_rejected():
    with pytest.raises(CalculationError):
        calculate("10^101")
