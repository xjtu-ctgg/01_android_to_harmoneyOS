#!/usr/bin/env python3
"""Task 7 contracts for cart, detail, filter, and root routing."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS = ROOT / "entry" / "src" / "main" / "ets"
STORE = ETS / "state" / "AppStore.ets"
INDEX = ETS / "pages" / "Index.ets"
SCREENS = {
    "cart": ETS / "screens" / "CartScreen.ets",
    "detail": ETS / "screens" / "DetailScreen.ets",
    "filter": ETS / "screens" / "FilterOverlay.ets",
}
QUANTITY_SELECTOR = ETS / "components" / "QuantitySelector.ets"
FILTER_BAR = ETS / "components" / "FilterBar.ets"
STRINGS = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "string.json"
PLURALS = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "plural.json"
BASE_COLORS = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "color.json"
DARK_COLORS = ROOT / "entry" / "src" / "main" / "resources" / "dark" / "element" / "color.json"
ANDROID_SOURCE = (
    ROOT / "source-facts" / "android-source" / "app" / "src" / "main" /
    "java" / "com" / "example" / "jetsnack" / "ui"
)
ANDROID_SNACKBAR_MANAGER = ANDROID_SOURCE.parent / "model" / "SnackbarManager.kt"
ANDROID_FILTER = ANDROID_SOURCE.parent / "model" / "Filter.kt"
ANDROID_SNACKBAR = ANDROID_SOURCE / "components" / "Snackbar.kt"
ANDROID_SCAFFOLD = ANDROID_SOURCE / "components" / "Scaffold.kt"
ANDROID_SHAPES = ANDROID_SOURCE / "theme" / "Shape.kt"


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


class CartDetailFilterContractTests(unittest.TestCase):
    def test_01_cart_state_preserves_amounts_failure_interval_and_remove_boundary(self) -> None:
        source = read(STORE)
        for declaration in (
            r"cartLines\s*:\s*OrderLine\s*\[\s*\]\s*=\s*createInitialCartLines\(\)",
            r"cartRequestCount\s*:\s*number\s*=\s*0",
            r"cartSnackbarMessage\s*:\s*Resource\s*=\s*\$r\('app\.string\.cart_increase_error'\)",
            r"cartSnackbarVisible\s*:\s*boolean\s*=\s*false",
            r"hiddenCartIds\s*:\s*number\s*\[\s*\]\s*=\s*\[\s*\]",
        ):
            self.assertRegex(source, declaration)
        for method in (
            "cartSubtotalCents(): number",
            "cartTotalCents(): number",
            "increaseCartItem(stableId: number): void",
            "decreaseCartItem(stableId: number): void",
            "removeCartItem(stableId: number): void",
            "hideCartItem(stableId: number): void",
        ):
            self.assertIn(method, source)
        self.assertIn("% QUANTITY_FAILURE_INTERVAL === 0", source)
        self.assertIn("SHIPPING_CENTS", source)
        self.assertIn("line.quantity === 1", source)
        self.assertIn("this.removeCartItem(stableId)", source)

        hide_start = source.find("hideCartItem(stableId: number): void")
        hide_end = source.find("acknowledgeCheckout", hide_start)
        self.assertGreater(hide_end, hide_start)
        hide_body = source[hide_start:hide_end]
        self.assertIn("hiddenCartIds", hide_body)
        self.assertNotIn("removeCartItem", hide_body)

    def test_02_detail_state_resets_per_open_and_quantity_has_zero_floor(self) -> None:
        source = read(STORE)
        self.assertRegex(source, r"detailQuantity\s*:\s*number\s*=\s*1")
        self.assertRegex(source, r"detailExpanded\s*:\s*boolean\s*=\s*false")
        open_start = source.find("openDetail(stableId: number, origin: string): void")
        open_end = source.find("goBack(): void", open_start)
        self.assertGreater(open_end, open_start)
        open_body = source[open_start:open_end]
        self.assertIn("this.detailQuantity = 1", open_body)
        self.assertIn("this.detailExpanded = false", open_body)
        self.assertIn("incrementDetailQuantity(): void", source)
        self.assertIn("decrementDetailQuantity(): void", source)
        self.assertRegex(source, r"if\s*\(\s*this\.detailQuantity\s*>\s*0\s*\)")
        self.assertIn("toggleDetailExpanded(): void", source)

    def test_03_filter_state_is_visual_only_and_reset_is_explicit_no_op(self) -> None:
        android_filter = read(ANDROID_FILTER)
        self.assertIn("val enabled = mutableStateOf(enabled)", android_filter)
        self.assertIn("val priceFilters = listOf(", android_filter)
        self.assertIn("val categoryFilters = listOf(", android_filter)
        self.assertIn("val lifeStyleFilters = listOf(", android_filter)

        source = read(STORE)
        for field in (
            r"filterSort\s*:\s*string",
            r"filterMaxCalories\s*:\s*number\s*=\s*0",
            r"filterSelections\s*:\s*string\s*\[\s*\]",
        ):
            self.assertRegex(source, field)
        for method in (
            "selectFilterSort(sort: string): void",
            "setFilterMaxCalories(value: number): void",
            "toggleFilterSelection(name: string): void",
            "acknowledgeFilterReset(): void",
        ):
            self.assertIn(method, source)
        reset_start = source.find("acknowledgeFilterReset(): void")
        reset_end = source.find("}", reset_start)
        reset_body = source[reset_start:reset_end]
        self.assertNotIn("filterSort =", reset_body)
        self.assertNotIn("filterSelections =", reset_body)

        show_start = source.find("showFilters(): void")
        show_end = source.find("hideFilters(): void", show_start)
        show_body = source[show_start:show_end]
        self.assertIn("this.filterSort = DEFAULT_FILTER_SORT", show_body)
        self.assertIn("this.filterMaxCalories = 0", show_body)
        self.assertNotIn("this.filterSelections = []", show_body)

        overlay = read(SCREENS["filter"])
        self.assertIn("@State filterChipHeight: number = 28", overlay)
        self.assertIn("private filterChipTouchHeight(): number", overlay)
        self.assertIn("return Math.max(48, this.filterChipHeight)", overlay)
        self.assertIn("private filterChipTouchTop(): number", overlay)
        self.assertIn("(this.filterChipHeight - this.filterChipTouchHeight()) / 2", overlay)
        self.assertIn("height: this.filterChipTouchHeight()", overlay)
        self.assertIn("this.filterChipHeight = height", overlay)
        self.assertIn("@State filterSortHeights: number[] = [38, 38, 38]", overlay)
        self.assertIn("private filterSortHeight(index: number): number", overlay)
        self.assertIn("this.filterSortHeights[index] ?? 38", overlay)
        self.assertIn("private filterSortTouchHeight(index: number): number", overlay)
        self.assertIn("Math.max(48, this.filterSortHeight(index))", overlay)
        self.assertIn("private filterSortTouchTop(index: number): number", overlay)
        self.assertIn("this.filterSortTouchHeight(index)", overlay)
        self.assertIn("height: this.filterSortTouchHeight(index)", overlay)
        self.assertIn("this.filterSortHeights = heights", overlay)

    def test_04_three_screens_expose_stable_ids_and_no_op_actions(self) -> None:
        sources = {name: read(path) for name, path in SCREENS.items()}
        expected = {
            "cart": (
                "screen.cart",
                "action.cart.checkout",
                "action.cart.remove",
                "action.cart.swipeDismiss.persistence",
            ),
            "detail": ("screen.detail", "detail.back", "action.detail.addToCart", "action.detail.related.select"),
            "filter": ("overlay.filter", "filter.scrim", "filter.close", "action.filter.reset", "filter.slider.maxCalories"),
        }
        for screen, ids in expected.items():
            for stable_id in ids:
                with self.subTest(screen=screen, stable_id=stable_id):
                    self.assertIn(stable_id, sources[screen])
            self.assertNotIn("=> {}", sources[screen])
            self.assertNotRegex(sources[screen], r"\bany\b")

    def test_05_root_renders_cart_and_detail_and_overlays_filter(self) -> None:
        source = read(INDEX)
        for symbol in (
            "ROUTE_CART",
            "ROUTE_DETAIL",
            "CartScreen",
            "DetailScreen",
            "FilterOverlay",
        ):
            self.assertRegex(source, rf"\b{symbol}\b")
        self.assertRegex(source, r"this\.appStore\.currentRoute\s*===\s*ROUTE_CART")
        self.assertRegex(source, r"this\.appStore\.currentRoute\s*===\s*ROUTE_DETAIL")
        self.assertIn("CartScreen({ appStore: this.appStore })", source)
        detail_call = source[source.index("DetailScreen({"):source.index("})", source.index("DetailScreen({"))]
        self.assertIn("appStore: this.appStore", detail_call)
        self.assertIn("topInset: this.topInset()", detail_call)
        self.assertIn("leftInset: this.leftInset()", detail_call)
        self.assertIn("rightInset: this.rightInset()", detail_call)
        self.assertIn("if (this.appStore.filterVisible)", source)
        self.assertIn("FilterOverlay({ appStore: this.appStore })", source)

        content_builder = source.find("private currentTab()")
        detail_condition = source.find("currentRoute === ROUTE_DETAIL", content_builder)
        detail_branch = source[detail_condition:detail_condition + 500]
        self.assertIn("DetailScreen", detail_branch)

    def test_06_required_visible_strings_are_resource_backed(self) -> None:
        resources = {
            item["name"]: item["value"]
            for item in json.loads(STRINGS.read_text(encoding="utf-8"))["string"]
        }
        expected = {
            "detail_header": "Details",
            "detail_placeholder": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut tempus, sem vitae convallis imperdiet, lectus nunc pharetra diam, ac rhoncus quam eros eu risus. Nulla pulvinar condimentum erat, pulvinar tempus turpis blandit ut. Etiam sed ipsum sed lacus eleifend hendrerit eu quis quam. Etiam ligula eros, finibus vestibulum tortor ac, ultrices accumsan dolor. Vivamus vel nisl a libero lobortis posuere. Aenean facilisis nibh vel ultrices bibendum. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Suspendisse ac est vitae lacus commodo efficitur at ut massa. Etiam vestibulum sit amet sapien sed varius. Aliquam non ipsum imperdiet, pulvinar enim nec, mollis risus. Fusce id tincidunt nisl.",
            "ingredients": "Ingredients",
            "ingredients_list": "Vanilla, Almond Flour, Eggs, Butter, Cream, Sugar",
            "quantity": "Qty",
            "add_to_cart": "ADD TO CART",
            "cart_summary_header": "Summary",
            "cart_subtotal_label": "Subtotal",
            "cart_shipping_label": "Shipping & Handling",
            "cart_total_label": "Total",
            "cart_checkout": "Checkout",
            "filters_title": "Filters",
            "reset": "Reset",
            "sort": "Sort",
            "price": "Price",
            "category": "Category",
            "max_calories": "Max Calories",
            "lifestyle": "LifeStyle",
        }
        for name, value in expected.items():
            self.assertEqual(value, resources.get(name), name)

    def test_07_filter_uses_exact_source_choices_icons_and_450vp_panel(self) -> None:
        source = read(SCREENS["filter"])
        for value in (
            "Rating",
            "Alphabetical",
            "'$'",
            "'$$'",
            "'$$$'",
            "'$$$$'",
            "Chips & crackers",
            "Fruit snacks",
            "Desserts",
            "Nuts",
            "Organic",
            "Gluten-free",
            "Dairy-free",
            "Sweet",
            "Savory",
        ):
            self.assertIn(value, source)
        self.assertIn("value: 'Android\\'s favorite (default)'", source)
        for icon in ("ic_android", "ic_star", "ic_sort_by_alpha", "ic_check"):
            self.assertIn(icon, source)
        self.assertIn(".height('calc(100% - 32vp)')", source)
        self.assertIn(".constraintSize({ maxHeight: 450 })", source)
        self.assertNotIn(".height(450)", source)
        self.assertNotIn(".height('88%')", source)

    def test_08_cart_preserves_close_remove_and_half_width_rectangular_checkout(self) -> None:
        source = read(SCREENS["cart"])
        self.assertIn("app.media.ic_close", source)
        self.assertIn("removeCartItem(line.snackStableId)", source)
        self.assertRegex(source, r"action\.cart\.remove\.\$\{line\.snackStableId\}")
        checkout = source[source.find("private checkoutBar"):source.find("build()", source.find("private checkoutBar"))]
        self.assertIn("Blank()", checkout)
        self.assertIn(".layoutWeight(1)", checkout)
        self.assertNotIn(".borderRadius(24)", checkout)

    def test_09_detail_hero_is_responsive_and_collapses_with_source_geometry(self) -> None:
        source = read(SCREENS["detail"])
        self.assertIn("@State detailScrollOffset: number = 0", source)
        self.assertIn("@State detailViewportWidth: number = 360", source)
        self.assertIn("private detailScroller: Scroller = new Scroller()", source)
        for method in (
            "private collapseFraction(): number",
            "private detailImageSize(): number",
            "private detailImageOffsetY(): number",
            "private detailTitleOffsetY(): number",
            "private detailImageOffsetX(): number",
        ):
            self.assertIn(method, source)
        self.assertIn("expandedSize - (expandedSize - collapsedSize) * this.collapseFraction()", source)
        self.assertIn("56 - 44 * this.collapseFraction()", source)
        self.assertIn("Math.max(56, 351 - this.detailScrollOffset)", source)
        self.assertIn("Math.min(300, this.detailSafeWidth() - 48)", source)
        self.assertIn("this.detailViewportWidth - this.rightInset - 24 - imageSize", source)

        gradient_start = source.find("private detailGradient()")
        gradient_end = source.find("private detailImage", gradient_start)
        gradient = source[gradient_start:gradient_end]
        self.assertIn("angle: 135", gradient)
        self.assertIn("app.color.detail_gradient_start", gradient)
        self.assertIn("app.color.detail_gradient_end", gradient)
        self.assertIn(".blur(40)", gradient)

        image_start = source.find("private detailImage(snack: Snack)")
        image_end = source.find("private detailTitle", image_start)
        image = source[image_start:image_end]
        self.assertIn(".width(this.detailImageSize())", image)
        self.assertIn(".height(this.detailImageSize())", image)
        self.assertIn(".borderRadius(this.detailImageSize() / 2)", image)
        self.assertIn(".position({ x: this.detailImageOffsetX(), y: this.detailImageOffsetY() })", image)

        build_start = source.find("build()")
        build = source[build_start:]
        self.assertIn("Scroll(this.detailScroller)", build)
        self.assertIn(".onDidScroll", build)
        self.assertIn("this.detailScroller.currentOffset().yOffset", build)
        self.assertRegex(build, r"Blank\(\)\s*\.height\(this\.topInset \+ 495\)")
        self.assertIn("this.detailGradient()", build)
        self.assertIn("this.detailImage(this.selectedSnack())", build)
        self.assertIn("this.detailTitle(this.selectedSnack())", build)
        self.assertIn(".onAreaChange", build)
        self.assertIn("this.detailViewportWidth = width", build)

        body = source[
            source.find("private detailBody"):source.find("private relatedCollections")
        ]
        self.assertNotIn("Text(snack.name)", body)
        self.assertNotIn("Text(snack.tagline)", body)

        base_colors = json.loads(
            (ROOT / "entry/src/main/resources/base/element/color.json").read_text(encoding="utf-8")
        )["color"]
        dark_colors = json.loads(
            (ROOT / "entry/src/main/resources/dark/element/color.json").read_text(encoding="utf-8")
        )["color"]
        base = {item["name"]: item["value"] for item in base_colors}
        dark = {item["name"]: item["value"] for item in dark_colors}
        self.assertEqual("#7057F5", base.get("detail_gradient_start"))
        self.assertEqual("#86F7FA", base.get("detail_gradient_end"))
        self.assertEqual(base.get("detail_gradient_start"), dark.get("detail_gradient_start"))
        self.assertEqual(base.get("detail_gradient_end"), dark.get("detail_gradient_end"))

    def test_10_nested_cart_and_quantity_controls_stop_touch_propagation(self) -> None:
        cart = read(SCREENS["cart"])
        quantity = read(QUANTITY_SELECTOR)

        controls = (
            (
                "cart remove",
                cart,
                ".id(`action.cart.remove.${line.snackStableId}`)",
                "this.appStore.removeCartItem(line.snackStableId);",
            ),
            (
                "quantity decrease",
                quantity,
                ".id(this.decreaseId())",
                "this.onDecrease();",
            ),
            (
                "quantity increase",
                quantity,
                ".id(this.increaseId())",
                "this.onIncrease();",
            ),
        )
        for label, source, anchor, action in controls:
            with self.subTest(control=label):
                touch_handler = event_handler_after(source, anchor, "onTouch")
                self.assertRegex(
                    touch_handler,
                    r"\A\.onTouch\(\(event:\s*TouchEvent\)\s*=>\s*\{",
                    f"{label} must receive an explicit TouchEvent",
                )
                self.assertIn("event.stopPropagation();", touch_handler)

                click_handler = event_handler_after(source, anchor, "onClick")
                self.assertRegex(click_handler, r"\A\.onClick\(\(\)\s*=>\s*\{")
                self.assertIn(action, click_handler, f"{label} must still invoke its business callback")
                anchor_index = source.find(anchor)
                touch_index = source.find(".onTouch(", anchor_index)
                monopoly_index = source.find(".monopolizeEvents(true)", anchor_index)
                click_index = source.find(".onClick(", anchor_index)
                self.assertGreater(monopoly_index, touch_index, f"{label} must exclusively own the interaction")
                self.assertLess(monopoly_index, click_index, f"{label} must own events before its action")

        cart_row_handler = event_handler_after(
            cart,
            ".id(`action.cart.swipeDismiss.persistence.${line.snackStableId}`)",
            "onClick",
        )
        self.assertIn("this.appStore.openDetail(line.snackStableId, 'cart');", cart_row_handler)

        detail = read(SCREENS["detail"])
        for source, prefix, decrease, increase in (
            (
                cart,
                "stableIdPrefix: `cart.quantity.${line.snackStableId}`",
                "this.appStore.decreaseCartItem(line.snackStableId);",
                "this.appStore.increaseCartItem(line.snackStableId);",
            ),
            (
                detail,
                "stableIdPrefix: 'detail.quantity'",
                "this.appStore.decrementDetailQuantity();",
                "this.appStore.incrementDetailQuantity();",
            ),
        ):
            with self.subTest(quantity_prefix=prefix):
                self.assertIn(prefix, source)
                self.assertIn(decrease, source)
                self.assertIn(increase, source)

    def test_11_filter_panel_scrolls_as_one_source_aligned_surface(self) -> None:
        source = read(SCREENS["filter"])
        panel_start = source.find("private panel()")
        panel_end = source.find("build()", panel_start)
        self.assertGreater(panel_start, 0)
        self.assertGreater(panel_end, panel_start)
        panel = source[panel_start:panel_end]

        self.assertRegex(panel, r"private panel\(\)\s*\{\s*Scroll\(\)\s*\{\s*Column\(\)")
        self.assertEqual(1, panel.count("Scroll()"))
        self.assertNotIn("Divider()", panel)
        self.assertIn(".id('nav.filter')", panel)
        self.assertIn(".id('action.filter.applyToFeed')", panel)
        self.assertNotIn("maxWidth: 450", panel)
        self.assertIn("this.sectionTitle($r('app.string.sort'))", panel)

        section_title_start = source.find("private sectionTitle")
        section_title_end = source.find("private sortChoice", section_title_start)
        section_title = source[section_title_start:section_title_end]
        self.assertIn(".fontColor(BRAND_COLOR)", section_title)
        self.assertNotIn("topMargin", section_title)
        self.assertIn(".lineHeight(24)", section_title)
        self.assertIn(".margin({ bottom: 8 })", section_title)

        sort_start = source.find("private sortChoice")
        sort_end = source.find("private filterChip", sort_start)
        self.assertIn(".fontFamily(MONTSERRAT_SEMIBOLD)", source[sort_start:sort_end])

        self.assertIn(".fontFamily(MONTSERRAT_MEDIUM)", panel)
        self.assertIn(".fontColor(BRAND_COLOR)", panel)
        self.assertIn(".margin({ left: 10, top: 5 })", panel)
        self.assertIn(".enabled(this.appStore.filterSort !== DEFAULT_FILTER_SORT)", panel)

    def test_12_cart_keeps_destination_fixed_and_uses_source_typography(self) -> None:
        source = read(SCREENS["cart"])
        build_start = source.find("build()")
        self.assertGreater(build_start, 0)
        build = source[build_start:]
        self.assertEqual(1, build.count("DestinationBar()"))
        destination_index = build.find("DestinationBar()")
        scroll_bar_index = build.find(".scrollBar(BarState.Off)")
        self.assertGreater(destination_index, scroll_bar_index, "destination bar must sit above the scrolling content")
        self.assertIn(".align(Alignment.Top)", build[destination_index:])
        scroll_content = build[:destination_index]
        self.assertRegex(scroll_content, r"Blank\(\)\s*\.height\(56\)")

        cart_line_start = source.find("private cartLine")
        cart_line_end = source.find("private summaryRow", cart_line_start)
        cart_line = source[cart_line_start:cart_line_end]
        name_start = cart_line.find("Text(this.cartSnack(line).name)")
        name_end = cart_line.find("Text(this.cartSnack(line).tagline)", name_start)
        self.assertIn(".fontSize(16)", cart_line[name_start:name_end])
        price_start = cart_line.find("Text(formatPrice")
        price_end = cart_line.find("QuantitySelector", price_start)
        self.assertIn(".fontFamily(MONTSERRAT_SEMIBOLD)", cart_line[price_start:price_end])

        summary_row_start = source.find("private summaryRow")
        summary_row_end = source.find("private orderSummary", summary_row_start)
        summary_row = source[summary_row_start:summary_row_end]
        label_start = summary_row.find("Text(label)")
        value_start = summary_row.find("Text(value)")
        self.assertIn(".fontFamily(KARLA_REGULAR)", summary_row[label_start:value_start])
        self.assertIn(".fontSize(16)", summary_row[label_start:value_start])
        self.assertIn(".lineHeight(28)", summary_row[label_start:value_start])
        self.assertIn(
            ".fontFamily(emphasized ? MONTSERRAT_SEMIBOLD : KARLA_REGULAR)",
            summary_row[value_start:],
        )
        self.assertIn(".fontSize(16)", summary_row[value_start:])

        self.assertRegex(
            build,
            r"cart_order_header[\s\S]*?\.fontColor\(BRAND_COLOR\)",
        )
        summary_start = source.find("private orderSummary")
        summary_end = source.find("private snackbar", summary_start)
        self.assertRegex(
            source[summary_start:summary_end],
            r"cart_summary_header[\s\S]*?\.fontColor\(BRAND_COLOR\)",
        )

    def test_13_cart_swipe_has_progress_feedback_and_a_dismiss_threshold(self) -> None:
        source = read(SCREENS["cart"])
        for state in (
            "@State activeSwipeStableId: number = 0",
            "@State activeSwipeOffset: number = 0",
            "@State cartViewportWidth: number = 360",
            "const CART_SWIPE_DISMISS_THRESHOLD: number = 56",
            "const CART_SWIPE_DISMISS_VELOCITY: number = 125",
        ):
            self.assertIn(state, source)
        self.assertIn("private updateCartSwipe(stableId: number, offsetX: number): void", source)
        self.assertIn("Math.min(0, offsetX)", source)
        finish_start = source.find("private finishCartSwipe")
        finish_end = source.find("@Builder", finish_start)
        finish = source[finish_start:finish_end]
        self.assertIn("const dismissedByDistance: boolean", finish)
        self.assertIn("const dismissedByVelocity: boolean", finish)
        self.assertIn("this.appStore.hideCartItem(stableId)", finish)

        cart_line_start = source.find("private cartLine")
        cart_line_end = source.find("private summaryRow", cart_line_start)
        cart_line = source[cart_line_start:cart_line_end]
        self.assertIn("app.media.ic_delete_forever", cart_line)
        self.assertIn("app.string.remove_item", cart_line)
        self.assertIn(".backgroundColor(ERROR_COLOR)", cart_line)
        self.assertIn(".translate({ x: this.swipeOffsetFor(line.snackStableId) })", cart_line)
        self.assertRegex(cart_line, r"\.onActionUpdate\(\(event:\s*GestureEvent\)")
        self.assertIn("this.updateCartSwipe(line.snackStableId, event.offsetX)", cart_line)
        self.assertIn("this.finishCartSwipe(line.snackStableId, event.velocityX)", cart_line)

    def test_14_cart_swipe_background_matches_android_progress_ranges(self) -> None:
        source = read(SCREENS["cart"])
        self.assertIn("private swipeBackgroundSize(stableId: number): number", source)
        self.assertIn("private swipeBackgroundPadding(stableId: number): number", source)
        self.assertIn("private swipeBackgroundRadius(stableId: number): number", source)
        self.assertIn("Math.abs(this.swipeOffsetFor(stableId)) / this.cartViewportWidth", source)
        self.assertIn("Math.min(Math.abs(this.swipeOffsetFor(stableId)), this.cartViewportWidth)", source)
        self.assertNotIn("CART_SWIPE_PROGRESS_DISTANCE", source)
        self.assertIn("progress >= 0.125 && progress <= 0.475", source)
        self.assertIn("progress > 0.4 ? 0.5 : 1", source)
        self.assertIn(".width(this.swipeBackgroundSize(line.snackStableId))", source)
        self.assertIn(".height(this.swipeBackgroundSize(line.snackStableId))", source)
        self.assertIn(".padding(this.swipeBackgroundPadding(line.snackStableId))", source)
        self.assertIn(".borderRadius(this.swipeBackgroundRadius(line.snackStableId))", source)

    def test_15_cart_error_snackbar_uses_source_fifo_queue_and_shared_tab_host(self) -> None:
        android_manager = read(ANDROID_SNACKBAR_MANAGER)
        self.assertIn("currentMessages + Message(", android_manager)
        self.assertIn("snackbarManager.messages.collect", read(ANDROID_SCAFFOLD))

        source = read(STORE)
        index = read(ROOT / "entry" / "src" / "main" / "ets" / "pages" / "Index.ets")
        cart = read(SCREENS["cart"])
        self.assertIn("const CART_SNACKBAR_DURATION_MS: number = 4000", source)
        self.assertIn("private cartSnackbarGeneration: number = 0", source)
        self.assertIn("private cartSnackbarQueue: Resource[] = []", source)
        self.assertIn("private showCartSnackbar(message: Resource): void", source)
        self.assertIn("private showNextCartSnackbar(): void", source)
        self.assertIn("this.cartSnackbarQueue.slice()", source)
        self.assertIn("pending.push(message)", source)
        self.assertIn("this.cartSnackbarQueue = this.cartSnackbarQueue.slice(1)", source)
        self.assertIn("this.cartSnackbarGeneration += 1", source)
        self.assertIn("setTimeout(() =>", source)
        self.assertIn("generation !== this.cartSnackbarGeneration", source)
        self.assertIn("CART_SNACKBAR_DURATION_MS", source)
        self.assertIn("this.cartSnackbarVisible = true", source)
        self.assertIn("this.cartSnackbarVisible = false", source)
        self.assertIn("this.showNextCartSnackbar()", source)
        self.assertIn("this.showCartSnackbar($r('app.string.cart_increase_error'))", source)
        self.assertIn("this.showCartSnackbar($r('app.string.cart_decrease_error'))", source)
        self.assertNotIn('this.showCartSnackbar("There was an error', source)
        self.assertNotIn("clearCartSnackbar(): void", source)
        self.assertIn("private snackbar()", index)
        self.assertIn("this.snackbar()", index)
        self.assertIn("this.appStore.currentRoute !== ROUTE_DETAIL", index)
        self.assertNotIn("private snackbar()", cart)
        self.assertNotIn("this.snackbar()", cart)

        detail_start = source.find("openDetail(stableId: number, origin: string): void")
        detail_end = source.find("incrementDetailQuantity(): void", detail_start)
        detail_body = source[detail_start:detail_end]
        self.assertIn("this.cartSnackbarGeneration += 1", detail_body)
        self.assertIn("this.cartSnackbarVisible = false", detail_body)

        back_start = source.find("goBack(): void")
        back_end = source.find("showFilters(): void", back_start)
        back_body = source[back_start:back_end]
        self.assertIn("if (!this.cartSnackbarVisible)", back_body)
        self.assertIn("this.showNextCartSnackbar()", back_body)

    def test_15b_cart_snackbar_matches_android_material3_surface(self) -> None:
        android_snackbar = read(ANDROID_SNACKBAR)
        android_scaffold = read(ANDROID_SCAFFOLD)
        android_shapes = read(ANDROID_SHAPES)
        self.assertIn("backgroundColor: Color = JetsnackTheme.colors.uiBackground", android_snackbar)
        self.assertIn("contentColor: Color = JetsnackTheme.colors.textSecondary", android_snackbar)
        self.assertIn("shape: Shape = MaterialTheme.shapes.small", android_snackbar)
        self.assertIn("small = RoundedCornerShape(percent = 50)", android_shapes)
        self.assertIn("snackbarHost = {", android_scaffold)
        self.assertIn("snackbarHost(snackBarHostState)", android_scaffold)

        source = read(ROOT / "entry" / "src" / "main" / "ets" / "pages" / "Index.ets")
        start = source.find("private snackbar()")
        end = source.find("build()", start)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        snackbar = source[start:end]

        self.assertIn(".fontFamily(MONTSERRAT_MEDIUM)", snackbar)
        self.assertIn(".fontSize(14)", snackbar)
        self.assertIn(".lineHeight(20)", snackbar)
        self.assertIn(".letterSpacing(0.25)", snackbar)
        self.assertIn(".fontColor(SECONDARY_TEXT_COLOR)", snackbar)
        self.assertIn(".width('calc(100% - 24vp)')", snackbar)
        self.assertIn(".constraintSize({ minHeight: 68 })", snackbar)
        self.assertIn(".padding({ left: 16, right: 8, top: 6, bottom: 6 })", snackbar)
        self.assertIn(".margin({ left: 12, right: 12, top: 12, bottom: 12 })", snackbar)
        self.assertIn(".borderRadius('50%')", snackbar)
        self.assertIn(".backgroundColor(BACKGROUND_COLOR)", snackbar)
        self.assertIn(".shadow(ShadowStyle.OUTER_DEFAULT_MD)", snackbar)
        self.assertNotIn("ERROR_COLOR", snackbar)
        self.assertNotIn(".onClick(", snackbar)

        journeys = (ROOT / "journeys" / "core.yaml").read_text(encoding="utf-8")
        self.assertIn('"snackbar.shadow:OUTER_DEFAULT_MD"', journeys)

        build_start = source.find("build()", end)
        build = source[build_start:]
        self.assertIn("this.snackbar()", build)
        self.assertLess(build.find("this.currentTab()"), build.find("this.snackbar()"))

    def test_16_cart_order_header_uses_android_equivalent_plural_resource(self) -> None:
        source = read(SCREENS["cart"])
        strings = {
            item["name"] for item in json.loads(STRINGS.read_text(encoding="utf-8"))["string"]
        }
        self.assertNotIn("cart_order_header", strings)
        plural_items = json.loads(PLURALS.read_text(encoding="utf-8"))["plural"]
        plural = next(item for item in plural_items if item["name"] == "cart_order_header")
        values = {item["quantity"]: item["value"] for item in plural["value"]}
        self.assertEqual("Order (%d item)", values.get("one"))
        self.assertEqual("Order (%d items)", values.get("other"))
        self.assertIn(
            "$r('app.plural.cart_order_header', this.appStore.cartLines.length)",
            source,
        )

    def test_17_cart_checkout_and_scroll_clearance_match_source_button_geometry(self) -> None:
        source = read(SCREENS["cart"])
        checkout_start = source.find("private checkoutBar()")
        build_start = source.find("build()", checkout_start)
        self.assertGreater(checkout_start, 0)
        self.assertGreater(build_start, checkout_start)
        checkout = source[checkout_start:build_start]
        self.assertIn(".constraintSize({ minHeight: 40 })", checkout)
        self.assertNotIn(".height(40)", checkout)
        self.assertIn(".padding({ left: 24, right: 24, top: 8, bottom: 8 })", checkout)
        self.assertIn(".margin({ left: 12, right: 12, top: 8, bottom: 8 })", checkout)
        self.assertIn(".constraintSize({ minHeight: 56 })", checkout)
        self.assertNotIn(".height(48)", checkout)
        self.assertIn("@State checkoutButtonHeight: number = 40", source)
        self.assertIn("private checkoutTouchHeight(): number", source)
        self.assertIn("return Math.max(48, this.checkoutButtonHeight)", source)
        self.assertIn("height: this.checkoutTouchHeight()", checkout)
        self.assertIn("this.checkoutButtonHeight = height", checkout)

        build = source[build_start:]
        self.assertGreaterEqual(
            len(re.findall(r"Blank\(\)\s*\.height\(56\)", build)),
            2,
            "Android source keeps 56dp for both destination offset and final list clearance",
        )
        self.assertNotRegex(build, r"Blank\(\)\s*\.height\(88\)")

    def test_18_cart_title_and_summary_match_android_source_geometry(self) -> None:
        source = read(SCREENS["cart"])
        summary_start = source.find("private orderSummary()")
        summary_end = source.find("private checkoutBar()", summary_start)
        self.assertGreater(summary_start, 0)
        self.assertGreater(summary_end, summary_start)
        summary = source[summary_start:summary_end]

        self.assertIn(".id('cart.summary')", summary)
        self.assertRegex(
            summary,
            r"Text\(\$r\('app\.string\.cart_summary_header'\)\)"
            r"[\s\S]*?\.lineHeight\(24\)[\s\S]*?\.constraintSize\(\{ minHeight: 56 \}\)",
        )
        self.assertIn("this.summaryRow($r('app.string.cart_subtotal_label'),", summary)
        self.assertIn("this.summaryRow($r('app.string.cart_shipping_label'),", summary)
        self.assertIn("SHIPPING_CENTS), false, 8)", summary)
        self.assertIn("true, 8)", summary)
        self.assertRegex(summary, r"Blank\(\)\s*\.height\(8\)")
        self.assertEqual(2, summary.count("Divider()"))
        self.assertNotIn("padding({ left: 24, right: 24, top: 16, bottom: 8 })", summary)

        row_start = source.find("private summaryRow")
        row_end = source.find("private orderSummary", row_start)
        row = source[row_start:row_end]
        self.assertIn("verticalPadding: number = 0", row)
        self.assertIn(".constraintSize({ minHeight: 28 + verticalPadding * 2 })", row)
        self.assertNotIn(".height(28 + verticalPadding * 2)", row)
        self.assertIn("top: verticalPadding", row)
        self.assertIn("bottom: verticalPadding", row)
        self.assertIn(".textAlign(emphasized ? TextAlign.End : TextAlign.Start)", row)
        self.assertIn(".margin({ right: emphasized ? 16 : 0 })", row)

        build = source[source.find("build()") :]
        self.assertRegex(
            build,
            r"Text\(\$r\('app\.plural\.cart_order_header'[^\n]*\)\)"
            r"[\s\S]*?\.lineHeight\(24\)[\s\S]*?\.constraintSize\(\{ minHeight: 56 \}\)",
        )
        self.assertIn(".id('cart.order.header')", build)
        self.assertNotIn("top: 16, bottom: 16", build)

    def test_19_filter_panel_spacing_and_shapes_match_android_custom_theme(self) -> None:
        source = read(SCREENS["filter"])
        panel_start = source.find("private panel()")
        panel_end = source.find("build()", panel_start)
        panel = source[panel_start:panel_end]
        self.assertIn(".borderRadius(20)", panel)
        self.assertIn(".constraintSize({ minHeight: 48 })", panel)
        self.assertNotIn(".height(52)", panel)

        chip_start = source.find("private filterChip")
        chip_end = source.find("private chipGroup", chip_start)
        chip = source[chip_start:chip_end]
        self.assertIn(".padding({ left: 20, right: 20, top: 6, bottom: 6 })", chip)
        self.assertIn(".borderRadius('50%')", chip)
        self.assertIn(".margin({ right: 4, bottom: 8 })", chip)
        self.assertIn(".shadow(ShadowStyle.OUTER_DEFAULT_XS)", chip)
        self.assertIn("app.color.filter_elevated_background", chip)
        self.assertIn("app.color.filter_elevated_selected", chip)

        journeys = (ROOT / "journeys" / "core.yaml").read_text(encoding="utf-8")
        self.assertIn('"filter.chip.shadow:OUTER_DEFAULT_XS"', journeys)
        self.assertIn('"filter.chip.selectedBackground:#8EF8FA"', journeys)
        self.assertIn('"filter.chip.selectedBackground:#C0FDFD"', journeys)

        group_start = source.find("private chipGroup")
        group_end = source.find("private panel", group_start)
        group = source[group_start:group_end]
        self.assertIn(".padding({ left: 4, right: 4, top: 12, bottom: 16 })", group)

        sort_start = source.find("private sortChoice")
        sort_end = source.find("private filterChip", sort_start)
        sort_choice = source[sort_start:sort_end]
        self.assertIn(".constraintSize({ minHeight: 38 })", sort_choice)
        self.assertNotIn(".height(38)", sort_choice)
        self.assertIn(".padding({ top: 14 })", sort_choice)
        self.assertIn(".margin({ left: 10 })", sort_choice)
        self.assertRegex(panel, r"ForEach\(SORT_CHOICES[\s\S]*?Blank\(\)\s*\.height\(24\)")

        header_start = panel.find("Row()")
        header_end = panel.find("this.sectionTitle", header_start)
        header = panel[header_start:header_end]
        self.assertGreaterEqual(header.count(".constraintSize({ minWidth: 48, minHeight: 48 })"), 2)
        self.assertIn(".constraintSize({ minHeight: 48 })", header)

        calories_start = panel.find("Text($r('app.string.max_calories'))")
        calories_end = panel.find("Slider({", calories_start)
        calories = panel[calories_start:calories_end]
        self.assertIn(".fontSize(20)", calories)
        self.assertIn(".lineHeight(24)", calories)
        self.assertIn(".fontColor(BRAND_COLOR)", calories)
        self.assertNotIn(".fontSize(12)", calories)

        slider_start = panel.find("Slider({", calories_end)
        slider_end = panel.find("this.sectionTitle($r('app.string.lifestyle'))", slider_start)
        slider = panel[slider_start:slider_end]
        self.assertIn(".trackThickness(16)", slider)
        self.assertIn(".blockSize({ width: 4, height: 44 })", slider)
        self.assertIn(".showSteps(true)", slider)
        self.assertIn(".stepSize(4)", slider)

        journeys = (ROOT / "journeys" / "core.yaml").read_text(encoding="utf-8")
        self.assertIn('"slider.track:16vp"', journeys)
        self.assertIn('"slider.handle:4x44vp"', journeys)

    def test_20_cart_swipe_viewport_width_tracks_the_rendered_surface(self) -> None:
        source = read(SCREENS["cart"])
        build = source[source.find("build()") :]
        self.assertIn(".onAreaChange((_oldValue: Area, newValue: Area)", build)
        self.assertIn("this.cartViewportWidth = width", build)
        update_start = source.find("private updateCartSwipe")
        update_end = source.find("private resetCartSwipe", update_start)
        update = source[update_start:update_end]
        self.assertIn("Math.max(-this.cartViewportWidth, Math.min(0, offsetX))", update)
        self.assertIn("Math.min(this.cartViewportWidth, Math.max(0, offsetX))", update)

    def test_21_cart_swipe_end_to_start_follows_runtime_layout_direction(self) -> None:
        source = read(SCREENS["cart"])
        self.assertIn("import { i18n } from '@kit.LocalizationKit';", source)
        self.assertIn("private isRtlLayout(): boolean", source)
        self.assertIn("i18n.System.getSystemLanguage()", source)
        self.assertIn("i18n.isRTL(systemLanguage)", source)
        self.assertIn("PanGesture({ direction: PanDirection.Horizontal, distance: 8 })", source)
        finish_start = source.find("private finishCartSwipe")
        finish_end = source.find("@Builder", finish_start)
        finish = source[finish_start:finish_end]
        self.assertIn("this.isRtlLayout() ?", finish)
        self.assertIn("this.activeSwipeOffset >= CART_SWIPE_DISMISS_THRESHOLD", finish)
        self.assertIn("velocityX >= CART_SWIPE_DISMISS_VELOCITY", finish)
        self.assertIn("this.activeSwipeOffset <= -CART_SWIPE_DISMISS_THRESHOLD", finish)
        self.assertIn("velocityX <= -CART_SWIPE_DISMISS_VELOCITY", finish)

    def test_22_source_buttons_use_light_and_dark_interactive_primary_gradients(self) -> None:
        base = {
            item["name"]: item["value"]
            for item in json.loads(BASE_COLORS.read_text(encoding="utf-8"))["color"]
        }
        dark = {
            item["name"]: item["value"]
            for item in json.loads(DARK_COLORS.read_text(encoding="utf-8"))["color"]
        }
        self.assertEqual("#7057F5", base.get("button_gradient_start"))
        self.assertEqual("#001787", base.get("button_gradient_end"))
        self.assertEqual("#86F7FA", dark.get("button_gradient_start"))
        self.assertEqual("#9B86FA", dark.get("button_gradient_end"))

        targets = (
            (read(SCREENS["cart"]), "action.cart.checkout", ".id('action.cart.checkout')"),
            (read(SCREENS["detail"]), "action.detail.addToCart", ".id('action.detail.addToCart')"),
            (read(ETS / "screens" / "SearchScreen.ets"), "action.search.result.add", ".id(this.addActionId())"),
        )
        for source, stable_id, node_anchor in targets:
            with self.subTest(stable_id=stable_id):
                anchor = source.find(node_anchor)
                self.assertGreater(anchor, 0)
                segment = source[anchor : anchor + 1000]
                self.assertIn(".linearGradient({", segment)
                self.assertIn("app.color.button_gradient_start", segment)
                self.assertIn("app.color.button_gradient_end", segment)
                self.assertNotIn(".backgroundColor(BRAND_COLOR)", segment)

        detail = read(SCREENS["detail"])
        anchor = detail.find("action.detail.addToCart")
        button = detail[anchor : anchor + 1400]
        self.assertIn(".constraintSize({ minHeight: 40 })", button)
        self.assertNotIn(".height(40)", button)
        self.assertIn(".padding({ left: 24, right: 24, top: 8, bottom: 8 })", button)
        self.assertIn(".borderRadius('50%')", button)
        self.assertNotIn(".height(48)", button)
        self.assertIn("@State addButtonHeight: number = 40", detail)
        self.assertIn("private addButtonTouchHeight(): number", detail)
        self.assertIn("return Math.max(48, this.addButtonHeight)", detail)
        self.assertIn("height: this.addButtonTouchHeight()", button)
        self.assertIn("this.addButtonHeight = height", button)

        detail_bar_start = detail.find("private cartBottomBar")
        detail_bar_end = detail.find("build()", detail_bar_start)
        self.assertIn(".constraintSize({ minHeight: 56 })", detail[detail_bar_start:detail_bar_end])

    def test_23_filter_controls_use_themed_interactive_secondary_gradient_borders(self) -> None:
        base = {
            item["name"]: item["value"]
            for item in json.loads(BASE_COLORS.read_text(encoding="utf-8"))["color"]
        }
        dark = {
            item["name"]: item["value"]
            for item in json.loads(DARK_COLORS.read_text(encoding="utf-8"))["color"]
        }
        self.assertEqual("#86F7FA", base.get("filter_border_gradient_start"))
        self.assertEqual("#9B86FA", base.get("filter_border_gradient_end"))
        self.assertEqual("#57EFF5", dark.get("filter_border_gradient_start"))
        self.assertEqual("#C8BBFD", dark.get("filter_border_gradient_end"))

        feed = read(FILTER_BAR)
        overlay = read(SCREENS["filter"])
        for source in (feed, overlay):
            self.assertIn(".borderImage({", source)
            self.assertIn("app.color.filter_border_gradient_start", source)
            self.assertIn("app.color.filter_border_gradient_end", source)
            self.assertIn("direction: GradientDirection.RightBottom", source)
        self.assertGreaterEqual(feed.count(".borderImage({"), 2)
        self.assertIn(
            "width: this.appStore.isQuickFilterSelected(this.value) ? 0 : 2",
            feed,
        )
        self.assertIn("width: this.appStore.isFilterSelected(choice.value) ? 0 : 2", overlay)
        self.assertRegex(
            overlay,
            r"\.fontColor\(this\.appStore\.isFilterSelected\(choice\.value\)\s*\?\s*"
            r"\$r\('app\.color\.text_on_secondary'\)\s*:\s*SECONDARY_TEXT_COLOR\)",
        )
        self.assertNotIn(".border({ width:", feed)

    def test_24_quantity_buttons_match_source_visual_size_gradient_and_touch_target(self) -> None:
        base = {
            item["name"]: item["value"]
            for item in json.loads(BASE_COLORS.read_text(encoding="utf-8"))["color"]
        }
        dark = {
            item["name"]: item["value"]
            for item in json.loads(DARK_COLORS.read_text(encoding="utf-8"))["color"]
        }
        self.assertEqual("#86F7FA", base.get("quantity_border_gradient_start"))
        self.assertEqual("#9B86FA", base.get("quantity_border_gradient_end"))
        self.assertEqual("#57EFF5", dark.get("quantity_border_gradient_start"))
        self.assertEqual("#C8BBFD", dark.get("quantity_border_gradient_end"))

        source = read(QUANTITY_SELECTOR)
        for theme, expected in (("base", ("#86F7FA", "#9B86FA")), ("dark", ("#57EFF5", "#C8BBFD"))):
            for icon in ("ic_quantity_add.svg", "ic_quantity_remove.svg"):
                icon_source = read(ROOT / "entry/src/main/resources" / theme / "media" / icon)
                self.assertIn("<linearGradient", icon_source)
                self.assertIn(expected[0], icon_source)
                self.assertIn(expected[1], icon_source)
        for anchor in (".id(this.decreaseId())", ".id(this.increaseId())"):
            with self.subTest(control=anchor):
                start = source.find(anchor)
                self.assertGreater(start, 0)
                control = source[start : start + 1000]
                self.assertIn(".width(24)", control)
                self.assertIn(".height(24)", control)
                self.assertIn(".responseRegion({ x: -12, y: -12, width: 48, height: 48 })", control)
                self.assertIn(".borderImage({", control)
                self.assertIn("app.color.quantity_border_gradient_start", control)
                self.assertIn("app.color.quantity_border_gradient_end", control)
                self.assertIn("direction: GradientDirection.RightBottom", control)
                self.assertNotIn(".border({ width: 2, color: SECONDARY_COLOR })", control)
                self.assertNotIn(".fillColor(BRAND_COLOR)", control)

    def test_24b_shared_gradient_controls_preserve_android_pressed_feedback(self) -> None:
        android_button = read(
            ROOT / "source-facts/android-source/app/src/main/java/com/example/jetsnack/"
            "ui/components/GradientTintedIconButton.kt"
        )
        android_filters = read(
            ROOT / "source-facts/android-source/app/src/main/java/com/example/jetsnack/"
            "ui/components/Filters.kt"
        )
        for source in (android_button, android_filters):
            self.assertIn("collectIsPressedAsState()", source)
            self.assertIn("offsetGradientBackground(", source)

        feed = read(FILTER_BAR)
        overlay = read(SCREENS["filter"])
        quantity = read(QUANTITY_SELECTOR)
        self.assertIn("@State pressed: boolean = false", feed)
        self.assertIn("@State pressedFilterId: string = ''", overlay)
        for source in (feed, overlay, quantity):
            self.assertIn("TouchType.Down", source)
            self.assertIn("TouchType.Up", source)
            self.assertIn("TouchType.Cancel", source)
            self.assertIn("direction: GradientDirection.Right", source)
        self.assertIn("@State decreasePressed: boolean = false", quantity)
        self.assertIn("@State increasePressed: boolean = false", quantity)
        self.assertIn("if (this.decreasePressed)", quantity)
        self.assertIn("if (this.increasePressed)", quantity)
        self.assertIn("Image($r('app.media.ic_remove'))", quantity)
        self.assertIn("Image($r('app.media.ic_add'))", quantity)
        self.assertIn("app.color.quantity_border_gradient_start", quantity)
        self.assertIn("app.color.quantity_border_gradient_end", quantity)

        journeys = read(ROOT / "journeys/core.yaml")
        self.assertIn("visual.pressed.feed-filter-chip", journeys)
        self.assertIn("visual.pressed.quantity-button", journeys)
        pressed_quantity_start = journeys.find("- id: visual.pressed.quantity-button")
        pressed_quantity = journeys[pressed_quantity_start:pressed_quantity_start + 700]
        self.assertIn('"detail.quantity:1"', pressed_quantity)
        self.assertNotIn('"detail.quantity:0"', pressed_quantity)

    def test_25_detail_title_and_expand_control_use_source_min_heights(self) -> None:
        source = read(SCREENS["detail"])
        title_start = source.find("private detailTitle(snack: Snack)")
        title_end = source.find("private detailBackButton", title_start)
        self.assertGreater(title_start, 0)
        self.assertGreater(title_end, title_start)
        title = source[title_start:title_end]
        self.assertIn(".constraintSize({ minHeight: 128 })", title)
        self.assertNotIn(".height(128)", title)

        back_start = source.find("private detailBackButton()")
        back_end = source.find("private detailBody()", back_start)
        back = source[back_start:back_end]
        self.assertIn(".width(36)", back)
        self.assertIn(".height(36)", back)
        self.assertIn(".responseRegion({ x: -6, y: -6, width: 48, height: 48 })", back)

        body_start = source.find("private detailBody")
        body_end = source.find("private relatedCollections", body_start)
        body = source[body_start:body_end]
        expand_start = body.find("Text(this.expansionLabel())")
        ingredients_start = body.find("app.string.ingredients", expand_start)
        self.assertGreater(expand_start, 0)
        self.assertGreater(ingredients_start, expand_start)
        expand = body[expand_start:ingredients_start]
        self.assertIn(".constraintSize({ minHeight: 20 })", expand)
        self.assertIn(".padding({ top: 15 })", expand)
        self.assertNotIn(".height(44)", expand)
        self.assertIn("@State expansionControlHeight: number = 31", source)
        self.assertIn("private expansionTouchHeight(): number", source)
        self.assertIn("return Math.max(48, this.expansionControlHeight)", source)
        self.assertIn("private expansionTouchTop(): number", source)
        self.assertIn("height: this.expansionTouchHeight()", expand)
        self.assertIn("this.expansionControlHeight = height", expand)

    def test_26_cart_items_grow_with_text_and_keep_image_at_source_top_inset(self) -> None:
        source = read(SCREENS["cart"])
        start = source.find("private cartLine")
        end = source.find("private summaryRow", start)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        line = source[start:end]

        image_start = line.find("SnackImage({")
        name_start = line.find("Text(this.cartSnack(line).name)", image_start)
        tagline_start = line.find("Text(this.cartSnack(line).tagline)", name_start)
        price_start = line.find("Text(formatPrice", tagline_start)
        self.assertGreater(name_start, image_start)
        self.assertGreater(tagline_start, name_start)
        self.assertGreater(price_start, tagline_start)

        self.assertIn("imageSize: 100", line[image_start:name_start])
        self.assertIn(".margin({ top: 16, bottom: 16 })", line[image_start:name_start])
        self.assertNotIn(".maxLines(1)", line[name_start:tagline_start])
        self.assertNotIn("TextOverflow.Ellipsis", line[name_start:tagline_start])
        self.assertIn(".lineHeight(28)", line[tagline_start:price_start])
        self.assertIn(".padding({ right: 16 })", line[tagline_start:price_start])
        self.assertGreaterEqual(line.count(".constraintSize({ minHeight: 132 })"), 2)
        self.assertNotIn(".height(132)", line)
        self.assertIn(".alignItems(VerticalAlign.Top)", line)

    def test_27_detail_bottom_clearance_matches_source_56_plus_8(self) -> None:
        source = read(SCREENS["detail"])
        build_start = source.find("build() {")
        self.assertGreater(build_start, 0)
        build = source[build_start:]
        self.assertRegex(build, r"Blank\(\)\s*\.height\(64\)")
        self.assertNotRegex(build, r"Blank\(\)\s*\.height\(80\)")

    def test_28_checkout_keeps_android_physical_left_text_in_rtl(self) -> None:
        source = read(SCREENS["cart"])
        start = source.find("Text($r('app.string.cart_checkout'))")
        end = source.find(".onClick", start)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        checkout = source[start:end]
        self.assertIn(".direction(Direction.Ltr)", checkout)
        self.assertIn(".textAlign(TextAlign.Start)", checkout)

    def test_29_detail_collapsed_image_uses_logical_end_in_rtl(self) -> None:
        source = read(SCREENS["detail"])
        self.assertIn("import { i18n } from '@kit.LocalizationKit';", source)
        self.assertIn("private isRtlLayout(): boolean", source)
        self.assertIn("i18n.System.getSystemLanguage()", source)
        self.assertIn("i18n.isRTL(systemLanguage)", source)
        start = source.find("private detailImageOffsetX(): number")
        end = source.find("private detailTitleOffsetY", start)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        offset = source[start:end]
        self.assertIn("const collapsedX: number = this.isRtlLayout() ? this.leftInset + 24 :", offset)
        self.assertIn("this.detailViewportWidth - this.rightInset - 24 - imageSize", offset)

    def test_30_filter_scrim_dismisses_while_panel_background_captures_taps(self) -> None:
        source = read(SCREENS["filter"])
        scrim_start = source.find(".id('filter.scrim')")
        panel_render = source.find("this.panel()", scrim_start)
        self.assertGreater(scrim_start, 0)
        self.assertGreater(panel_render, scrim_start)

        scrim_click = source[scrim_start:panel_render]
        self.assertIn("this.appStore.hideFilters()", scrim_click)

        panel_capture_start = source.find(".id('action.filter.applyToFeed')")
        panel_capture_end = source.find(".id('nav.filter')", panel_capture_start)
        self.assertGreater(panel_capture_start, 0)
        self.assertGreater(panel_capture_end, panel_capture_start)
        panel_capture = source[panel_capture_start:panel_capture_end]
        self.assertIn("this.appStore.acknowledgeFilterApplyToFeed()", panel_capture)
        self.assertNotIn("this.appStore.hideFilters()", panel_capture)


if __name__ == "__main__":
    unittest.main(verbosity=2)
