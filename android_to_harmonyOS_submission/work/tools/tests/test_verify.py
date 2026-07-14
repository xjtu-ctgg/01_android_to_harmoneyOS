#!/usr/bin/env python3
"""Behavior tests for the build and Code Linter verification gate."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


WORK_ROOT = Path(__file__).resolve().parents[2]


class VerifyGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_root = Path(self.temporary_directory.name)
        self.project = self.temp_root / "project"
        shutil.copytree(
            WORK_ROOT,
            self.project,
            ignore=shutil.ignore_patterns(
                ".git",
                ".hvigor",
                "build",
                "oh_modules",
                "__pycache__",
            ),
        )
        # A copied verifier must exercise the production gate without running
        # the complete outer contract suite again for every gate-behavior case.
        nested_tests = self.project / "tools/tests"
        shutil.rmtree(nested_tests)
        nested_tests.mkdir()
        (nested_tests / "test_nested_smoke.py").write_text(
            "import unittest\n"
            "from pathlib import Path\n\n"
            "ROOT = Path(__file__).resolve().parents[2]\n\n"
            "class NestedVerifySmokeTests(unittest.TestCase):\n"
            "    def test_required_project_entry_exists(self):\n"
            "        self.assertTrue((ROOT / 'entry/src/main/ets/pages/Index.ets').is_file())\n",
            encoding="utf-8",
        )

        self.home = self.temp_root / "home"
        self.home.mkdir()
        self.tool_root = self.temp_root / "fake tools"
        self.tool_root.mkdir()
        self.build_log = self.temp_root / "build-cwds.log"
        self.hvigor_args = self.temp_root / "hvigor-args.log"
        self.sdk_log = self.temp_root / "sdk-roots.log"
        self.linter_args = self.temp_root / "linter-args.log"
        self.profile_log = self.temp_root / "build-profile.json5"
        self.module_log = self.temp_root / "module.json5"
        self.sdk = self.make_sdk(self.temp_root / "official sdk")

    def make_sdk(self, root: Path) -> Path:
        metadata = root / "ets/oh-uni-package.json"
        metadata.parent.mkdir(parents=True)
        metadata.write_text(
            "{\n"
            '  "apiVersion": "20",\n'
            '  "version": "6.0.0.48"\n'
            "}\n",
            encoding="utf-8",
        )
        return root

    def make_hvigor(self, *, produce_hap: bool) -> Path:
        tool = self.tool_root / "hvigorw"
        private_path = "/" + "Users" + "/private/deveco/path"
        hap_script = ""
        if produce_hap:
            hap_script = (
                "mkdir -p entry/build/default/outputs/default\n"
                "printf 'fresh-hap\\n' > entry/build/default/outputs/default/entry-default-unsigned.hap\n"
            )
        tool.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = --version ]; then\n"
            "  printf 'fake-hvigor 6.20.0\\n'\n"
            "  exit 0\n"
            "fi\n"
            'printf "%s\\n" "$PWD" >> "$BUILD_CWD_LOG"\n'
            ': > "$HVIGOR_ARGS_LOG"\n'
            'for argument in "$@"; do printf "%s\\n" "$argument" >> "$HVIGOR_ARGS_LOG"; done\n'
            'printf "%s\\n" "$DEVECO_SDK_HOME" >> "$SDK_ROOT_LOG"\n'
            'if [ -n "${PROFILE_LOG:-}" ]; then cp build-profile.json5 "$PROFILE_LOG"; fi\n'
            'if [ -n "${MODULE_LOG:-}" ]; then cp entry/src/main/module.json5 "$MODULE_LOG"; fi\n'
            "mkdir -p .hvigor\n"
            f"printf '{private_path}\\n' > .hvigor/personal-path.txt\n"
            f"{hap_script}"
            "exit 0\n",
            encoding="utf-8",
        )
        tool.chmod(0o755)
        return tool

    def make_codelinter(self, *, write_report: bool) -> Path:
        tool = self.tool_root / "codelinter"
        report_script = ""
        if write_report:
            report_script = (
                'if [ -n "$report" ]; then\n'
                '  mkdir -p "$(dirname "$report")"\n'
                "  printf '[]\\n' > \"$report\"\n"
                "fi\n"
            )
        tool.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = --version ]; then\n"
            "  printf 'fake-codelinter 6.0.0\\n'\n"
            "  exit 0\n"
            "fi\n"
            ': > "$LINTER_ARGS_LOG"\n'
            'for argument in "$@"; do\n'
            '  printf "%s\\n" "$argument" >> "$LINTER_ARGS_LOG"\n'
            "done\n"
            "report=\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "  if [ \"$1\" = -o ]; then\n"
            "    shift\n"
            "    report=${1:-}\n"
            "  fi\n"
            "  shift\n"
            "done\n"
            f"{report_script}"
            "exit 0\n",
            encoding="utf-8",
        )
        tool.chmod(0o755)
        return tool

    def make_hanging_hvigor(self) -> Path:
        tool = self.tool_root / "hanging-hvigorw"
        tool.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = --version ]; then\n"
            "  printf 'fake-hvigor 6.20.0\\n'\n"
            "  exit 0\n"
            "fi\n"
            "sleep 30\n",
            encoding="utf-8",
        )
        tool.chmod(0o755)
        return tool

    def environment(self, hvigor: Path, codelinter: Path | None = None) -> dict[str, str]:
        env = os.environ.copy()
        for name in ("OHOS_BASE_SDK_HOME", "DEVECO_HOME", "CODELINTER", "HDC"):
            env.pop(name, None)
        env.update(
            {
                "HOME": str(self.home),
                "HVIGORW": str(hvigor),
                "DEVECO_SDK_HOME": str(self.sdk),
                "BUILD_CWD_LOG": str(self.build_log),
                "HVIGOR_ARGS_LOG": str(self.hvigor_args),
                "SDK_ROOT_LOG": str(self.sdk_log),
                "LINTER_ARGS_LOG": str(self.linter_args),
                "PROFILE_LOG": str(self.profile_log),
                "MODULE_LOG": str(self.module_log),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        if codelinter is not None:
            env["CODELINTER"] = str(codelinter)
        return env

    def run_verify(self, mode: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.project / "tools/verify.sh"), mode],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_nested_verifier_fixture_contains_only_the_smoke_contract(self) -> None:
        nested_tests = sorted(
            path.name for path in (self.project / "tools/tests").glob("test_*.py")
        )
        self.assertEqual(["test_nested_smoke.py"], nested_tests)
        smoke = (self.project / "tools/tests/test_nested_smoke.py").read_text(encoding="utf-8")
        self.assertIn("class NestedVerifySmokeTests", smoke)
        self.assertIn("entry/src/main/ets/pages/Index.ets", smoke)

    def test_static_verification_reports_named_stages_and_verbose_test_progress(self) -> None:
        hvigor = self.make_hvigor(produce_hap=True)

        completed = self.run_verify("--static", self.environment(hvigor))

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        combined_output = completed.stdout + completed.stderr
        self.assertIn("stage=contract_check", combined_output)
        self.assertIn("stage=unit_tests", combined_output)
        self.assertIn("test_required_project_entry_exists", combined_output)
        self.assertIn("stage=completed", combined_output)

    def test_cross_build_removes_stale_output_before_toolchain_checks(self) -> None:
        stale_hap = self.project / "build/cross/entry-default-unsigned.hap"
        stale_hap.parent.mkdir(parents=True)
        stale_hap.write_text("stale-cross-hap\n", encoding="utf-8")
        env = os.environ.copy()
        env["OHOS_CROSS_SDK_HOME"] = str(self.temp_root / "missing-public-sdk")

        completed = subprocess.run(
            [str(self.project / "tools/cross_build_openharmony.sh")],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=missing_public_api_sdk", completed.stdout)
        self.assertFalse(stale_hap.exists())

    def test_cross_build_supports_an_isolated_release_build(self) -> None:
        hvigor = self.make_hvigor(produce_hap=True)
        arguments_log = self.temp_root / "cross-build-arguments.log"
        env = os.environ.copy()
        env.update(
            {
                "HVIGORW": str(hvigor),
                "OHOS_CROSS_SDK_HOME": str(self.sdk),
                "HVIGOR_USER_HOME": str(self.home / ".hvigor"),
                "BUILD_CWD_LOG": str(self.build_log),
                "HVIGOR_ARGS_LOG": str(self.hvigor_args),
                "SDK_ROOT_LOG": str(self.sdk_log),
                "LINTER_ARGS_LOG": str(arguments_log),
                "PROFILE_LOG": str(self.profile_log),
                "MODULE_LOG": str(self.module_log),
            }
        )

        completed = subprocess.run(
            [str(self.project / "tools/cross_build_openharmony.sh"), "--release"],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("build_mode=release", completed.stdout)
        self.assertIn("hap=build/cross/release/entry-default-unsigned.hap", completed.stdout)
        arguments = self.hvigor_args.read_text(encoding="utf-8").splitlines()
        self.assertIn("buildMode=release", arguments)
        self.assertTrue(
            (self.project / "build/cross/release/entry-default-unsigned.hap").is_file()
        )

    def test_strict_uses_full_linter_and_requires_a_json_report(self) -> None:
        hvigor = self.make_hvigor(produce_hap=True)
        codelinter = self.make_codelinter(write_report=True)

        completed = self.run_verify("--strict", self.environment(hvigor, codelinter))

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        arguments = self.linter_args.read_text(encoding="utf-8").splitlines()
        self.assertNotIn("-i", arguments)
        self.assertIn("-f", arguments)
        self.assertEqual("json", arguments[arguments.index("-f") + 1])
        self.assertIn("-e", arguments)
        self.assertEqual("error,warn,suggestion", arguments[arguments.index("-e") + 1])
        report = Path(arguments[arguments.index("-o") + 1])
        self.assertEqual((self.project / "build/reports/codelinter.json").resolve(), report.resolve())
        self.assertEqual(str(self.project.resolve()), arguments[-1])
        self.assertTrue(report.is_file())
        self.assertGreater(report.stat().st_size, 0)

    def test_strict_rejects_zero_exit_linter_without_report(self) -> None:
        hvigor = self.make_hvigor(produce_hap=True)
        codelinter = self.make_codelinter(write_report=False)

        completed = self.run_verify("--strict", self.environment(hvigor, codelinter))

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=missing_codelinter_report", completed.stdout)

    def test_build_rejects_and_removes_a_stale_hap(self) -> None:
        stale_hap = self.project / "entry/build/default/outputs/default/entry-default-unsigned.hap"
        stale_hap.parent.mkdir(parents=True)
        stale_hap.write_text("stale-hap\n", encoding="utf-8")
        hvigor = self.make_hvigor(produce_hap=False)

        completed = self.run_verify("--build", self.environment(hvigor))

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=missing_hap", completed.stdout)
        self.assertFalse(stale_hap.exists())

    def test_build_times_out_a_hung_hvigor_process(self) -> None:
        hvigor = self.make_hanging_hvigor()
        env = self.environment(hvigor)
        env["VERIFY_BUILD_TIMEOUT_SECONDS"] = "1"

        started = time.monotonic()
        completed = self.run_verify("--build", env)
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 5, completed.stdout + completed.stderr)
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=build_timeout", completed.stdout)

    def test_build_runs_twice_in_clean_temporary_copies(self) -> None:
        hvigor = self.make_hvigor(produce_hap=True)
        env = self.environment(hvigor)

        first = self.run_verify("--build", env)
        second = self.run_verify("--build", env)

        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        build_cwds = self.build_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(2, len(build_cwds))
        self.assertEqual(2, len(set(build_cwds)))
        self.assertTrue(all(Path(path) != self.project for path in build_cwds))
        self.assertFalse((self.project / ".hvigor").exists())
        hap = self.project / "entry/build/default/outputs/default/entry-default-unsigned.hap"
        self.assertEqual("fresh-hap\n", hap.read_text(encoding="utf-8"))

    def test_repository_discovered_sdk_is_exported_to_hvigor(self) -> None:
        repository_sdk = self.make_sdk(self.project / "sdk")
        hvigor = self.make_hvigor(produce_hap=True)
        env = self.environment(hvigor)
        env.pop("DEVECO_SDK_HOME")

        completed = self.run_verify("--build", env)

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual(
            [str(repository_sdk.resolve())],
            self.sdk_log.read_text(encoding="utf-8").splitlines(),
        )

    def test_bundled_public_sdk_uses_only_a_temporary_compatibility_profile(self) -> None:
        public_toolchain = self.temp_root / ".toolchains/openharmony-api20"
        self.make_sdk(public_toolchain / "sdk")
        public_base = public_toolchain / "base"
        (public_base / "20").mkdir(parents=True)
        hvigor = self.make_hvigor(produce_hap=True)
        env = self.environment(hvigor)
        env.pop("DEVECO_SDK_HOME")

        completed = self.run_verify("--build", env)

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("build_scope=public_api_compatibility", completed.stdout)
        profile = json.loads(self.profile_log.read_text(encoding="utf-8"))
        product = profile["app"]["products"][0]
        self.assertEqual(20, product["compileSdkVersion"])
        self.assertEqual(20, product["compatibleSdkVersion"])
        self.assertEqual(20, product["targetSdkVersion"])
        self.assertEqual("OpenHarmony", product["runtimeOS"])
        module = json.loads(self.module_log.read_text(encoding="utf-8"))
        self.assertEqual(["default"], module["module"]["deviceTypes"])
        self.assertEqual([str(public_base.resolve())], self.sdk_log.read_text(encoding="utf-8").splitlines())

        formal_profile = json.loads((self.project / "build-profile.json5").read_text(encoding="utf-8"))
        self.assertEqual("HarmonyOS", formal_profile["app"]["products"][0]["runtimeOS"])

    def test_external_public_sdk_is_detected_from_metadata_not_repository_path(self) -> None:
        public_toolchain = self.temp_root / "external public toolchain"
        external_sdk = self.make_sdk(public_toolchain / "sdk")
        public_base = public_toolchain / "base"
        (public_base / "20").mkdir(parents=True)
        hvigor = self.make_hvigor(produce_hap=True)
        env = self.environment(hvigor)
        env["DEVECO_SDK_HOME"] = str(external_sdk)

        completed = self.run_verify("--build", env)

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("build_scope=public_api_compatibility", completed.stdout)
        self.assertEqual(
            [str(public_base.resolve())],
            self.sdk_log.read_text(encoding="utf-8").splitlines(),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
