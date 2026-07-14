#!/usr/bin/env python3
"""Contracts for the Android RecentOrders widget migration to Form Kit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "entry/src/main/module.json5"
ENTRY_ABILITY = ROOT / "entry/src/main/ets/entryability/EntryAbility.ets"
FORM_ABILITY = ROOT / "entry/src/main/ets/entryformability/RecentOrdersFormAbility.ets"
FORM_PAGE = ROOT / "entry/src/main/ets/form/RecentOrdersForm.ets"
FORM_DATA = ROOT / "entry/src/main/ets/form/RecentOrdersFormData.ets"
FORM_CONFIG = ROOT / "entry/src/main/resources/base/profile/form_config.json"
WIDGET_FACTS = ROOT / "source-facts/android-widget.json"
STRINGS = ROOT / "entry/src/main/resources/base/element/string.json"
BASE_COLORS = ROOT / "entry/src/main/resources/base/element/color.json"
DARK_COLORS = ROOT / "entry/src/main/resources/dark/element/color.json"
WIDGET_LOGO = ROOT / "entry/src/main/resources/base/media/widget_logo.svg"
ADD_SHOPPING_CART = ROOT / "entry/src/main/resources/base/media/add_shopping_cart.svg"
SHOPPING_CART = ROOT / "entry/src/main/resources/base/media/shopping_cart.svg"


class RecentOrdersFormContractTests(unittest.TestCase):
    def test_android_widget_facts_are_frozen(self) -> None:
        facts = json.loads(WIDGET_FACTS.read_text(encoding="utf-8"))
        self.assertEqual(
            "23e1421b72b602d80486777efbf24dd248abf3bb",
            facts["sourceCommit"],
        )
        self.assertEqual(
            "app/src/main/java/com/example/jetsnack/widget/layout/ImageTextListLayout.kt",
            facts["sourceLayout"],
        )
        self.assertEqual(
            [[0, 20], [1, 21], [2, 22], [3, 23], [4, 24]],
            facts["demoItemIndices"],
        )
        self.assertEqual(["2*2", "2*4", "4*4"], facts["targetDimensions"])
        self.assertEqual(
            {
                "mediumMinWidth": 260,
                "largeMinWidth": 479,
                "titleMinHeight": 180,
                "trailingMediumMinWidth": 340,
                "trailingMediumMaxWidth": 479,
                "trailingLargeExclusiveMinWidth": 620,
            },
            facts["layoutBreakpointsVp"],
        )
        self.assertEqual(
            {"2*2": [172, 224], "2*4": [360, 224], "4*4": [480, 359]},
            facts["fallbackGeometryVp"],
        )
        self.assertEqual(["titleCart", "trailingCart"], facts["clickTargets"])
        self.assertFalse(facts["wholeRowClickable"])
        self.assertEqual("openCartOnly", facts["actionResult"])

    def test_form_files_exist(self) -> None:
        for path in (FORM_ABILITY, FORM_PAGE, FORM_DATA, FORM_CONFIG):
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), path)

    def test_glance_visual_contract_is_frozen(self) -> None:
        facts = json.loads(WIDGET_FACTS.read_text(encoding="utf-8"))
        visual = facts["visualContract"]
        self.assertEqual("1.2.0-rc01", visual["glanceAppWidgetVersion"])
        self.assertEqual(
            {
                "height": 48,
                "horizontalPadding": 4,
                "startSlot": 48,
                "startPadding": 2,
                "iconSize": 24,
                "titleMaxLines": 1,
            },
            visual["titleBarVp"],
        )
        self.assertEqual(16, visual["contentSpacingVp"])
        self.assertEqual(4, visual["gridGutterVp"])
        self.assertEqual("shopping_cart", visual["titleActionVector"])
        self.assertEqual(
            {
                "light": {
                    "widgetBackground": "#E0F3FF",
                    "secondaryContainer": "#E8DEF8",
                    "primary": "#6750A4",
                    "secondary": "#625B71",
                    "onSurface": "#1C1B1F",
                },
                "dark": {
                    "widgetBackground": "#20333D",
                    "secondaryContainer": "#4A4458",
                    "primary": "#D0BCFF",
                    "secondary": "#CCC2DC",
                    "onSurface": "#E6E1E5",
                },
            },
            visual["fallbackPalette"],
        )

    def test_form_has_dedicated_glance_palette_resources(self) -> None:
        expected = {
            "base": {
                "form_widget_background": "#E0F3FF",
                "form_secondary_container": "#E8DEF8",
                "form_primary": "#6750A4",
                "form_secondary": "#625B71",
                "form_on_surface": "#1C1B1F",
            },
            "dark": {
                "form_widget_background": "#20333D",
                "form_secondary_container": "#4A4458",
                "form_primary": "#D0BCFF",
                "form_secondary": "#CCC2DC",
                "form_on_surface": "#E6E1E5",
            },
        }
        for mode, path in (("base", BASE_COLORS), ("dark", DARK_COLORS)):
            colors = {
                item["name"]: item["value"]
                for item in json.loads(path.read_text(encoding="utf-8"))["color"]
            }
            for name, value in expected[mode].items():
                with self.subTest(mode=mode, name=name):
                    self.assertEqual(value, colors[name])

    def test_title_cart_uses_exact_android_widget_vector(self) -> None:
        svg = SHOPPING_CART.read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 24 24"', svg)
        self.assertIn("M7,18c-1.1,0 -1.99,0.9 -1.99,2", svg)
        self.assertIn("M1,2v2h2l3.6,7.59", svg)
        self.assertIn("M17,18c-1.1,0 -1.99,0.9", svg)

    def test_module_registers_form_extension(self) -> None:
        module = json.loads(MODULE.read_text(encoding="utf-8"))["module"]
        extension = next(
            item
            for item in module["extensionAbilities"]
            if item["name"] == "RecentOrdersFormAbility"
        )
        self.assertEqual("form", extension["type"])
        self.assertEqual(
            "./ets/entryformability/RecentOrdersFormAbility.ets",
            extension["srcEntry"],
        )
        self.assertTrue(extension["exported"])
        self.assertEqual("ohos.extension.form", extension["metadata"][0]["name"])
        self.assertEqual("$profile:form_config", extension["metadata"][0]["resource"])

    def test_form_profile_declares_resizable_dimensions(self) -> None:
        form = json.loads(FORM_CONFIG.read_text(encoding="utf-8"))["forms"][0]
        self.assertEqual("RecentOrdersForm", form["name"])
        self.assertEqual("./ets/form/RecentOrdersForm.ets", form["src"])
        self.assertEqual("arkts", form["uiSyntax"])
        self.assertEqual("auto", form["colorMode"])
        self.assertTrue(form["isDynamic"])
        self.assertTrue(form["resizable"])
        self.assertFalse(form["updateEnabled"])
        self.assertEqual(["2*2", "2*4", "4*4"], form["supportDimensions"])
        self.assertEqual("2*4", form["defaultDimension"])

    def test_form_ability_publishes_dimension_and_live_geometry_binding(self) -> None:
        source = FORM_ABILITY.read_text(encoding="utf-8")
        for marker in (
            "FormExtensionAbility",
            "createFormBindingData",
            "FormParam.IDENTITY_KEY",
            "FormParam.DIMENSION_KEY",
            "FormParam.WIDTH_KEY",
            "FormParam.HEIGHT_KEY",
            "Dimension_2_4",
            "formWidth",
            "formHeight",
            "onSizeChanged",
            "newRect.width",
            "newRect.height",
            "updateForm",
            "FormState.READY",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("Resource", source)
        self.assertNotIn("ESObject", source)

    def test_form_data_matches_all_five_android_orders(self) -> None:
        source = FORM_DATA.read_text(encoding="utf-8")
        expected_rows = (
            ("'1'", "'Cupcake'", "'Cupcake, Apples'", "app.media.cupcake", "'0 20'"),
            ("'2'", "'Donut'", "'Donut, Apple sauce'", "app.media.donut", "'1 21'"),
            ("'3'", "'Eclair'", "'Eclair, Apple chips'", "app.media.eclair", "'2 22'"),
            ("'4'", "'Froyo'", "'Froyo, Apple juice'", "app.media.froyo", "'3 23'"),
            ("'5'", "'Gingerbread'", "'Gingerbread, Apple pie'", "app.media.gingerbread", "'4 24'"),
        )
        for row in expected_rows:
            with self.subTest(row=row):
                for marker in row:
                    self.assertIn(marker, source)
        self.assertEqual(5, source.count("new RecentOrderFormItem("))
        self.assertIn("image: Resource", source)

    def test_form_ui_is_responsive_and_only_exposes_source_click_targets(self) -> None:
        source = FORM_PAGE.read_text(encoding="utf-8")
        for marker in (
            "@Entry(recentOrdersStorage)",
            "@LocalStorageProp('formDimension')",
            "@LocalStorageProp('formWidth')",
            "@LocalStorageProp('formHeight')",
            "FORM_MEDIUM_MIN_WIDTH: number = 260",
            "FORM_LARGE_MIN_WIDTH: number = 479",
            "FORM_TITLE_MIN_HEIGHT: number = 180",
            "FORM_TRAILING_MEDIUM_MIN_WIDTH: number = 340",
            "FORM_TRAILING_MEDIUM_MAX_WIDTH: number = 479",
            "FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH: number = 620",
            "this.formWidth < FORM_MEDIUM_MIN_WIDTH",
            "this.formWidth >= FORM_LARGE_MIN_WIDTH",
            "this.formHeight >= FORM_TITLE_MIN_HEIGHT",
            "this.formWidth > FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH",
            "List({ space: 4 })",
            ".lanes(this.isLarge() ? 2 : 1, this.isLarge() ? 4 : 0)",
            "ForEach(RECENT_ORDER_FORM_ITEMS",
            "item.stableKey",
            "postCardAction",
            "action: string = 'router'",
            "abilityName: string = 'EntryAbility'",
            "targetRoute: string = 'home/cart'",
            "form.recentOrders",
            "form.action.cart.title",
            "form.action.cart.${item.stableKey}",
            ".width(68)",
            ".height(68)",
            ".borderRadius(12)",
            ".borderRadius(16)",
            ".clip(true)",
            ".width(48)",
            ".height(48)",
            ".maxLines(2)",
        ):
            self.assertIn(marker, source)
        self.assertEqual(2, source.count(".onClick("), "only title and trailing cart may click")
        self.assertNotIn("@kit.FormKit", source)
        self.assertNotIn("wholeRow", source)
        self.assertNotIn("ESObject", source)

    def test_form_matches_glance_title_spacing_palette_and_grid(self) -> None:
        source = FORM_PAGE.read_text(encoding="utf-8")
        for marker in (
            "app.media.shopping_cart",
            ".padding({ left: 4, right: 4 })",
            ".padding({ left: 2 })",
            ".margin({ left: this.isSmall() ? 0 : 16 })",
            ".margin({ left: 16 })",
            ".lanes(this.isLarge() ? 2 : 1, this.isLarge() ? 4 : 0)",
            "app.color.form_widget_background",
            "app.color.form_secondary_container",
            "app.color.form_primary",
            "app.color.form_secondary",
            "app.color.form_on_surface",
        ):
            self.assertIn(marker, source)
        title_bar_start = source.index("private titleBar()")
        title_bar_end = source.index("private trailingCart", title_bar_start)
        title_bar = source[title_bar_start:title_bar_end]
        self.assertIn(".height(48)", title_bar)
        self.assertIn(".maxLines(1)", title_bar)
        self.assertNotIn(".height(56)", title_bar)
        self.assertNotIn(".maxLines(2)", title_bar)
        self.assertNotIn("app.media.ic_shopping_cart", source)
        self.assertNotIn("app.color.page_background", source)
        self.assertNotIn("app.color.ui_floated", source)

    def test_form_breakpoint_operators_match_android_source_exactly(self) -> None:
        source = FORM_PAGE.read_text(encoding="utf-8")
        self.assertIn("this.formWidth >= FORM_TRAILING_MEDIUM_MIN_WIDTH", source)
        self.assertIn("this.formWidth <= FORM_TRAILING_MEDIUM_MAX_WIDTH", source)
        self.assertIn("this.formWidth > FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH", source)
        self.assertNotIn("this.formWidth >= FORM_TRAILING_LARGE_EXCLUSIVE_MIN_WIDTH", source)
        self.assertIn("if (this.showTitleBar())", source)
        self.assertIn("if (this.showTrailingCart())", source)
        self.assertIn("if (!this.isSmall())", source)

    def test_missing_geometry_uses_deterministic_reference_device_fallbacks(self) -> None:
        source = FORM_ABILITY.read_text(encoding="utf-8")
        self.assertRegex(
            source,
            r"(?s)Dimension_2_2\) \{\s+return 172;.*Dimension_4_4\) \{\s+return 480;.*return 360;",
        )
        self.assertRegex(
            source,
            r"(?s)Dimension_2_2\) \{\s+return 224;.*Dimension_4_4\) \{\s+return 359;.*return 224;",
        )
        self.assertIn("typeof value === 'number' && value > 0", source)

    def test_form_strings_match_the_android_widget(self) -> None:
        entries = json.loads(STRINGS.read_text(encoding="utf-8"))["string"]
        strings = {entry["name"]: entry["value"] for entry in entries}
        self.assertEqual("Jetsnack Recent Orders", strings["recent_orders_form_name"])
        self.assertEqual(
            "Quickly view and reorder your recent orders.",
            strings["recent_orders_form_description"],
        )
        self.assertEqual("Recent Jetsnack orders", strings["recent_orders_form_title"])
        self.assertEqual("View shopping cart", strings["recent_orders_form_cart"])
        self.assertEqual("Add to Shopping Cart", strings["recent_orders_form_add_to_cart"])

    def test_entry_ability_accepts_only_the_cart_form_route(self) -> None:
        source = ENTRY_ABILITY.read_text(encoding="utf-8")
        for marker in (
            "want.parameters?.['params']",
            "JSON.parse",
            "Record<string, Object>",
            "['targetRoute']",
            "targetRoute === ROUTE_CART",
            "want.parameters?.['targetRoute']",
            "private publishWarmRoute(want: Want): void",
            "onCreate(want: Want",
            "onNewWant(want: Want",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("return targetRoute;", source)

    def test_form_uses_the_exact_android_widget_vectors(self) -> None:
        form_source = FORM_PAGE.read_text(encoding="utf-8")
        self.assertIn("app.media.widget_logo", form_source)
        self.assertIn("app.media.shopping_cart", form_source)
        self.assertIn("app.media.add_shopping_cart", form_source)
        widget_logo = WIDGET_LOGO.read_text(encoding="utf-8")
        shopping_cart = SHOPPING_CART.read_text(encoding="utf-8")
        add_cart = ADD_SHOPPING_CART.read_text(encoding="utf-8")
        self.assertIn("M12,0C18.627,0 24,5.373 24,12", widget_logo)
        self.assertIn("M7,18c-1.1,0 -1.99,0.9 -1.99,2", shopping_cart)
        self.assertIn("M440,240L360,240", add_cart)
        self.assertIn('viewBox="0 0 24 24"', widget_logo)
        self.assertIn('viewBox="0 0 24 24"', shopping_cart)
        self.assertIn('viewBox="0 0 960 960"', add_cart)


if __name__ == "__main__":
    unittest.main()
