#!/usr/bin/env bash
# run.sh: see the tool work on the synthetic data in examples/, with no setup.
# It installs into a temporary copy of examples/herdr-home, then undoes it.
# The output must match examples/expected-output.txt (a test checks it).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/space_logos.py --demo
