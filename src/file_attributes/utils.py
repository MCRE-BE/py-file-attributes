# ruff: noqa: N803
"""Utils using FileAttributes to retrieve data from cloud storage."""

# %%
import builtins
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from typing_extensions import Self

from file_attributes import FileAttributes


class FileRecallManager:
    """Context Manager to recall a cloud-stored file to local storage.

    A context manager that checks the attributes of the passed filepath
    and, if the file is not available on the local hard-drive, performs
    a data access request to trigger it's download.

    As long as the data access request is not completed successfully
    (no OSError), there is a retry policy managed by RETRY_MAX and
    RETRY_DELAY.

    The returned object is simply the filepath to not disrupt other classes.

    See Also
    --------
    FileAttributes

    Attributes
    ----------
    filename : Path
        The file we are accessing
    fileattributes : FileAttributes
        Class that retrieves all FileAttributes from the OS.
        Only works with Windows environment.

    Examples
    --------
    >>> import pandas as pd
    >>>
    >>> with FileRecallManager(test.xlsx) as f:
    >>>    display(pd.read_excel(f, engine="calamine"))
    """

    RETRY_MAX = 5
    RETRY_DELAY = 10
    READ_MODE = "r+b"

    def __init__(
        self: Self,
        filename: Path | str,
    ):
        self.filename = Path(filename)
        self.fileattributes = FileAttributes(self.filename)

    def __enter__(self: Self) -> Path:
        download_offline_file(
            self.filename,
            self.RETRY_MAX,
            self.RETRY_DELAY,
            self.READ_MODE,
        )

        return self.filename

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def download_offline_file(
    file: Path,
    RETRY_MAX: int = 5,
    RETRY_DELAY: int = 10,
    READ_MODE: str = "r+b",
) -> None:
    """Trigger download from cloud storage for a single file."""
    fileattributes = FileAttributes(file)

    # Check if file is available on the drive, otherwise trigger its download.
    # Retry several times
    if fileattributes.in_cloud:
        test_counter = 0
        while test_counter < RETRY_MAX:
            try:
                with builtins.open(file, READ_MODE):
                    pass
                break
            except OSError:
                pass
            finally:
                test_counter += 1
                time.sleep(RETRY_DELAY)
        else:
            raise OSError(f"Unable to retrieve {file.as_posix()} from cloud storage. Retry policy exceeded.")


def download_offline_files_sequential(
    to_download: list[str | Path],
    RETRY_MAX: int = 5,
    RETRY_DELAY: int = 10,
    READ_MODE: str = "r+b",
) -> None:
    """Trigger download from cloud storage for all provided files.

    Parameters
    ----------
    to_download : list[str | Path]
        List of files to ensure are available on HDD
    RETRY_MAX : int, by default = 5
        Amount of times to try and trigger the download
    RETRY_DELAY : int, by default = 10
        Amount of time to wait between two tries
    READ_MODE : str, by default = r+b
        Read mode to be used by open(file, READ_MODE) to trigger the data_access
        It should not matter, but just in case.

    See Also
    --------
    FileAttributes

    Raises
    ------
    OSError
        If FileAttributes.in_cloud does not shift to False (= Available on HDD)
        after amount of tries is larger then RETRY_MAX, then fail.
    """

    for file in [Path(x) for x in to_download]:
        download_offline_file(file, RETRY_MAX, RETRY_DELAY, READ_MODE)


def download_offline_files_parallel(
    to_download: list[str | Path],
    RETRY_MAX: int = 5,
    RETRY_DELAY: int = 10,
    READ_MODE: str = "r+b",
    max_workers: int = 4,
) -> None:
    """Trigger download from cloud storage for all provided files in parallel.

    Parameters
    ----------
    to_download : list[str | Path]
        List of files to ensure are available on HDD.
    RETRY_MAX : int, optional
        Amount of times to try and trigger the download, by default 5.
    RETRY_DELAY : int, optional
        Amount of time to wait between two tries, by default 10 seconds.
    READ_MODE : str, optional
        Read mode to be used by open(file, READ_MODE) to trigger the data access, by default "r+b".
    max_workers : int, optional
        Maximum number of threads to use for parallel processing, by default 4.

    Raises
    ------
    OSError
        If FileAttributes.in_cloud does not shift to False (= Available on HDD)
        after the amount of tries is larger than RETRY_MAX, then fail.
    """

    if isinstance(to_download, (str, Path)):
        download_offline_file(Path(to_download), RETRY_MAX, RETRY_DELAY, READ_MODE)

    elif isinstance(to_download, list) and len(to_download) == 1:
        download_offline_file(Path(to_download[0]), RETRY_MAX, RETRY_DELAY, READ_MODE)

    elif isinstance(to_download, list) and len(to_download) > 1:
        _paths = [Path(x) for x in to_download]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(download_offline_file, file, RETRY_MAX, RETRY_DELAY, READ_MODE) for file in _paths
            ]
            for future in as_completed(futures):
                future.result()  # This will raise an exception if the future raised one

    else:
        raise ValueError(f"Invalid type for to_download: {type(to_download)}")
