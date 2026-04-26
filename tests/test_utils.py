from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from file_attributes.utils import (
    FileRecallManager,
    download_offline_file,
    download_offline_files_parallel,
    download_offline_files_sequential,
)


def test_download_offline_files_sequential_success():
    file_list = ["fake_file1.txt", Path("fake_file2.txt")]

    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_sequential(file_list, RETRY_MAX=3, RETRY_DELAY=2, READ_MODE="r")

        assert mock_download.call_count == 2
        mock_download.assert_any_call(Path("fake_file1.txt"), 3, 2, "r")
        mock_download.assert_any_call(Path("fake_file2.txt"), 3, 2, "r")


def test_download_offline_files_sequential_empty():
    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_sequential([])
        mock_download.assert_not_called()


def test_download_offline_file_retry_exhaustion():
    file_path = Path("fake_file.txt")

    with (
        patch("file_attributes.utils.FileAttributes") as mock_file_attributes,
        patch("builtins.open", side_effect=OSError("Cloud error")),
        patch("time.sleep") as mock_sleep,
    ):
        mock_attrs = mock_file_attributes.return_value
        mock_attrs.in_cloud = True

        with pytest.raises(OSError, match="Retry policy exceeded"):
            download_offline_file(file_path, RETRY_MAX=3, RETRY_DELAY=0)

        assert mock_sleep.call_count == 2


def test_download_offline_file_success_after_retry():
    file_path = Path("fake_file.txt")

    # Mock open to fail twice, then succeed
    mock_open = MagicMock(side_effect=[OSError("Cloud error"), OSError("Cloud error"), MagicMock()])

    with (
        patch("file_attributes.utils.FileAttributes") as mock_file_attributes,
        patch("builtins.open", mock_open),
        patch("time.sleep") as mock_sleep,
    ):
        mock_attrs = mock_file_attributes.return_value
        mock_attrs.in_cloud = True

        # Should not raise exception
        download_offline_file(file_path, RETRY_MAX=3, RETRY_DELAY=0)

        assert mock_open.call_count == 3
        assert mock_sleep.call_count == 2


def test_download_offline_file_not_in_cloud():
    file_path = Path("fake_file.txt")

    with patch("file_attributes.utils.FileAttributes") as mock_file_attributes, patch("builtins.open") as mock_open:
        mock_attrs = mock_file_attributes.return_value
        mock_attrs.in_cloud = False

        download_offline_file(file_path)

        mock_open.assert_not_called()


def test_download_offline_file_error_path():
    file_path = Path("error_path_test.txt")

    with (
        patch("file_attributes.utils.FileAttributes") as mock_file_attributes,
        patch("builtins.open", side_effect=OSError),
        patch("time.sleep"),
    ):
        mock_attrs = mock_file_attributes.return_value
        mock_attrs.in_cloud = True

        expected_msg = f"Unable to retrieve {file_path.as_posix()} from cloud storage. Retry policy exceeded."
        with pytest.raises(OSError, match=expected_msg):
            download_offline_file(file_path, RETRY_MAX=3, RETRY_DELAY=0)


def test_file_recall_manager_success():
    file_path = Path("fake_file.txt")
    with (
        patch("file_attributes.utils.FileAttributes"),
        patch("file_attributes.utils.download_offline_file") as mock_download,
    ):
        with FileRecallManager(file_path) as f:
            assert f == file_path
        mock_download.assert_called_once_with(
            file_path,
            FileRecallManager.RETRY_MAX,
            FileRecallManager.RETRY_DELAY,
            FileRecallManager.READ_MODE,
        )


def test_download_offline_files_sequential():
    files = ["fake_file1.txt", Path("fake_file2.txt")]
    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_sequential(files)
        assert mock_download.call_count == 2
        mock_download.assert_any_call(Path("fake_file1.txt"), 5, 10, "r+b")
        mock_download.assert_any_call(Path("fake_file2.txt"), 5, 10, "r+b")


def test_download_offline_files_parallel_single_str():
    file = "fake_file.txt"
    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_parallel(cast("list[str | Path]", file))
        mock_download.assert_called_once_with(Path(file), 5, 10, "r+b")


def test_download_offline_files_parallel_single_list():
    file = ["fake_file.txt"]
    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_parallel(cast("list[str | Path]", file))
        mock_download.assert_called_once_with(Path(file[0]), 5, 10, "r+b")


def test_download_offline_files_parallel_multiple():
    files = ["fake_file1.txt", Path("fake_file2.txt")]
    with patch("file_attributes.utils.download_offline_file") as mock_download:
        download_offline_files_parallel(files)
        assert mock_download.call_count == 2


def test_download_offline_files_parallel_multiple_exception():
    files = ["fake_file1.txt", Path("fake_file2.txt")]
    with (
        patch("file_attributes.utils.download_offline_file", side_effect=OSError("Parallel Error")),
        pytest.raises(OSError, match="Parallel Error"),
    ):
        download_offline_files_parallel(files)


def test_download_offline_files_parallel_invalid_type():
    with pytest.raises(ValueError, match="Invalid type for to_download:"):
        download_offline_files_parallel(cast("list[str | Path]", 123))
