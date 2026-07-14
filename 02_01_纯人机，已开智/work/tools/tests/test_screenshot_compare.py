#!/usr/bin/env python3
"""Behavior tests for the dependency-free screenshot comparison gate."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "screenshot_compare.py"


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(payload, checksum)
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def write_rgba_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixels[y * width + x])
    payload = bytearray(b"\x89PNG\r\n\x1a\n")
    payload.extend(png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    payload.extend(png_chunk(b"IDAT", zlib.compress(bytes(rows))))
    payload.extend(png_chunk(b"IEND", b""))
    path.write_bytes(payload)


def paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
    return (left, above, upper_left)[distances.index(min(distances))]


def write_filtered_rgba_png(
    path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]
) -> None:
    rows = bytearray()
    previous = bytes(width * 4)
    for y in range(height):
        raw = bytes(channel for pixel in pixels[y * width:(y + 1) * width] for channel in pixel)
        filter_type = y % 5
        encoded = bytearray(len(raw))
        for index, value in enumerate(raw):
            left = raw[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            predictions = (0, left, above, (left + above) // 2, paeth(left, above, upper_left))
            encoded[index] = (value - predictions[filter_type]) & 0xFF
        rows.append(filter_type)
        rows.extend(encoded)
        previous = raw
    payload = bytearray(b"\x89PNG\r\n\x1a\n")
    payload.extend(png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    payload.extend(png_chunk(b"IDAT", zlib.compress(bytes(rows))))
    payload.extend(png_chunk(b"IEND", b""))
    path.write_bytes(payload)


class ScreenshotCompareTests(unittest.TestCase):
    def run_compare(self, reference: Path, actual: Path, report: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--reference",
                str(reference),
                "--actual",
                str(actual),
                "--output",
                str(report),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_identical_raw_png_passes_with_exact_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "android.png"
            actual = root / "harmony.png"
            report = root / "comparison.json"
            pixels = [(24, 48, 96, 255)] * (16 * 16)
            write_rgba_png(reference, 16, 16, pixels)
            write_rgba_png(actual, 16, 16, pixels)

            result = self.run_compare(reference, actual, report)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("passed", payload["status"])
            self.assertEqual(0, payload["metrics"]["meanAbsoluteError"])
            self.assertEqual(0, payload["metrics"]["pixelMismatchRate"])
            self.assertEqual(1, payload["metrics"]["ssim"])
            self.assertEqual("android.png", payload["reference"])
            self.assertEqual("harmony.png", payload["actual"])

    def test_visually_different_png_fails_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "android.png"
            actual = root / "harmony.png"
            report = root / "comparison.json"
            write_rgba_png(reference, 16, 16, [(0, 0, 0, 255)] * (16 * 16))
            write_rgba_png(actual, 16, 16, [(255, 255, 255, 255)] * (16 * 16))

            result = self.run_compare(reference, actual, report)

            self.assertEqual(1, result.returncode)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("failed", payload["status"])
            self.assertEqual(255, payload["metrics"]["meanAbsoluteError"])
            self.assertEqual(1, payload["metrics"]["pixelMismatchRate"])
            self.assertLess(payload["metrics"]["ssim"], 0.01)
            self.assertEqual(
                ["mean_absolute_error", "pixel_mismatch_rate", "ssim"],
                payload["failedThresholds"],
            )

    def test_all_standard_png_row_filters_decode_to_the_same_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "android.png"
            actual = root / "harmony.png"
            report = root / "comparison.json"
            pixels = [
                ((x * 29 + y * 7) % 256, (x * 11 + y * 31) % 256, (x * 3 + y * 47) % 256, 255)
                for y in range(10)
                for x in range(9)
            ]
            write_rgba_png(reference, 9, 10, pixels)
            write_filtered_rgba_png(actual, 9, 10, pixels)

            result = self.run_compare(reference, actual, report)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(0, payload["metrics"]["meanAbsoluteError"])
            self.assertEqual(1, payload["metrics"]["ssim"])

    def test_dimension_mismatch_is_a_stable_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "android.png"
            actual = root / "harmony.png"
            report = root / "comparison.json"
            write_rgba_png(reference, 16, 16, [(0, 0, 0, 255)] * (16 * 16))
            write_rgba_png(actual, 8, 16, [(0, 0, 0, 255)] * (8 * 16))

            result = self.run_compare(reference, actual, report)

            self.assertEqual(2, result.returncode)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("input_error", payload["status"])
            self.assertEqual("dimension_mismatch", payload["reason"])
            self.assertEqual({"width": 16, "height": 16}, payload["referenceSize"])
            self.assertEqual({"width": 8, "height": 16}, payload["actualSize"])


if __name__ == "__main__":
    unittest.main()
