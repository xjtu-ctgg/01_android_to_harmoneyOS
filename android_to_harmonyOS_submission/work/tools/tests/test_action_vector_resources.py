#!/usr/bin/env python3
"""Contracts for Android action-vector resources migrated to Harmony SVG.

The Android source uses white as a neutral, tintable foreground rather than a
semantic color.  Harmony SVGs therefore normalize that neutral foreground to
black so ArkUI ``Image.fillColor`` can tint it reliably.  Geometry is not
normalized: viewport values, path ordering, pathData strings, and any explicit
fillType remain source-identical.
"""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_DRAWABLE = ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "res" / "drawable"
HARMONY_MEDIA = ROOT / "entry" / "src" / "main" / "resources" / "base" / "media"

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = f"{{{ANDROID_NS}}}"
SVG_NS = "http://www.w3.org/2000/svg"
SVG = f"{{{SVG_NS}}}"

ACTION_VECTORS = (
    "ic_add",
    "ic_remove",
    "ic_close",
    "ic_delete_forever",
    "ic_check",
    "ic_android",
    "ic_star",
    "ic_sort_by_alpha",
)

# Android's enum uses camelCase while SVG uses CSS spelling.
FILL_RULE = {
    "nonZero": "nonzero",
    "evenOdd": "evenodd",
}


def _android_vector(name: str) -> ET.Element:
    source = ANDROID_DRAWABLE / f"{name}.xml"
    if not source.is_file():
        raise AssertionError(f"missing Android vector source: {source.relative_to(ROOT)}")
    return ET.parse(source).getroot()


def _harmony_svg(name: str) -> ET.Element:
    target = HARMONY_MEDIA / f"{name}.svg"
    if not target.is_file():
        raise AssertionError(f"missing Harmony SVG target: {target.relative_to(ROOT)}")
    return ET.parse(target).getroot()


class ActionVectorResourcesTest(unittest.TestCase):
    def test_all_required_action_vectors_have_harmony_targets(self) -> None:
        missing = [
            f"{name}.svg"
            for name in ACTION_VECTORS
            if not (HARMONY_MEDIA / f"{name}.svg").is_file()
        ]
        self.assertEqual([], missing, f"missing migrated action vectors: {missing}")

    def test_svg_size_and_viewport_match_android_vector(self) -> None:
        for name in ACTION_VECTORS:
            with self.subTest(vector=name):
                android = _android_vector(name)
                harmony = _harmony_svg(name)

                expected_width = android.attrib[f"{ANDROID}width"].removesuffix("dp")
                expected_height = android.attrib[f"{ANDROID}height"].removesuffix("dp")
                viewport_width = android.attrib[f"{ANDROID}viewportWidth"]
                viewport_height = android.attrib[f"{ANDROID}viewportHeight"]

                self.assertEqual(expected_width, harmony.attrib.get("width"))
                self.assertEqual(expected_height, harmony.attrib.get("height"))
                self.assertEqual(
                    f"0 0 {viewport_width} {viewport_height}",
                    harmony.attrib.get("viewBox"),
                )

    def test_path_geometry_and_order_are_source_identical(self) -> None:
        for name in ACTION_VECTORS:
            with self.subTest(vector=name):
                android_paths = _android_vector(name).findall("path")
                harmony_paths = _harmony_svg(name).findall(f"{SVG}path")

                self.assertEqual(
                    len(android_paths),
                    len(harmony_paths),
                    "multi-path vectors must preserve path count and ordering",
                )
                for android_path, harmony_path in zip(android_paths, harmony_paths):
                    self.assertEqual(
                        android_path.attrib[f"{ANDROID}pathData"],
                        harmony_path.attrib.get("d"),
                    )

    def test_neutral_android_foreground_is_tintable_black(self) -> None:
        for name in ACTION_VECTORS:
            with self.subTest(vector=name):
                android_paths = _android_vector(name).findall("path")
                harmony_paths = _harmony_svg(name).findall(f"{SVG}path")
                for android_path, harmony_path in zip(android_paths, harmony_paths):
                    self.assertEqual(
                        "@android:color/white",
                        android_path.attrib.get(f"{ANDROID}fillColor"),
                        "a semantic source color needs an explicit migration decision",
                    )
                    self.assertEqual("#000000", harmony_path.attrib.get("fill"))

    def test_explicit_android_fill_type_maps_to_svg_fill_rule(self) -> None:
        for name in ACTION_VECTORS:
            with self.subTest(vector=name):
                android_paths = _android_vector(name).findall("path")
                harmony_paths = _harmony_svg(name).findall(f"{SVG}path")
                for android_path, harmony_path in zip(android_paths, harmony_paths):
                    android_fill_type = android_path.attrib.get(f"{ANDROID}fillType")
                    svg_fill_rule = harmony_path.attrib.get("fill-rule")
                    if android_fill_type is None:
                        self.assertIsNone(
                            svg_fill_rule,
                            "do not invent a fill rule when Android uses its default",
                        )
                    else:
                        self.assertEqual(FILL_RULE[android_fill_type], svg_fill_rule)


if __name__ == "__main__":
    unittest.main()
