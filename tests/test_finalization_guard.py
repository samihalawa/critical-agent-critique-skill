import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


guard = load_module("finalization_guard", ROOT / "hooks" / "finalization_guard.py")
installer = load_module(
    "install_global_hook", ROOT / "scripts" / "install-global-hook.py"
)


class GuardTests(unittest.TestCase):
    def invoke(self, stdin: str, verdict: tuple[str, str]):
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["finalization_guard.py", "Stop"]),
            mock.patch.object(sys, "stdin", io.StringIO(stdin)),
            mock.patch.object(sys, "stdout", stdout),
            mock.patch.object(guard, "_run_critic", return_value=verdict),
        ):
            self.assertEqual(guard.main(), 0)
        return json.loads(stdout.getvalue())

    def test_pass_continues(self):
        result = self.invoke("{}", ("pass", "complete at the promised layer"))
        self.assertTrue(result["continue"])
        self.assertIn("PASS", result["systemMessage"])

    def test_revise_blocks_with_root_cause_instruction(self):
        result = self.invoke("{}", ("revise", "missing remote read-back"))
        self.assertEqual(result["decision"], "block")
        self.assertIn("root cause", result["reason"])
        self.assertIn("sweep sibling", result["reason"])

    def test_malformed_input_blocks(self):
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["finalization_guard.py", "Stop"]),
            mock.patch.object(sys, "stdin", io.StringIO("{")),
            mock.patch.object(sys, "stdout", stdout),
        ):
            self.assertEqual(guard.main(), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["decision"], "block")
        self.assertIn("input was invalid", result["reason"])

    def test_critic_error_blocks_first_attempt(self):
        result = self.invoke("{}", ("error", "critic unavailable"))
        self.assertEqual(result["decision"], "block")

    def test_critic_error_allows_one_active_continuation(self):
        result = self.invoke(
            '{"stop_hook_active": true}', ("error", "critic unavailable")
        )
        self.assertTrue(result["continue"])
        self.assertIn("unavailable after one continuation", result["systemMessage"])

    def test_reviewer_disables_hooks_to_prevent_recursion(self):
        command = guard._review_command("/tmp", "/tmp/result")
        self.assertEqual(command[command.index("--disable") + 1], "hooks")
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")

    def test_verdict_parser_requires_first_nonempty_line(self):
        self.assertEqual(guard._parse_verdict("\nPASS: good"), ("pass", "good"))
        self.assertEqual(guard._parse_verdict("REVISE: gap"), ("revise", "gap"))
        self.assertEqual(guard._parse_verdict("preface\nPASS: late")[0], "error")


class InstallerTests(unittest.TestCase):
    def test_install_is_idempotent_preserves_other_hooks_and_enables_feature(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory) / ".codex"
            codex_home.mkdir()
            (codex_home / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {
                                    "hooks": [
                                        {"type": "command", "command": "keep-me"}
                                    ]
                                },
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": (
                                                "python /old/hooks/"
                                                "finalization_guard.py Stop"
                                            ),
                                        }
                                    ]
                                },
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            (codex_home / "config.toml").write_text(
                'model = "gpt-5"\n\n[features]\ncodex_hooks = false\nother = true\n',
                encoding="utf-8",
            )

            installer.install(codex_home, Path("/usr/bin/python3"))
            snapshot = {
                path.relative_to(codex_home): path.read_bytes()
                for path in codex_home.rglob("*")
                if path.is_file()
            }
            installer.install(codex_home, Path("/usr/bin/python3"))
            repeated = {
                path.relative_to(codex_home): path.read_bytes()
                for path in codex_home.rglob("*")
                if path.is_file()
            }
            self.assertEqual(snapshot, repeated)
            self.assertEqual(
                (codex_home / "hooks" / "finalization_guard.py").read_bytes(),
                (ROOT / "hooks" / "finalization_guard.py").read_bytes(),
            )

            document = json.loads(
                (codex_home / "hooks.json").read_text(encoding="utf-8")
            )
            commands = [
                hook["command"]
                for group in document["hooks"]["Stop"]
                for hook in group.get("hooks", [])
                if isinstance(hook, dict) and "command" in hook
            ]
            self.assertIn("keep-me", commands)
            managed = [
                command
                for command in commands
                if installer.MANAGED_FRAGMENT in command
            ]
            self.assertEqual(len(managed), 1)
            self.assertIn(
                str(codex_home / "hooks" / "finalization_guard.py"), managed[0]
            )

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn("[features]\nhooks = true\nother = true", config)
            self.assertNotIn("codex_hooks", config)


if __name__ == "__main__":
    unittest.main()
