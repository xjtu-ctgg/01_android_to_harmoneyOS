#!/usr/bin/env python3
"""Executable contract for Search state, four displays, and UI actions."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS = ROOT / "entry" / "src" / "main" / "ets"
STORE = ETS / "state" / "AppStore.ets"
SCREEN = ETS / "screens" / "SearchScreen.ets"
SEARCH_DATA = ETS / "data" / "SearchData.ets"
STRINGS = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "string.json"
FACTS = ROOT / "source-facts" / "android-facts.json"
JOURNEYS = ROOT / "journeys" / "core.yaml"
ANDROID_SEARCH = (
    ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "java" /
    "com" / "example" / "jetsnack" / "ui" / "home" / "search" / "Search.kt"
)
ANDROID_SEARCH_REPO = (
    ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "java" /
    "com" / "example" / "jetsnack" / "model" / "Search.kt"
)


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing authored file: {path.relative_to(ROOT).as_posix()}")
    source = path.read_text(encoding="utf-8")
    if len(re.sub(r"\s+", "", source)) < 96:
        raise AssertionError(f"placeholder file: {path.relative_to(ROOT).as_posix()}")
    return source


def event_handler_after(source: str, anchor: str, event_name: str) -> str:
    anchor_index = source.find(anchor)
    if anchor_index < 0:
        raise AssertionError(f"missing click anchor: {anchor}")
    handler_start = source.find(f".{event_name}(", anchor_index)
    if handler_start < 0:
        raise AssertionError(f"missing {event_name} handler after: {anchor}")
    handler_end = source.find("})", handler_start)
    if handler_end < 0:
        raise AssertionError(f"unterminated {event_name} handler after: {anchor}")
    return source[handler_start:handler_end + 2]


class SearchContractTests(unittest.TestCase):
    def test_01_android_search_boundaries_are_frozen_correctly(self) -> None:
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        boundary = facts["search"]["queryExpectations"]
        self.assertEqual([21, 22, 23, 24, 25], boundary["Apple"])
        self.assertEqual([20], boundary["Cheese"])
        self.assertEqual([7, 22, 23, 24, 25], boundary[" "])
        self.assertEqual([], boundary[" Apple "])
        source = read(SEARCH_DATA)
        self.assertIn("query.toLowerCase()", source)
        self.assertNotIn(".trim()", source)

    def test_02_store_declares_four_display_states_in_android_order(self) -> None:
        source = read(STORE)
        enum_match = re.search(r"export\s+enum\s+SearchDisplay\s*\{(?P<body>[\s\S]*?)\}", source)
        self.assertIsNotNone(enum_match, "missing SearchDisplay enum")
        body = enum_match.group("body") if enum_match is not None else ""
        names = re.findall(r"\b(CATEGORIES|SUGGESTIONS|RESULTS|NO_RESULTS)\b", body)
        self.assertEqual(["CATEGORIES", "SUGGESTIONS", "RESULTS", "NO_RESULTS"], names)

        method_start = source.find("getSearchDisplay(): SearchDisplay")
        method_end = source.find("setSearchFocused(", method_start)
        self.assertGreaterEqual(method_start, 0)
        self.assertGreater(method_end, method_start)
        method = source[method_start:method_end]
        ordered = (
            "!this.searchFocused && this.searchQuery.length === 0",
            "this.searchFocused && this.searchQuery.length === 0",
            "this.searchResults.length === 0",
            "SearchDisplay.RESULTS",
        )
        cursor = 0
        for token in ordered:
            index = method.find(token, cursor)
            self.assertGreaterEqual(index, cursor, f"missing/out-of-order search display branch: {token}")
            cursor = index + len(token)

    def test_03_store_matches_source_cancellable_200ms_search_and_clear_semantics(self) -> None:
        android_repo = read(ANDROID_SEARCH_REPO)
        self.assertIn("suspend fun search(query: String)", android_repo)
        self.assertIn("delay(200L)", android_repo)

        source = read(STORE)
        required_fields = (
            r"searchQuery\s*:\s*string\s*=\s*['\"]['\"]",
            r"searchFocused\s*:\s*boolean\s*=\s*false",
            r"searching\s*:\s*boolean\s*=\s*false",
            r"searchResults\s*:\s*Snack\s*\[\s*\]",
            r"searchGeneration\s*:\s*number\s*=\s*0",
        )
        for pattern in required_fields:
            self.assertRegex(source, pattern)
        start = source.find("setSearchQuery(query: string): void")
        end = source.find("refreshSearchResults(): void", start)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        search = source[start:end]
        self.assertIn("this.searchQuery = query", search)
        self.assertIn("this.searching = true", search)
        self.assertIn("this.searchGeneration += 1", search)
        self.assertIn("const generation: number = this.searchGeneration", search)
        self.assertIn("setTimeout", search)
        self.assertIn("generation !== this.searchGeneration", search)
        self.assertIn("this.searchResults = searchSnacks(query)", search)
        self.assertIn("this.searching = false", search)
        self.assertIn("SEARCH_DELAY_MS", source)

        clear_start = source.find("clearSearchQuery(): void")
        clear_end = source.find("selectSearchSuggestion(", clear_start)
        self.assertGreater(clear_end, clear_start)
        clear = source[clear_start:clear_end]
        self.assertIn("this.setSearchQuery('')", clear)
        self.assertNotIn("this.searchFocused = false", clear)

    def test_04_search_screen_exposes_all_four_displays_and_stable_actions(self) -> None:
        source = read(SCREEN)
        self.assertRegex(source, r"@Component\s+export\s+struct\s+SearchScreen")
        self.assertIn("@ObjectLink appStore: AppStore", source)
        for display in ("CATEGORIES", "SUGGESTIONS", "RESULTS", "NO_RESULTS"):
            self.assertIn(f"SearchDisplay.{display}", source)
        for stable_id in (
            "screen.search",
            "search.input",
            "search.clear",
            "action.search.category.select",
            "action.search.result.add",
        ):
            self.assertIn(stable_id, source)
        self.assertIn("this.appStore.openDetail(stableId, 'search')", source)
        self.assertNotIn("=> {}", source)
        self.assertNotRegex(source, r"\bany\b")

    def test_05_search_fixed_text_is_resource_backed(self) -> None:
        resources = {
            item["name"]: item["value"]
            for item in json.loads(STRINGS.read_text(encoding="utf-8"))["string"]
        }
        expected = {
            "search_jetsnack": "Search Jetsnack",
            "search_no_matches": "No matches for “%s”",
            "search_no_matches_retry": "Try broadening your search",
            "search_count": "%d items",
            "label_add": "Add to cart",
            "label_search": "Perform search",
            "label_back": "Back",
        }
        for name, value in expected.items():
            self.assertEqual(value, resources.get(name))
        source = read(SCREEN)
        for name in expected:
            self.assertIn(f"app.string.{name}", source)

    def test_06_result_add_stops_touch_propagation_and_row_still_opens_detail(self) -> None:
        source = read(SCREEN)
        row_start = source.find("struct SearchResultRow")
        row_end = source.find("@Component\nexport struct SearchScreen", row_start)
        self.assertGreaterEqual(row_start, 0)
        self.assertGreater(row_end, row_start)
        row = source[row_start:row_end]

        add_anchor = ".id(this.addActionId())"
        touch_handler = event_handler_after(row, add_anchor, "onTouch")
        self.assertRegex(
            touch_handler,
            r"\A\.onTouch\(\(event:\s*TouchEvent\)\s*=>\s*\{",
            "search result add must receive an explicit TouchEvent",
        )
        self.assertIn("event.stopPropagation();", touch_handler)

        click_handler = event_handler_after(row, add_anchor, "onClick")
        self.assertRegex(click_handler, r"\A\.onClick\(\(\)\s*=>\s*\{")
        self.assertIn("this.onAdd();", click_handler)
        touch_index = row.find(".onTouch(", row.find(add_anchor))
        monopoly_index = row.find(".monopolizeEvents(true)", row.find(add_anchor))
        click_index = row.find(".onClick(", row.find(add_anchor))
        self.assertGreater(monopoly_index, touch_index, "search result add must exclusively own the interaction")
        self.assertLess(monopoly_index, click_index, "event ownership must be configured before adding")
        self.assertIn(".width(36)", row)
        self.assertIn(".height(36)", row)
        self.assertIn(".responseRegion({ x: -6, y: -6, width: 48, height: 48 })", row)

        row_handler = event_handler_after(
            row,
            ".id(`search.result.${this.snack.stableId}`)",
            "onClick",
        )
        self.assertIn("this.onOpen(this.snack.stableId);", row_handler)
        self.assertIn("this.appStore.openDetail(stableId, 'search');", source)

    def test_07_search_hint_category_cards_and_result_header_match_source_geometry(self) -> None:
        source = read(SCREEN)
        self.assertIn("private searchHint()", source)
        hint_start = source.find("private searchHint()")
        hint_end = source.find("private searchBar()", hint_start)
        self.assertGreater(hint_end, hint_start)
        hint = source[hint_start:hint_end]
        self.assertIn("app.media.ic_search", hint)
        self.assertIn("app.string.search_jetsnack", hint)
        self.assertIn(".width(8)", hint)

        search_bar_start = source.find("private searchBar()")
        search_bar_end = source.find("private searchCategories()", search_bar_start)
        search_bar = source[search_bar_start:search_bar_end]
        self.assertIn("this.appStore.searchQuery.length === 0", search_bar)
        self.assertIn("this.searchHint()", search_bar)
        self.assertRegex(search_bar, r"TextInput\s*\(\s*\{[\s\S]*?placeholder:\s*''")
        clear_start = search_bar.find(".id('search.clear')")
        clear_end = search_bar.find("TextInput({", clear_start)
        clear = search_bar[clear_start:clear_end]
        self.assertIn(".width(48)", clear)
        self.assertIn(".height(40)", clear)
        self.assertIn(".responseRegion({ x: 0, y: -4, width: 48, height: 48 })", clear)

        category_start = source.find("struct SearchCategoryCard")
        category_end = source.find("struct SearchResultRow", category_start)
        category = source[category_start:category_end]
        self.assertIn(".aspectRatio(1.45)", category)
        self.assertIn(".width('55%')", category)
        self.assertIn(".height('100%')", category)
        self.assertIn(".aspectRatio(1)", category)
        self.assertIn(".constraintSize({ minWidth: 134, minHeight: 134 })", category)
        self.assertIn(".borderRadius('50%')", category)
        self.assertIn(".shadow(ShadowStyle.OUTER_DEFAULT_SM)", category)
        self.assertNotIn(".shadow({ radius: 3", category)
        self.assertNotIn(".maxLines(2)", category)
        self.assertNotIn(".width(92)", category)
        self.assertNotIn(".height(112)", category)

        results_start = source.find("private searchResults()")
        results_end = source.find("private noResults()", results_start)
        results = source[results_start:results_end]
        count_start = results.find("app.string.search_count")
        count_end = results.find("ForEach(", count_start)
        count_header = results[count_start:count_end]
        self.assertIn("top: 4, bottom: 4", count_header)
        self.assertNotIn(".height(56)", count_header)

    def test_08_category_grid_and_rows_adapt_to_viewport_and_large_font(self) -> None:
        source = read(SCREEN)
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "columns": 2,
                "outerHorizontalPaddingDp": 16,
                "itemPaddingDp": 8,
                "visibleCardWidthFormula": "viewportWidth / 2 - 32",
                "cardAspectRatio": 1.45,
                "minimumImageSizeDp": 134,
                "cardElevationDp": 3,
                "targetShadowStyle": "OUTER_DEFAULT_SM",
            },
            facts["search"]["categoryGeometry"],
        )
        self.assertIn("@State searchViewportWidth: number = 360", source)
        self.assertIn("private categoryGridHeight(itemCount: number): number", source)
        # Android applies 16dp to VerticalGrid and another 8dp to each
        # SearchCategory. The visible card is therefore viewport/2 - 32dp.
        self.assertIn("const cardWidth: number = Math.max(0, this.searchViewportWidth / 2 - 32)", source)
        self.assertIn("return rowCount * (cardWidth / 1.45 + 16)", source)
        self.assertIn(".height(this.categoryGridHeight(group.items.length))", source)
        self.assertIn(".padding({ left: 16, right: 16 })", source)
        self.assertIn(".onAreaChange", source)
        self.assertIn("this.searchViewportWidth = width", source)
        self.assertNotIn(".height(group.items.length / 2 * 128)", source)
        self.assertIn(
            '"category.shadow:OUTER_DEFAULT_SM"',
            JOURNEYS.read_text(encoding="utf-8"),
        )

        categories_start = source.find("private searchCategories()")
        suggestions_start = source.find("private searchSuggestions()")
        categories = source[categories_start:suggestions_start]
        suggestions_end = source.find("private searchResults()", suggestions_start)
        suggestions = source[suggestions_start:suggestions_end]
        self.assertIn(".constraintSize({ minHeight: 56 })", categories)
        self.assertIn(".constraintSize({ minHeight: 56 })", suggestions)
        self.assertIn(".constraintSize({ minHeight: 48 })", suggestions)

    def test_09_no_results_illustration_preserves_ratio_without_narrow_screen_clipping(self) -> None:
        source = read(SCREEN)
        start = source.find("private noResults()")
        end = source.find("build()", start)
        no_results = source[start:end]
        self.assertIn("Image($r('app.media.empty_state_search'))", no_results)
        self.assertIn(".width('100%')", no_results)
        self.assertIn(".constraintSize({ maxWidth: 341 })", no_results)
        self.assertIn(".aspectRatio(341 / 179)", no_results)
        self.assertNotIn(".width(341)", no_results)
        self.assertNotIn(".height(179)", no_results)

    def test_10_search_group_rows_preserve_source_min_height_under_large_font(self) -> None:
        source = read(SCREEN)
        categories_start = source.find("private searchCategories()")
        suggestions_start = source.find("private searchSuggestions()", categories_start)
        results_start = source.find("private searchResults()", suggestions_start)
        categories = source[categories_start:suggestions_start]
        suggestions = source[suggestions_start:results_start]

        for section in (categories, suggestions):
            self.assertIn(".constraintSize({ minHeight: 56 })", section)
            self.assertIn(".padding({ left: 24, right: 24, top: 4, bottom: 4 })", section)
            self.assertIn(".alignItems(VerticalAlign.Center)", section)
            self.assertRegex(section, r"Blank\(\)\s*\.height\(4\)")
            self.assertNotIn("top: 16, bottom: 16", section)

        self.assertIn(".constraintSize({ minHeight: 48 })", suggestions)
        self.assertIn(".padding({ left: 24, right: 24 })", suggestions)
        self.assertNotIn("top: 12, bottom: 12", suggestions)

    def test_11_search_result_text_wraps_like_source_instead_of_forced_single_line(self) -> None:
        source = read(SCREEN)
        row_start = source.find("struct SearchResultRow")
        row_end = source.find("@Component\nexport struct SearchScreen", row_start)
        self.assertGreater(row_start, 0)
        self.assertGreater(row_end, row_start)
        row = source[row_start:row_end]

        name_start = row.find("Text(this.snack.name)")
        tagline_start = row.find("Text(this.snack.tagline)", name_start)
        price_start = row.find("Text(formatPrice", tagline_start)
        self.assertGreater(tagline_start, name_start)
        self.assertGreater(price_start, tagline_start)
        self.assertNotIn(".maxLines(1)", row[name_start:tagline_start])
        self.assertNotIn(".maxLines(1)", row[tagline_start:price_start])

    def test_12_plain_remember_search_state_resets_after_disposal_and_configuration(self) -> None:
        android = read(ANDROID_SEARCH)
        self.assertIn("state: SearchState = rememberSearchState()", android)
        self.assertIn("return remember {", android)
        self.assertNotIn("rememberSaveable", android)

        store = read(STORE)
        self.assertIn("resetSearchState(): void", store)
        reset_start = store.find("resetSearchState(): void")
        reset_end = store.find("setSearchFocused(", reset_start)
        reset = store[reset_start:reset_end]
        self.assertIn("this.searchQuery = ''", reset)
        self.assertIn("this.searchFocused = false", reset)
        self.assertIn("this.searching = false", reset)
        self.assertIn("this.searchResults = []", reset)
        self.assertIn("this.searchGeneration += 1", reset)

        select_start = store.find("selectTab(route: string): void")
        select_end = store.find("getSearchDisplay(): SearchDisplay", select_start)
        select = store[select_start:select_end]
        self.assertIn("this.currentRoute === ROUTE_SEARCH", select)
        self.assertIn("route !== ROUTE_SEARCH", select)
        self.assertIn("this.resetSearchState()", select)

        detail_start = store.find("openDetail(stableId: number, origin: string): void")
        detail_end = store.find("incrementDetailQuantity(): void", detail_start)
        detail = store[detail_start:detail_end]
        self.assertIn("this.currentRoute === ROUTE_SEARCH", detail)
        self.assertIn("this.resetSearchState()", detail)

        ability = read(ETS / "entryability" / "EntryAbility.ets")
        index = read(ETS / "pages" / "Index.ets")
        self.assertIn("AppStorage.setOrCreate<number>('configurationRequestId'", ability)
        self.assertIn("@StorageProp('configurationRequestId')", index)
        self.assertIn("@Watch('onConfigurationRequestChanged')", index)
        config_start = index.find("onConfigurationRequestChanged(): void")
        config_end = index.find("aboutToAppear(): void", config_start)
        config = index[config_start:config_end]
        self.assertIn("this.appStore.resetSearchState()", config)
        self.assertIn("this.appStore.currentRoute === ROUTE_SEARCH", config)
        self.assertIn("this.appStore.refreshSearchResults()", config)

    def test_13_search_category_foreach_key_uses_business_identity_not_index(self) -> None:
        source = read(SCREEN)
        categories_start = source.find("private searchCategories()")
        suggestions_start = source.find("private searchSuggestions()", categories_start)
        categories = source[categories_start:suggestions_start]

        self.assertIn(
            "}, (name: string): string => `${group.name}.${name}`)",
            categories,
        )
        self.assertNotIn(
            "}, (name: string): string => `${groupIndex}.${name}`)",
            categories,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
