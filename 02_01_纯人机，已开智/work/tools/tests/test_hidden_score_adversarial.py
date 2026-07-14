#!/usr/bin/env python3
"""Adversarial static checks that approximate common hidden scoring gates."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS_ROOT = ROOT / "entry/src/main/ets"
RESOURCE_ROOT = ROOT / "entry/src/main/resources"


def authored_ets() -> dict[Path, str]:
    return {path: path.read_text(encoding="utf-8") for path in sorted(ETS_ROOT.rglob("*.ets"))}


def element_values(theme: str, kind: str) -> dict[str, object]:
    path = RESOURCE_ROOT / theme / "element" / f"{kind}.json"
    return {item["name"]: item["value"] for item in json.loads(path.read_text(encoding="utf-8"))[kind]}


class HiddenScoreAdversarialTests(unittest.TestCase):
    def test_01_all_resource_references_resolve(self) -> None:
        source = "\n".join(authored_ets().values())
        references = set(re.findall(r"\$r\('app\.(color|string|media|plural)\.([^']+)'\)", source))
        available = {
            "color": set(element_values("base", "color")),
            "string": set(element_values("base", "string")),
            "media": {path.stem for path in (RESOURCE_ROOT / "base/media").iterdir()},
            "plural": set(element_values("base", "plural")),
        }
        missing = sorted((kind, name) for kind, name in references if name not in available[kind])
        self.assertEqual([], missing)

    def test_02_dark_and_light_color_contracts_are_identical(self) -> None:
        base = element_values("base", "color")
        dark = element_values("dark", "color")
        self.assertEqual(set(base), set(dark))
        self.assertEqual(len(base), len(dark))

    def test_03_element_resources_have_no_duplicate_names(self) -> None:
        for path in sorted(RESOURCE_ROOT.glob("*/element/*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            kind = next(iter(payload))
            names = [item["name"] for item in payload[kind]]
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(len(names), len(set(names)))

    def test_04_literal_automation_ids_are_unique(self) -> None:
        source = "\n".join(authored_ets().values())
        identifiers = re.findall(r"\.id\('([^']+)'\)", source)
        duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
        self.assertEqual([], duplicates)

    def test_05_every_screen_and_overlay_has_a_stable_root_id(self) -> None:
        expected = {
            "FeedScreen.ets": "screen.feed",
            "SearchScreen.ets": "screen.search",
            "CartScreen.ets": "screen.cart",
            "ProfileScreen.ets": "screen.profile",
            "DetailScreen.ets": "screen.detail",
            "FilterOverlay.ets": "overlay.filter",
        }
        for filename, stable_id in expected.items():
            source = (ETS_ROOT / "screens" / filename).read_text(encoding="utf-8")
            with self.subTest(screen=filename):
                self.assertIn(f".id('{stable_id}')", source)

    def test_06_no_webview_or_cross_platform_wrapper_bypasses_native_arkui(self) -> None:
        source = "\n".join(authored_ets().values())
        for forbidden in ("web({", "@ohos.web.webview", "flutter", "react-native", "uni-app"):
            self.assertNotIn(forbidden, source.lower())

    def test_07_no_machine_paths_or_embedded_credentials(self) -> None:
        text_paths = [
            *authored_ets().keys(),
            ROOT / "build-profile.json5",
            ROOT / "oh-package.json5",
            ROOT / "migration-manifest.json",
            ROOT / "journeys/core.yaml",
        ]
        source = "\n".join(path.read_text(encoding="utf-8") for path in text_paths)
        self.assertNotIn("/" + "Users/", source)
        self.assertNotRegex(source, r"/" + r"home/(?:runner|ubuntu|developer)/")
        self.assertNotRegex(source, r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE " + r"KEY")
        self.assertNotRegex(source, r"AK" + r"IA[0-9A-Z]{16}")

    def test_08_manifest_targets_exist_and_are_confined_to_the_repository(self) -> None:
        manifest = json.loads((ROOT / "migration-manifest.json").read_text(encoding="utf-8"))
        missing: list[str] = []
        escaped: list[str] = []
        for mapping in manifest["mappings"]:
            target = mapping["target"]
            if target.startswith("entry/"):
                resolved = (ROOT / target).resolve()
                if ROOT.resolve() not in resolved.parents:
                    escaped.append(target)
                if not resolved.exists():
                    missing.append(target)
        self.assertEqual([], escaped)
        self.assertEqual([], missing)

    def test_09_deep_link_has_cold_and_warm_start_handlers(self) -> None:
        ability = (ETS_ROOT / "entryability/EntryAbility.ets").read_text(encoding="utf-8")
        self.assertIn("onCreate(want: Want", ability)
        self.assertIn("onNewWant(want: Want", ability)
        self.assertGreaterEqual(ability.count("this.publishRoute(want)"), 2)
        self.assertIn("navigationRequestId", ability)

    def test_10_recreated_filter_overlay_resets_local_controls_but_keeps_global_chips(self) -> None:
        store = (ETS_ROOT / "state/AppStore.ets").read_text(encoding="utf-8")
        start = store.find("showFilters(): void")
        end = store.find("hideFilters(): void", start)
        body = store[start:end]
        for statement in (
            "this.filterSort = DEFAULT_FILTER_SORT",
            "this.filterMaxCalories = 0",
            "this.filterVisible = true",
        ):
            self.assertIn(statement, body)
        self.assertNotIn("this.filterSelections = []", body)
        index = (ETS_ROOT / "pages/Index.ets").read_text(encoding="utf-8")
        config_start = index.find("onConfigurationRequestChanged(): void")
        config_end = index.find("aboutToAppear(): void", config_start)
        config_body = index[config_start:config_end]
        self.assertIn("this.appStore.hideFilters()", config_body)

    def test_11_system_bar_foreground_tracks_light_and_dark_configuration(self) -> None:
        ability = (ETS_ROOT / "entryability/EntryAbility.ets").read_text(encoding="utf-8")
        self.assertIn("ConfigurationConstant.ColorMode.COLOR_MODE_DARK", ability)
        self.assertIn("onConfigurationUpdate(newConfig: Configuration)", ability)
        self.assertIn("this.applySystemBars(newConfig.colorMode)", ability)
        self.assertRegex(ability, r"statusBarContentColor:\s*contentColor")
        self.assertRegex(ability, r"navigationBarContentColor:\s*contentColor")

    def test_12_root_safe_area_uses_window_avoid_areas_not_fixed_insets(self) -> None:
        ability = (ETS_ROOT / "entryability/EntryAbility.ets").read_text(encoding="utf-8")
        index = (ETS_ROOT / "pages/Index.ets").read_text(encoding="utf-8")
        self.assertIn("getWindowAvoidArea(window.AvoidAreaType.TYPE_SYSTEM)", ability)
        self.assertIn("getWindowAvoidArea(window.AvoidAreaType.TYPE_CUTOUT)", ability)
        self.assertIn("getWindowAvoidArea(window.AvoidAreaType.TYPE_NAVIGATION_INDICATOR)", ability)
        self.assertIn("this.mainWindow.on('avoidAreaChange'", ability)
        self.assertIn("this.mainWindow.off('avoidAreaChange'", ability)
        self.assertIn("AppStorage.setOrCreate<number>('topInsetPx'", ability)
        self.assertIn("AppStorage.setOrCreate<number>('bottomInsetPx'", ability)
        self.assertIn("AppStorage.setOrCreate<number>('leftInsetPx'", ability)
        self.assertIn("AppStorage.setOrCreate<number>('rightInsetPx'", ability)
        self.assertIn("@StorageProp('topInsetPx')", index)
        self.assertIn("@StorageProp('bottomInsetPx')", index)
        self.assertIn("@StorageProp('leftInsetPx')", index)
        self.assertIn("@StorageProp('rightInsetPx')", index)
        self.assertIn("this.getUIContext().px2vp(this.topInsetPx)", index)
        self.assertIn("this.getUIContext().px2vp(this.bottomInsetPx)", index)
        self.assertIn("this.getUIContext().px2vp(this.leftInsetPx)", index)
        self.assertIn("this.getUIContext().px2vp(this.rightInsetPx)", index)
        self.assertIn("left: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.leftInset()", index)
        self.assertIn("right: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.rightInset()", index)
        self.assertIn("top: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.topInset()", index)
        detail_call = index[index.index("DetailScreen({"):index.index("})", index.index("DetailScreen({"))]
        self.assertIn("topInset: this.topInset()", detail_call)
        self.assertIn("leftInset: this.leftInset()", detail_call)
        self.assertIn("rightInset: this.rightInset()", detail_call)
        detail = (ETS_ROOT / "screens/DetailScreen.ets").read_text(encoding="utf-8")
        self.assertIn("@Prop topInset: number", detail)
        self.assertIn("@Prop leftInset: number", detail)
        self.assertIn("@Prop rightInset: number", detail)
        self.assertIn("return Math.max(0, this.detailViewportWidth - this.leftInset - this.rightInset)", detail)
        self.assertIn("const expandedX: number = this.leftInset + (this.detailSafeWidth() - imageSize) / 2", detail)
        self.assertIn("this.leftInset + 24", detail)
        self.assertIn("this.rightInset + 24", detail)
        self.assertIn("return this.topInset + 56 - 44 * this.collapseFraction()", detail)
        self.assertIn("return this.topInset + Math.max(56, 351 - this.detailScrollOffset)", detail)
        self.assertIn(".margin({ left: this.leftInset + 16, top: this.topInset + 10 })", detail)
        self.assertIn(".height(this.topInset + 495)", detail)
        self.assertNotIn(".padding({ top: 24, bottom: 24 })", index)

    def test_12b_tab_content_avoids_side_cutout_without_shrinking_bottom_nav_surface(self) -> None:
        index = (ETS_ROOT / "pages/Index.ets").read_text(encoding="utf-8")
        stack_start = index.index("      Stack() {")
        bottom_nav_start = index.index("      if (this.appStore.currentRoute !== ROUTE_DETAIL)")
        content_stack = index[stack_start:bottom_nav_start]
        self.assertIn(".padding({", content_stack)
        self.assertIn("top: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.topInset()", content_stack)
        self.assertIn("bottom: this.appStore.currentRoute === ROUTE_DETAIL ? this.bottomInset() : 0", content_stack)
        self.assertIn("left: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.leftInset()", content_stack)
        self.assertIn("right: this.appStore.currentRoute === ROUTE_DETAIL ? 0 : this.rightInset()", content_stack)
        root = index[index.index("    .id('screen.root')"):]
        self.assertNotIn(".padding({", root)

    def test_13_dynamic_feed_collection_action_ids_are_unique(self) -> None:
        collection = (ETS_ROOT / "components/SnackCollection.ets").read_text(encoding="utf-8")
        method_start = collection.index("private collectionActionId(): string")
        method_end = collection.index("@Builder", method_start)
        method = collection[method_start:method_end]
        self.assertIn("this.collection.stableId === 1", method)
        self.assertNotIn("this.collection.stableId <= 2", method)
        self.assertIn("`action.feed.collection.${this.collection.stableId}`", method)

    def test_14_expanded_feed_ids_remain_unique_when_products_repeat(self) -> None:
        data = (ETS_ROOT / "data/SnackData.ets").read_text(encoding="utf-8")
        start = data.index("export const SNACK_COLLECTIONS")
        end = data.index("export const RELATED_COLLECTIONS", start)
        collections = re.findall(
            r"stableId:\s*(\d+).*?snackStableIds:\s*\[([^\]]+)\]",
            data[start:end],
            re.DOTALL,
        )
        identifiers: list[str] = []
        for collection_text, snacks_text in collections:
            collection_id = int(collection_text)
            identifiers.append(f"feed.collection.{collection_id}")
            identifiers.append(
                "action.feed.collection" if collection_id == 1
                else f"action.feed.collection.{collection_id}"
            )
            for snack_id in (int(value) for value in re.findall(r"\d+", snacks_text)):
                suffix = str(snack_id) if collection_id <= 2 else f"{collection_id}.{snack_id}"
                identifiers.extend((f"snack.card.{suffix}", f"snack.image.{suffix}"))
        self.assertGreater(len(collections), 1)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_15_user_visible_static_copy_is_resource_backed(self) -> None:
        source = "\n".join(authored_ets().values())
        collection = (ETS_ROOT / "components/SnackCollection.ets").read_text(encoding="utf-8")
        self.assertNotIn('showCartSnackbar("There was an error', source)
        self.assertNotIn(".accessibilityText(`View ${", source)
        self.assertIn("$r('app.string.view_collection', this.collection.name)", collection)
        self.assertIn("view_collection", element_values("base", "string"))

    def test_16_authored_arkts_follows_official_style_hard_edges(self) -> None:
        violations: list[str] = []
        for path, source in authored_ets().items():
            relative = path.relative_to(ROOT)
            for line_number, line in enumerate(source.splitlines(), 1):
                if "\t" in line:
                    violations.append(f"{relative}:{line_number}:tab")
                if len(line) > 120:
                    violations.append(f"{relative}:{line_number}:line-length-{len(line)}")
            if re.search(r"\bvar\s+", source):
                violations.append(f"{relative}:var")
            if re.search(r"(?<![=!])==(?!=)", source):
                violations.append(f"{relative}:non-strict-equality")
            if re.search(r"(?<![=!])!=(?!=)", source):
                violations.append(f"{relative}:non-strict-inequality")
            if re.search(r"(?:==|!=|===|!==)\s*Number\.NaN|Number\.NaN\s*(?:==|!=|===|!==)", source):
                violations.append(f"{relative}:nan-comparison")
            for line_number, line in enumerate(source.splitlines(), 1):
                if re.search(r'"(?:[^"\\]|\\.)*"', line):
                    violations.append(f"{relative}:{line_number}:double-quoted-string")
        self.assertEqual([], violations)

    def test_16b_authored_arkts_avoids_official_safety_rule_antipatterns(self) -> None:
        violations: list[str] = []
        for path, source in authored_ets().items():
            relative = path.relative_to(ROOT)
            if "Array<" in source:
                violations.append(f"{relative}:generic-array-type")
            if re.search(r"\bESObject\b", source):
                violations.append(f"{relative}:esobject")
            if re.search(r"\b(?:if|while|for)\s*\([^\n]*(?<![=!<>])=(?!=)[^\n]*\)", source):
                violations.append(f"{relative}:assignment-in-control-condition")
            if re.search(
                r"\b(?:let|const)\s+[A-Za-z_$][\w$]*(?:\s*:[^=;,]+)?\s*=.*?,\s*"
                r"[A-Za-z_$][\w$]*(?:\s*:[^=;,]+)?\s*=",
                source,
            ):
                violations.append(f"{relative}:multiple-variable-declaration")
            if re.search(r"\bfinally\s*\{[^}]*\b(?:return|break|continue|throw)\b", source, re.DOTALL):
                violations.append(f"{relative}:abrupt-finally")
        self.assertEqual([], violations)

    def test_16c_authored_arkts_avoids_remaining_official_style_antipatterns(self) -> None:
        violations: list[str] = []
        negative_boolean = re.compile(r"\b(?:isNot|isNo|hasNo|canNot|shouldNot)[A-Z_][A-Za-z0-9_]*\b")
        shorthand_float = re.compile(r"(?<![A-Za-z0-9_.])(?:\.[0-9]+|[0-9]+\.)(?![A-Za-z0-9_.])")
        for path, source in authored_ets().items():
            relative = path.relative_to(ROOT)
            for line_number, line in enumerate(source.splitlines(), 1):
                if negative_boolean.search(line):
                    violations.append(f"{relative}:{line_number}:negative-boolean-name")
                if shorthand_float.search(line):
                    violations.append(f"{relative}:{line_number}:shorthand-floating-point")
        self.assertEqual([], violations)

    def test_17_configuration_rebuild_resets_detail_plain_remember_state(self) -> None:
        store = (ETS_ROOT / "state/AppStore.ets").read_text(encoding="utf-8")
        reset_start = store.find("resetDetailTransientState(): void")
        reset_end = store.find("\n  }", reset_start)
        self.assertGreaterEqual(reset_start, 0)
        reset_body = store[reset_start:reset_end]
        self.assertIn("this.detailQuantity = 1", reset_body)
        self.assertIn("this.detailExpanded = false", reset_body)

        index = (ETS_ROOT / "pages/Index.ets").read_text(encoding="utf-8")
        config_start = index.find("onConfigurationRequestChanged(): void")
        config_end = index.find("aboutToAppear(): void", config_start)
        config_body = index[config_start:config_end]
        self.assertIn("this.appStore.resetDetailTransientState()", config_body)

    def test_18_custom_android_controls_keep_equivalent_accessibility_roles(self) -> None:
        filter_bar = (ETS_ROOT / "components/FilterBar.ets").read_text(encoding="utf-8")
        quantity = (ETS_ROOT / "components/QuantitySelector.ets").read_text(encoding="utf-8")
        destination = (ETS_ROOT / "components/DestinationBar.ets").read_text(encoding="utf-8")
        bottom_nav = (ETS_ROOT / "components/BottomNav.ets").read_text(encoding="utf-8")
        overlay = (ETS_ROOT / "screens/FilterOverlay.ets").read_text(encoding="utf-8")
        cart = (ETS_ROOT / "screens/CartScreen.ets").read_text(encoding="utf-8")
        search = (ETS_ROOT / "screens/SearchScreen.ets").read_text(encoding="utf-8")
        detail = (ETS_ROOT / "screens/DetailScreen.ets").read_text(encoding="utf-8")
        form = (ETS_ROOT / "form/RecentOrdersForm.ets").read_text(encoding="utf-8")

        self.assertGreaterEqual(
            filter_bar.count(".accessibilityRole(AccessibilityRoleType.CHECKBOX)"), 1
        )
        self.assertGreaterEqual(
            overlay.count(".accessibilityRole(AccessibilityRoleType.CHECKBOX)"), 1
        )
        sort_block = overlay[overlay.index("private sortChoice("):overlay.index("private filterChip(")]
        self.assertIn(".accessibilitySelected(this.appStore.filterSort === choice.value)", sort_block)
        self.assertNotIn(".accessibilityChecked(", sort_block)
        for source, minimum in (
            (filter_bar, 1),
            (quantity, 2),
            (destination, 1),
            (bottom_nav, 1),
            (overlay, 2),
            (cart, 2),
            (search, 2),
            (detail, 2),
            (form, 2),
        ):
            with self.subTest(source=source[:40]):
                self.assertGreaterEqual(
                    source.count(".accessibilityRole(AccessibilityRoleType.BUTTON)"), minimum
                )

        journeys = (ROOT / "journeys/core.yaml").read_text(encoding="utf-8")
        for journey_id in (
            "interface.accessibility.navigation-and-toggle-roles",
            "interface.accessibility.cart-button-roles",
            "interface.accessibility.filter-button-roles",
        ):
            self.assertIn(f"- id: {journey_id}", journeys)

    def test_19_filter_overlay_hides_the_shared_feed_trigger_below_the_scrim(self) -> None:
        android_filter = (
            ROOT
            / "source-facts/android-source/app/src/main/java/com/example/jetsnack/ui/components/Filters.kt"
        ).read_text(encoding="utf-8")
        harmony_filter = (ETS_ROOT / "components/FilterBar.ets").read_text(encoding="utf-8")
        journeys = (ROOT / "journeys/core.yaml").read_text(encoding="utf-8")

        self.assertIn("AnimatedVisibility(visible = !filterScreenVisible)", android_filter)
        self.assertIn("if (!this.appStore.filterVisible)", harmony_filter)
        self.assertIn("- id: visual.filter.underlay-trigger-hidden", journeys)
        self.assertIn('"feed.filters.open:absent"', journeys)

    def test_20_source_clickable_leaf_nodes_expose_button_roles(self) -> None:
        card = (ETS_ROOT / "components/SnackCard.ets").read_text(encoding="utf-8")
        collection = (ETS_ROOT / "components/SnackCollection.ets").read_text(encoding="utf-8")
        search = (ETS_ROOT / "screens/SearchScreen.ets").read_text(encoding="utf-8")
        detail = (ETS_ROOT / "screens/DetailScreen.ets").read_text(encoding="utf-8")
        self.assertIn(".accessibilityRole(AccessibilityRoleType.BUTTON)\n    .onClick", card)
        self.assertGreaterEqual(collection.count(".accessibilityRole(AccessibilityRoleType.BUTTON)"), 2)
        self.assertIn(".id(`search.suggestion.${suggestion}`)", search)
        suggestion = search[search.index(".id(`search.suggestion.${suggestion}`)"):]
        self.assertIn(".accessibilityRole(AccessibilityRoleType.BUTTON)", suggestion[:300])
        expansion = detail[detail.index(".id('detail.seeMore')"):detail.index("Text($r('app.string.ingredients'))")]
        self.assertIn(".accessibilityRole(AccessibilityRoleType.BUTTON)", expansion)

    def test_21_private_like_journeys_cover_input_clamps_and_invalid_routes(self) -> None:
        journeys = (ROOT / "journeys/core.yaml").read_text(encoding="utf-8")
        for journey_id in (
            "edge.search.padded-query-is-not-trimmed",
            "edge.filter.slider-clamps-below-zero",
            "edge.filter.slider-clamps-above-maximum",
            "edge.navigation.invalid-warm-uri-preserves-current-task",
            "edge.navigation.invalid-cold-uri-opens-feed",
        ):
            self.assertIn(f"- id: {journey_id}", journeys)

    def test_22_search_category_cards_expose_button_semantics(self) -> None:
        source = (ETS_ROOT / "screens/SearchScreen.ets").read_text(encoding="utf-8")
        start = source.index("struct SearchCategoryCard")
        end = source.index("struct SearchResultRow", start)
        card = source[start:end]
        self.assertIn(".accessibilityText(this.category.name)", card)
        self.assertIn(".accessibilityRole(AccessibilityRoleType.BUTTON)", card)
        self.assertIn(".onClick(() =>", card)
        journeys = (ROOT / "journeys/core.yaml").read_text(encoding="utf-8")
        self.assertIn("- id: interface.accessibility.search-category-card", journeys)


if __name__ == "__main__":
    unittest.main(verbosity=2)
