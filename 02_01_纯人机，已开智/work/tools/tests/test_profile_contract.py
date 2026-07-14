#!/usr/bin/env python3
"""Executable contract for the migrated Jetsnack profile screen.

The Android Compose source and its light/dark VectorDrawables remain the
oracle.  These checks deliberately compare authored SVG geometry and paint
semantics to that oracle instead of accepting a visually similar redraw.
"""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "entry" / "src" / "main" / "ets" / "screens" / "ProfileScreen.ets"
ANDROID_RES = ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "res"
HARMONY_RES = ROOT / "entry" / "src" / "main" / "resources"

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
SVG_NS = "{http://www.w3.org/2000/svg}"


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing authored file: {path.relative_to(ROOT).as_posix()}")
    source = path.read_text(encoding="utf-8")
    if not source.strip():
        raise AssertionError(f"empty authored file: {path.relative_to(ROOT).as_posix()}")
    return source


def _compact_code(source: str) -> str:
    """Remove comments and insignificant whitespace from simple ArkTS source."""

    without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    return re.sub(r"\s+", "", without_comments)


def _assert_pattern(test: unittest.TestCase, source: str, pattern: str, message: str) -> None:
    test.assertRegex(source, re.compile(pattern, re.DOTALL), message)


class ProfileScreenContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _read(PROFILE_PATH)
        self.code = _compact_code(self.source)

    def test_profile_is_an_exported_arkui_component_with_stable_id(self) -> None:
        _assert_pattern(
            self,
            self.source,
            r"@Component\s+export\s+struct\s+ProfileScreen\b",
            "ProfileScreen must be an exported ArkUI component",
        )
        self.assertIn(".id('screen.profile')", self.code)
        self.assertNotIn(".accessibilityGroup(true)", self.code)

    def test_profile_preserves_empty_state_ratio_without_overflowing_narrow_screens(self) -> None:
        _assert_pattern(
            self,
            self.code,
            r"Image\(\$r\('app\.media\.empty_state_search'\)\)"
            r"(?:(?!Image\().)*?\.width\('100%'\)"
            r"(?:(?!Image\().)*?\.constraintSize\(\{maxWidth:341\}\)"
            r"(?:(?!Image\().)*?\.aspectRatio\(341/179\)",
            "profile illustration must preserve 341:179 while respecting its padded parent width",
        )

    def test_profile_preserves_compose_centering_and_spacing(self) -> None:
        self.assertIn(".width('100%')", self.code)
        self.assertIn(".height('100%')", self.code)
        self.assertIn(".padding(24)", self.code)
        self.assertIn(".alignItems(HorizontalAlign.Center)", self.code)
        self.assertIn(".justifyContent(FlexAlign.Center)", self.code)
        _assert_pattern(
            self,
            self.code,
            r"Image\(\$r\('app\.media\.empty_state_search'\)\)"
            r"(?:(?!\bText\().)*?\.margin\(\{bottom:24\}\)"
            r"(?:(?!\bText\().)*?Text\(\$r\('app\.string\.work_in_progress'\)\)",
            "the title must follow the image after 24vp",
        )
        _assert_pattern(
            self,
            self.code,
            r"Text\(\$r\('app\.string\.work_in_progress'\)\)"
            r"(?:(?!\bText\().)*?\.margin\(\{bottom:16\}\)"
            r"(?:(?!\bText\().)*?Text\(\$r\('app\.string\.grab_beverage'\)\)",
            "the body must follow the title after 16vp",
        )

    def test_profile_typography_matches_material_title_and_body(self) -> None:
        _assert_pattern(
            self,
            self.code,
            r"Text\(\$r\('app\.string\.work_in_progress'\)\)"
            r"(?:(?!\bText\().)*?\.fontSize\(16\)"
            r"(?:(?!\bText\().)*?\.fontFamily\(MONTSERRAT_SEMIBOLD\)"
            r"(?:(?!\bText\().)*?\.lineHeight\(24\)"
            r"(?:(?!\bText\().)*?\.textAlign\(TextAlign\.Center\)",
            "profile title typography must match Android titleMedium",
        )
        _assert_pattern(
            self,
            self.code,
            r"Text\(\$r\('app\.string\.grab_beverage'\)\)"
            r"(?:(?!\bText\().)*?\.fontSize\(14\)"
            r"(?:(?!\bText\().)*?\.fontFamily\(MONTSERRAT_MEDIUM\)"
            r"(?:(?!\bText\().)*?\.lineHeight\(20\)"
            r"(?:(?!\bText\().)*?\.textAlign\(TextAlign\.Center\)",
            "profile body typography must match Android bodyMedium",
        )


class EmptyStateSvgContractTests(unittest.TestCase):
    def _assert_exact_conversion(self, android_path: Path, harmony_path: Path) -> None:
        android_root = ET.parse(android_path).getroot()
        svg_root = ET.parse(harmony_path).getroot()

        self.assertEqual(svg_root.tag, f"{SVG_NS}svg")
        self.assertEqual(svg_root.attrib.get("width"), android_root.attrib[f"{ANDROID_NS}width"].removesuffix("dp"))
        self.assertEqual(svg_root.attrib.get("height"), android_root.attrib[f"{ANDROID_NS}height"].removesuffix("dp"))
        expected_view_box = (
            f"0 0 {android_root.attrib[f'{ANDROID_NS}viewportWidth']} "
            f"{android_root.attrib[f'{ANDROID_NS}viewportHeight']}"
        )
        self.assertEqual(svg_root.attrib.get("viewBox"), expected_view_box)

        android_paths = android_root.findall("path")
        svg_paths = svg_root.findall(f"{SVG_NS}path")
        self.assertEqual(len(svg_paths), len(android_paths), "SVG path count changed")
        for index, (android_shape, svg_shape) in enumerate(zip(android_paths, svg_paths, strict=True)):
            self.assertEqual(
                svg_shape.attrib.get("d"),
                android_shape.attrib[f"{ANDROID_NS}pathData"],
                f"path {index} geometry changed",
            )
            self.assertEqual(
                svg_shape.attrib.get("fill", "").lower(),
                android_shape.attrib[f"{ANDROID_NS}fillColor"].lower(),
                f"path {index} fill changed",
            )
            android_fill_type = android_shape.attrib.get(f"{ANDROID_NS}fillType", "nonZero").lower()
            svg_fill_rule = svg_shape.attrib.get("fill-rule", "nonzero").lower()
            self.assertEqual(svg_fill_rule, android_fill_type, f"path {index} fillType changed")

    def test_light_vector_is_converted_without_redrawing(self) -> None:
        self._assert_exact_conversion(
            ANDROID_RES / "drawable" / "empty_state_search.xml",
            HARMONY_RES / "base" / "media" / "empty_state_search.svg",
        )

    def test_dark_vector_is_converted_without_redrawing(self) -> None:
        self._assert_exact_conversion(
            ANDROID_RES / "drawable-night" / "empty_state_search.xml",
            HARMONY_RES / "dark" / "media" / "empty_state_search.svg",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
