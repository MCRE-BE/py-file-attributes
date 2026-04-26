"""All the tests.

Notes
-----
Fixtures: The temp_file fixture creates a temporary file for testing and ensures it is cleaned up after the tests.

Cross-Platform Tests:

- test_read_only: Tests setting and getting the read-only attribute.
- test_hidden: Tests setting and getting the hidden attribute.
- test_executable: Tests setting and getting the executable attribute (skipped on Windows).
- test_immutable: Tests setting and getting the immutable attribute (skipped on Windows).
- test_append_only: Tests setting and getting the append-only attribute (skipped on Windows).
- test_no_dump: Tests setting and getting the no-dump attribute (skipped on Windows).
- test_directory: Tests checking if a path is a directory.

Platform-Specific Tests:

- test_windows_specific_attributes: Tests Windows-specific attributes like system, archive, and compressed.
- test_macos_specific_attributes: Tests macOS-specific attributes like immutable, append_only, and no_dump.
- test_linux_specific_attributes: Tests Linux-specific attributes like immutable, append_only, and no_dump.
"""

####################
# IMPORT STATEMENT #
####################
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from file_attributes import FileAttributes


############
# Fixtures #
############
@pytest.fixture
def temp_file() -> Generator[Path]:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        yield Path(temp.name)


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp:
        yield Path(temp)


# ==================== #
# Cross-Platform Tests #
# ==================== #
def test_read_only(temp_file):
    """Test setting and getting the read-only attribute."""
    file_attrs = FileAttributes(temp_file)
    assert not file_attrs.read_only
    file_attrs.set_read_only(True)
    assert file_attrs.read_only, "Failed to set read-only attribute"
    file_attrs.set_read_only(False)
    assert not file_attrs.read_only, "Failed to unset read-only attribute"


def test_hidden(temp_file):
    """Test setting and getting the hidden attribute."""
    file_attrs = FileAttributes(temp_file)
    assert not file_attrs.hidden
    file_attrs.set_hidden(True)
    assert file_attrs.hidden, "Failed to set hidden attribute"
    file_attrs.set_hidden(False)
    assert not file_attrs.hidden, "Failed to unset hidden attribute"


def test_directory(temp_file, temp_dir):
    """Test if a path is correctly identified as a directory."""
    file_attrs = FileAttributes(temp_file)
    assert not file_attrs.directory

    dir_attrs = FileAttributes(temp_dir)
    assert dir_attrs.directory, "Failed to identify directory"


def test_in_cloud(temp_file):  # noqa: C901
    """Test the `in_cloud` property.

    Notes
    -----
    Add placeholder logic to simulate a cloud-only file and test this attribute.
    """
    file_attrs = FileAttributes(temp_file)
    assert not file_attrs.in_cloud

    if sys.platform == "win32":
        with patch.object(
            type(file_attrs),
            "get_file_attributes",
            return_value=0x400000,  # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
        ):
            assert file_attrs.in_cloud

    elif sys.platform == "darwin":

        def mock_run_side_effect_icloud(*args, **kwargs):
            if "brctl" in args[0]:

                class MockResult:
                    stdout = "status = evicted"

                return MockResult()

            class MockResultEmpty:
                stdout = ""

            return MockResultEmpty()

        with patch("subprocess.run", side_effect=mock_run_side_effect_icloud):
            assert file_attrs.in_cloud

        def mock_run_side_effect_onedrive(*args, **kwargs):
            if "xattr" in args[0]:

                class MockResult:
                    stdout = "user.onedrive.hydrationState DEHYDRATED"

                return MockResult()

            class MockResultEmpty:
                stdout = ""

            return MockResultEmpty()

        with patch("subprocess.run", side_effect=mock_run_side_effect_onedrive):
            assert file_attrs.in_cloud

    elif sys.platform == "linux":

        def mock_run_side_effect_rcloud(*args, **kwargs):
            if "rclone" in args[0]:

                class MockResult:
                    stdout = f'[{{"Path": "{temp_file}", "IsDir": false, "Size": 0}}]'

                return MockResult()

            class MockResultEmpty:
                stdout = ""

            return MockResultEmpty()

        with patch("subprocess.run", side_effect=mock_run_side_effect_rcloud):
            assert file_attrs.in_cloud

        def mock_run_side_effect_onedrive_linux(*args, **kwargs):
            if "xattr" in args[0]:

                class MockResult:
                    stdout = "user.onedrive.hydrationState DEHYDRATED"

                return MockResult()
            if "rclone" in args[0]:

                class MockResultJson:
                    stdout = "[]"

                return MockResultJson()

            class MockResultEmpty:
                stdout = ""

            return MockResultEmpty()

        with patch("subprocess.run", side_effect=mock_run_side_effect_onedrive_linux):
            assert file_attrs.in_cloud


# ====================== #
# Windows-Specific Tests #
# ====================== #
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_windows_specific_attributes(temp_file):
    """Test Windows-specific attributes like archive and compressed."""
    file_attrs = cast("Any", FileAttributes(temp_file))

    # Archive attribute
    file_attrs.set_archive(True)
    assert file_attrs.archive, "Failed to set archive attribute"
    file_attrs.set_archive(False)
    assert not file_attrs.archive, "Failed to unset archive attribute"

    # Compressed attribute
    assert not file_attrs.compressed
    file_attrs.set_compressed(True)
    assert file_attrs.compressed, "Failed to set compressed attribute"
    file_attrs.set_compressed(False)
    assert not file_attrs.compressed, "Failed to unset compressed attribute"


# ========================== #
# Linux/macOS-Specific Tests #
# ========================== #
@pytest.mark.skipif(sys.platform != "linux" and sys.platform != "darwin", reason="Unix-specific test")
def test_unix_specific_attributes(temp_file):
    file_attrs = cast("Any", FileAttributes(temp_file))

    # Immutable attribute
    assert not file_attrs.immutable
    file_attrs.set_immutable(True)
    assert file_attrs.immutable, "Failed to set immutable attribute"
    file_attrs.set_immutable(False)
    assert not file_attrs.immutable, "Failed to unset immutable attribute"

    # Append-only attribute
    assert not file_attrs.append_only
    file_attrs.set_append_only(True)
    assert file_attrs.append_only, "Failed to set append-only attribute"
    file_attrs.set_append_only(False)
    assert not file_attrs.append_only, "Failed to unset append-only attribute"

    # No-dump attribute
    assert not file_attrs.no_dump
    file_attrs.set_no_dump(True)
    assert file_attrs.no_dump, "Failed to set no-dump attribute"
    file_attrs.set_no_dump(False)
    assert not file_attrs.no_dump, "Failed to unset no-dump attribute"
