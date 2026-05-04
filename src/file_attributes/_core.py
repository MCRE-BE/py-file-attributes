"""The core FileAttributes class shared by all."""

####################
# IMPORT STATEMENT #
####################
import dataclasses
import stat
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path

from typing_extensions import Self


###########
# CLASSES #
###########
@dataclasses.dataclass(repr=False, eq=True)  # As overwritten anyway (as a reminder)
class _FileAttributesCore:
    """Access the File metadata Attributes.

    Attributes
    ----------
    in_cloud: bool
        Whether the file is stored in a cloud provider and not physically on the local disk.
    """

    file: Path

    def __post_init__(self: Self) -> None:
        """Initialize the FileAttributes instance."""
        if isinstance(self.file, str):
            self.file = Path(self.file)

    def __repr__(self: Self) -> str:
        """Return a string representation of the file attributes.

        Returns
        -------
        str
            A string representation of the file attributes.
        """
        from pprint import pformat

        attributes = self.get_property_fields(self)
        nodes = {attr: getattr(self, attr) for attr in attributes}
        # cluster them: True first, then False, sorted alphabetically
        sorted_nodes = {k: nodes[k] for k in sorted(nodes.keys(), key=lambda x: (not nodes[x], x))}
        return f"{self.__class__.__name__}(\n {pformat(sorted_nodes, sort_dicts=False, indent=2)}\n)"

    def __str__(self: Self) -> str:
        """Return a detailed string representation of the file attributes.

        Returns
        -------
        str
            A detailed string representation of the file attributes.
        """
        res = []
        res.append(f"File: {self.file.as_posix()}")

        if hasattr(self, "mode"):
            res.append(f"mode                : {oct(int(str(self.mode)))}")
        if hasattr(self, "extended_attributes"):
            res.append(f"extended_attributes : {self.extended_attributes}")
        if hasattr(self, "raw_attribute_mask"):
            val = self.raw_attribute_mask
            val_int = int(str(val))
            res.append(f"raw_attribute_mask  : {bin(val_int)} | {int(val_int)} | {hex(val_int)}")

        attributes = self.get_property_fields(self)
        enabled = []
        disabled = []
        for attr in attributes:
            if getattr(self, attr):
                enabled.append(attr)
            else:
                disabled.append(attr)

        enabled.sort()
        disabled.sort()

        max_len = max((len(a) for a in attributes), default=0)
        max_len = max(max_len, len("Attribute"))

        header = f"| {'Attribute'.ljust(max_len)} | Value |"
        res.append("-" * len(header))
        res.append(header)
        res.append("-" * len(header))

        res.extend(f"| {attr.ljust(max_len)} | True  |" for attr in enabled)
        res.extend(f"| {attr.ljust(max_len)} | False |" for attr in disabled)
        res.append("-" * len(header))

        return "\n".join(res)

    @cached_property
    def _cached_property_fields(self) -> tuple[str, ...]:
        """Cache the property fields for the instance."""
        my_class = type(self)
        properties = set()
        for cls in my_class.__mro__:
            for attr, value in vars(cls).items():
                if isinstance(value, property) and value.fget is not None:
                    properties.add(attr)
        return tuple(properties)

    # ... Helper Methods ...
    @staticmethod
    def get_property_fields(my_class) -> tuple[str, ...]:
        """Get all attributes defined through @property.

        Returns
        -------
        Returns a tuple of all attribute names defined with @property

        See Also
        --------
        https://stackoverflow.com/a/49943617/20716078
        """
        if not isinstance(my_class, type):
            if hasattr(my_class, "_cached_property_fields"):
                return my_class._cached_property_fields
            my_class = type(my_class)

        # Iterate over MRO to get all properties including inherited ones
        properties = set()
        for cls in my_class.__mro__:
            for attr, value in vars(cls).items():
                if isinstance(value, property) and value.fget is not None:
                    properties.add(attr)
        return tuple(properties)


