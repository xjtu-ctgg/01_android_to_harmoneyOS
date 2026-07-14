#!/usr/bin/env python3
"""Task 6 root-shell contract for real Search/Profile tab rendering."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS = ROOT / "entry" / "src" / "main" / "ets"
INDEX = ETS / "pages" / "Index.ets"
STORE = ETS / "state" / "AppStore.ets"
SEARCH = ETS / "screens" / "SearchScreen.ets"
PROFILE = ETS / "screens" / "ProfileScreen.ets"
JOURNEYS = ROOT / "journeys" / "core.yaml"


def read_authored(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing authored file: {path.relative_to(ROOT).as_posix()}")
    source = path.read_text(encoding="utf-8")
    code = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*|\s+", "", source)
    if len(code) < 96:
        raise AssertionError(f"placeholder file: {path.relative_to(ROOT).as_posix()}")
    return source


class RootTabContractTests(unittest.TestCase):
    def test_01_search_and_profile_screens_are_authored(self) -> None:
        search = read_authored(SEARCH)
        profile = read_authored(PROFILE)
        self.assertIn("export struct SearchScreen", search)
        self.assertIn(".id('screen.search')", search)
        self.assertIn("export struct ProfileScreen", profile)
        self.assertIn(".id('screen.profile')", profile)

    def test_02_index_conditionally_renders_real_tab_screens(self) -> None:
        source = read_authored(INDEX)
        required_imports = (
            "ROUTE_SEARCH",
            "ROUTE_PROFILE",
            "FeedScreen",
            "SearchScreen",
            "ProfileScreen",
        )
        for symbol in required_imports:
            with self.subTest(symbol=symbol):
                self.assertRegex(source, rf"\b{symbol}\b")

        self.assertRegex(source, r"this\.appStore\.currentRoute\s*===\s*ROUTE_SEARCH")
        self.assertRegex(source, r"this\.appStore\.currentRoute\s*===\s*ROUTE_PROFILE")
        self.assertIn("SearchScreen({ appStore: this.appStore })", source)
        self.assertIn("ProfileScreen()", source)
        self.assertIn("FeedScreen({ appStore: this.appStore })", source)
        self.assertIn("BottomNav({", source)

    def test_03_tab_switch_dismisses_feed_overlay_and_keeps_route_guard(self) -> None:
        source = read_authored(STORE)
        start = source.find("selectTab(route: string): void")
        end = source.find("openDetail(", start)
        self.assertGreaterEqual(start, 0, "missing typed selectTab")
        self.assertGreater(end, start, "selectTab must precede openDetail")
        body = source[start:end]
        self.assertIn("isTabRoute(route)", body)
        self.assertIn("this.currentRoute = route", body)
        self.assertIn("this.filterVisible = false", body)

        same_route_guard = body.find("this.currentRoute === route")
        route_assignment = body.find("this.currentRoute = route")
        self.assertGreaterEqual(same_route_guard, 0, "reselecting the active tab must be a no-op")
        self.assertLess(same_route_guard, route_assignment)

    def test_04_invalid_snack_ids_cannot_enter_detail(self) -> None:
        source = read_authored(STORE)
        start = source.find("openDetail(stableId: number, origin: string): void")
        end = source.find("incrementDetailQuantity", start)
        self.assertGreaterEqual(start, 0)
        self.assertGreater(end, start)
        body = source[start:end]

        lookup = body.find("getSnackById(stableId)")
        invalid_guard = body.find("=== undefined", lookup)
        selected_assignment = body.find("this.selectedSnackId = stableId")
        self.assertGreaterEqual(lookup, 0, "detail routing must validate the data-set ID")
        self.assertGreater(invalid_guard, lookup)
        self.assertGreater(selected_assignment, invalid_guard)
        self.assertIn("return;", body[invalid_guard:selected_assignment])

    def test_05_tab_pages_stay_mounted_while_visibility_selects_the_active_route(self) -> None:
        source = read_authored(INDEX)
        start = source.find("private currentTab()")
        end = source.find("private snackbar()", start)
        self.assertGreaterEqual(start, 0, "missing tab content builder")
        self.assertGreater(end, start, "tab content builder must precede snackbar")
        body = source[start:end]

        expected = (
            ("FeedScreen({ appStore: this.appStore })", "ROUTE_FEED"),
            ("SearchScreen({ appStore: this.appStore })", "ROUTE_SEARCH"),
            ("CartScreen({ appStore: this.appStore })", "ROUTE_CART"),
            ("ProfileScreen()", "ROUTE_PROFILE"),
        )
        for component, route in expected:
            with self.subTest(component=component):
                component_start = body.find(component)
                self.assertGreaterEqual(component_start, 0)
                visibility = body.find(".visibility(", component_start)
                self.assertGreater(visibility, component_start)
                next_component = min(
                    (position for candidate, _ in expected
                     if (position := body.find(candidate, component_start + len(component))) >= 0),
                    default=len(body),
                )
                self.assertLess(visibility, next_component)
                self.assertIn(route, body[visibility:next_component])
                self.assertIn("Visibility.Hidden", body[visibility:next_component])

        self.assertIn("if (this.appStore.currentRoute === ROUTE_DETAIL)", body)

    def test_06_journeys_cover_vertical_and_horizontal_tab_scroll_restoration(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        expected = {
            "edge.navigation.feed-scroll-restored-after-detail": (
                "scroll_to:feed.collection.4",
                "scroll_right:feed.collection.4:372vp",
                "tap:snack.card.4.17",
                "system_back",
                "verticalScroll:restored",
                "horizontalScroll:restored",
            ),
            "edge.navigation.cart-scroll-restored-after-tab-switch": (
                "scroll_to:cart.summary",
                "tap:nav.feed",
                "tap:nav.cart",
                "scrollPosition:restored",
            ),
        }
        for journey_id, markers in expected.items():
            with self.subTest(journey_id=journey_id):
                start = source.find(f"  - id: {journey_id}")
                end = source.find("\n  - id: ", start + 1)
                self.assertGreaterEqual(start, 0)
                journey = source[start:] if end < 0 else source[start:end]
                for marker in markers:
                    self.assertIn(marker, journey)


if __name__ == "__main__":
    unittest.main(verbosity=2)
