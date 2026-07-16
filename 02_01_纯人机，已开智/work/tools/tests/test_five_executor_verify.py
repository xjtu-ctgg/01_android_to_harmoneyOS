#!/usr/bin/env python3
"""Executable contracts for the five independent platform Executor preflight."""

from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/five_executor_verify.py"


class FiveExecutorVerifyTests(unittest.TestCase):
    def make_archive(
        self,
        directory: Path,
        *,
        fail_executor: int | None = None,
        bad_entry: str | None = None,
        symlink: bool = False,
        include_report: bool = True,
    ) -> Path:
        root_name = "02_01_测试队"
        archive = directory / f"{root_name}.zip"
        script = """#!/bin/sh
set -eu
name=$(basename "$(dirname "$PWD")")
printf '%s\n' 'Ran 5 tests' 'status=passed'
"""
        if fail_executor is not None:
            script += (
                f'[ "$name" != "executor_{fail_executor}" ] '
                "|| { printf '%s\\n' 'forced executor failure'; exit 9; }\n"
            )
        script += """
if [ "${1:---build}" = "--build" ]; then
  mkdir -p entry/build/default/outputs/default
  printf 'fake-hap' > entry/build/default/outputs/default/entry-default-unsigned.hap
fi
"""
        files = {
            f"{root_name}/INSTRUCTION.md": "# Reproduce\nRun work/tools/verify.sh.\n",
            f"{root_name}/result/output.md": "# Self validation\nPassed.\n",
            f"{root_name}/logs/interaction.md": "# Interaction\n",
            f"{root_name}/logs/trace/validation.md": "# Trace\n",
            f"{root_name}/work/AppScope/app.json5": "{}\n",
            f"{root_name}/work/entry/src/main/module.json5": "{}\n",
            f"{root_name}/work/entry/src/main/ets/pages/Index.ets": "@Entry @Component struct Index {}\n",
            f"{root_name}/work/skills/android-to-harmonyos/SKILL.md": "# Migration skill\n",
            f"{root_name}/work/tools/verify.sh": script,
            f"{root_name}/work/journeys/core.yaml": "journeys:\n  - id: fake.case\n",
        }
        if include_report:
            files[f"{root_name}/work/migration-report.md"] = "# Migration report\nSource evidence index.\n"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as stream:
            for name, content in files.items():
                stream.writestr(name, content)
            if bad_entry is not None:
                stream.writestr(bad_entry, "escape")
            if symlink:
                info = zipfile.ZipInfo(f"{root_name}/work/link")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                stream.writestr(info, "target")
        return archive

    def run_harness(self, archive: Path, mode: str = "static") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HARNESS), "--archive", str(archive), "--mode", mode],
            cwd=ROOT.parent,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_runs_same_case_suite_in_five_isolated_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_harness(self.make_archive(Path(temporary)))
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(5, len(summary["executors"]))
        self.assertTrue(all(item["success"] for item in summary["executors"]))
        self.assertTrue(all(item["artifact_valid"] for item in summary["executors"]))
        self.assertTrue(all(item["package_root_read_only"] for item in summary["executors"]))
        self.assertEqual(5, summary["stability_passed_cases"])
        self.assertEqual(5, summary["accuracy_passed_cases"])
        self.assertTrue(summary["all_source_trees_equal"])

    def test_failure_in_one_executor_fails_stability_and_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = self.make_archive(Path(temporary), fail_executor=3)
            result = self.run_harness(archive)
        self.assertNotEqual(0, result.returncode)
        summary = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual("executor_3", summary["executors"][2]["name"])
        self.assertFalse(summary["executors"][2]["success"])
        self.assertEqual(0, summary["stability_passed_cases"])
        self.assertEqual(5, summary["accuracy_passed_cases"])

    def test_build_requires_a_nonempty_hap_from_every_executor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_harness(self.make_archive(Path(temporary)), "build")
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[-1])
        self.assertTrue(all(item["hap_valid"] for item in summary["executors"]))

    def test_rejects_archive_without_scorer_migration_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = self.make_archive(Path(temporary), include_report=False)
            result = self.run_harness(archive)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("work/migration-report.md", result.stderr)

    def test_rejects_zip_slip_wrong_top_level_and_symlink(self) -> None:
        cases = (
            {"bad_entry": "../escape"},
            {"bad_entry": "/absolute"},
            {"bad_entry": "extra.txt"},
            {"bad_entry": "02_01_测试队/work/source-facts/android-source/.gradle/cache.bin"},
            {"bad_entry": "02_01_测试队/work/entry/build/output.hap"},
            {"bad_entry": "02_01_测试队/work/entry/oh_modules/cache.bin"},
            {"bad_entry": "02_01_测试队/work/tools/__pycache__/test.pyc"},
            {"symlink": True},
        )
        for options in cases:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary:
                archive = self.make_archive(Path(temporary), **options)
                result = self.run_harness(archive)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("archive rejected", result.stderr)

    def test_real_executor_processes_inherit_adjacent_local_toolchains(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("def local_tool_environment()", source)
        self.assertIn(".toolchains/openharmony-api20/sdk", source)
        self.assertIn(".toolchains/harmony-cli/bin/hvigorw", source)
        self.assertIn(".toolchains/hvigor-home", source)
        self.assertIn("env=local_tool_environment()", source)

    def test_default_is_sequential_to_avoid_nested_gate_resource_starvation(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--jobs", type=int, default=1)', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