@dataclasses.dataclass(repr=False)
class _FileAttributesUnix(_FileAttributesCore, ABC):
    """Shared FileAttributes for Unix systems.

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
    in_cloud: bool
    """

    # ... Magic Methods ...
    def __post_init__(self: Self) -> None:
        """Initialize the FileAttributes instance."""
        super().__post_init__()
        self.mode = self.file.stat().st_mode
        self.extended_attributes = self.get_file_attributes(self.file)

    # ... Helper Methods ...
    @staticmethod
    @abstractmethod
    def get_file_attributes(path: Path) -> str | list[str]:
        """Retrieve the extended file attributes from the OS.

        Returns
        -------
        list[str]
            The extended file attributes as a list of strings.
        """

    @abstractmethod
    def set_file_attributes(
        self: Self,
        attributes: str | list[str],
        enable: bool = True,
    ) -> None:
        """Set the extended file attributes.

        Parameters
        ----------
        attributes : str
            The extended file attributes to set.
        """

    @abstractmethod
    def set_attribute(self: Self, attribute: int, enable: bool) -> None:
        """Set or unset a specific attribute.

        Parameters
        ----------
        attribute : int
            The attribute to set or unset.
        enable : bool
            True to enable the attribute, False to disable it.
        """

    # ... Properties ...
    @property
    def read_only(self: Self) -> bool:
        """A file that is read-only. Applications can read the file, but cannot write to it or delete it."""
        return not (self.mode & stat.S_IWUSR)

    @property
    def hidden(self: Self) -> bool:
        """The file or directory is hidden. It is not included in an ordinary directory listing."""
        return self.file.name.startswith(".")

    @property
    def executable(self: Self) -> bool:
        """A file that is executable."""
        return bool(self.mode & stat.S_IXUSR)

    @property
    def directory(self: Self) -> bool:
        """The handle that identifies a directory."""
        return stat.S_ISDIR(self.mode)

    @property
    def symlink(self: Self) -> bool:
        """The handle that identifies a symbolic link."""
        return stat.S_ISLNK(self.mode)

    # ... Setters ...
    def set_read_only(self: Self, enable: bool) -> None:
        """Set or unset the read-only attribute.

        Parameters
        ----------
        enable : bool
            True to enable the read-only attribute, False to disable it.
        """
        self.set_attribute(stat.S_IWUSR, not enable)

    def set_hidden(self: Self, enable: bool) -> None:
        """Set or unset the hidden attribute.

        Parameters
        ----------
        enable : bool
            True to enable the hidden attribute, False to disable it.
        """
        if enable:
            new_path = self.file.parent / (f".{self.file.name}")
            self.file.rename(new_path)
            self.file = new_path
        else:
            new_path = self.file.parent / self.file.name[1:]
            self.file.rename(new_path)
            self.file = new_path

    def set_executable(self: Self, enable: bool) -> None:
        """Set or unset the executable attribute.

        Parameters
        ----------
        enable : bool
            True to enable the executable attribute, False to disable it.
        """
        self.set_attribute(stat.S_IXUSR, enable)

    def set_immutable(self: Self, enable: bool) -> None:
        """Set or unset the immutable attribute.

        Parameters
        ----------
        enable : bool
            True to enable the immutable attribute, False to disable it.
        """
        self.set_file_attributes("+i" if enable else "-i")

    def set_append_only(self: Self, enable: bool) -> None:
        """Set or unset the append-only attribute.

        Parameters
        ----------
        enable : bool
            True to enable the append-only attribute, False to disable it.
        """
        self.set_file_attributes("+a" if enable else "-a")

    def set_no_dump(self: Self, enable: bool) -> None:
        """Set or unset the no dump attribute.

        Parameters
        ----------
        enable : bool
            True to enable the no dump attribute, False to disable it.
        """
        self.set_file_attributes("+d" if enable else "-d")
