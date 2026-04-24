# ruff: noqa: S603, S607
"""Linux specific implementation of FileAttributes."""

####################
# IMPORT STATEMENT #
####################
import dataclasses
import os
import re
import subprocess
from pathlib import Path

from typing_extensions import Self

from file_attributes._core import _FileAttributesUnix


###########
# CLASSES #
###########
@dataclasses.dataclass(repr=False)
class FileAttributesLinux(_FileAttributesUnix):
    """Access the File metadata Attributes for linux systems.

    Attributes
    ----------
    read_only: bool
    hidden: bool
    executable: bool
    directory: bool
    symlink: bool
    immutable: bool
    append_only: bool
    no_dump: bool

    Notes
    -----
    Common File Attributes:

    +-------------+---------------------------------------------------------------------------------------------+
    | Attribute    | Description                                                                                 |
    +=============+=============================================================================================+
    | i           | Immutable: The file cannot be modified, deleted, or renamed. Even root cannot change        |
    |             | the file until the attribute is removed (e.g., by running ``chattr -i``).                   |
    +-------------+---------------------------------------------------------------------------------------------+
    | a           | Append-only: The file can only be appended to; existing data cannot be overwritten.          |
    +-------------+---------------------------------------------------------------------------------------------+
    | d           | No dump: The file is excluded from backups made by the ``dump`` command.                     |
    +-------------+---------------------------------------------------------------------------------------------+
    | e           | Extents: The file uses extents for mapping blocks, which is more efficient for large files.  |
    +-------------+---------------------------------------------------------------------------------------------+
    | s           | Secure deletion: When the file is deleted, its data is zeroed out to prevent recovery.       |
    +-------------+---------------------------------------------------------------------------------------------+
    | u           | Undeletable: When the file is deleted, its contents can still be recovered.                  |
    +-------------+---------------------------------------------------------------------------------------------+
    | c           | Compressed: Data in the file is compressed automatically at the filesystem level.            |
    +-------------+---------------------------------------------------------------------------------------------+
    | t           | Top: A directory with this attribute will store files data separately to improve             |
    |             | performance.                                                                                |
    +-------------+---------------------------------------------------------------------------------------------+
    | T           | No tail-merging: Prevents optimization where file tails are shared with other files.         |
    +-------------+---------------------------------------------------------------------------------------------+

    """

    # ... Magic Methods ...
    def __repr__(self: Self) -> str:
        """Return a string representation of the file attributes.

        Returns
        -------
        str
            A string representation of the file attributes.
        """
        result = f"{self.file.as_posix()}\n"
        result += f"mode : {oct(self.mode)}\n"
        result += f"extended_attributes : {self.extended_attributes}\n"
        return result

    def __str__(self: Self) -> str:
        """Return a detailed string representation of the file attributes.

        Returns
        -------
        str
            A detailed string representation of the file attributes.
        """
        result = f"{self.file.as_posix()}\n"
        result += f"mode : {oct(self.mode)}\n"
        result += f"extended_attributes : {self.extended_attributes}\n"

        attributes = self.get_property_fields(self)
        for attr in attributes:
            result += f"{attr}: {getattr(self, attr)}\n"
        return result

    # ... Helper Methods ...
    @staticmethod
    def get_file_attributes(path: Path) -> str:
        """Retrieve the extended file attributes from the OS.

        Examples
        --------
        >>> get_file_attributes(file.txt)
        >>> "----i--------e---- file.txt"

        Explanation:
            ----i--------e---- : File permissions (i for immutable, extents
                indicating a more efficient block mapping for the file).
            file.txt: File name.

        Returns
        -------
        str
            The extended file attributes as a string.
        """
        try:
            result = subprocess.run(
                ["lsattr", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            match = re.search(r"[-a-zA-Z]+\s+.*?\s+(.*?)$", result.stdout)
            return match.group(1) if match else ""
        except subprocess.CalledProcessError:
            return ""

    def set_file_attributes(
        self: Self,
        attributes: str | list[str],
        enable: bool = True,
    ) -> None:
        """Set the extended file attributes.

        Parameters
        ----------
        attributes : str | list[str]
            The extended file attributes to set.
        enable : bool
            True to enable the attributes, False to disable them.
        """
        if isinstance(attributes, str):
            attributes = [attributes]
        for attr in attributes:
            try:
                # attr should be just the name, we add + or - based on enable
                cmd = f"{'+' if enable else '-'}{attr}"
                subprocess.run(["sudo", "chattr", cmd, str(self.file)], check=True)
            except subprocess.CalledProcessError as e:  # noqa: PERF203
                raise ValueError(f"Failed to set attribute: {attr}") from e
            except FileNotFoundError as e:
                raise ImportError("chattr tool is not found. Please ensure it is installed on your system.") from e

        self.extended_attributes = self.get_file_attributes(self.file)

    def set_attribute(
        self: Self,
        attribute: int,
        enable: bool,
    ) -> None:
        """Set or unset a specific attribute.

        Parameters
        ----------
        attribute : int
            The attribute to set or unset.
        enable : bool
            True to enable the attribute, False to disable it.
        """
        if enable:
            self.mode |= attribute
        else:
            self.mode &= ~attribute
        os.chmod(self.file, self.mode)

    # ... Properties ...
    @property
    def immutable(self: Self) -> bool:
        """A file that is immutable."""
        return "i" in self.extended_attributes

    @property
    def append_only(self: Self) -> bool:
        """A file that is append-only."""
        return "a" in self.extended_attributes

    @property
    def no_dump(self: Self) -> bool:
        """A file that should not be dumped."""
        return "d" in self.extended_attributes

    # ... Setters ...
    def set_immutable(self: Self, enable: bool) -> None:
        """Set or unset the immutable attribute.

        Parameters
        ----------
        enable : bool
            True to enable the immutable attribute, False to disable it.
        """
        self.set_file_attributes("i", enable)

    def set_append_only(self: Self, enable: bool) -> None:
        """Set or unset the append-only attribute.

        Parameters
        ----------
        enable : bool
            True to enable the append-only attribute, False to disable it.
        """
        self.set_file_attributes("a", enable)

    def set_no_dump(self: Self, enable: bool) -> None:
        """Set or unset the no dump attribute.

        Parameters
        ----------
        enable : bool
            True to enable the no dump attribute, False to disable it.
        """
        self.set_file_attributes("d", enable)

    # ... Add specific functions for cloud...
    @property
    def in_cloud(self: Self) -> bool:
        return any([
            self.is_rcloud_file_in_cloud(self.file),
            self.is_onedrive_file_in_cloud(self.file),
        ])

    @staticmethod
    def is_rcloud_file_in_cloud(file_path: Path) -> bool:
        """Check if rcloud managed file is in the cloud."""
        import json

        try:
            result = subprocess.run(
                ["rclone", "lsjson", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            file_info = json.loads(result.stdout)
            # Check the output for indications that the file is in the cloud
            return any(
                file["Path"] == str(file_path) and not file.get("IsDir") and file.get("Size") == 0 for file in file_info
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def is_onedrive_file_in_cloud(file_path: Path) -> bool:
        """Check if OneDrive managed file is in the cloud."""
        try:
            result = subprocess.run(
                ["xattr", "-l", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        else:
            return "user.onedrive.hydrationState" in result.stdout and "DEHYDRATED" in result.stdout
