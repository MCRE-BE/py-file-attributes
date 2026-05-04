# File Attributes

A cross-platform library to manage file attributes on Windows, macOS, and Linux.

## Features

- Set and get file attributes such as read-only, hidden, executable, etc.
- Supports Windows, macOS, and Linux.
- Easy-to-use API.

## CLI Usage

The package comes with a command-line interface to easily view or manage attributes for a given file.

```sh
# View attributes of a file
file-attributes example.txt

# Set or unset an attribute (pass True/1 or False/0)
file-attributes example.txt --hidden True
file-attributes example.txt --read_only False
```

You can view all available flags for your operating system using:
```sh
file-attributes --help
```

## Installation

You can install the library using pip:

```sh
pip install py-file-attributes
```

## Development & Testing

When developing locally, we use `pytest` and `coverage` to ensure code quality.

**Important Note on Coverage:** `py-file-attributes` is a cross-platform library. If you run test coverage locally on a single operating system (e.g., macOS), your local coverage report will naturally be lower than 100%. This is expected because Python will safely skip over OS-specific files (like `_windows.py` and `_linux.py`) and tests that belong to the other operating systems. Do not attempt to force 100% coverage locally. Instead, push your branch and let the GitHub Actions CI pipeline run tests across Ubuntu, Windows, and macOS to achieve and report the true 100% aggregate coverage.

## Credits
The project was initially inspired by : [eden from Meta](https://github.com/facebook/sapling/blob/0.2.20241203-120811%2Ba2174689/eden/integration/projfs_buffer.py).
The code was initially heavily manually modified, before being used as a good generation test for AI. Final code was ran through [Le Chat from Mistral AI](https://chat.mistral.ai/chat).
