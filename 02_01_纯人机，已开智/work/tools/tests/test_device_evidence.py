#!/usr/bin/env python3
"""Behavior tests for the device screenshot evidence collector."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "tools" / "device_evidence.py"


class DeviceEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_root = Path(self.temporary_directory.name)
        self.fake_hdc = self.temp_root / "fake-hdc"
        self.fake_hdc.write_text(
            "#!/usr/bin/env python3\n"
            "import json\n"
            "import os\n"
            "from pathlib import Path\n"
            "import sys\n\n"
            "args = sys.argv[1:]\n"
            "if args == ['list', 'targets']:\n"
            "    print(os.environ.get('FAKE_TARGETS', 'device-1'))\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['file', 'recv']:\n"
            "    remote, local = args[2], Path(args[3])\n"
            "    local.parent.mkdir(parents=True, exist_ok=True)\n"
            "    if remote.endswith('.json'):\n"
            "        stable_id = os.environ.get('FAKE_STABLE_ID', 'screen.feed')\n"
            "        payload = {'windows': [{'attributes': {\n"
            "            'id': stable_id,\n"
            "            'text': \"Android's picks\",\n"
            "            'visible': True,\n"
            "            'bounds': '[0,0][360,800]'\n"
            "        }}]}\n"
            "        local.write_text(json.dumps(payload), encoding='utf-8')\n"
            "    else:\n"
            "        local.write_bytes(b'\\x89PNG\\r\\n\\x1a\\n' + b'raw-device-png')\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['shell', 'uitest']:\n"
            "    raise SystemExit(0)\n"
            "print('unexpected arguments: ' + repr(args), file=sys.stderr)\n"
            "raise SystemExit(9)\n",
            encoding="utf-8",
        )
        self.fake_hdc.chmod(0o755)

    def run_collector(
        self,
        *,
        stable_id: str = "screen.feed",
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        if extra_environment is not None:
            environment.update(extra_environment)
        return subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--hdc",
                str(self.fake_hdc),
                "--journey-id",
                "core.feed",
                "--stable-id",
                stable_id,
                "--expected-text",
                "Android's picks",
                "--repetitions",
                "2",
                "--settle-ms",
                "0",
                "--output-dir",
                str(self.temp_root / "evidence"),
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_collects_raw_png_layout_and_metadata_by_stable_id(self) -> None:
        completed = self.run_collector()

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("status=passed", completed.stdout)
        evidence = self.temp_root / "evidence"
        self.assertEqual(2, len(list(evidence.glob("*-layout.json"))))
        self.assertEqual(2, len(list(evidence.glob("*-screen.png"))))
        metadata = json.loads((evidence / "checkpoint.json").read_text(encoding="utf-8"))
        self.assertEqual("core.feed", metadata["journeyId"])
        self.assertEqual("screen.feed", metadata["stableId"])
        self.assertEqual("device-1", metadata["target"])
        self.assertEqual(2, len(metadata["captures"]))
        self.assertTrue(metadata["allPngHashesEqual"])
        self.assertEqual("[0,0][360,800]", metadata["captures"][0]["node"]["bounds"])

    def test_rejects_ambiguous_device_selection(self) -> None:
        completed = self.run_collector(extra_environment={"FAKE_TARGETS": "device-1\ndevice-2"})

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=expected_exactly_one_target", completed.stdout)

    def test_rejects_a_layout_without_the_requested_stable_id(self) -> None:
        completed = self.run_collector(
            stable_id="screen.search",
            extra_environment={"FAKE_STABLE_ID": "screen.feed"},
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reason=stable_id_not_found", completed.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
