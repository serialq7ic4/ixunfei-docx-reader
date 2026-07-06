$ErrorActionPreference = "Stop"

python -m compileall -q src
python -m pytest -q
ixfdoc --version
ixfdoc doctor --json | Out-Null
ixfdoc setup skills --runtimes none --json | Out-Null
