#!/usr/bin/env python3
"""Rehearse one submission in five isolated platform-style Executor workdirs."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


EXECUTOR_COUNT = 5
REQUIRED_ARTIFACTS = (
    "INSTRUCTION.md",
    "result/output.md",
    "logs/interaction.md",
    "work/AppScope/app.json5",
    "work/entry/src/main/module.json5",
    "work/entry/src/main/ets/pages/Index.ets",
    "work/skills/android-to-harmonyos/SKILL.md",
    "work/tools/verify.sh",
)
REQUIRED_DIRECTORIES = ("work", "result", "logs", "logs/trace")
FORBIDDEN_ARCHIVE_PARTS = {
    ".git",
    ".gradle",
    ".hvigor",
    "__pycache__",
    "build",
    "node_modules",
    "oh_modules",
}
FORBIDDEN_ARCHIVE_NAMES = {".DS_Store"}
FORBIDDEN_ARCHIVE_SUFFIXES = {".hap", ".pyc"}
IGNORED_DIGEST_PARTS = {
    ".git",
    ".hvigor",
    "__pycache__",
    "build",
    "node_modules",
    "oh_modules",
}
HAP_PATH = Path("work/entry/build/default/outputs/default/entry-default-unsigned.hap")
DELIVERY_ROOT = Path(__file__).resolve().parents[2]


class ArchiveRejected(ValueError):
    """The submitted archive does not satisfy the platform delivery boundary."""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--mode", choices=("static", "build"), default="static")
    parser.add_argument("--keep-workdirs", type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= EXECUTOR_COUNT:
        parser.error(f"--jobs must be between 1 and {EXECUTOR_COUNT}")
    return args


def validated_members(
    stream: zipfile.ZipFile,
    expected_root_name: str,
) -> list[zipfile.ZipInfo]:
    members = stream.infolist()
    if not members:
        raise ArchiveRejected("archive is empty")
    seen: set[str] = set()
    top_level: set[str] = set()
    for info in members:
        raw_name = info.filename
        path = PurePosixPath(raw_name)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ArchiveRejected(f"unsafe path: {raw_name}")
        forbidden_parts = sorted(set(path.parts) & FORBIDDEN_ARCHIVE_PARTS)
        if forbidden_parts:
            raise ArchiveRejected(
                f"generated or cache path is forbidden: {raw_name} ({', '.join(forbidden_parts)})"
            )
        if path.name in FORBIDDEN_ARCHIVE_NAMES or path.suffix.lower() in FORBIDDEN_ARCHIVE_SUFFIXES:
            raise ArchiveRejected(f"generated artifact is forbidden: {raw_name}")
        normalized = path.as_posix().rstrip("/")
        if not normalized or normalized in seen:
            raise ArchiveRejected(f"duplicate or empty path: {raw_name}")
        seen.add(normalized)
        top_level.add(path.parts[0])
        unix_mode = info.external_attr >> 16
        if stat.S_ISLNK(unix_mode):
            raise ArchiveRejected(f"symbolic link is forbidden: {raw_name}")
    if top_level != {expected_root_name}:
        actual = ", ".join(sorted(top_level)) or "<empty>"
        raise ArchiveRejected(
            f"archive must contain exactly one root directory named {expected_root_name}: {actual}"
        )
    return members


def extract_submission(archive: Path, destination: Path) -> Path:
    if not archive.is_file():
        raise ArchiveRejected(f"archive does not exist: {archive}")
    expected_root_name = archive.stem
    with zipfile.ZipFile(archive) as stream:
        members = validated_members(stream, expected_root_name)
        for info in members:
            relative = PurePosixPath(info.filename)
            target = destination.joinpath(*relative.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with stream.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            unix_mode = info.external_attr >> 16
            if unix_mode:
                target.chmod(unix_mode & 0o777)
    submission_root = destination / expected_root_name
    if not submission_root.is_dir():
        raise ArchiveRejected(f"missing submission root directory: {expected_root_name}")
    missing = [path for path in REQUIRED_ARTIFACTS if not (submission_root / path).is_file()]
    if missing:
        raise ArchiveRejected("missing required artifacts: " + ", ".join(missing))
    missing_directories = [
        path for path in REQUIRED_DIRECTORIES if not (submission_root / path).is_dir()
    ]
    if missing_directories:
        raise ArchiveRejected("missing required directories: " + ", ".join(missing_directories))
    if not (submission_root / "INSTRUCTION.md").read_text(encoding="utf-8").strip():
        raise ArchiveRejected("INSTRUCTION.md is empty")
    if not (submission_root / "result/output.md").read_text(encoding="utf-8").strip():
        raise ArchiveRejected("result/output.md is empty")
    return submission_root


def make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode & ~0o222)
    root.chmod(stat.S_IMODE(root.stat().st_mode) & ~0o222)


def make_writable(root: Path) -> None:
    root.chmod(stat.S_IMODE(root.stat().st_mode) | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    for path in root.rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            path.chmod(mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        else:
            path.chmod(mode | stat.S_IRUSR | stat.S_IWUSR)


def is_read_only(root: Path) -> bool:
    paths = (root, *root.rglob("*"))
    return all(not (stat.S_IMODE(path.stat().st_mode) & 0o222) for path in paths)


def artifact_valid(root: Path) -> bool:
    return all((root / path).is_file() for path in REQUIRED_ARTIFACTS) and bool(
        (root / "INSTRUCTION.md").read_text(encoding="utf-8").strip()
    )


def source_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIGEST_PARTS for part in relative.parts):
            continue
        if not path.is_file():
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def parse_case_count(output: str) -> int:
    matches = re.findall(r"Ran\s+(\d+)\s+tests?", output)
    return int(matches[-1]) if matches else 0


def journey_count(root: Path) -> int:
    journey_file = root / "work/journeys/core.yaml"
    if not journey_file.is_file():
        return 0
    return len(re.findall(r"^\s*- id:\s+\S+", journey_file.read_text(encoding="utf-8"), re.MULTILINE))


def local_tool_environment() -> dict[str, str]:
    """Promote workspace-adjacent local tools to absolute paths for temp copies."""
    environment = os.environ.copy()
    candidates = {
        "DEVECO_SDK_HOME": DELIVERY_ROOT / ".toolchains/openharmony-api20/sdk",
        "HVIGORW": DELIVERY_ROOT / ".toolchains/harmony-cli/bin/hvigorw",
        "HVIGOR_USER_HOME": DELIVERY_ROOT / ".toolchains/hvigor-home",
    }
    for name, candidate in candidates.items():
        if name not in environment and candidate.exists():
            environment[name] = str(candidate.resolve())
    return environment


def run_executor(
    name: str,
    root: Path,
    mode: str,
    package_root_read_only: bool,
) -> dict[str, Any]:
    work = root / "work"
    digest = source_tree_digest(root)
    base_artifact_valid = artifact_valid(root)
    command = ["/bin/sh", "tools/verify.sh", f"--{mode}"]
    print(f"{name}: start mode={mode}", file=sys.stderr, flush=True)
    completed = subprocess.run(
        command,
        cwd=work,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=local_tool_environment(),
        check=False,
    )
    output = completed.stdout
    cases = parse_case_count(output)
    hap_valid = mode != "build" or ((root / HAP_PATH).is_file() and (root / HAP_PATH).stat().st_size > 0)
    success = completed.returncode == 0 and base_artifact_valid and cases > 0 and hap_valid
    print(
        f"{name}: done exit={completed.returncode} cases={cases} hap_valid={hap_valid}",
        file=sys.stderr,
        flush=True,
    )
    return {
        "name": name,
        "success": success,
        "exit_code": completed.returncode,
        "artifact_valid": base_artifact_valid,
        "hap_valid": hap_valid,
        "case_count": cases,
        "passed_cases": cases if success else 0,
        "journey_count": journey_count(root),
        "package_root_read_only": package_root_read_only,
        "source_tree_sha256": digest,
        "output_tail": output[-2000:],
    }


def prepare_run_root(keep_workdirs: Path | None) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if keep_workdirs is None:
        temporary = tempfile.TemporaryDirectory(prefix="five-executor-")
        return Path(temporary.name), temporary
    run_root = keep_workdirs.resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise ValueError(f"--keep-workdirs must be absent or empty: {run_root}")
    run_root.mkdir(parents=True, exist_ok=True)
    return run_root, None


def execute(args: argparse.Namespace) -> dict[str, Any]:
    archive = args.archive.resolve()
    extraction = tempfile.TemporaryDirectory(prefix="submission-package-")
    package_root = Path(extraction.name) / "package_root"
    package_root.mkdir()
    submission_root = extract_submission(archive, package_root)
    make_read_only(package_root)
    package_read_only = is_read_only(package_root)

    run_root, retained = prepare_run_root(args.keep_workdirs)
    executor_roots: list[tuple[str, Path]] = []
    try:
        for number in range(1, EXECUTOR_COUNT + 1):
            name = f"executor_{number}"
            executor_root = run_root / name
            shutil.copytree(submission_root, executor_root)
            make_writable(executor_root)
            executor_roots.append((name, executor_root))

        results_by_name: dict[str, dict[str, Any]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {
                pool.submit(run_executor, name, root, args.mode, package_read_only): name
                for name, root in executor_roots
            }
            for future in concurrent.futures.as_completed(futures):
                results_by_name[futures[future]] = future.result()
        results = [results_by_name[f"executor_{number}"] for number in range(1, EXECUTOR_COUNT + 1)]

        counts = [int(item["case_count"]) for item in results]
        digests = {str(item["source_tree_sha256"]) for item in results}
        all_counts_equal = len(set(counts)) == 1 and counts[0] > 0
        all_source_equal = len(digests) == 1
        all_artifacts = all(bool(item["artifact_valid"]) for item in results)
        stability = min(int(item["passed_cases"]) for item in results)
        accuracy = max(int(item["passed_cases"]) for item in results)
        summary: dict[str, Any] = {
            "executor_count": EXECUTOR_COUNT,
            "mode": args.mode,
            "case_count": counts[0] if all_counts_equal else 0,
            "stability_passed_cases": stability,
            "accuracy_passed_cases": accuracy,
            "all_artifacts_valid": all_artifacts,
            "all_case_counts_equal": all_counts_equal,
            "all_source_trees_equal": all_source_equal,
            "package_root_read_only": package_read_only,
            "executors": results,
        }
        summary["success"] = (
            package_read_only
            and all_artifacts
            and all_counts_equal
            and all_source_equal
            and all(bool(item["success"]) for item in results)
        )
        if args.keep_workdirs is not None:
            (run_root / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return summary
    finally:
        if retained is not None:
            retained.cleanup()
        make_writable(package_root)
        extraction.cleanup()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = execute(args)
    except (ArchiveRejected, zipfile.BadZipFile, UnicodeError) as error:
        print(f"archive rejected: {error}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as error:
        print(f"preflight failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
