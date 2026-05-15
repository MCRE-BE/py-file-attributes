import unittest
from pathlib import Path
from unittest.mock import patch

from file_attributes._mac import FileAttributesMacOS


class TestArgumentInjection(unittest.TestCase):
    def test_argument_injection_raises_value_error(self):
        with patch("subprocess.run") as mock_run:
            file_path = Path("test_file")
            # Mocking stat for __post_init__
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_mode = 0o644
                with patch.object(FileAttributesMacOS, "get_file_attributes", return_value=[]):
                    fa = FileAttributesMacOS(file_path)

                    # These should now raise ValueError because they are not in the allowlist
                    try:
                        fa.set_file_attributes("-h", enable=True)
                    except ValueError as e:
                        msg = str(e)
                        if "Invalid or restricted attribute: -h" not in msg:
                            raise AssertionError(f"Wrong error message: {msg}") from e
                    else:
                        raise AssertionError("Should have raised ValueError")

                    try:
                        fa.set_file_attributes(["uchg", "-R"], enable=True)
                    except ValueError as e:
                        msg = str(e)
                        if "Invalid or restricted attribute: -R" not in msg:
                            raise AssertionError(f"Wrong error message: {msg}") from e
                    else:
                        raise AssertionError("Should have raised ValueError")

                    # Ensure subprocess.run was not called for the invalid attributes
                    for call in mock_run.call_args_list:
                        args, _ = call
                        if "-R" in args[0] or "-h" in args[0]:
                            raise AssertionError(f"Invalid flag passed to subprocess.run: {args[0]}")

    def test_valid_attributes_pass(self):
        with patch("subprocess.run") as mock_run:
            file_path = Path("test_file")
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_mode = 0o644
                with patch.object(FileAttributesMacOS, "get_file_attributes", return_value=[]):
                    fa = FileAttributesMacOS(file_path)

                    # Valid attributes should still work
                    fa.set_file_attributes("uchg", enable=True)
                    fa.set_file_attributes("hidden", enable=False)

                    if mock_run.call_count != 2:
                        raise AssertionError(f"Expected 2 calls, got {mock_run.call_count}")
                    mock_run.assert_any_call(["chflags", "uchg", str(file_path.absolute())], check=True)
                    mock_run.assert_any_call(["chflags", "nohidden", str(file_path.absolute())], check=True)


if __name__ == "__main__":
    unittest.main()
