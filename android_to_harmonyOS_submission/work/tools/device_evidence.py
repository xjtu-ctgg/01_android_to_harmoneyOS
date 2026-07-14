#!/usr/bin/env python3
"""Collect unmodified HarmonyOS layout and screenshot evidence for one checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ID_KEYS = {"id", "inspectorid", "resourceid", "resource-id", "key"}
NODE_FIELDS = (
    "id",
    "inspectorId",
    "resourceId",
    "key",
    "text",
    "description",
    "hint",
    "bounds",
    "visible",
    "clickable",
    "enabled",
    "selected",
    "checked",
)


class EvidenceError(Exception):
    """Expected evidence collection failure with a stable machine reason."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journey-id", required=True)
    parser.add_argument("--stable-id", required=True)
    parser.add_argument("--expected-text", action="append", default=[])
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--settle-ms", type=int, default=500)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bundle", default="com.example.jetsnack")
    parser.add_argument("--hdc", default=os.environ.get("HDC", ""))
    return parser.parse_args()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or repr(command)
        raise EvidenceError("hdc_command_failed", detail)
    return completed


def resolve_hdc(argument: str) -> str:
    if argument:
        candidate = Path(argument).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        raise EvidenceError("missing_hdc", argument)
    candidate = shutil.which("hdc")
    if candidate is None:
        raise EvidenceError("missing_hdc")
    return candidate


def one_target(hdc: str) -> str:
    output = run([hdc, "list", "targets"]).stdout
    targets = [
        line.strip()
        for line in output.splitlines()
        if line.strip() and line.strip().lower() not in {"[empty]", "empty"}
    ]
    if len(targets) != 1:
        raise EvidenceError("expected_exactly_one_target", f"count={len(targets)}")
    return targets[0]


def dictionaries(value: object) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if isinstance(value, dict):
        found.append(value)
        for key, child in value.items():
            if key in {"attributes", "properties", "attrs"} and isinstance(child, dict):
                continue
            found.extend(dictionaries(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(dictionaries(child))
    return found


def property_maps(node: dict[str, object]) -> list[dict[str, object]]:
    maps = [node]
    for key in ("attributes", "properties", "attrs"):
        value = node.get(key)
        if isinstance(value, dict):
            maps.insert(0, value)
    return maps


def node_has_id(node: dict[str, object], stable_id: str) -> bool:
    for properties in property_maps(node):
        for key, value in properties.items():
            if key.lower() in ID_KEYS and value == stable_id:
                return True
    return False


def selected_node(node: dict[str, object], stable_id: str) -> dict[str, object]:
    selected: dict[str, object] = {"id": stable_id}
    for properties in reversed(property_maps(node)):
        for key in NODE_FIELDS:
            value = properties.get(key)
            if isinstance(value, (str, int, float, bool)):
                selected[key] = value
    selected["id"] = stable_id
    return selected


def validate_layout(path: Path, stable_id: str, expected_texts: list[str]) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError("invalid_layout_json", str(error)) from error
    nodes = [node for node in dictionaries(payload) if node_has_id(node, stable_id)]
    if not nodes:
        raise EvidenceError("stable_id_not_found", stable_id)
    if len(nodes) != 1:
        raise EvidenceError("stable_id_not_unique", f"{stable_id}:{len(nodes)}")
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    missing_texts = [text for text in expected_texts if text not in serialized]
    if missing_texts:
        raise EvidenceError("expected_text_not_found", ",".join(missing_texts))
    node = selected_node(nodes[0], stable_id)
    if node.get("visible") is False:
        raise EvidenceError("stable_id_not_visible", stable_id)
    return node


def validate_png(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise EvidenceError("missing_png", str(error)) from error
    if len(payload) <= len(PNG_SIGNATURE) or not payload.startswith(PNG_SIGNATURE):
        raise EvidenceError("invalid_png", path.name)
    return hashlib.sha256(payload).hexdigest()


def collect(args: argparse.Namespace) -> dict[str, object]:
    if args.repetitions < 1:
        raise EvidenceError("invalid_repetitions", str(args.repetitions))
    if args.settle_ms < 0:
        raise EvidenceError("invalid_settle_ms", str(args.settle_ms))
    hdc = resolve_hdc(args.hdc)
    target = one_target(hdc)
    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    captures: list[dict[str, object]] = []
    token = f"jetsnack-{os.getpid()}"
    for number in range(1, args.repetitions + 1):
        if args.settle_ms:
            time.sleep(args.settle_ms / 1000)
        prefix = f"{number:02d}"
        remote_layout = f"/data/local/tmp/{token}-{prefix}.json"
        remote_png = f"/data/local/tmp/{token}-{prefix}.png"
        local_layout = output_dir / f"{prefix}-layout.json"
        local_png = output_dir / f"{prefix}-screen.png"
        run([hdc, "shell", "uitest", "dumpLayout", "-b", args.bundle, "-p", remote_layout])
        run([hdc, "file", "recv", remote_layout, str(local_layout)])
        run([hdc, "shell", "uitest", "screenCap", "-p", remote_png])
        run([hdc, "file", "recv", remote_png, str(local_png)])
        node = validate_layout(local_layout, args.stable_id, args.expected_text)
        captures.append(
            {
                "index": number,
                "layout": local_layout.name,
                "png": local_png.name,
                "pngSha256": validate_png(local_png),
                "node": node,
            }
        )
    png_hashes = [str(capture["pngSha256"]) for capture in captures]
    metadata: dict[str, object] = {
        "schemaVersion": 1,
        "journeyId": args.journey_id,
        "stableId": args.stable_id,
        "expectedText": args.expected_text,
        "bundle": args.bundle,
        "target": target,
        "repetitions": args.repetitions,
        "allPngHashesEqual": len(set(png_hashes)) == 1,
        "captures": captures,
    }
    (output_dir / "checkpoint.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    args = parse_arguments()
    try:
        metadata = collect(args)
    except EvidenceError as error:
        print("status=failed")
        print(f"reason={error.reason}")
        if error.detail:
            print(f"detail={error.detail}")
        return 1
    print("status=passed")
    print(f"journey_id={metadata['journeyId']}")
    print(f"stable_id={metadata['stableId']}")
    print(f"captures={metadata['repetitions']}")
    print(f"all_png_hashes_equal={str(metadata['allPngHashesEqual']).lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
