"""Windows specific implementation of FileAttributes."""

####################
# IMPORT STATEMENT #
####################
import ctypes
import dataclasses
from functools import cached_property
from pathlib import Path
from stat import (
    FILE_ATTRIBUTE_ARCHIVE,
    FILE_ATTRIBUTE_COMPRESSED,
    FILE_ATTRIBUTE_DEVICE,
    FILE_ATTRIBUTE_DIRECTORY,
    FILE_ATTRIBUTE_ENCRYPTED,
    FILE_ATTRIBUTE_HIDDEN,
    FILE_ATTRIBUTE_INTEGRITY_STREAM,
    FILE_ATTRIBUTE_NO_SCRUB_DATA,
    FILE_ATTRIBUTE_NORMAL,
    FILE_ATTRIBUTE_NOT_CONTENT_INDEXED,
    FILE_ATTRIBUTE_OFFLINE,
    FILE_ATTRIBUTE_READONLY,
    FILE_ATTRIBUTE_REPARSE_POINT,
    FILE_ATTRIBUTE_SPARSE_FILE,
    FILE_ATTRIBUTE_SYSTEM,
    FILE_ATTRIBUTE_TEMPORARY,
    FILE_ATTRIBUTE_VIRTUAL,
)

from typing_extensions import Self

from file_attributes._core import _FileAttributesCore

# See: https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
# Add missing attributes not defined in stat
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000  # FILE_ATTRIBUTE_EA
FILE_ATTRIBUTE_PINNED = 0x00080000
FILE_ATTRIBUTE_UNPINNED = 0x00100000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000


