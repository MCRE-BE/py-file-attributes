"""Command Line Interface for py-file-attributes."""

import argparse
from pathlib import Path

from file_attributes import FileAttributes


def str2bool(v: str) -> bool:
    """Convert string to boolean.

    Parameters
    ----------
    v : str
        The string to convert.

    Returns
    -------
    bool
        The converted boolean value.

    Raises
    ------
    argparse.ArgumentTypeError
        If the string cannot be converted to a boolean.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def main() -> None:
    """Run the CLI application."""
    parser = argparse.ArgumentParser(
        prog="file-attributes",
        description="A cross-platform library to manage file attributes on Windows, macOS, and Linux.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("file", type=Path, help="The file to examine or manage attributes for.")

    attrs = list(FileAttributes.get_property_fields(FileAttributes))
    attrs.sort()
    for attr in attrs:
        prop = getattr(FileAttributes, attr)
        doc = prop.__doc__ or "No description available."
        doc = doc.replace("\n", " ").strip()

        setter_name = f"set_{attr}"
        has_setter = hasattr(FileAttributes, setter_name)

        if has_setter:
            parser.add_argument(f"--{attr}", type=str2bool, metavar="BOOL", help=f"Set or unset: {doc}")

    args = parser.parse_args()

    try:
        file_attrs = FileAttributes(args.file)

        changed = False
        for attr in attrs:
            if hasattr(args, attr) and getattr(args, attr) is not None:
                val = getattr(args, attr)
                setter = getattr(file_attrs, f"set_{attr}")
                setter(val)
                changed = True

        if changed:
            # Refresh to reflect updated attributes
            file_attrs = FileAttributes(args.file)

        print(file_attrs)  # noqa: T201
    except Exception as e:
        print(f"Error: {e}")  # noqa: T201


if __name__ == "__main__":
    main()
