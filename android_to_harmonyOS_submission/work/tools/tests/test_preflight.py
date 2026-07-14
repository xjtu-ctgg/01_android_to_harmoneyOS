#!/usr/bin/env python3
"""Behavior tests for the portable HarmonyOS toolchain preflight."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


WORK_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = WORK_ROOT / "tools" / "preflight.sh"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(PREFLIGHT.is_file(), f"missing production script: {PREFLIGHT}")
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_root = Path(self.temporary_directory.name)
        self.project = self.temp_root / "project"
        self.tools = self.project / "tools"
        self.tools.mkdir(parents=True)
        self.script = self.tools / "preflight.sh"
        shutil.copy2(PREFLIGHT, self.script)

        self.home = self.temp_root / "home"
        self.home.mkdir()
        self.path_bin = self.temp_root / "path-bin"
        self.path_bin.mkdir()
        self.call_log = self.temp_root / "calls.log"

    def base_environment(self) -> dict[str, str]:
        env = {
            "HOME": str(self.home),
            "PATH": f"{self.path_bin}:/usr/bin:/bin",
            "CALL_LOG": str(self.call_log),
            "LC_ALL": "C",
        }
        for name in (
            "HVIGORW",
            "CODELINTER",
            "HDC",
            "DEVECO_SDK_HOME",
            "OHOS_BASE_SDK_HOME",
            "DEVECO_HOME",
        ):
            env.pop(name, None)
        return env

    def make_tool(
        self,
        path: Path,
        label: str,
        *,
        exit_code: int = 0,
        ansi: bool = False,
        accepted_argument: str = "--version",
        reported_version: str | None = None,
        write_cwd_marker: bool = False,
    ) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        version = reported_version if reported_version is not None else f"fake-{label} 1.2.3"
        if ansi:
            version = f"\\033[32m{version}\\033[0m"
        marker_script = ""
        if write_cwd_marker:
            marker_script = (
                'mkdir -p .hvigor\n'
                'printf "%s\\n" "$PWD" >> "$PROBE_CWD_LOG"\n'
            )
        path.write_text(
            "#!/bin/sh\n"
            f"printf '{label}:%s\\n' \"${{1:-none}}\" >> \"$CALL_LOG\"\n"
            f"{marker_script}"
            f'if [ "${{1:-}}" = "{accepted_argument}" ]; then\n'
            f"  printf '{version}\\n'\n"
            f"  exit {exit_code}\n"
            "fi\n"
            "exit 1\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def make_sdk(
        self,
        root: Path,
        api: str = "20",
        *,
        api_line: str | None = None,
    ) -> Path:
        metadata = root / "ets" / "oh-uni-package.json"
        metadata.parent.mkdir(parents=True, exist_ok=True)
        if api_line is None:
            api_line = f'  "apiVersion": "{api}",'
        metadata.write_text(
            "{\n"
            f"{api_line}\n"
            '  "displayName": "Ets",\n'
            '  "releaseType": "Release",\n'
            '  "version": "6.0.0.48"\n'
            "}\n",
            encoding="utf-8",
        )
        return root

    def make_broken_codelinter_wrapper(self, path: Path, label: str) -> Path:
        """Create the official wrapper shape without its required backend."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/bin/sh\n"
            f"printf '{label}:%s\\n' \"${{1:-none}}\" >> \"$CALL_LOG\"\n"
            'backend="$(dirname "$0")/../codelinter/bin/codelinter"\n'
            'if [ ! -x "$backend" ]; then\n'
            '  printf "File not found: %s\\n" "$backend"\n'
            "  exit 1\n"
            "fi\n"
            'exec "$backend" "$@"\n',
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def run_preflight(
        self,
        *arguments: str,
        env_overrides: dict[str, str] | None = None,
        unset_environment: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        env = self.base_environment()
        if env_overrides:
            env.update(env_overrides)
        for name in unset_environment:
            env.pop(name, None)
        return subprocess.run(
            [str(self.script), *arguments],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def parse_output(self, completed: subprocess.CompletedProcess[str]) -> dict[str, str]:
        self.assertEqual(completed.stderr, "")
        self.assertNotRegex(completed.stdout, ANSI_ESCAPE)
        result: dict[str, str] = {}
        lines = completed.stdout.splitlines()
        self.assertGreater(len(lines), 0)
        for line in lines:
            self.assertRegex(line, r"^[a-z][a-z0-9_]*=.*$")
            key, value = line.split("=", 1)
            self.assertNotIn(key, result, f"duplicate output key: {key}")
            result[key] = value
        return result

    def test_missing_hvigor_has_stable_failure_reason(self) -> None:
        completed = self.run_preflight()

        self.assertNotEqual(completed.returncode, 0)
        values = self.parse_output(completed)
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "missing_hvigor")
        self.assertEqual(values["hvigor_status"], "missing")

    def test_home_may_be_unset_in_an_env_i_style_environment(self) -> None:
        completed = self.run_preflight(unset_environment=("HOME",))

        self.assertNotEqual(completed.returncode, 0)
        values = self.parse_output(completed)
        self.assertEqual(values["mode"], "strict")
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "missing_hvigor")

    def test_rejects_every_extra_argument_even_after_a_valid_mode(self) -> None:
        completed = self.run_preflight("--strict", "unexpected")

        self.assertEqual(completed.returncode, 2)
        values = self.parse_output(completed)
        self.assertEqual(values["mode"], "invalid")
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "invalid_argument")

    def test_explicit_tools_take_priority_and_strict_mode_passes(self) -> None:
        explicit_hvigor = self.make_tool(self.temp_root / "explicit" / "hvigorw", "explicit-hvigor", ansi=True)
        self.make_tool(self.project / "hvigorw", "repo-hvigor")
        self.make_tool(self.path_bin / "hvigorw", "path-hvigor")
        explicit_linter = self.make_tool(self.temp_root / "explicit" / "codelinter", "explicit-linter")
        explicit_hdc = self.make_tool(self.temp_root / "explicit" / "hdc", "explicit-hdc")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(explicit_hvigor),
                "CODELINTER": str(explicit_linter),
                "HDC": str(explicit_hdc),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["mode"], "strict")
        self.assertEqual(values["status"], "passed")
        self.assertEqual(values["reason"], "ok")
        self.assertEqual(values["hvigor_status"], "passed")
        self.assertEqual(values["hvigor_source"], "environment")
        self.assertEqual(values["hvigor_path"], str(explicit_hvigor))
        self.assertEqual(values["sdk_status"], "passed")
        self.assertEqual(values["sdk_api"], "20")
        self.assertEqual(values["codelinter_status"], "passed")
        self.assertEqual(values["hdc_status"], "passed")
        self.assertEqual(values["path_persistence"], "sensitive")
        calls = self.call_log.read_text(encoding="utf-8")
        self.assertIn("explicit-hvigor:--version", calls)
        self.assertIn("explicit-linter:--version", calls)
        self.assertIn("explicit-hdc:--version", calls)
        self.assertNotIn("repo-hvigor", calls)
        self.assertNotIn("path-hvigor", calls)

    def test_repository_wrapper_takes_priority_over_path(self) -> None:
        repo_hvigor = self.make_tool(self.project / "hvigorw", "repo-hvigor")
        self.make_tool(self.path_bin / "hvigorw", "path-hvigor")
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "CODELINTER": str(linter),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["hvigor_source"], "repository")
        self.assertEqual(values["hvigor_path"], "repository:hvigorw")
        calls = self.call_log.read_text(encoding="utf-8")
        self.assertIn("repo-hvigor:--version", calls)
        self.assertNotIn("path-hvigor", calls)

    def test_zero_exit_failure_banner_is_not_accepted_as_a_tool_version(self) -> None:
        self.make_tool(
            self.project / "hvigorw",
            "invalid-hvigor",
            reported_version="Invalid custom userhome hvigor data dir:relative/path",
        )
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "CODELINTER": str(linter),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        values = self.parse_output(completed)
        self.assertEqual(values["hvigor_status"], "unusable")
        self.assertEqual(values["hvigor_version"], "none")
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "missing_hvigor")

    def test_sdk_directory_without_api_metadata_is_rejected(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        empty_sdk = self.temp_root / "empty-sdk"
        empty_sdk.mkdir()

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "CODELINTER": str(linter),
                "DEVECO_SDK_HOME": str(empty_sdk),
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        values = self.parse_output(completed)
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "missing_sdk")
        self.assertEqual(values["sdk_status"], "missing")

    def test_sdk_api_metadata_requires_a_complete_numeric_json_value(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        invalid_lines = (
            '  "apiVersion": "20beta",',
            '  "apiVersion": "20" trailing-garbage',
            '  "apiVersion": 20beta,',
        )

        for index, invalid_line in enumerate(invalid_lines):
            with self.subTest(invalid_line=invalid_line):
                sdk = self.make_sdk(
                    self.temp_root / f"invalid-sdk-{index}",
                    api_line=invalid_line,
                )
                completed = self.run_preflight(
                    env_overrides={
                        "HVIGORW": str(hvigor),
                        "CODELINTER": str(linter),
                        "DEVECO_SDK_HOME": str(sdk),
                    }
                )

                self.assertNotEqual(completed.returncode, 0)
                values = self.parse_output(completed)
                self.assertEqual(values["sdk_status"], "missing")
                self.assertEqual(values["reason"], "missing_sdk")

    def test_broken_repository_codelinter_wrapper_is_not_accepted(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        self.make_broken_codelinter_wrapper(
            self.project / "bin" / "codelinter",
            "wrapper-without-backend",
        )
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        values = self.parse_output(completed)
        self.assertEqual(values["status"], "failed")
        self.assertEqual(values["reason"], "missing_codelinter")
        self.assertEqual(values["codelinter_status"], "unusable")
        self.assertEqual(values["codelinter_source"], "repository")
        self.assertEqual(
            values["codelinter_path"],
            "repository:bin/codelinter",
        )

    def test_unusable_repository_wrapper_falls_through_to_path_tool(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        self.make_broken_codelinter_wrapper(
            self.project / "bin" / "codelinter",
            "broken-wrapper",
        )
        path_linter = self.make_tool(self.path_bin / "codelinter", "path-linter")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["codelinter_status"], "passed")
        self.assertEqual(values["codelinter_source"], "path")
        self.assertEqual(values["codelinter_path"], str(path_linter))
        calls = self.call_log.read_text(encoding="utf-8")
        self.assertIn("broken-wrapper:--version", calls)
        self.assertIn("path-linter:--version", calls)

    def test_standard_sdk_layout_is_discovered_and_metadata_is_required(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        sdk = self.make_sdk(self.home / "Library" / "Huawei" / "Sdk" / "20")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "CODELINTER": str(linter),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["sdk_status"], "passed")
        self.assertEqual(values["sdk_source"], "standard")
        self.assertEqual(values["sdk_path"], "home:Library/Huawei/Sdk")
        self.assertEqual(values["sdk_api"], "20")

    def test_adjacent_repository_toolchain_paths_are_relative(self) -> None:
        hvigor = self.make_tool(
            self.temp_root / ".toolchains" / "harmony-cli" / "bin" / "hvigorw",
            "adjacent-hvigor",
        )
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        sdk = self.make_sdk(
            self.temp_root / ".toolchains" / "openharmony-api20" / "sdk"
        )
        hdc = self.make_tool(sdk / "toolchains" / "hdc", "sdk-hdc")

        completed = self.run_preflight(env_overrides={"CODELINTER": str(linter)})

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["hvigor_source"], "repository")
        self.assertEqual(
            values["hvigor_path"],
            "repository:../.toolchains/harmony-cli/bin/hvigorw",
        )
        self.assertEqual(values["sdk_source"], "repository")
        self.assertEqual(
            values["sdk_path"],
            "repository:../.toolchains/openharmony-api20/sdk",
        )
        self.assertEqual(values["sdk_api"], "20")
        self.assertEqual(values["hdc_status"], "passed")
        self.assertEqual(values["hdc_source"], "repository")
        self.assertEqual(
            values["hdc_path"],
            "repository:../.toolchains/openharmony-api20/sdk/toolchains/hdc",
        )
        self.assertTrue(hvigor.is_file())
        self.assertTrue(sdk.is_dir())
        self.assertTrue(hdc.is_file())

    def test_probes_use_a_clean_temporary_cwd_and_support_spaced_paths(self) -> None:
        probe_cwd_log = self.temp_root / "probe cwd paths.log"
        spaced_root = self.temp_root / "paths with spaces"
        hvigor = self.make_tool(
            spaced_root / "hvigor tool",
            "hvigor",
            accepted_argument="--help",
            write_cwd_marker=True,
        )
        linter = self.make_tool(
            spaced_root / "code linter",
            "linter",
            accepted_argument="-v",
            write_cwd_marker=True,
        )
        hdc = self.make_tool(
            spaced_root / "hdc tool",
            "hdc",
            accepted_argument="--version",
            write_cwd_marker=True,
        )
        sdk = self.make_sdk(spaced_root / "SDK root")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "CODELINTER": str(linter),
                "HDC": str(hdc),
                "DEVECO_SDK_HOME": str(sdk),
                "PROBE_CWD_LOG": str(probe_cwd_log),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["hvigor_path"], str(hvigor))
        self.assertEqual(values["sdk_path"], str(sdk))
        calls = self.call_log.read_text(encoding="utf-8")
        self.assertIn("hvigor:--version", calls)
        self.assertIn("hvigor:-v", calls)
        self.assertIn("hvigor:--help", calls)
        self.assertIn("linter:--version", calls)
        self.assertIn("linter:-v", calls)
        self.assertFalse((self.project / ".hvigor").exists())
        probe_directories = {
            Path(line) for line in probe_cwd_log.read_text(encoding="utf-8").splitlines()
        }
        self.assertGreater(len(probe_directories), 0)
        self.assertNotIn(self.project, probe_directories)
        for directory in probe_directories:
            self.assertFalse(directory.exists(), f"probe cwd leaked: {directory}")

    def test_strict_mode_does_not_require_hdc(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        linter = self.make_tool(self.temp_root / "codelinter", "linter")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            env_overrides={
                "HVIGORW": str(hvigor),
                "CODELINTER": str(linter),
                "DEVECO_SDK_HOME": str(sdk),
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["status"], "passed")
        self.assertEqual(values["hdc_status"], "optional_missing")

    def test_build_only_marks_missing_optional_tools_without_faking_pass(self) -> None:
        hvigor = self.make_tool(self.temp_root / "hvigorw", "hvigor")
        sdk = self.make_sdk(self.temp_root / "sdk")

        completed = self.run_preflight(
            "--build-only",
            env_overrides={
                "HVIGORW": str(hvigor),
                "DEVECO_SDK_HOME": str(sdk),
            },
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        values = self.parse_output(completed)
        self.assertEqual(values["mode"], "build-only")
        self.assertEqual(values["status"], "passed")
        self.assertEqual(values["reason"], "ok")
        self.assertEqual(values["codelinter_status"], "optional_missing")
        self.assertEqual(values["hdc_status"], "optional_missing")
        self.assertNotEqual(values["codelinter_status"], "passed")
        self.assertNotEqual(values["hdc_status"], "passed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
