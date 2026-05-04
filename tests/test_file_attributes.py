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
from unittest.mock import PropertyMock, patch

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


def test_argument_injection():
    """Test that file names starting with '-' do not cause argument injection errors."""
    with tempfile.NamedTemporaryFile(prefix="-", delete=False) as temp:
        temp_path = Path(temp.name)

    file_attrs = FileAttributes(temp_path)
    try:
        # Verify read and write don't fail due to parameter injection
        file_attrs.set_read_only(True)
        assert file_attrs.read_only
    finally:
        file_attrs.set_read_only(False)
        temp_path.unlink()


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
            "raw_attribute_mask",
            new_callable=PropertyMock,
        ) as mock_raw:
            mock_raw.return_value = 0x400000  # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
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

        with patch.object(
            file_attrs,
            "extended_attributes",
            ["dataless"],
        ):
            assert file_attrs.dataless
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

    # Some Unix environments (like CI containers) may not support setting these attributes even for root
    # or may return "Operation not permitted" (EPERM).
    try:
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
    except ValueError as e:
        if "Failed to set attribute" in str(e):
            pytest.skip(f"Environment does not support setting Unix specific attributes: {e}")
        raise


def test_mac_error_handling(temp_file):
    """Test macOS specific error handling for chflags/ls exceptions."""
    import subprocess

    from file_attributes._mac import FileAttributesMacOS

    file_attrs = FileAttributesMacOS(temp_file)

    # Test get_file_attributes exception
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ls")):
        assert FileAttributesMacOS.get_file_attributes(temp_file) == []

    # Test set_file_attributes FileNotFoundError
    with (
        patch("subprocess.run", side_effect=FileNotFoundError()),
        pytest.raises(ImportError, match="chflags tool is not found"),
    ):
        file_attrs.set_file_attributes("uchg")

    # Test set_file_attributes CalledProcessError
    with (
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "chflags")),
        pytest.raises(ValueError, match="Failed to set attribute"),
    ):
        file_attrs.set_file_attributes("uchg")

    # Test darwin major parsing exception and warning
    with patch("platform.release", return_value="invalid_release"):
        _ = file_attrs.in_cloud

    with patch("platform.release", return_value="20.0.0"), patch("warnings.warn") as mock_warn:
        _ = file_attrs.in_cloud
        assert mock_warn.called


def test_linux_error_handling(temp_file):
    """Test Linux specific error handling for chattr/lsattr exceptions."""
    import subprocess
    from unittest.mock import MagicMock

    from file_attributes._linux import FileAttributesLinux

    with patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0)):
        file_attrs = FileAttributesLinux(temp_file)

    # Test get_file_attributes exception
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "lsattr")):
        assert FileAttributesLinux.get_file_attributes(temp_file) == ""

    # Test set_file_attributes FileNotFoundError
    with (
        patch("subprocess.run", side_effect=FileNotFoundError()),
        pytest.raises(ImportError, match="chattr tool is not found"),
    ):
        file_attrs.set_file_attributes("i")

    # Test set_file_attributes CalledProcessError
    with (
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "chattr")),
        pytest.raises(ValueError, match="Failed to set attribute"),
    ):
        file_attrs.set_file_attributes("i")

    with patch.object(file_attrs, "set_file_attributes") as mock_set:
        file_attrs.set_append_only(True)
        file_attrs.set_no_dump(True)
        assert mock_set.call_count == 2


def test_windows_all_attributes(temp_file):
    """Test all windows specific attributes via mock to achieve full coverage."""
    from file_attributes._windows import FileAttributesWindows

    file_attrs = FileAttributesWindows(temp_file)

    attributes_to_test = [
        ("read_only", "set_read_only"),
        ("hidden", "set_hidden"),
        ("system", None),
        ("directory", "set_directory"),
        ("archive", "set_archive"),
        ("device", None),
        ("normal", "set_normal"),
        ("temporary", "set_temporary"),
        ("sparse", "set_sparse"),
        ("reparse", "set_reparse"),
        ("compressed", "set_compressed"),
        ("offline", None),
        ("not_content_indexed", "set_not_content_indexed"),
        ("encrypted", "set_encrypted"),
        ("integrity_stream", "set_integrity_stream"),
        ("virtual", "set_virtual"),
        ("no_scrub_data", "set_no_scrub_data"),
        ("pinned", "set_pinned"),
        ("unpinned", "set_unpinned"),
        ("recall_on_open", "set_recall_on_open"),
        ("recall_on_data_access", "set_recall_on_data_access"),
    ]

    with patch.object(file_attrs, "set_attribute") as mock_set:
        for attr, setter_name in attributes_to_test:
            # Test getter using a mocked raw_attribute_mask
            with patch.object(FileAttributesWindows, "raw_attribute_mask", new_callable=PropertyMock) as mock_mask:
                mock_mask.return_value = 0xFFFFFFFF  # Set all bits to 1
                assert getattr(file_attrs, attr) is True

            # Test setter if it exists
            if setter_name:
                setter = getattr(file_attrs, setter_name)
                setter(True)
                setter(False)
        assert mock_set.call_count > 0


def test_mac_is_onedrive_exception(temp_file):
    """Test exception block in is_onedrive_file_in_cloud for Mac."""
    import subprocess

    from file_attributes._mac import FileAttributesMacOS

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "xattr")):
        assert not FileAttributesMacOS.is_onedrive_file_in_cloud(temp_file)


def test_core_setters_coverage(temp_file):
    """Ensure set_executable, set_immutable, set_append_only, set_no_dump are hit without permission bounds."""
    from file_attributes._core import _FileAttributesUnix

    # Create a dummy subclass to test abstract methods
    class DummyUnixAttrs(_FileAttributesUnix):
        @staticmethod
        def get_file_attributes(path):
            _ = path
            return []

        def set_file_attributes(self, attributes, enable=True):
            _ = attributes
            _ = enable

        def set_attribute(self, attribute, enable):
            _ = attribute
            _ = enable

    file_attrs = DummyUnixAttrs(temp_file)
    with patch.object(file_attrs, "set_attribute") as mock_set_attr:
        file_attrs.set_executable(True)
        assert mock_set_attr.called

    with patch.object(file_attrs, "set_file_attributes") as mock_set_file_attrs:
        file_attrs.set_immutable(True)
        file_attrs.set_append_only(True)
        file_attrs.set_no_dump(True)
        assert mock_set_file_attrs.call_count == 3
