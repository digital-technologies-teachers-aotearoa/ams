#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import sys

from configurations.management import execute_from_command_line


def main() -> None:
    """Run administrative tasks."""
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
