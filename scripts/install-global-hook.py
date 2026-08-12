#!/usr/bin/env python3
"""Install the tracked finish critic as the global Codex Stop hook."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / "hooks" / "finalization_guard.py"
MANAGED_FRAGMENT = "/hooks/finalization_guard.py"


def _atomic_write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _hooks_document(existing: bytes | None, codex_home: Path, python: Path) -> bytes:
    if existing:
        document = json.loads(existing.decode("utf-8"))
        if not isinstance(document, dict):
            raise ValueError("hooks.json must contain a JSON object")
    else:
        document = {}

    hooks = document.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks.json 'hooks' must be a JSON object")
    stop_groups = hooks.setdefault("Stop", [])
    if not isinstance(stop_groups, list):
        raise ValueError("hooks.json hooks.Stop must be a JSON array")

    retained = []
    for group in stop_groups:
        if not isinstance(group, dict):
            retained.append(group)
            continue
        commands = group.get("hooks")
        if not isinstance(commands, list):
            retained.append(group)
            continue
        filtered = [
            item
            for item in commands
            if not (
                isinstance(item, dict)
                and MANAGED_FRAGMENT in str(item.get("command") or "")
            )
        ]
        if filtered:
            copied = dict(group)
            copied["hooks"] = filtered
            retained.append(copied)

    command = f'{python} "{codex_home / "hooks" / "finalization_guard.py"}" Stop'
    retained.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": 240,
                    "statusMessage": "Running independent finish critic",
                }
            ]
        }
    )
    hooks["Stop"] = retained
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _config_document(existing: bytes | None) -> bytes:
    text = existing.decode("utf-8") if existing else ""
    lines = text.splitlines()
    output: list[str] = []
    in_features = False
    found_features = False
    wrote_hooks = False

    for line in lines:
        section = re.match(r"^\s*\[([^]]+)]\s*$", line)
        if section:
            if in_features and not wrote_hooks:
                output.append("hooks = true")
                wrote_hooks = True
            in_features = section.group(1).strip() == "features"
            found_features = found_features or in_features
            output.append(line)
            continue
        if in_features and re.match(r"^\s*(?:hooks|codex_hooks)\s*=", line):
            if not wrote_hooks:
                output.append("hooks = true")
                wrote_hooks = True
            continue
        output.append(line)

    if in_features and not wrote_hooks:
        output.append("hooks = true")
    if not found_features:
        if output and output[-1].strip():
            output.append("")
        output.extend(("[features]", "hooks = true"))
    return ("\n".join(output).rstrip() + "\n").encode("utf-8")


def install(codex_home: Path, python: Path) -> None:
    targets = {
        codex_home / "hooks" / "finalization_guard.py": SOURCE_HOOK.read_bytes(),
        codex_home / "hooks.json": None,
        codex_home / "config.toml": None,
    }
    originals = {path: path.read_bytes() if path.exists() else None for path in targets}
    targets[codex_home / "hooks.json"] = _hooks_document(
        originals[codex_home / "hooks.json"], codex_home, python
    )
    targets[codex_home / "config.toml"] = _config_document(
        originals[codex_home / "config.toml"]
    )

    written: list[Path] = []
    try:
        for path, content in targets.items():
            assert content is not None
            _atomic_write(path, content, 0o755 if path.name.endswith(".py") else 0o644)
            written.append(path)
    except Exception:
        for path in reversed(written):
            original = originals[path]
            if original is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                _atomic_write(
                    path, original, 0o755 if path.name.endswith(".py") else 0o644
                )
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--python", type=Path, default=Path(sys.executable).resolve())
    args = parser.parse_args()
    codex_home = args.codex_home.expanduser().resolve()
    install(codex_home, args.python.expanduser().resolve())
    print(f"Installed finish critic hook in {codex_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
