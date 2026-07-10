#!/bin/sh
set -eu

python -m compileall -q src
python -m pytest -q

wheel_count="$(find dist -maxdepth 1 -type f -name 'ixunfei_docx_reader-*.whl' | wc -l | tr -d '[:space:]')"
if [ "$wheel_count" -ne 1 ]; then
    echo "expected exactly one wheel under dist/, found $wheel_count" >&2
    exit 1
fi

wheel="$(find dist -maxdepth 1 -type f -name 'ixunfei_docx_reader-*.whl' -print)"
smoke_root="$(mktemp -d "${TMPDIR:-/tmp}/ixfdoc-smoke.XXXXXX")"
trap 'rm -rf "$smoke_root"' EXIT HUP INT TERM

venv_dir="$smoke_root/venv"
smoke_home="$smoke_root/home"
mkdir -p "$smoke_home"
python -m venv --system-site-packages "$venv_dir"

venv_python="$venv_dir/bin/python"
venv_ixfdoc="$venv_dir/bin/ixfdoc"
"$venv_python" -m pip install --no-deps "$wheel"

package_version=$("$venv_python" -c 'import importlib.metadata; print(importlib.metadata.version("ixunfei-docx-reader"))')
cli_version=$(HOME="$smoke_home" "$venv_ixfdoc" --version)
if [ "$cli_version" != "ixfdoc $package_version" ]; then
    echo "CLI version mismatch: $cli_version != ixfdoc $package_version" >&2
    exit 1
fi

printf '%s\n' "$cli_version"
HOME="$smoke_home" "$venv_ixfdoc" doctor --json >/dev/null
HOME="$smoke_home" "$venv_ixfdoc" setup skills --runtimes codex --json >/dev/null

skill_path="$smoke_home/.codex/skills/ixunfei-docx-reader/SKILL.md"
test -f "$skill_path"
grep -q "ixfdoc outline" "$skill_path"
