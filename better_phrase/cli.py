"""Command-line entry point: `better-phrase <subcommand>`."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import __version__, config


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="better-phrase",
        description="Better Phrase — English phrasing polish via Claude Code hook.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    sub.add_parser(
        "hook",
        help="Read a UserPromptSubmit payload from stdin and emit polish context.",
    )

    translate_parser = sub.add_parser(
        "translate",
        help="Show or change the Chinese-to-English translation setting.",
    )
    translate_parser.add_argument(
        "state",
        nargs="?",
        choices=("on", "off"),
        default=None,
        help="'on' to enable, 'off' to disable. Omit to show current state.",
    )

    args = parser.parse_args(argv)

    if args.command == "hook":
        from .hook import run

        return run()

    if args.command == "translate":
        return _translate_command(args.state)

    parser.print_help()
    return 1


def _translate_command(new_state: str | None) -> int:
    if new_state is None:
        current = "on" if config.get_translate_enabled() else "off"
        print(f"Chinese translation: {current}")
        print()
        print("English polish is always on (the product's core feature).")
        print("To toggle translation:")
        print("  better-phrase translate on    # enable")
        print("  better-phrase translate off   # disable")
        return 0

    enabled = new_state == "on"
    config.set_translate_enabled(enabled)
    if enabled:
        print("✓ Chinese translation: on")
        print("  Writing Chinese will now show an English version above the response.")
    else:
        print("✓ Chinese translation: off")
        print("  Writing Chinese will be silent. English polish is still active.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
