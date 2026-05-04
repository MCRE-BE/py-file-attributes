import unittest
from pathlib import Path
from unittest.mock import patch

from file_attributes._linux import FileAttributesLinux
from file_attributes._mac import FileAttributesMacOS


class TestSecurityFix(unittest.TestCase):
    def test_macos_no_sudo_in_set_file_attributes(self):
        with patch("subprocess.run") as mock_run:
            file_path = Path("test_file_mac")
            # Mocking stat for __post_init__
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_mode = 0o644
                with patch.object(FileAttributesMacOS, "get_file_attributes", return_value=[]):
                    fa = FileAttributesMacOS(file_path)

                    # Test enabling an attribute
                    fa.set_file_attributes("uchg", enable=True)

                    # Check all calls to subprocess.run
                    for call in mock_run.call_args_list:
                        args, _ = call
                        cmd = args[0]
                        assert "sudo" not in cmd, f"sudo found in macOS command: {cmd}"

    def test_linux_no_sudo_in_set_file_attributes(self):
        with patch("subprocess.run") as mock_run:
            file_path = Path("test_file_linux")
            # Mocking stat for __post_init__
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_mode = 0o644
                with patch.object(FileAttributesLinux, "get_file_attributes", return_value=""):
                    fa = FileAttributesLinux(file_path)

                    # Test enabling an attribute
                    fa.set_file_attributes("i", enable=True)

                    # Check all calls to subprocess.run
                    for call in mock_run.call_args_list:
                        args, _ = call
                        cmd = args[0]
                        assert "sudo" not in cmd, f"sudo found in Linux command: {cmd}"


if __name__ == "__main__":
    unittest.main()
