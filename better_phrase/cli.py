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

    timing_parser = sub.add_parser(
        "timing",
        help="Show or change the overhead-timing display.",
    )
    timing_parser.add_argument(
        "state",
        nargs="?",
        choices=("on", "off"),
        default=None,
        help="'on' to show timing footer in every BP block, 'off' to hide.",
    )

    args = parser.parse_args(argv)

    if args.command == "hook":
        from .hook import run

        return run()

    if args.command == "translate":
        return _translate_command(args.state)

    if args.command == "timing":
        return _timing_command(args.state)

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


def _timing_command(new_state: str | None) -> int:
    if new_state is None:
        current = "on" if config.get_show_timing() else "off"
        print(f"Overhead timing display: {current}")
        print()
        print("When on, every BP block ends with a footer like:")
        print("  *(⏱ Better Phrase: 52ms hook)*")
        print()
        print("To toggle:")
        print("  better-phrase timing on     # show timing footer")
        print("  better-phrase timing off    # hide it")
        return 0

    enabled = new_state == "on"
    config.set_show_timing(enabled)
    if enabled:
        print("✓ Timing display: on")
        print("  Every BP block now ends with a ⏱ overhead line.")
    else:
        print("✓ Timing display: off")
        print("  BP blocks will no longer include the overhead line.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
