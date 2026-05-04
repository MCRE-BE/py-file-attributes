import argparse

import pytest

from file_attributes.cli import str2bool


@pytest.mark.parametrize("value", ["yes", "TRUE", "True", "t", "y", "1"])
def test_str2bool_truthy(value: str):
    """Test that truthy strings are correctly converted to True."""
    assert str2bool(value) is True


@pytest.mark.parametrize("value", ["no", "FALSE", "False", "f", "n", "0"])
def test_str2bool_falsy(value: str):
    """Test that falsy strings are correctly converted to False."""
    assert str2bool(value) is False


@pytest.mark.parametrize("value", [True, False])
def test_str2bool_boolean(value: bool):
    """Test that boolean inputs are returned as-is."""
    assert str2bool(value) is value


@pytest.mark.parametrize("value", ["abc", "2", "maybe", "", "  "])
def test_str2bool_invalid(value: str):
    """Test that invalid strings raise argparse.ArgumentTypeError."""
    with pytest.raises(argparse.ArgumentTypeError, match=r"Boolean value expected\."):
        str2bool(value)
