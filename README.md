# Vigil

**Vigil** is a lightweight Python monitoring/watchdog project for keeping an eye on files, folders, scripts, small systems, and repeated checks.

The aim is simple: give a project a watchful layer that can notice when something changes, breaks, goes stale, or needs attention — without turning it into a heavy enterprise monitoring platform.

## What Vigil is for

Vigil is intended for small, practical monitoring tasks such as:

- Watching files or folders for changes
- Checking whether expected files still exist
- Spotting stale outputs or missed updates
- Logging simple project events clearly
- Running repeatable checks from a script or command line
- Helping developers learn how monitoring, automation, and watchdog-style Python tools work

## Project status

This repository is currently an early-stage scaffold. The README defines the project direction and replaces an incorrect copied README from another project.

The next step is to add the actual Python package/module structure and the first working watcher/check utilities.

## Planned features

- File and folder watching
- Simple check functions for common project health tasks
- Clear console output and optional log files
- Small command-line interface
- Beginner-readable Python with comments and docstrings
- Tests for the core checks
- Example scripts showing real use cases

## Suggested structure

```text
Vigil/
├── vigil/
│   ├── __init__.py
│   ├── watcher.py
│   ├── checks.py
│   └── logging_utils.py
├── examples/
│   └── watch_folder.py
├── tests/
│   └── test_checks.py
├── README.md
└── LICENSE
```

## Example direction

Once the package is implemented, usage could look like this:

```python
from vigil import watch_path

watch_path("./my-project", on_change=print)
```

Or from the command line:

```bash
python -m vigil watch ./my-project
```

These examples show the intended direction, not a finished API yet.

## Roadmap

1. Add the base `vigil` package folder
2. Create a simple folder watcher
3. Add basic health-check helpers
4. Add CLI support
5. Add examples
6. Add tests
7. Cut the first release once the core watcher works

## Why the name

A vigil is a watch kept over something important. That fits the purpose of the project: a small tool that quietly watches a project and alerts you when something changes or needs attention.

## License

MIT License.
