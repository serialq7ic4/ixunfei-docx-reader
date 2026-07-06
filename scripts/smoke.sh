#!/bin/sh
set -eu

python -m compileall -q src
python -m pytest -q
ixfdoc --version
ixfdoc doctor --json >/dev/null
ixfdoc setup skills --runtimes none --json >/dev/null
