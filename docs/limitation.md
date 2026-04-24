---
hide:
  - navigation
---

# Limitations

### Platform-Specific Attributes
Because file systems fundamentally differ between Windows and Unix-like operating systems, `py-file-attributes` exposes platform-specific properties natively. 

Accessing an attribute like `archive` on macOS, or `immutable` on Windows, will result in an `AttributeError` at runtime, and static type checkers like `pyright` may complain if the instance is not correctly type-cast in cross-platform environments. 

### Privileges
Certain attributes, especially on Unix systems (like `immutable` and `append_only`), require elevated privileges (`sudo` or `root` access) to set or unset via `chattr` or `chflags`. An error will be raised if you attempt to modify these without the required permissions.
