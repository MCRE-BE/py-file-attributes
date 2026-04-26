# ruff: noqa: S603, S607

"""MacOS specific implementation of FileAttributes."""

####################
# IMPORT STATEMENT #
####################
import dataclasses
import os
import subprocess
from pathlib import Path

from typing_extensions import Self

from file_attributes._core import _FileAttributesUnix


###########
# CLASSES #
###########
@dataclasses.dataclass(repr=False, eq=True)
class FileAttributesMacOS(_FileAttributesUnix):
    """Access the File metadata Attributes for Mac Systems.

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
    Common File Flags on macOS:

    +-------------+---------------------------------------------------------------------------------------------+
    | Attribute    | Description                                                                                 |
    +=============+=============================================================================================+
    | uchg        | Immutable: The file cannot be modified, deleted, or renamed. Even root cannot change        |
    |             | the file until the flag is removed (e.g., by running ``chflags nouchg``).                   |
    +-------------+---------------------------------------------------------------------------------------------+
    | uappnd      | Append-only: The file can only be appended to; existing data cannot be overwritten.          |
    +-------------+---------------------------------------------------------------------------------------------+
    | nodump      | No dump: The file is excluded from backups made by the ``dump`` command.                     |
    +-------------+---------------------------------------------------------------------------------------------+
    | hidden      | Hidden: The file or directory is hidden in Finder.                                           |
    +-------------+---------------------------------------------------------------------------------------------+
    | sunlnk      | No symbolic link: Disallows linking with symbolic links.                                     |
    +-------------+---------------------------------------------------------------------------------------------+
    | archived    | Archived: The file is marked as archived for possible future processing.                     |
    +-------------+---------------------------------------------------------------------------------------------+
    | opaque      | Opaque: Marks the file or directory as opaque during union mounting.                         |
    +-------------+---------------------------------------------------------------------------------------------+


    """

    @staticmethod
    def get_file_attributes(path: Path) -> list[str]:
        """Retrieve the extended file attributes from the OS.

        Examples
        --------
        >>> get_file_attributes(file.txt)
        >>> "-rw-r--r--  1 username  staff  -        1234 Oct  9 12:00 file.txt"

        Explanation:
            -rw-r--r--: File permissions (read/write/execute bits for user, group, others).
            username/staff: File owner and group.
            -: The file flags. In this case, there are no special flags (- indicates none).
            1234: File size in bytes.
            Oct  9 12:00: Last modification date and time.
            file.txt: File name.

        Returns
        -------
        list[str]
            The extended file attributes as a list of strings.
        """
        try:
            result = subprocess.run(
                ["ls", "-lO", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            parts = result.stdout.split()
            attributes = parts[4].split(",") if len(parts) > 4 and parts[4] != "-" else []
        except subprocess.CalledProcessError:
            return []
        else:
            return attributes

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
            if enable:
                subprocess.run(
                    ["sudo", "chflags", attr, str(self.file)],
                    check=True,
                )
            else:
                disable_attr = attr[2:] if attr.startswith("no") else "no" + attr
                subprocess.run(
                    ["sudo", "chflags", disable_attr, str(self.file)],
                    check=True,
                )
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
        return "uchg" in self.extended_attributes

    @property
    def append_only(self: Self) -> bool:
        """A file that is append-only."""
        return "uappnd" in self.extended_attributes

    @property
    def no_dump(self: Self) -> bool:
        """A file that should not be dumped."""
        return "nodump" in self.extended_attributes

    # ... Setters ...
    def set_immutable(self: Self, enable: bool) -> None:
        """Set or unset the immutable attribute.

        Parameters
        ----------
        enable : bool
            True to enable the immutable attribute, False to disable it.
        """
        self.set_file_attributes(["uchg"], enable)

    def set_append_only(self: Self, enable: bool) -> None:
        """Set or unset the append-only attribute.

        Parameters
        ----------
        enable : bool
            True to enable the append-only attribute, False to disable it.
        """
        self.set_file_attributes(["uappnd"], enable)

    def set_no_dump(self: Self, enable: bool) -> None:
        """Set or unset the no dump attribute.

        Parameters
        ----------
        enable : bool
            True to enable the no dump attribute, False to disable it.
        """
        self.set_file_attributes(["nodump"], enable)

    # ... Add specific functions for cloud...
    @property
    def in_cloud(self: Self) -> bool:
        return any([
            self.is_icloud_file_in_cloud(self.file),
            self.is_onedrive_file_in_cloud(self.file),
        ])

    @staticmethod
    def is_icloud_file_in_cloud(file_path: Path | str) -> bool:
        """Check if icloud managed file is in the cloud."""
        try:
            result = subprocess.run(
                ["brctl", "query", "--id", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            # Check the output for indications that the file is in the cloud
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        else:
            return "status = evicted" in result.stdout or "status = external" in result.stdout

    @staticmethod
    def is_onedrive_file_in_cloud(file_path: Path | str) -> bool:
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
