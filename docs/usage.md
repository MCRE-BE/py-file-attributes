---
hide:
  - navigation
---

# Usage

`py-file-attributes` dynamically provides the correct handler based on your operating system.

## Basic Operations

You can set and get common attributes that are available across all platforms.

```python
from pathlib import Path
from file_attributes import FileAttributes

attrs = FileAttributes(Path("example.txt"))

# Read-only
attrs.set_read_only(True)
print(f"Is read-only: {attrs.read_only}")

# Hidden
attrs.set_hidden(True)
print(f"Is hidden: {attrs.hidden}")

# Check if it's a directory
print(f"Is directory: {attrs.directory}")
```

## Platform-Specific Attributes

Some attributes only make sense on specific operating systems. Be careful when accessing these in cross-platform code, as they will raise an `AttributeError` if the attribute does not exist on the host OS.

### Windows
```python
# Archive
attrs.set_archive(True)
print(attrs.archive)

# Compressed
attrs.set_compressed(True)
print(attrs.compressed)
```

### macOS / Linux
```python
# Immutable
attrs.set_immutable(True)
print(attrs.immutable)

# Append Only
attrs.set_append_only(True)
print(attrs.append_only)

# No Dump
attrs.set_no_dump(True)
print(attrs.no_dump)
```