###########
# CLASSES #
###########
@dataclasses.dataclass(repr=False, eq=True)
class FileAttributesWindows(_FileAttributesCore):
    """Access the File metadata Attributes.

    See Also
    --------
    https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants

    Attributes
    ----------
    read_only: bool
    hidden: bool
    system: bool
    directory: bool
    archive: bool
    device: bool
    normal: bool
    temporary: bool
    sparse: bool
    reparse: bool
    compressed: bool
    offline: bool
    in_cloud : alias for recall_on_data_access
    not_content_indexed: bool
    encrypted: bool
    integrity_stream: bool
    virtual: bool
    no_scrub_data: bool
    pinned: bool
    unpinned: bool
    recall_on_open: bool
    recall_on_data_access: bool

    Methods
    -------
    set_read_only
    set_hidden
    # set_system
    set_directory
    set_archive
    # set_device
    set_normal
    set_temporary
    set_sparse
    set_reparse
    set_compressed
    set_offline
    set_not_content_indexed
    set_encrypted
    set_integrity_stream
    set_virtual
    set_no_scrub_data
    set_pinned
    set_unpinned
    set_recall_on_open
    set_recall_on_data_access

    Notes
    -----
    Common File Attributes:

    +-------------------------+-----------------------------------------------------------------------------------------------+
    | Attribute               | Description                                                                                   |
    +=========================+===============================================================================================+
    | read_only               | A file that is read-only. Applications can read the file, but cannot write to it or delete    |
    |                         | it.                                                                                           |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | hidden                  | The file or directory is hidden. It is not included in an ordinary directory listing.         |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | system                  | A file or directory that the operating system uses a part of, or uses exclusively.            |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | directory               | The handle that identifies a directory.                                                       |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | archive                 | A file or directory that is an archive file or directory. Applications typically use this     |
    |                         | attribute to mark files for backup or removal.                                                |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | device                  | Value reserved for system use.                                                                |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | normal                  | A file that does not have other attributes set. This attribute is valid only when used alone. |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | temporary               | A file that is being used for temporary storage. File systems avoid writing data back to mass |
    |                         | storage if sufficient cache memory is available, because typically, an application deletes a  |
    |                         | temporary file after the handle is closed. In that scenario, the system can entirely avoid    |
    |                         | writing the data. Otherwise, the data is written after the handle is closed.                  |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | sparse                  | A file that is a sparse file.                                                                 |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | reparse                 | A file or directory that has an associated reparse point, or a file that is a symbolic link.  |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | compressed              | A file or directory that is compressed. For a file, all of the data in the file is            |
    |                         | compressed. For a directory, compression is the default for newly created files and           |
    |                         | subdirectories.                                                                               |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | offline                 | The data of a file is not available immediately. This attribute indicates that the file data  |
    |                         | is physically moved to offline storage. This attribute is used by Remote Storage, which is    |
    |                         | the hierarchical storage management software. Applications should not arbitrarily change this |
    |                         | attribute.                                                                                    |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | not_content_indexed     | The file or directory is not to be indexed by the content indexing service.                   |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | encrypted               | A file or directory that is encrypted. For a file, all data streams in the file are           |
    |                         | encrypted. For a directory, encryption is the default for newly created files and             |
    |                         | subdirectories.                                                                               |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | integrity_stream        | The directory or user data stream is configured with integrity (only supported on ReFS        |
    |                         | volumes). It is not included in an ordinary directory listing. The integrity setting persists |
    |                         | with the file if it's renamed. If a file is copied the destination file will have integrity   |
    |                         | set if either the source file or destination directory have integrity set.                    |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | virtual                 | Value reserved for system use.                                                                |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | no_scrub_data           | The user data stream not to be read by the background data integrity scanner (AKA scrubber).  |
    |                         | When set on a directory it only provides inheritance. This flag is only supported on Storage  |
    |                         | Spaces and ReFS volumes. It is not included in an ordinary directory listing.                 |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | pinned                  | File or directory should be kept fully present locally even when not being actively accessed. |
    |                         | This attribute is for use with hierarchical storage management software.                      |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | unpinned                | File or directory should not be kept fully present locally except when being actively         |
    |                         | accessed. This attribute is for use with hierarchical storage management software.            |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | recall_on_open          | File or directory has no physical representation on the local system; the item is virtual.    |
    |                         | Opening the item will be more expensive than normal, e.g. it will cause at least some of it   |
    |                         | to be fetched from a remote store. This attribute only appears in directory enumeration       |
    |                         | classes (FILE_DIRECTORY_INFORMATION, FILE_BOTH_DIR_INFORMATION, etc.).                        |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    | recall_on_data_access   | File or directory is not fully present locally. For a file that means that not all of its     |
    |                         | data is on local storage (e.g. it may be sparse with some data still in remote storage). For  |
    |                         | a directory it means that some of the directory contents are being virtualized from another   |
    |                         | location. Reading the file / enumerating the directory will be more expensive than normal,    |
    |                         | e.g. it will cause at least some of the file/directory content to be fetched from a remote    |
    |                         | store. Only kernel-mode callers can set this bit.                                             |
    +-------------------------+-----------------------------------------------------------------------------------------------+
    """

    # ... Helper Methods
    @staticmethod
    def get_file_attributes(path: Path) -> int:
        """Retrieve the file attributes from the OS.

        Parameters
        ----------
        path : Path
            The path to the file.

        Returns
        -------
        int
            The file attributes as an integer.

        Notes
        -----
        Returns an integer, but the real data is stored in binary format.
        Credits to https://stackoverflow.com/a/77225871/20716078
        """
        windll = getattr(ctypes, "windll")  # noqa: B009
        _t = windll.kernel32.GetFileAttributesW(str(path))
        return _t or 0

    def set_file_attributes(
        self: Self,
        attributes: int,
    ) -> None:
        """Set the file attributes.

        Parameters
        ----------
        path : Path
            The path to the file.
        attributes : int
            The file attributes to set.
        """
        windll = getattr(ctypes, "windll")  # noqa: B009
        windll.kernel32.SetFileAttributesW(str(self.file), attributes)

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
            self.raw_attribute_mask |= attribute
        else:
            self.raw_attribute_mask &= ~attribute
        self.set_file_attributes(self.raw_attribute_mask)

    # ... All Properties ...
    @cached_property
    def raw_attribute_mask(self: Self) -> int:
        return self.get_file_attributes(Path(self.file))

    @property
    def read_only(self: Self) -> bool:
        """A file that is read-only. Applications can read the file, but cannot write to it or delete it."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_READONLY) == FILE_ATTRIBUTE_READONLY

    @property
    def hidden(self: Self) -> bool:
        """The file or directory is hidden. It is not included in an ordinary directory listing."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_HIDDEN) == FILE_ATTRIBUTE_HIDDEN

    @property
    def system(self: Self) -> bool:
        """A file or directory that the operating system uses a part of, or uses exclusively."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_SYSTEM) == FILE_ATTRIBUTE_SYSTEM

    @property
    def directory(self: Self) -> bool:
        """The handle that identifies a directory."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_DIRECTORY) == FILE_ATTRIBUTE_DIRECTORY

    @property
    def archive(self: Self) -> bool:
        """A file or directory that is an archive file or directory.

        Applications typically use this attribute to mark files for backup or removal.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_ARCHIVE) == FILE_ATTRIBUTE_ARCHIVE

    @property
    def device(self: Self) -> bool:
        """Value reserved for system use."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_DEVICE) == FILE_ATTRIBUTE_DEVICE

    @property
    def normal(self: Self) -> bool:
        """A file that does not have other attributes set.

        This attribute is valid only when used alone.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_NORMAL) == FILE_ATTRIBUTE_NORMAL

    @property
    def temporary(self: Self) -> bool:
        """A file that is being used for temporary storage.

        File systems avoid writing data back to mass storage if sufficient cache memory is available,
        because typically, an application deletes a temporary file after the handle is closed.
        In that scenario, the system can entirely avoid writing the data. Otherwise, the data
        is written after the handle is closed.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_TEMPORARY) == FILE_ATTRIBUTE_TEMPORARY

    @property
    def sparse(self: Self) -> bool:
        """A file that is a sparse file."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_SPARSE_FILE) == FILE_ATTRIBUTE_SPARSE_FILE

    @property
    def reparse(self: Self) -> bool:
        """A file or directory that has an associated reparse point, or a file that is a symbolic link."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_REPARSE_POINT) == FILE_ATTRIBUTE_REPARSE_POINT

    @property
    def compressed(self: Self) -> bool:
        """A file or directory that is compressed.

        For a file, all of the data in the file is compressed. For a directory, compression is
        the default for newly created files and subdirectories.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_COMPRESSED) == FILE_ATTRIBUTE_COMPRESSED

    @property
    def offline(self: Self) -> bool:
        """The data of a file is not available immediately.

        This attribute indicates that the file data is physically moved to offline storage.
        This attribute is used by Remote Storage, which is the hierarchical storage management software.
        Applications should not arbitrarily change this attribute.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_OFFLINE) == FILE_ATTRIBUTE_OFFLINE

    @property
    def not_content_indexed(self: Self) -> bool:
        """The file or directory is not to be indexed by the content indexing service."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_NOT_CONTENT_INDEXED) == FILE_ATTRIBUTE_NOT_CONTENT_INDEXED

    @property
    def encrypted(self: Self) -> bool:
        """A file or directory that is encrypted.

        For a file, all data streams in the file are encrypted.
        For a directory, encryption is the default for newly created files and subdirectories.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_ENCRYPTED) == FILE_ATTRIBUTE_ENCRYPTED

    @property
    def integrity_stream(self: Self) -> bool:
        """The directory or user data stream is configured with integrity (only supported on ReFS volumes).

        It is not included in an ordinary directory listing. The integrity setting persists with the file if
        it's renamed. If a file is copied the destination file will have integrity set if either the source
        file or destination directory have integrity set.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_INTEGRITY_STREAM) == FILE_ATTRIBUTE_INTEGRITY_STREAM

    @property
    def virtual(self: Self) -> bool:
        """Value reserved for system use."""
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_VIRTUAL) == FILE_ATTRIBUTE_VIRTUAL

    @property
    def no_scrub_data(self: Self) -> bool:
        """The user data stream not to be read by the background data integrity scanner (AKA scrubber).

        When set on a directory it only provides inheritance. This flag is only supported on Storage Spaces
        and ReFS volumes. It is not included in an ordinary directory listing.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_NO_SCRUB_DATA) == FILE_ATTRIBUTE_NO_SCRUB_DATA

    @property
    def pinned(self: Self) -> bool:
        """File or directory should be kept fully present locally even when not being actively accessed.

        This attribute is for use with hierarchical storage management software.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_PINNED) == FILE_ATTRIBUTE_PINNED

    @property
    def unpinned(self: Self) -> bool:
        """File or directory should not be kept fully present locally except when being actively accessed.

        This attribute is for use with hierarchical storage management software.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_UNPINNED) == FILE_ATTRIBUTE_UNPINNED

    @property
    def recall_on_open(self: Self) -> bool:
        """File or directory has no physical representation on the local system; the item is virtual.

        Opening the item will be more expensive than normal, e.g. it will cause at least some of it to be fetched from a remote store.
        This attribute only appears in directory enumeration classes (FILE_DIRECTORY_INFORMATION, FILE_BOTH_DIR_INFORMATION, etc.).
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_RECALL_ON_OPEN) == FILE_ATTRIBUTE_RECALL_ON_OPEN

    @property
    def recall_on_data_access(self: Self) -> bool:
        """File or directory is not fully present locally.

        For a file that means that not all of its data is on local storage (e.g. it may be sparse with some data still
        in remote storage). For a directory it means that some of the directory contents are being virtualized from
        another location. Reading the file / enumerating the directory will be more expensive than normal, e.g. it will
        cause at least some of the file/directory content to be fetched from a remote store. Only kernel-mode callers
        can set this bit.
        """
        return (self.raw_attribute_mask & FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS) == FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS

    @property
    def in_cloud(self: Self) -> bool:
        """Alias for self.recall_on_data_access."""
        return self.recall_on_data_access

    # ... All Setters ...
    def set_read_only(self: Self, enable: bool) -> None:
        """Set or unset the read-only attribute.

        Parameters
        ----------
        enable : bool
            True to enable the read-only attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_READONLY, enable)

    def set_hidden(self: Self, enable: bool) -> None:
        """Set or unset the hidden attribute.

        Parameters
        ----------
        enable : bool
            True to enable the hidden attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_HIDDEN, enable)

    # ! : Removed to not mess with System files
    # def set_system(self: Self, enable: bool) -> None:
    #     """Set or unset the system attribute.

    #     Parameters
    #     ----------
    #     enable : bool
    #         True to enable the system attribute, False to disable it.
    #     """
    #     self.set_attribute(FILE_ATTRIBUTE_SYSTEM, enable)

    def set_directory(self: Self, enable: bool) -> None:
        """Set or unset the directory attribute.

        Parameters
        ----------
        enable : bool
            True to enable the directory attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_DIRECTORY, enable)

    def set_archive(self: Self, enable: bool) -> None:
        """Set or unset the archive attribute.

        Parameters
        ----------
        enable : bool
            True to enable the archive attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_ARCHIVE, enable)

    # ! : Removed to not mess with System files
    # def set_device(self: Self, enable: bool) -> None:
    #     """Set or unset the device attribute.

    #     Parameters
    #     ----------
    #     enable : bool
    #         True to enable the device attribute, False to disable it.
    #     """
    #     self.set_attribute(FILE_ATTRIBUTE_DEVICE, enable)

    def set_normal(self: Self, enable: bool) -> None:
        """Set or unset the normal attribute.

        Parameters
        ----------
        enable : bool
            True to enable the normal attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_NORMAL, enable)

    def set_temporary(self: Self, enable: bool) -> None:
        """Set or unset the temporary attribute.

        Parameters
        ----------
        enable : bool
            True to enable the temporary attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_TEMPORARY, enable)

    def set_sparse(self: Self, enable: bool) -> None:
        """Set or unset the sparse attribute.

        Parameters
        ----------
        enable : bool
            True to enable the sparse attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_SPARSE_FILE, enable)

    def set_reparse(self: Self, enable: bool) -> None:
        """Set or unset the reparse attribute.

        Parameters
        ----------
        enable : bool
            True to enable the reparse attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_REPARSE_POINT, enable)

    def set_compressed(self: Self, enable: bool) -> None:
        """Set or unset the compressed attribute.

        Parameters
        ----------
        enable : bool
            True to enable the compressed attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_COMPRESSED, enable)

    # ! : Removed to not mess with System files
    # def set_offline(self: Self, enable: bool) -> None:
    #     """Set or unset the offline attribute.

    #     Parameters
    #     ----------
    #     enable : bool
    #         True to enable the offline attribute, False to disable it.
    #     """
    #     self.set_attribute(FILE_ATTRIBUTE_OFFLINE, enable)

    def set_not_content_indexed(self: Self, enable: bool) -> None:
        """Set or unset the not content indexed attribute.

        Parameters
        ----------
        enable : bool
            True to enable the not content indexed attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_NOT_CONTENT_INDEXED, enable)

    def set_encrypted(self: Self, enable: bool) -> None:
        """Set or unset the encrypted attribute.

        Parameters
        ----------
        enable : bool
            True to enable the encrypted attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_ENCRYPTED, enable)

    def set_integrity_stream(self: Self, enable: bool) -> None:
        """Set or unset the integrity stream attribute.

        Parameters
        ----------
        enable : bool
            True to enable the integrity stream attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_INTEGRITY_STREAM, enable)

    def set_virtual(self: Self, enable: bool) -> None:
        """Set or unset the virtual attribute.

        Parameters
        ----------
        enable : bool
            True to enable the virtual attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_VIRTUAL, enable)

    def set_no_scrub_data(self: Self, enable: bool) -> None:
        """Set or unset the no scrub data attribute.

        Parameters
        ----------
        enable : bool
            True to enable the no scrub data attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_NO_SCRUB_DATA, enable)

    def set_pinned(self: Self, enable: bool) -> None:
        """Set or unset the pinned attribute.

        Parameters
        ----------
        enable : bool
            True to enable the pinned attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_PINNED, enable)

    def set_unpinned(self: Self, enable: bool) -> None:
        """Set or unset the unpinned attribute.

        Parameters
        ----------
        enable : bool
            True to enable the unpinned attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_UNPINNED, enable)

    def set_recall_on_open(self: Self, enable: bool) -> None:
        """Set or unset the recall on open attribute.

        Parameters
        ----------
        enable : bool
            True to enable the recall on open attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_RECALL_ON_OPEN, enable)

    def set_recall_on_data_access(self: Self, enable: bool) -> None:
        """Set or unset the recall on data access attribute.

        Parameters
        ----------
        enable : bool
            True to enable the recall on data access attribute, False to disable it.
        """
        self.set_attribute(FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS, enable)
