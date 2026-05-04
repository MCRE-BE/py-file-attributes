import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from file_attributes.cli import main, str2bool


def test_str2bool():
    from typing import cast

    assert str2bool(cast("str", True)) is True
    assert str2bool(cast("str", False)) is False
    for v in ("yes", "true", "t", "y", "1", "YES", "True"):
        assert str2bool(v) is True
    for v in ("no", "false", "f", "n", "0", "NO", "False"):
        assert str2bool(v) is False

    with pytest.raises(argparse.ArgumentTypeError):
        str2bool("invalid")


@patch("file_attributes.cli.FileAttributes")
def test_main_print_only(mock_file_attrs_class, capsys):
    mock_instance = MagicMock()
    mock_instance.__str__.return_value = "Mocked Attributes"
    mock_file_attrs_class.return_value = mock_instance
    mock_file_attrs_class.get_property_fields.return_value = ("read_only", "hidden")

    test_args = ["file-attributes", "dummy.txt"]
    with patch.object(sys, "argv", test_args):
        main()

    mock_file_attrs_class.assert_called_once_with(Path("dummy.txt"))
    captured = capsys.readouterr()
    assert "Mocked Attributes" in captured.out


@patch("file_attributes.cli.FileAttributes")
def test_main_set_attribute(mock_file_attrs_class, capsys):
    mock_instance = MagicMock()
    mock_instance.__str__.return_value = "Mocked Attributes"
    mock_file_attrs_class.return_value = mock_instance

    # We must ensure the dynamically built parser sees valid arguments.
    # We mock get_property_fields to return "read_only", and ensure
    # FileAttributes has a "set_read_only" method so the CLI adds the --read_only flag.
    mock_file_attrs_class.get_property_fields.return_value = ("read_only",)

    # Python's hasattr uses getattr, so we attach mock methods to the class itself.
    mock_file_attrs_class.set_read_only = lambda _self, _enable: None

    test_args = ["file-attributes", "dummy.txt", "--read_only", "True"]
    with patch.object(sys, "argv", test_args):
        main()

    # The instance should have had set_read_only called with True.
    mock_instance.set_read_only.assert_called_once_with(True)

    # It should recreate the instance to refresh attributes since changed=True
    assert mock_file_attrs_class.call_count == 2
    captured = capsys.readouterr()
    assert "Mocked Attributes" in captured.out


@patch("file_attributes.cli.FileAttributes")
def test_main_exception(mock_file_attrs_class, capsys):
    mock_file_attrs_class.side_effect = ValueError("Test Error")

    test_args = ["file-attributes", "dummy.txt"]
    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    assert "Error: Test Error" in captured.out
