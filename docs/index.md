---
hide:
  - navigation
---

# py-file-attributes

**py-file-attributes** is a cross-platform python library for managing file attributes on Windows, macOS, and Linux.

It provides a unified, simple API to set and get file attributes such as `read_only`, `hidden`, and platform-specific attributes like `archive` or `immutable`.

Basic usage:

```python
from pathlib import Path
from file_attributes import FileAttributes

file_attrs = FileAttributes(Path("my_file.txt"))

# Check if the file is read-only
print(file_attrs.read_only)

# Set the file to read-only
file_attrs.set_read_only(True)
```