#!/usr/bin/env bash
# Better Phrase — UserPromptSubmit hook shim.
#
# The actual logic lives in the better_phrase/ Python package next to this file.
# Keeping a bash shim here means hooks.json / settings.json never needs to change
# when the Python implementation evolves.

set -eu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If python3 is missing, no-op silently — never break the user's Claude session.
if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m better_phrase hook
