#!/usr/bin/env python3
"""Executable delivery contract for the Jetsnack HarmonyOS migration."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FACTS_PATH = ROOT / "source-facts" / "android-facts.json"
MANIFEST_PATH = ROOT / "migration-manifest.json"
CHECKER_PATH = ROOT / "tools" / "contract_check.py"

SOURCE_COMMIT = "23e1421b72b602d80486777efbf24dd248abf3bb"
EXPECTED_ROUTES = (
    "home/feed",
    "home/search",
    "home/cart",
    "home/profile",
    "snack/{snackId}?origin={origin}",
    "overlay/filter",
)
EXPECTED_SNACKS = (
    (1, "Cupcake", "cupcake.jpg", 299),
    (2, "Donut", "donut.jpg", 299),
    (3, "Eclair", "eclair.jpg", 299),
    (4, "Froyo", "froyo.jpg", 299),
    (5, "Gingerbread", "gingerbread.jpg", 499),
    (6, "Honeycomb", "honeycomb.jpg", 299),
    (7, "Ice Cream Sandwich", "ice_cream_sandwich.jpg", 1299),
    (8, "Jellybean", "jelly_bean.jpg", 299),
    (9, "KitKat", "kitkat.jpg", 549),
    (10, "Lollipop", "lollipop.jpg", 299),
    (11, "Marshmallow", "marshmallow.jpg", 299),
    (12, "Nougat", "nougat.jpg", 299),
    (13, "Oreo", "oreo.jpg", 299),
    (14, "Pie", "pie.jpg", 299),
    (15, "Chips", "chips.jpg", 299),
    (16, "Pretzels", "pretzels.jpg", 299),
    (17, "Smoothies", "smoothies.jpg", 299),
    (18, "Popcorn", "popcorn.jpg", 299),
    (19, "Almonds", "almonds.jpg", 299),
    (20, "Cheese", "cheese.jpg", 299),
    (21, "Apples", "apples.jpg", 299),
    (22, "Apple sauce", "apple_sauce.jpg", 299),
    (23, "Apple chips", "apple_chips.jpg", 299),
    (24, "Apple juice", "apple_juice.jpg", 299),
    (25, "Apple pie", "apple_pie.jpg", 299),
    (26, "Grapes", "grapes.jpg", 299),
    (27, "Kiwi", "kiwi.jpg", 299),
    (28, "Mango", "mango.jpg", 299),
)
REQUIRED_TEXTS = {
    "HOME",
    "Android's picks",
    "SEARCH",
    "Categories",
    "MY CART",
    "Order (3 items)",
    "PROFILE",
    "This is currently work in progress",
    "Chips",
    "ADD TO CART",
}
DETAIL_DESCRIPTION = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut tempus, sem vitae convallis "
    "imperdiet, lectus nunc pharetra diam, ac rhoncus quam eros eu risus. Nulla pulvinar "
    "condimentum erat, pulvinar tempus turpis blandit ut. Etiam sed ipsum sed lacus eleifend "
    "hendrerit eu quis quam. Etiam ligula eros, finibus vestibulum tortor ac, ultrices accumsan "
    "dolor. Vivamus vel nisl a libero lobortis posuere. Aenean facilisis nibh vel ultrices "
    "bibendum. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac "
    "turpis egestas. Suspendisse ac est vitae lacus commodo efficitur at ut massa. Etiam "
    "vestibulum sit amet sapien sed varius. Aliquam non ipsum imperdiet, pulvinar enim nec, "
    "mollis risus. Fusce id tincidunt nisl."
)
NO_RESULTS_TITLE_TEMPLATE = "No matches for “%1s”"
NO_RESULTS_RETRY = "Try broadening your search"
EXPECTED_NO_OPS = {
    "delivery.address.expand",
    "feed.collection.action",
    "filter.reset",
    "search.category.select",
    "search.result.add",
    "cart.checkout",
    "cart.swipeDismiss.persistence",
    "detail.addToCart",
    "detail.related.select",
    "filter.applyToFeed",
}

REQUIRED_PATHS = (
    "AppScope/app.json5",
    "build-profile.json5",
    "entry/build-profile.json5",
    "entry/src/main/module.json5",
    "entry/src/main/ets/entryability/EntryAbility.ets",
    "entry/src/main/ets/pages/Index.ets",
    "migration-manifest.json",
    "skills/android-to-harmonyos/SKILL.md",
    "journeys/core.yaml",
            "tools/device_evidence.py",
            "tools/screenshot_compare.py",
)

TEXT_SUFFIXES = {
    ".ets",
    ".json",
    ".json5",
    ".kt",
    ".kts",
    ".md",
    ".properties",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".xml",
    ".yaml",
    ".yml",
}

IGNORED_SCAN_PARTS = {
    ".git",
    ".gradle",
    ".hvigor",
    ".idea",
    ".kotlin",
    "build",
    "generated",
    "node_modules",
    "oh_modules",
    "third-party",
    "third_party",
    "vendor",
}

# The source Android tree remains in place until the Harmony HAP is proven.  It is
# not part of the new delivery surface scanned by this task; final packaging has a
# separate hard gate that removes it and its caches.
LEGACY_ANDROID_ROOTS = {
    ".gradle",
    ".kotlin",
    "app",
    "gradle",
}
LEGACY_ROOT_FILES = {
    "README.md",
    "build.gradle.kts",
    "gradle.properties",
    "gradlew",
    "gradlew.bat",
    "local.properties",
    "settings.gradle.kts",
}

LEGAL_MIGRATION_STATUSES = {"planned", "in_progress", "implemented", "verified", "not_applicable"}
LEGAL_MAPPING_KINDS = {"page", "route", "action", "data", "state", "theme", "resource", "component"}


def _is_ignored_scan_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in IGNORED_SCAN_PARTS for part in relative.parts)


def _iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if _is_ignored_scan_path(path, ROOT):
            continue
        if relative.parts[0] in LEGACY_ANDROID_ROOTS or relative.as_posix() in LEGACY_ROOT_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def _personal_path_patterns() -> tuple[re.Pattern[str], ...]:
    unix_roots = ("/" + "Users" + "/", "/" + "home" + "/")
    slash = chr(92)
    windows_root = "C:" + slash + "Users" + slash
    boundary = r"(?:^|[\s'\"=:(])"
    return (
        *(re.compile(boundary + re.escape(root) + r"[^/\s]+/", re.MULTILINE) for root in unix_roots),
        re.compile(
            boundary + re.escape(windows_root) + r"[^" + re.escape(slash) + r"\s]+" + re.escape(slash),
            re.MULTILINE,
        ),
    )


def _secret_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
    rsa_key_marker = "-----BEGIN " + "RSA PRIVATE KEY-----"
    aws_key_prefix = "AK" + "IA"
    github_token_prefix = "gh" + "p_"
    return (
        ("private key", re.compile(re.escape(private_key_marker))),
        ("RSA private key", re.compile(re.escape(rsa_key_marker))),
        ("AWS access key", re.compile(re.escape(aws_key_prefix) + r"[0-9A-Z]{16}")),
        ("GitHub token", re.compile(re.escape(github_token_prefix) + r"[A-Za-z0-9]{36}")),
    )


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(f"missing contract JSON: {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def _mask_arkts_non_code(source: str) -> str:
    """Blank ArkTS comments and literal text while retaining template code.

    The result has exactly the same length and newline positions as ``source``.
    This lets the policy regexes inspect authored code without false positives
    from user-visible copy, URLs, or comments. Template ``${...}`` expressions
    are recursively treated as code, including nested objects and templates.
    """

    output = ["\n" if char == "\n" else " " for char in source]
    source_length = len(source)

    def mask_quoted(index: int, quote: str) -> int:
        index += 1
        while index < source_length:
            char = source[index]
            if char == "\\":
                index += 2
                continue
            index += 1
            if char == quote:
                break
        return index

    def mask_line_comment(index: int) -> int:
        index += 2
        while index < source_length and source[index] != "\n":
            index += 1
        return index

    def mask_block_comment(index: int) -> int:
        index += 2
        while index < source_length:
            if source[index] == "*" and index + 1 < source_length and source[index + 1] == "/":
                return index + 2
            index += 1
        return index

    def mask_template(index: int) -> int:
        index += 1
        while index < source_length:
            char = source[index]
            following = source[index + 1] if index + 1 < source_length else ""
            if char == "\\":
                index += 2
                continue
            if char == "`":
                return index + 1
            if char == "$" and following == "{":
                index = mask_code(index + 2, stop_at_closing_brace=True)
                continue
            index += 1
        return index

    def mask_code(index: int, *, stop_at_closing_brace: bool) -> int:
        brace_depth = 0
        while index < source_length:
            char = source[index]
            following = source[index + 1] if index + 1 < source_length else ""

            if char == "/" and following == "/":
                index = mask_line_comment(index)
                continue
            if char == "/" and following == "*":
                index = mask_block_comment(index)
                continue
            if char in {"'", '"'}:
                index = mask_quoted(index, char)
                continue
            if char == "`":
                index = mask_template(index)
                continue
            if char == "{":
                output[index] = char
                brace_depth += 1
                index += 1
                continue
            if char == "}" and stop_at_closing_brace:
                if brace_depth == 0:
                    return index + 1
                brace_depth -= 1

            output[index] = char
            index += 1
        return index

    mask_code(0, stop_at_closing_brace=False)
    return "".join(output)


ARKTS_ANY_PATTERNS = (re.compile(r"\b(?:any|unknown)\b"),)

EMPTY_EVENT_PATTERN = re.compile(
    r"\b(?:onAction|onChange|onClick|onSelect|onSubmit|onTouch)"
    r"\s*(?:\(|:|=)[^{}\n]*=>\s*\{\s*\}",
)

# OpenHarmony's ArkTS coding guide classifies Array methods as the preferred
# traversal form.  Keeping authored application code free of classic array
# loops also avoids index-bound mistakes and the corresponding Code Linter
# finding category.
CLASSIC_FOR_LOOP_PATTERN = re.compile(r"\bfor\s*\(")

OFFICIAL_ARKTS_STYLE_PATTERNS = (
    re.compile(r"\bArray\s*<"),
    re.compile(r"\bESObject\b"),
    re.compile(r"\bexport\s*\*"),
    re.compile(r"\bglobalThis\b"),
    re.compile(r"\bdebugger\s*;"),
    re.compile(r"\bas\s+const\b"),
    re.compile(r"\*\*"),
    re.compile(r"\bfor\s*\([^)]*\bin\b"),
    re.compile(r"\[[A-Za-z_$][\w$]*\s*:\s*(?:string|number)\s*\]\s*:"),
    re.compile(r"(?:===?|!==?)\s*Number\.NaN\b|\bNumber\.NaN\s*(?:===?|!==?)"),
    re.compile(r"\bfinally\s*\{[^}]*\b(?:return|break|continue|throw)\b", re.DOTALL),
)

# ArkTS 2.0 rejects JavaScript regexp literals (arkts-no-regexp-literals).
# Require a syntactic expression prefix so division operators are not mistaken
# for regexp literals. Strings and comments are already blanked by the scanner.
REGEXP_LITERAL_PATTERN = re.compile(
    r"(?:^|[=(,:\[!&|?{};])\s*/(?![/*])(?:\\.|[^/\\\n])+/[dgimsuvy]*",
    re.MULTILINE,
)


def _iter_authored_arkts_files(root: Path = ROOT) -> list[Path]:
    """Return ArkTS authored under top-level Harmony module source trees."""

    files: list[Path] = []
    for source_root in sorted(root.glob("*/src"), key=lambda item: item.as_posix()):
        module_name = source_root.parent.name
        if module_name in LEGACY_ANDROID_ROOTS or module_name in IGNORED_SCAN_PARTS:
            continue
        for path in source_root.rglob("*.ets"):
            if path.is_file() and not _is_ignored_scan_path(path, root):
                files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def _arkts_violation_paths(root: Path, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    violations: list[str] = []
    for path in _iter_authored_arkts_files(root):
        source = _mask_arkts_non_code(path.read_text(encoding="utf-8", errors="ignore"))
        if any(pattern.search(source) for pattern in patterns):
            violations.append(path.relative_to(root).as_posix())
    return violations


class DeliveryContractTests(unittest.TestCase):
    def test_01_required_delivery_files_exist(self) -> None:
        for relative_path in REQUIRED_PATHS:
            with self.subTest(path=relative_path):
                self.assertTrue(
                    (ROOT / relative_path).is_file(),
                    f"missing required delivery file: {relative_path}",
                )

    def test_01b_required_submission_metadata_exists(self) -> None:
        delivery_root = ROOT.parent
        if not (delivery_root / "INSTRUCTION.md").is_file():
            self.skipTest("work-only build copy intentionally has no delivery metadata")
        required_files = (
            "result/output.md",
            "logs/interaction.md",
            "logs/trace/validation.md",
        )
        for relative_path in required_files:
            with self.subTest(path=relative_path):
                path = delivery_root / relative_path
                self.assertTrue(path.is_file(), f"missing required submission file: {relative_path}")
                self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_02_delivery_contains_no_personal_absolute_paths(self) -> None:
        violations: list[str] = []
        patterns = _personal_path_patterns()
        for path in _iter_text_files():
            source = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern.search(source) for pattern in patterns):
                violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], violations, f"personal absolute paths found in: {violations}")

    def test_03_delivery_contains_no_key_material(self) -> None:
        violations: list[str] = []
        patterns = _secret_patterns()
        for path in _iter_text_files():
            source = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in patterns:
                if pattern.search(source):
                    violations.append(f"{path.relative_to(ROOT).as_posix()}: {label}")
        self.assertEqual([], violations, f"possible key material found: {violations}")

    def test_04_arkts_uses_no_any_types(self) -> None:
        violations = _arkts_violation_paths(ROOT, ARKTS_ANY_PATTERNS)
        self.assertEqual([], violations, f"ArkTS any types found in: {violations}")

    def test_05_arkts_uses_no_empty_event_placeholders(self) -> None:
        violations = _arkts_violation_paths(ROOT, (EMPTY_EVENT_PATTERN,))
        self.assertEqual([], violations, f"empty ArkTS event handlers found in: {violations}")

    def test_05b_arkts_array_traversal_uses_array_methods(self) -> None:
        violations = _arkts_violation_paths(ROOT, (CLASSIC_FOR_LOOP_PATTERN,))
        self.assertEqual([], violations, f"classic ArkTS for loops found in: {violations}")

    def test_05c_arkts_avoids_official_style_rule_antipatterns(self) -> None:
        violations = _arkts_violation_paths(ROOT, OFFICIAL_ARKTS_STYLE_PATTERNS)
        self.assertEqual([], violations, f"official ArkTS style violations found in: {violations}")

    def test_05d_arkts_avoids_regexp_literals(self) -> None:
        violations = _arkts_violation_paths(ROOT, (REGEXP_LITERAL_PATTERN,))
        self.assertEqual([], violations, f"ArkTS regexp literals found in: {violations}")

    def test_06_delivery_contains_no_android_build_artifacts(self) -> None:
        violations: list[str] = []
        for suffix in ("*.aab", "*.aar", "*.apk", "*.dex"):
            for path in ROOT.rglob(suffix):
                relative = path.relative_to(ROOT)
                if ".git" in relative.parts or relative.parts[0] in LEGACY_ANDROID_ROOTS:
                    continue
                violations.append(relative.as_posix())
        self.assertEqual([], sorted(set(violations)), f"Android build artifacts found: {sorted(set(violations))}")

    def test_07_source_facts_capture_baseline_identity_and_six_pages(self) -> None:
        facts = _load_json(FACTS_PATH)
        self.assertEqual(1, facts["schemaVersion"])
        self.assertEqual(SOURCE_COMMIT, facts["source"]["commit"])
        self.assertEqual("app", facts["source"]["module"])

        pages = facts["pages"]
        self.assertEqual(6, len(pages))
        self.assertEqual(6, len({page["id"] for page in pages}))
        self.assertEqual(6, len({page["stableId"] for page in pages}))
        self.assertEqual(EXPECTED_ROUTES, tuple(page["route"] for page in pages))
        for page in pages:
            self.assertTrue((ROOT / page["source"]).is_file(), page["source"])

        routes = facts["routes"]
        self.assertEqual(EXPECTED_ROUTES, tuple(route["pattern"] for route in routes))
        self.assertEqual(6, len({route["stableId"] for route in routes}))

    def test_07b_source_facts_preserve_navigation_state_and_keyboard_resize_evidence(self) -> None:
        facts = _load_json(FACTS_PATH)
        self.assertIn("navigationContract", facts)
        self.assertIn("windowContract", facts)
        navigation_path = ROOT / facts["navigationContract"]["source"]
        manifest_path = ROOT / facts["windowContract"]["source"]

        self.assertTrue(navigation_path.is_file(), navigation_path)
        self.assertTrue(manifest_path.is_file(), manifest_path)

        navigation = navigation_path.read_text(encoding="utf-8")
        android_manifest = manifest_path.read_text(encoding="utf-8")
        self.assertIn("restoreState = true", navigation)
        self.assertIn("saveState = true", navigation)
        self.assertIn("launchSingleTop = true", navigation)
        self.assertIn('android:windowSoftInputMode="adjustResize"', android_manifest)

        self.assertEqual(
            "keep all four tab pages mounted and preserve each tab navigation state",
            facts["navigationContract"]["targetSemantics"],
        )
        self.assertEqual(
            "KeyboardAvoidMode.RESIZE",
            facts["windowContract"]["targetKeyboardAvoidMode"],
        )

    def test_07c_source_facts_preserve_the_public_android_instrumentation_contract(self) -> None:
        facts = _load_json(FACTS_PATH)
        contract = facts["publicTestContract"]
        source_path = ROOT / contract["source"]
        self.assertTrue(source_path.is_file(), source_path)
        self.assertEqual(contract["sha256"], hashlib.sha256(source_path.read_bytes()).hexdigest())
        source = source_path.read_text(encoding="utf-8")
        for marker in (
            "fun app_launches()",
            "fun app_canNavigateToAllScreens()",
            "fun app_canNavigateToDetailPage()",
            'onNodeWithText("MY CART")',
            'onNodeWithText("Chips")',
            'onNodeWithText("Lorem ipsum", substring = true)',
        ):
            self.assertIn(marker, source)
        self.assertEqual(
            [
                "core.feed",
                "core.public-app-test.navigate-all-screens",
                "core.public-app-test.open-chips-detail",
            ],
            contract["journeys"],
        )

    def test_07d_source_snapshot_preserves_all_android_kotlin_and_critical_build_inputs(self) -> None:
        snapshot_root = ROOT / "source-facts/android-source"
        self.assertEqual(50, len(list((snapshot_root / "app/src/main/java").rglob("*.kt"))))
        self.assertEqual(1, len(list((snapshot_root / "app/src/androidTest").rglob("*.kt"))))
        self.assertEqual(24, len(list((snapshot_root / "app/src/main/res").rglob("*.xml"))))

        expected_hashes = {
            "app/src/main/java/com/example/jetsnack/ui/components/Button.kt":
                "372283ae73bc53894f4b255249018fa97c022b79e8d5695755e2cccf5935ca2c",
            "app/src/main/java/com/example/jetsnack/ui/components/Card.kt":
                "d8449ab66583e14a75ded095abf92fa48022d001112d26590789bbedc2890a08",
            "app/src/main/java/com/example/jetsnack/ui/components/Surface.kt":
                "305f18ec196373d22129f121c901f6b1f8588eee5b73177560f44278e5adf87a",
            "app/src/main/java/com/example/jetsnack/ui/components/Gradient.kt":
                "e88e6122643c3ecb7af18b44b1ccdb36ac1daa9f6dbd56922175d20c35b9c531",
            "app/src/main/java/com/example/jetsnack/ui/home/search/Suggestions.kt":
                "e3ed638e866211283e2be26a16fb82ed02bbd938ad0d3666770121c6588bc4c2",
            "app/src/main/java/com/example/jetsnack/ui/MainActivity.kt":
                "3586bc3bd8c0f9a06a19b5af6c5e6c19dda289354db8f4d161342a54200b3093",
            "app/src/main/java/com/example/jetsnack/widget/RecentOrdersWidget.kt":
                "1689720b18456ef7ec88a5f34d219a7d8275778d69cf05654c596cf366799300",
            "app/src/main/java/com/example/jetsnack/widget/layout/ImageTextListLayout.kt":
                "37cb78adec81bb9ee0d7bd00c9de571a7786176cf638812dabd3d5761c5c81c7",
            "app/src/main/java/com/example/jetsnack/widget/utils/ActionUtils.kt":
                "18952a069d386bd7ef96a0e6b93c57eac526cfc43da871c43dc6156c0ee2e104",
            "app/build.gradle.kts":
                "1875e28ca0681991eb2c02f25ed968bd9d028521bac04194f3dd8ca6f69385e1",
            "gradle/libs.versions.toml":
                "c8f9f3ecfdf6e2ab7d89e8f4905ea2cfb9d96e7cb9251f98d1d7cbbe74efa85e",
            "README.md":
                "4124caf185ef732d978b48686376a96fdbf1386cadf8cc6ce7c80e42011dc9e5",
        }
        for relative_path, expected_hash in expected_hashes.items():
            with self.subTest(path=relative_path):
                source_path = snapshot_root / relative_path
                self.assertTrue(source_path.is_file(), relative_path)
                self.assertEqual(expected_hash, hashlib.sha256(source_path.read_bytes()).hexdigest())

    def test_08_source_facts_capture_all_28_snacks_with_stable_ids(self) -> None:
        facts = _load_json(FACTS_PATH)
        snacks = facts["snacks"]
        actual = tuple(
            (snack["stableId"], snack["name"], snack["image"], snack["priceCents"])
            for snack in snacks
        )
        self.assertEqual(EXPECTED_SNACKS, actual)
        self.assertEqual(list(range(28)), [snack["sourceIndex"] for snack in snacks])
        self.assertEqual(28, len({snack["stableId"] for snack in snacks}))

    def test_09_source_facts_capture_search_cart_resources_and_contract_text(self) -> None:
        facts = _load_json(FACTS_PATH)

        self.assertEqual([21, 22, 23, 24, 25], facts["search"]["queryExpectations"]["Apple"])
        self.assertEqual([20], facts["search"]["queryExpectations"]["Cheese"])
        self.assertEqual([], facts["search"]["queryExpectations"]["NoSuchSnack"])
        self.assertEqual(list(range(1, 29)), facts["search"]["queryExpectations"][""])
        self.assertEqual([7, 22, 23, 24, 25], facts["search"]["queryExpectations"][" "])
        self.assertEqual([], facts["search"]["queryExpectations"][" Apple "])
        self.assertEqual(["Categories", "Suggestions", "Results", "NoResults"], facts["search"]["states"])

        cart = facts["cart"]
        self.assertEqual(
            [(5, 2), (7, 3), (9, 1)],
            [(line["snackStableId"], line["quantity"]) for line in cart["initialLines"]],
        )
        prices = {snack["stableId"]: snack["priceCents"] for snack in facts["snacks"]}
        calculated_subtotal = sum(prices[line["snackStableId"]] * line["quantity"] for line in cart["initialLines"])
        self.assertEqual(5444, calculated_subtotal)
        self.assertEqual(5444, cart["subtotalCents"])
        self.assertEqual(369, cart["shippingCents"])
        self.assertEqual(5813, cart["totalCents"])
        self.assertEqual(5, cart["quantityFailureInterval"])
        self.assertTrue(cart["decrementAtOneRemoves"])

        resources = facts["resources"]
        self.assertEqual(36, len(resources["images"]))
        self.assertEqual(6, len(resources["fonts"]))
        for relative_path in resources["images"] + resources["fonts"]:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)
        self.assertEqual("#4B30ED", resources["theme"]["brand"])
        self.assertEqual("#86F7FA", resources["theme"]["secondary"])

        self.assertTrue(REQUIRED_TEXTS.issubset(set(facts["requiredTexts"])))
        self.assertIn("publicCopy", facts)
        self.assertEqual(DETAIL_DESCRIPTION, facts["publicCopy"]["detailDescription"])
        self.assertEqual(NO_RESULTS_TITLE_TEMPLATE, facts["publicCopy"]["noResultsTitleTemplate"])
        self.assertEqual(NO_RESULTS_RETRY, facts["publicCopy"]["noResultsRetry"])
        self.assertIn(DETAIL_DESCRIPTION, facts["requiredTexts"])
        self.assertIn(NO_RESULTS_TITLE_TEMPLATE, facts["requiredTexts"])
        self.assertIn(NO_RESULTS_RETRY, facts["requiredTexts"])
        self.assertNotIn("NoResults", facts["requiredTexts"])
        strings_root = ET.parse(
            ROOT / "source-facts/android-source/app/src/main/res/values/strings.xml"
        ).getroot()
        source_strings = {item.attrib["name"]: item.text for item in strings_root.findall("string")}
        self.assertEqual(source_strings["detail_placeholder"], facts["publicCopy"]["detailDescription"])
        self.assertEqual(source_strings["search_no_matches"], facts["publicCopy"]["noResultsTitleTemplate"])
        self.assertEqual(source_strings["search_no_matches_retry"], facts["publicCopy"]["noResultsRetry"])
        no_ops = facts["noOpContracts"]
        self.assertEqual(EXPECTED_NO_OPS, {item["id"] for item in no_ops})
        for item in no_ops:
            self.assertTrue((ROOT / item["source"]).is_file(), item["source"])

    def test_10_manifest_has_traceable_unique_mappings_and_legal_statuses(self) -> None:
        facts = _load_json(FACTS_PATH)
        manifest = _load_json(MANIFEST_PATH)
        self.assertEqual(1, manifest["schemaVersion"])
        self.assertEqual(SOURCE_COMMIT, manifest["sourceCommit"])
        mappings = manifest["mappings"]
        required_keys = {"id", "kind", "source", "target", "stableId", "status", "journey"}
        self.assertTrue(mappings)
        self.assertEqual(len(mappings), len({mapping["id"] for mapping in mappings}))
        self.assertEqual(len(mappings), len({mapping["stableId"] for mapping in mappings}))
        self.assertTrue(all(required_keys.issubset(mapping) for mapping in mappings))
        self.assertTrue(all(mapping["status"] in LEGAL_MIGRATION_STATUSES for mapping in mappings))
        self.assertTrue(all(mapping["kind"] in LEGAL_MAPPING_KINDS for mapping in mappings))
        self.assertTrue(all((ROOT / mapping["source"]).is_file() for mapping in mappings))
        self.assertTrue(all(not Path(mapping["target"]).is_absolute() for mapping in mappings))
        for fact_key, kind in (("pages", "page"), ("routes", "route"), ("noOpContracts", "action")):
            expected = {item["id"]: item for item in facts[fact_key]}
            actual = {mapping["id"]: mapping for mapping in mappings if mapping["kind"] == kind}
            if kind == "action":
                self.assertTrue(set(expected).issubset(actual), f"{kind} mapping coverage")
            else:
                self.assertEqual(set(expected), set(actual), f"{kind} mapping coverage")
            for item_id, fact in expected.items():
                with self.subTest(kind=kind, mapping=item_id):
                    mapping = actual[item_id]
                    self.assertIn("target", fact)
                    self.assertIn("stableId", fact)
                    self.assertIn("journey", fact)
                    self.assertEqual(fact["source"], mapping["source"])
                    self.assertEqual(fact["target"], mapping["target"])
                    self.assertEqual(fact["stableId"], mapping["stableId"])
                    self.assertEqual(fact["journey"], mapping["journey"])

    def test_11_contract_checker_accepts_frozen_baseline_deterministically(self) -> None:
        command = [sys.executable, str(CHECKER_PATH), "--root", str(ROOT)]
        first = subprocess.run(command, check=False, capture_output=True, text=True)
        second = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn("status=passed", first.stdout)
        self.assertIn("snacks=28", first.stdout)
        self.assertIn("pages=6", first.stdout)

    def test_12_contract_checker_rejects_duplicate_ids_and_invalid_status(self) -> None:
        facts = _load_json(FACTS_PATH)
        manifest = _load_json(MANIFEST_PATH)
        invalid_manifest = copy.deepcopy(manifest)
        invalid_manifest["mappings"][1]["stableId"] = invalid_manifest["mappings"][0]["stableId"]
        invalid_manifest["mappings"][1]["status"] = "done-ish"

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(invalid_manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            repeated = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertEqual(result.stdout, repeated.stdout)
        error_lines = [line for line in result.stdout.splitlines() if line.startswith("error=")]
        self.assertEqual(sorted(error_lines), error_lines)
        self.assertIn("status=failed", result.stdout)
        self.assertIn("invalid migration status", result.stdout)
        self.assertIn("duplicate mapping stableId", result.stdout)

    def test_13_contract_checker_rejects_wrong_fact_types_and_missing_route_fields(self) -> None:
        facts = copy.deepcopy(_load_json(FACTS_PATH))
        manifest = _load_json(MANIFEST_PATH)
        facts["pages"][0]["stableId"] = 7
        del facts["routes"][0]["id"]
        del facts["routes"][1]["kind"]
        facts["routes"][2]["kind"] = "drawer"

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("facts pages[0].stableId must be a non-empty string", result.stdout)
        self.assertIn("facts routes[0].id must be a non-empty string", result.stdout)
        self.assertIn("facts routes[1].kind must be one of: detail,overlay,tab", result.stdout)
        self.assertIn("facts routes[2].kind must be one of: detail,overlay,tab", result.stdout)

    def test_14_contract_checker_rejects_invalid_mapping_kind_and_missing_cross_table_mapping(self) -> None:
        facts = _load_json(FACTS_PATH)
        manifest = copy.deepcopy(_load_json(MANIFEST_PATH))
        manifest["mappings"][0]["kind"] = "nonsense"

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid mapping kind at mappings[0]: nonsense", result.stdout)
        self.assertIn("manifest is missing page mappings: feed", result.stdout)

    def test_15_contract_checker_rejects_semantically_wrong_route_contract(self) -> None:
        facts = copy.deepcopy(_load_json(FACTS_PATH))
        manifest = copy.deepcopy(_load_json(MANIFEST_PATH))
        facts["routes"][0]["id"] = "route.fake"
        facts["routes"][0]["kind"] = "detail"
        facts["routes"][2]["deepLink"] = "https://example.invalid/cart"
        route_mapping = next(mapping for mapping in manifest["mappings"] if mapping["id"] == "route.feed")
        route_mapping["id"] = "route.fake"

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("facts route ids do not match the six-route contract", result.stdout)
        self.assertIn("facts route kinds do not match the six-route contract", result.stdout)
        self.assertIn("facts cart route deepLink does not match the Android baseline", result.stdout)

    def test_16_contract_checker_rejects_non_scalar_enums_without_traceback(self) -> None:
        facts = copy.deepcopy(_load_json(FACTS_PATH))
        manifest = copy.deepcopy(_load_json(MANIFEST_PATH))
        facts["routes"][0]["kind"] = []
        facts["collections"][0]["type"] = {}
        manifest["mappings"][0]["kind"] = []
        manifest["mappings"][1]["status"] = {}

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            command = [
                sys.executable,
                str(CHECKER_PATH),
                "--root",
                str(ROOT),
                "--facts",
                str(facts_path),
                "--manifest",
                str(manifest_path),
            ]
            first = subprocess.run(command, check=False, capture_output=True, text=True)
            second = subprocess.run(command, check=False, capture_output=True, text=True)

        self.assertNotEqual(0, first.returncode)
        self.assertEqual(first.stdout, second.stdout)
        self.assertNotIn("Traceback", first.stdout + first.stderr)
        self.assertEqual("", first.stderr)
        self.assertIn("status=failed", first.stdout)
        self.assertIn("facts routes[0].kind must be one of: detail,overlay,tab", first.stdout)
        self.assertIn("facts collections[0].type must be one of: Highlight,Normal", first.stdout)
        self.assertIn("manifest mappings[0].kind must be a non-empty string", first.stdout)
        self.assertIn("manifest mappings[1].status must be a non-empty string", first.stdout)
        error_lines = [line for line in first.stdout.splitlines() if line.startswith("error=")]
        self.assertEqual(sorted(error_lines), error_lines)

    def test_17_arkts_policy_scans_only_authored_main_and_ohos_test_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            personal_path = "/" + "Users" + "/private/path"
            fixtures = {
                "entry/src/main/ets/Authored.ets": "const leaked: any = 1;\n",
                "entry/src/ohosTest/ets/AuthoredTest.ets": "Button().onClick(() => {})\n",
                "entry/src/generated/Generated.ets": "const generated: any = 1;\n",
                "entry/build/generated/BuildOutput.ets": "const output: any = 1;\n",
                "entry/oh_modules/example/Dependency.ets": "const dependency: any = 1;\n",
                ".hvigor/src/main/ets/Generated.ets": f"const cache: any = '{personal_path}';\n",
                "third_party/src/main/ets/Vendored.ets": "const vendored: any = 1;\n",
            }
            for relative_path, source in fixtures.items():
                path = temp_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            any_violations = _arkts_violation_paths(temp_root, ARKTS_ANY_PATTERNS)
            empty_handler_violations = _arkts_violation_paths(temp_root, (EMPTY_EVENT_PATTERN,))

        self.assertEqual(["entry/src/main/ets/Authored.ets"], any_violations)
        self.assertEqual(["entry/src/ohosTest/ets/AuthoredTest.ets"], empty_handler_violations)

    def test_18_arkts_code_masker_blanks_non_code_and_preserves_source_layout(self) -> None:
        cases = {
            "double quoted text": 'const text = "value: any and unknown";\nconst safe: string = "ok";\n',
            "single quoted text": "const text = 'onClick(() => {}) and any';\n",
            "template text": "const text = `type T = any | unknown; onClick(() => {})`;\n",
            "escaped template interpolation": "const text = `escaped \\${value as any}`;\n",
            "real comments": "// value: any\nconst safe: string = 'ok'; /* unknown */\n",
        }

        for label, source in cases.items():
            with self.subTest(case=label):
                masked = _mask_arkts_non_code(source)
                self.assertEqual(len(source), len(masked))
                self.assertEqual(
                    [index for index, char in enumerate(source) if char == "\n"],
                    [index for index, char in enumerate(masked) if char == "\n"],
                )
                self.assertFalse(any(pattern.search(masked) for pattern in ARKTS_ANY_PATTERNS))
                self.assertIsNone(EMPTY_EVENT_PATTERN.search(masked))

    def test_19_arkts_forbidden_type_tokens_cover_all_common_type_positions(self) -> None:
        cases = {
            "annotation any": "let value: any = input;",
            "generic unknown": "type Value = Box<unknown>;",
            "as any": "const value = input as any;",
            "extends unknown": "type Value<T extends unknown> = T;",
            "union any": "type Value = any | string;",
            "intersection any": "type Value = any & object;",
            "parenthesized unknown": "type Value = (unknown);",
            "array any": "type Value = any[];",
            "eof unknown": "type Value = unknown",
        }

        for label, source in cases.items():
            with self.subTest(case=label):
                masked = _mask_arkts_non_code(source)
                self.assertTrue(
                    any(pattern.search(masked) for pattern in ARKTS_ANY_PATTERNS),
                    f"forbidden type token was not detected in: {source}",
                )

    def test_20_arkts_template_interpolations_are_code_with_nested_lexical_states(self) -> None:
        cases = {
            "simple expression": "const text = `value=${value as any}`;",
            "nested object and template": (
                "const text = `outer ${condition ? { nested: `inner ${value as unknown}` } "
                ": { safe: \"https://example.test/a//b\" }} tail`;"
            ),
            "comments and strings inside expression": (
                "const text = `outer ${(() => { /* any */ const label = \"unknown // text\"; "
                "return value as any; })()} tail`;"
            ),
        }

        for label, source in cases.items():
            with self.subTest(case=label):
                masked = _mask_arkts_non_code(source)
                self.assertEqual(len(source), len(masked))
                self.assertTrue(any(pattern.search(masked) for pattern in ARKTS_ANY_PATTERNS))

        safe_source = (
            "const text = `outer ${(() => { /* any */ const label = 'unknown // text'; "
            "return value; })()} tail`;"
        )
        safe_masked = _mask_arkts_non_code(safe_source)
        self.assertFalse(any(pattern.search(safe_masked) for pattern in ARKTS_ANY_PATTERNS))

    def test_21_arkts_policy_scanner_ignores_text_but_detects_code_after_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            fixtures = {
                "entry/src/main/ets/DoubleText.ets": 'const text = "value: any";\n',
                "entry/src/main/ets/SingleText.ets": "const text = 'unknown & object';\n",
                "entry/src/main/ets/TemplateText.ets": (
                    "const text = `type T = any | string; onClick(() => {})`;\n"
                ),
                "entry/src/main/ets/CommentOnly.ets": (
                    "// type T = any | string\n/* type U = unknown */\n"
                ),
                "entry/src/main/ets/Union.ets": "type T = any | string;\n",
                "entry/src/main/ets/Intersection.ets": "type T = any & object;\n",
                "entry/src/main/ets/Eof.ets": "type T = unknown",
                "entry/src/main/ets/TemplateExpression.ets": (
                    "const text = `value=${value as any}`;\n"
                ),
                "entry/src/main/ets/UrlThenCode.ets": (
                    'const url = "https://example.test/a//b"; const leaked: any = input;\n'
                ),
            }
            for relative_path, source in fixtures.items():
                path = temp_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            violations = _arkts_violation_paths(temp_root, ARKTS_ANY_PATTERNS)

        self.assertEqual(
            [
                "entry/src/main/ets/Eof.ets",
                "entry/src/main/ets/Intersection.ets",
                "entry/src/main/ets/TemplateExpression.ets",
                "entry/src/main/ets/Union.ets",
                "entry/src/main/ets/UrlThenCode.ets",
            ],
            violations,
        )

    def test_22_empty_event_policy_ignores_strings_and_template_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            fixtures = {
                "entry/src/main/ets/DoubleText.ets": 'const text = "onClick(() => {})";\n',
                "entry/src/main/ets/SingleText.ets": "const text = 'onSubmit(() => {})';\n",
                "entry/src/main/ets/TemplateText.ets": "const text = `onChange(() => {})`;\n",
                "entry/src/main/ets/CommentOnly.ets": "// Button().onTouch(() => {})\n",
                "entry/src/main/ets/RealHandler.ets": "Button().onClick(() => {})\n",
            }
            for relative_path, source in fixtures.items():
                path = temp_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            violations = _arkts_violation_paths(temp_root, (EMPTY_EVENT_PATTERN,))

        self.assertEqual(["entry/src/main/ets/RealHandler.ets"], violations)

    def test_23_contract_checker_rejects_implemented_or_verified_directory_targets(self) -> None:
        facts = _load_json(FACTS_PATH)
        manifest = copy.deepcopy(_load_json(MANIFEST_PATH))
        manifest["mappings"][22]["status"] = "implemented"
        manifest["mappings"][22]["target"] = "."
        manifest["mappings"][23]["status"] = "verified"
        manifest["mappings"][23]["target"] = "tools"

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            facts_path = temp_root / "facts.json"
            manifest_path = temp_root / "manifest.json"
            facts_path.write_text(json.dumps(facts), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--root",
                    str(ROOT),
                    "--facts",
                    str(facts_path),
                    "--manifest",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("implemented target must be a file: .", result.stdout)
        self.assertIn("verified target must be a file: tools", result.stdout)

    def test_24_each_implemented_action_target_exposes_its_stable_id(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        dynamic_action_ids = {
            "form.action.cart.1": ("`form.action.cart.${item.stableKey}`", "item.stableKey"),
        }
        missing: list[str] = []
        for mapping in manifest["mappings"]:
            if mapping["kind"] != "action" or mapping["status"] not in {"implemented", "verified"}:
                continue
            target = ROOT / mapping["target"]
            source = target.read_text(encoding="utf-8")
            if (
                mapping["stableId"] not in source
                and not all(marker in source for marker in dynamic_action_ids.get(mapping["stableId"], ("<missing>",)))
            ):
                missing.append(mapping["id"])
        self.assertEqual([], missing, f"action stable IDs missing from targets: {missing}")

    def test_25_classic_for_policy_ignores_text_and_detects_authored_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            fixtures = {
                "entry/src/main/ets/StringOnly.ets": "const text: string = 'for (let index = 0)';\n",
                "entry/src/main/ets/CommentOnly.ets": "// for (let index = 0; index < 1; index += 1) {}\n",
                "entry/src/main/ets/ArrayMethod.ets": "const result: number[] = values.map((value: number) => value + 1);\n",
                "entry/src/main/ets/ClassicLoop.ets": "for (let index: number = 0; index < values.length; index += 1) {}\n",
            }
            for relative_path, source in fixtures.items():
                path = temp_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            violations = _arkts_violation_paths(temp_root, (CLASSIC_FOR_LOOP_PATTERN,))

        self.assertEqual(["entry/src/main/ets/ClassicLoop.ets"], violations)

    def test_26_instruction_uses_official_source_review_workflow(self) -> None:
        instruction_path = ROOT.parent / "INSTRUCTION.md"
        if not instruction_path.is_file():
            self.skipTest("work-only build copy intentionally has no delivery-root INSTRUCTION.md")
        instruction = instruction_path.read_text(encoding="utf-8")

        for marker in ("Scorer", "意图用例", "work/migration-report.md"):
            with self.subTest(marker=marker):
                self.assertIn(marker, instruction)
        for execution_marker in (
            "评分平台执行构建",
            "唯一必需",
        ):
            with self.subTest(execution_marker=execution_marker):
                self.assertNotIn(execution_marker, instruction)
        for context_only_marker in ("docs/", "introduction.md", "Git 上传", "最终 ZIP"):
            with self.subTest(context_only_marker=context_only_marker):
                self.assertNotIn(context_only_marker, instruction)

    def test_26c_instruction_describes_platform_reproduction_and_harmony_skill_handoff(self) -> None:
        instruction_path = ROOT.parent / "INSTRUCTION.md"
        if not instruction_path.is_file():
            self.skipTest("work-only build copy intentionally has no delivery-root INSTRUCTION.md")
        instruction = instruction_path.read_text(encoding="utf-8")
        for marker in (
            "环境准备",
            "执行方式",
            "执行完成判定",
            "sh tools/verify.sh --static",
            "sh tools/verify.sh --build",
            "HarmonyOS 评分 Skill",
            "BUILD SUCCESSFUL",
            "status=passed",
            "entry/build/default/outputs/default/entry-default-unsigned.hap",
            "不得临时联网安装",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, instruction)

    def test_26a_instruction_describes_reproducible_harmony_build_contract(self) -> None:
        instruction_path = ROOT.parent / "INSTRUCTION.md"
        if not instruction_path.is_file():
            self.skipTest("work-only build copy intentionally has no delivery-root INSTRUCTION.md")
        instruction = instruction_path.read_text(encoding="utf-8")
        for marker in (
            "API 20",
            "Hvigor",
            "Node.js/JDK",
            "sh tools/verify.sh --build",
            "BUILD SUCCESSFUL",
            "status=passed",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, instruction)

    def test_26b_migration_report_indexes_scorable_source_evidence(self) -> None:
        report_path = ROOT / "migration-report.md"
        self.assertTrue(report_path.is_file(), "missing scorer-facing work/migration-report.md")
        report = report_path.read_text(encoding="utf-8")
        for marker in (
            "entry/src/main/ets/pages/Index.ets",
            "entry/src/main/ets/state/AppStore.ets",
            "entry/src/main/ets/components/",
            "entry/src/main/resources/",
            "migration-manifest.json",
            "功能对照",
            "界面一致性",
            "代码规范",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, report)

    def test_27_official_style_policy_masks_text_and_detects_authored_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            fixtures = {
                "entry/src/main/ets/StringOnly.ets": "const text: string = 'Array<number> export * ESObject';\n",
                "entry/src/main/ets/CommentOnly.ets": "// Number.NaN === value\n",
                "entry/src/main/ets/GenericArray.ets": "const values: Array<number> = [];\n",
                "entry/src/main/ets/StarExport.ets": "export * from './Data';\n",
                "entry/src/main/ets/NaNCompare.ets": "const invalid: boolean = value === Number.NaN;\n",
                "entry/src/main/ets/FinallyReturn.ets": "try { run(); } finally { return; }\n",
                "entry/src/main/ets/Interop.ets": "const value: ESObject = getValue();\n",
                "entry/src/main/ets/GlobalThis.ets": "const root: object = globalThis;\n",
                "entry/src/main/ets/Debugger.ets": "debugger;\n",
                "entry/src/main/ets/ConstAssertion.ets": "const mode = 'dark' as const;\n",
                "entry/src/main/ets/Exponent.ets": "const squared: number = value ** 2;\n",
                "entry/src/main/ets/ForIn.ets": "for (const key in values) { consume(key); }\n",
                "entry/src/main/ets/IndexSignature.ets": "interface Bag { [key: string]: string }\n",
            }
            for relative_path, source in fixtures.items():
                path = temp_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            violations = _arkts_violation_paths(temp_root, OFFICIAL_ARKTS_STYLE_PATTERNS)

        self.assertEqual(
            [
                "entry/src/main/ets/ConstAssertion.ets",
                "entry/src/main/ets/Debugger.ets",
                "entry/src/main/ets/Exponent.ets",
                "entry/src/main/ets/FinallyReturn.ets",
                "entry/src/main/ets/ForIn.ets",
                "entry/src/main/ets/GenericArray.ets",
                "entry/src/main/ets/GlobalThis.ets",
                "entry/src/main/ets/IndexSignature.ets",
                "entry/src/main/ets/Interop.ets",
                "entry/src/main/ets/NaNCompare.ets",
                "entry/src/main/ets/StarExport.ets",
            ],
            violations,
        )

    def test_28_production_arkts_has_no_unhandled_empty_catch_blocks(self) -> None:
        violations: list[str] = []
        for path in sorted((ROOT / "entry/src/main/ets").rglob("*.ets")):
            source = path.read_text(encoding="utf-8")
            if re.search(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", source):
                violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main(verbosity=2)
