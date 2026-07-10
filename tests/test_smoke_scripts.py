from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_posix_smoke_uses_built_wheel_in_isolated_environment() -> None:
    script = (ROOT / "scripts" / "smoke.sh").read_text(encoding="utf-8")

    assert 'python -m venv --system-site-packages "$venv_dir"' in script
    assert '"$venv_python" -m pip install --no-deps "$wheel"' in script
    assert 'HOME="$smoke_home" "$venv_ixfdoc" --version' in script
    assert 'setup skills --runtimes codex --json' in script
    assert 'package_version=$("$venv_python" -c' in script
    assert "\nixfdoc --version\n" not in script


def test_windows_smoke_uses_built_wheel_in_isolated_environment() -> None:
    script = (ROOT / "scripts" / "smoke.ps1").read_text(encoding="utf-8")

    assert "python -m venv --system-site-packages $VenvDir" in script
    assert "$VenvPython -m pip install --no-deps $Wheel.FullName" in script
    assert "$VenvIxfdoc --version" in script
    assert "setup skills --runtimes codex --json" in script
    assert "importlib.metadata" in script
    assert "Invoke-NativeCommand ixfdoc --version" not in script
