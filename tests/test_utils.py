from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from file_attributes.utils import download_offline_file


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

        assert mock_sleep.call_count == 3


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
        assert mock_sleep.call_count == 3


def test_download_offline_file_not_in_cloud():
    file_path = Path("fake_file.txt")

    with patch("file_attributes.utils.FileAttributes") as mock_file_attributes, patch("builtins.open") as mock_open:
        mock_attrs = mock_file_attributes.return_value
        mock_attrs.in_cloud = False

        download_offline_file(file_path)

        mock_open.assert_not_called()
