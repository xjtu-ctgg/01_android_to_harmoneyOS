#!/usr/bin/env python3
"""Executable RED contracts for the Task 5 state, feed, and bottom bar.

The checks in this file intentionally inspect authored ArkTS declarations,
method bodies, object arrays, and real builder calls.  Comments and string
decoys cannot satisfy a structural assertion.  Search, cart, profile, detail,
and filter-overlay screens belong to later tasks and are not required here.
"""

from __future__ import annotations

import ast
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS_ROOT = ROOT / "entry" / "src" / "main" / "ets"
FACTS_PATH = ROOT / "source-facts" / "android-facts.json"
STRING_RESOURCE_PATH = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "string.json"

APP_ROUTE_PATH = ETS_ROOT / "state" / "AppRoute.ets"
APP_STORE_PATH = ETS_ROOT / "state" / "AppStore.ets"
FEED_SCREEN_PATH = ETS_ROOT / "screens" / "FeedScreen.ets"
INDEX_PATH = ETS_ROOT / "pages" / "Index.ets"
SNACK_DATA_PATH = ETS_ROOT / "data" / "SnackData.ets"

COMPONENT_PATHS = {
    "DestinationBar": ETS_ROOT / "components" / "DestinationBar.ets",
    "SnackImage": ETS_ROOT / "components" / "SnackImage.ets",
    "SnackCard": ETS_ROOT / "components" / "SnackCard.ets",
    "SnackCollection": ETS_ROOT / "components" / "SnackCollection.ets",
    "FilterBar": ETS_ROOT / "components" / "FilterBar.ets",
    "BottomNav": ETS_ROOT / "components" / "BottomNav.ets",
}

EXPECTED_ROUTES = (
    ("ROUTE_FEED", "home/feed"),
    ("ROUTE_SEARCH", "home/search"),
    ("ROUTE_CART", "home/cart"),
    ("ROUTE_PROFILE", "home/profile"),
    ("ROUTE_DETAIL", "snack/{snackId}?origin={origin}"),
    ("ROUTE_FILTER", "overlay/filter"),
)

EXPECTED_BOTTOM_NAV = (
    ("ROUTE_FEED", "Home", "nav.feed"),
    ("ROUTE_SEARCH", "Search", "nav.search"),
    ("ROUTE_CART", "My Cart", "nav.cart"),
    ("ROUTE_PROFILE", "Profile", "nav.profile"),
)


def _mask_arkts_non_code(source: str) -> str:
    """Mask comments and literal text, retaining code in template expressions."""

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


def _read_authored(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing authored file: {path.relative_to(ROOT).as_posix()}")
    source = path.read_text(encoding="utf-8")
    code = re.sub(r"\s+", "", _mask_arkts_non_code(source))
    if len(code) < 64:
        raise AssertionError(f"authored file is an empty placeholder: {path.relative_to(ROOT).as_posix()}")
    return source


def _find_matching(masked: str, start: int, opening: str, closing: str) -> int:
    if start >= len(masked) or masked[start] != opening:
        raise AssertionError(f"expected {opening!r} at offset {start}")
    depth = 0
    for index in range(start, len(masked)):
        char = masked[index]
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
    raise AssertionError(f"unterminated {opening}{closing} block")


def _declaration_body(source: str, kind: str, name: str, *, exported: bool = True) -> str:
    masked = _mask_arkts_non_code(source)
    prefix = r"\bexport\s+" if exported else r"(?:\bexport\s+)?"
    declaration = re.search(prefix + rf"{re.escape(kind)}\s+{re.escape(name)}\b", masked)
    if declaration is None:
        exported_text = "exported " if exported else ""
        raise AssertionError(f"missing {exported_text}{kind} declaration: {name}")
    start = masked.find("{", declaration.end())
    if start < 0:
        raise AssertionError(f"{name} has no declaration body")
    end = _find_matching(masked, start, "{", "}")
    return source[start : end + 1]


def _component_body(source: str, name: str, *, exported: bool = True) -> str:
    masked = _mask_arkts_non_code(source)
    export_pattern = r"export\s+" if exported else r"(?:export\s+)?"
    declaration = re.search(
        rf"@Component(?:V2)?\s+{export_pattern}struct\s+{re.escape(name)}\b",
        masked,
    )
    if declaration is None:
        raise AssertionError(f"missing @Component {name} struct")
    start = masked.find("{", declaration.end())
    if start < 0:
        raise AssertionError(f"component {name} has no body")
    end = _find_matching(masked, start, "{", "}")
    body = source[start : end + 1]
    build_body = _method_body(body, "build")
    build_code = _mask_arkts_non_code(build_body)
    if re.search(r"\b(?:Column|Row|Stack|List|Scroll|Grid|Image|Text|Button|ForEach)\s*\(", build_code) is None:
        raise AssertionError(f"component {name} build() has no ArkUI content")
    return body


def _method_body(source: str, name: str) -> str:
    masked = _mask_arkts_non_code(source)
    declaration = re.search(
        rf"\b{re.escape(name)}\s*\([^()]*\)\s*(?::\s*[A-Za-z_\[][A-Za-z0-9_<>, |\[\]]*)?\s*\{{",
        masked,
    )
    if declaration is None:
        raise AssertionError(f"missing method: {name}")
    start = masked.find("{", declaration.start())
    end = _find_matching(masked, start, "{", "}")
    return source[start : end + 1]


def _exported_string_constant(source: str, symbol: str) -> str:
    masked = _mask_arkts_non_code(source)
    declaration = re.search(
        rf"\bexport\s+const\s+{re.escape(symbol)}\s*:\s*string\s*=",
        masked,
    )
    if declaration is None:
        raise AssertionError(f"missing explicitly typed route constant: {symbol}")
    start = declaration.end()
    while start < len(source) and source[start].isspace():
        start += 1
    if start >= len(source) or source[start] not in {"'", '"'}:
        raise AssertionError(f"{symbol} must use a string literal")
    quote = source[start]
    index = start + 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == quote:
            return ast.literal_eval(source[start : index + 1])
        index += 1
    raise AssertionError(f"unterminated string literal for {symbol}")


def _exported_array_objects(source: str, symbol: str) -> list[str]:
    masked = _mask_arkts_non_code(source)
    declaration = re.search(rf"\bexport\s+const\s+{re.escape(symbol)}\b[^=]*=", masked)
    if declaration is None:
        raise AssertionError(f"missing exported object array: {symbol}")
    start = masked.find("[", declaration.end())
    if start < 0:
        raise AssertionError(f"{symbol} must be initialized with an array literal")
    end = _find_matching(masked, start, "[", "]")
    array_source = source[start : end + 1]
    array_code = masked[start : end + 1]

    objects: list[str] = []
    square_depth = 0
    index = 0
    while index < len(array_code):
        char = array_code[index]
        if char == "[":
            square_depth += 1
        elif char == "]":
            square_depth -= 1
        elif char == "{" and square_depth == 1:
            object_end = _find_matching(array_code, index, "{", "}")
            objects.append(array_source[index : object_end + 1])
            index = object_end
        index += 1
    return objects


def _object_property(object_source: str, property_name: str) -> str:
    masked = _mask_arkts_non_code(object_source)
    # Do not consume post-colon spaces from the masked view: literal contents
    # are spaces there as well.  Advance over actual source whitespace instead.
    match = re.search(rf"\b{re.escape(property_name)}\s*:", masked)
    if match is None:
        raise AssertionError(f"object is missing property: {property_name}")
    start = match.end()
    while start < len(object_source) and object_source[start].isspace():
        start += 1
    depth = 0
    end = start
    while end < len(masked):
        char = masked[end]
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth > 0:
            depth -= 1
        elif depth == 0 and char in ",}":
            break
        end += 1
    return object_source[start:end].strip()


def _quoted_value(value: str) -> str:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as error:
        raise AssertionError(f"expected a quoted string, got {value!r}") from error
    if not isinstance(parsed, str):
        raise AssertionError(f"expected a string, got {type(parsed).__name__}")
    return parsed


def _call_arguments(source: str, symbol: str, *, member: bool = False) -> list[str]:
    masked = _mask_arkts_non_code(source)
    prefix = r"\.\s*" if member else r"\b"
    pattern = re.compile(prefix + re.escape(symbol) + r"\s*\(")
    arguments: list[str] = []
    for call in pattern.finditer(masked):
        start = masked.find("(", call.start())
        end = _find_matching(masked, start, "(", ")")
        arguments.append(source[start + 1 : end].strip())
    return arguments


def _literal_member_call_values(source: str, method: str) -> list[str]:
    values: list[str] = []
    for argument in _call_arguments(source, method, member=True):
        if argument.startswith(("'", '"')):
            values.append(_quoted_value(argument))
    return values


def _string_resource_values() -> dict[str, str]:
    payload = json.loads(STRING_RESOURCE_PATH.read_text(encoding="utf-8"))
    return {item["name"]: item["value"] for item in payload["string"]}


def _display_value(expression: str) -> str:
    if expression.startswith(("'", '"')):
        return _quoted_value(expression)
    resource = re.match(
        r"\$r\(\s*['\"]app\.string\.([A-Za-z0-9_]+)['\"](?:\s*,[\s\S]*)?\)\s*$",
        expression,
    )
    if resource is None:
        raise AssertionError(f"not a literal or app string resource: {expression}")
    resource_name = resource.group(1)
    resources = _string_resource_values()
    if resource_name not in resources:
        raise AssertionError(f"missing app string resource: {resource_name}")
    return resources[resource_name]


def _member_call_display_values(source: str, method: str) -> list[str]:
    values: list[str] = []
    for argument in _call_arguments(source, method, member=True):
        if argument.startswith(("'", '"', "$r(")):
            values.append(_display_value(argument))
    return values


def _named_imports(source: str) -> set[str]:
    masked = _mask_arkts_non_code(source)
    symbols: set[str] = set()
    for declaration in re.finditer(r"\bimport\s*\{(?P<body>[^{}]*)\}\s*from\b", masked):
        for item in declaration.group("body").split(","):
            imported = item.strip().split()[0] if item.strip() else ""
            if imported:
                symbols.add(imported)
    return symbols


class StateFeedContractTests(unittest.TestCase):
    def test_01_required_state_screen_and_component_files_are_authored(self) -> None:
        _read_authored(APP_ROUTE_PATH)
        store_source = _read_authored(APP_STORE_PATH)
        feed_source = _read_authored(FEED_SCREEN_PATH)
        _declaration_body(store_source, "class", "AppStore")
        _component_body(feed_source, "FeedScreen")
        for component_name, path in COMPONENT_PATHS.items():
            with self.subTest(component=component_name):
                _component_body(_read_authored(path), component_name)

    def test_02_app_route_declares_the_exact_six_source_fact_routes(self) -> None:
        source = _read_authored(APP_ROUTE_PATH)
        actual = tuple((symbol, _exported_string_constant(source, symbol)) for symbol, _ in EXPECTED_ROUTES)
        self.assertEqual(EXPECTED_ROUTES, actual)
        self.assertEqual(6, len({route for _, route in actual}))

        facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(tuple(route[1] for route in EXPECTED_ROUTES), tuple(item["pattern"] for item in facts["routes"]))

    def test_03_app_store_has_deterministic_navigation_and_filter_state(self) -> None:
        source = _read_authored(APP_STORE_PATH)
        imports = _named_imports(source)
        # AppRoute owns all six constants; AppStore only needs the two that it
        # reads directly.  Requiring the other four here would create unused
        # imports and work against the competition's Code Linter gate.
        self.assertTrue({"ROUTE_FEED", "ROUTE_DETAIL"}.issubset(imports))
        body = _declaration_body(source, "class", "AppStore")
        code = _mask_arkts_non_code(body)

        required_fields = (
            r"\bcurrentRoute\s*:\s*string\s*=\s*ROUTE_FEED\b",
            r"\bselectedSnackId\s*:\s*number\s*\|\s*undefined\s*=\s*undefined\b",
            r"\bdetailOrigin\s*:\s*string\s*=\s*NO_DETAIL_ORIGIN\b",
            r"\bdetailReturnRoute\s*:\s*string\s*=\s*ROUTE_FEED\b",
            r"\bfilterVisible\s*:\s*boolean\s*=\s*false\b",
        )
        for pattern in required_fields:
            with self.subTest(field=pattern):
                self.assertRegex(code, pattern)

        signatures = (
            r"\bselectTab\s*\(\s*route\s*:\s*string\s*\)\s*:\s*void",
            r"\bopenDetail\s*\(\s*stableId\s*:\s*number\s*,\s*origin\s*:\s*string\s*\)\s*:\s*void",
            r"\bgoBack\s*\(\s*\)\s*:\s*void",
            r"\bshowFilters\s*\(\s*\)\s*:\s*void",
            r"\bhideFilters\s*\(\s*\)\s*:\s*void",
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                self.assertRegex(code, signature)

        select_tab = _mask_arkts_non_code(_method_body(body, "selectTab"))
        self.assertRegex(select_tab, r"\bthis\.currentRoute\s*=\s*route\b")
        self.assertRegex(select_tab, r"\bthis\.selectedSnackId\s*=\s*undefined\b")

        open_detail = _mask_arkts_non_code(_method_body(body, "openDetail"))
        self.assertRegex(
            open_detail,
            r"\bif\s*\(\s*this\.currentRoute\s*===\s*ROUTE_DETAIL\s*\)\s*\{\s*return\s*;?\s*\}",
        )
        self.assertLess(open_detail.find("this.currentRoute === ROUTE_DETAIL"), open_detail.find("this.selectedSnackId = stableId"))
        self.assertRegex(open_detail, r"\bthis\.selectedSnackId\s*=\s*stableId\b")
        self.assertRegex(open_detail, r"\bthis\.detailReturnRoute\s*=\s*this\.currentRoute\b")
        self.assertRegex(open_detail, r"\bthis\.detailOrigin\s*=\s*origin\b")
        self.assertRegex(open_detail, r"\bthis\.currentRoute\s*=\s*ROUTE_DETAIL\b")

        go_back = _mask_arkts_non_code(_method_body(body, "goBack"))
        self.assertRegex(go_back, r"\bthis\.currentRoute\s*=\s*this\.detailReturnRoute\b")
        self.assertRegex(go_back, r"\bthis\.selectedSnackId\s*=\s*undefined\b")

        show_filters = _mask_arkts_non_code(_method_body(body, "showFilters"))
        hide_filters = _mask_arkts_non_code(_method_body(body, "hideFilters"))
        self.assertRegex(show_filters, r"\bthis\.filterVisible\s*=\s*true\b")
        self.assertRegex(hide_filters, r"\bthis\.filterVisible\s*=\s*false\b")

    def test_04_feed_wires_all_five_collections_and_state_actions(self) -> None:
        facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
        expected_names = tuple(item["name"] for item in facts["collections"])
        self.assertEqual(5, len(expected_names))

        data_source = _read_authored(SNACK_DATA_PATH)
        collection_objects = _exported_array_objects(data_source, "SNACK_COLLECTIONS")
        actual_names = tuple(_quoted_value(_object_property(item, "name")) for item in collection_objects)
        self.assertEqual(expected_names, actual_names)

        source = _read_authored(FEED_SCREEN_PATH)
        self.assertTrue({"AppStore", "SNACK_COLLECTIONS", "DestinationBar", "FilterBar", "SnackCollection"}.issubset(_named_imports(source)))
        component = _component_body(source, "FeedScreen")
        code = _mask_arkts_non_code(component)
        self.assertRegex(code, r"\b(?:appStore|store)\s*:\s*AppStore\b")
        build = _method_body(component, "build")
        build_code = _mask_arkts_non_code(build)
        for child in ("DestinationBar", "FilterBar", "SnackCollection"):
            with self.subTest(child=child):
                self.assertRegex(build_code, rf"\b{child}\s*\(")

        self.assertIn("Stack", build_code)
        self.assertRegex(build_code, r"Blank\s*\(\s*\)\s*\.height\s*\(\s*56\s*\)")
        destination_index = build_code.rfind("DestinationBar")
        list_index = build_code.find("List")
        self.assertGreater(destination_index, list_index)
        self.assertTrue(
            any(re.match(r"\s*SNACK_COLLECTIONS\b", argument) for argument in _call_arguments(build, "ForEach")),
            "FeedScreen must render the five-item SNACK_COLLECTIONS array through ForEach",
        )
        self.assertRegex(build_code, r"\.(?:openDetail)\s*\(")
        self.assertRegex(build_code, r"\.(?:showFilters)\s*\(")
        self.assertIn("screen.feed", _literal_member_call_values(build, "id"))
        self.assertIn("Home", _member_call_display_values(build, "accessibilityText"))

    def test_05_bottom_navigation_is_a_structured_four_item_contract(self) -> None:
        source = _read_authored(COMPONENT_PATHS["BottomNav"])
        code = _mask_arkts_non_code(source)
        self.assertRegex(code, r"\bexport\s+interface\s+BottomNavItem\b")
        for field in ("route", "stableId"):
            self.assertRegex(code, rf"\b{field}\s*:\s*string\b")
        self.assertRegex(code, r"\blabel\s*:\s*Resource\b")

        objects = _exported_array_objects(source, "BOTTOM_NAV_ITEMS")
        actual = tuple(
            (
                _object_property(item, "route"),
                _display_value(_object_property(item, "label")),
                _quoted_value(_object_property(item, "stableId")),
            )
            for item in objects
        )
        self.assertEqual(EXPECTED_BOTTOM_NAV, actual)

        component = _component_body(source, "BottomNav")
        component_code = _mask_arkts_non_code(component)
        self.assertRegex(component_code, r"\bcurrentRoute\s*:\s*string\b")
        self.assertRegex(component_code, r"\bonSelect\s*:\s*\(\s*route\s*:\s*string\s*\)\s*=>\s*void\b")
        build = _method_body(component, "build")
        build_code = _mask_arkts_non_code(build)
        self.assertTrue(
            any(re.match(r"\s*BOTTOM_NAV_ITEMS\b", argument) for argument in _call_arguments(build, "ForEach")),
            "BottomNav must render BOTTOM_NAV_ITEMS through ForEach",
        )
        # The item body may be extracted into an @Builder member to keep the
        # root ForEach readable; validate the complete component in that case.
        self.assertRegex(component_code, r"\bthis\.onSelect\s*\(\s*\w+\.route\s*\)")
        self.assertRegex(component_code, r"\.id\s*\(\s*\w+\.stableId\s*\)")
        self.assertRegex(
            component_code,
            r"\.accessibilityText\s*\(\s*this\.localizedLabel\s*\(\s*\w+\s*\)\s*\)",
        )

    def test_06_feed_components_expose_stable_ids_and_accessibility(self) -> None:
        feed = _read_authored(FEED_SCREEN_PATH)
        self.assertIn("screen.feed", _literal_member_call_values(feed, "id"))
        self.assertIn("Home", _member_call_display_values(feed, "accessibilityText"))

        destination = _read_authored(COMPONENT_PATHS["DestinationBar"])
        self.assertIn("Delivery to 1600 Amphitheater Way", [_display_value(item) for item in _call_arguments(destination, "Text") if item.startswith(("'", '"', "$r("))])
        self.assertIn("action.delivery.address.expand", _literal_member_call_values(destination, "id"))
        destination_accessibility = _member_call_display_values(destination, "accessibilityText")
        self.assertIn("Delivery to 1600 Amphitheater Way", destination_accessibility)
        self.assertIn("Select delivery address", destination_accessibility)

        filter_bar = _read_authored(COMPONENT_PATHS["FilterBar"])
        self.assertIn("feed.filters.open", _literal_member_call_values(filter_bar, "id"))
        self.assertIn("Filters", _member_call_display_values(filter_bar, "accessibilityText"))

        snack_image = _read_authored(COMPONENT_PATHS["SnackImage"])
        snack_image_code = _mask_arkts_non_code(_component_body(snack_image, "SnackImage"))
        self.assertRegex(snack_image_code, r"\bcontentDescription\s*:\s*string\b")
        self.assertRegex(snack_image_code, r"\.accessibilityText\s*\(\s*this\.contentDescription\s*\)")

        snack_card = _read_authored(COMPONENT_PATHS["SnackCard"])
        snack_card_body = _component_body(snack_card, "SnackCard")
        snack_card_code = _mask_arkts_non_code(snack_card_body)
        self.assertRegex(snack_card_code, r"\bsnack\s*:\s*Snack\b")
        self.assertRegex(snack_card_code, r"\.accessibilityText\s*\(\s*this\.snack\.name\s*\)")
        dynamic_ids = _call_arguments(snack_card_body, "id", member=True)
        self.assertTrue(
            any(
                re.search(r"`snack\.card\.\$\{\s*this\.snack\.stableId\s*\}`", argument)
                or re.search(r"['\"]snack\.card\.['\"]\s*\+\s*this\.snack\.stableId\b", argument)
                for argument in dynamic_ids
            ),
            "SnackCard must derive .id() from the stable snack ID",
        )

    def test_07_index_composes_store_feed_and_bottom_nav_instead_of_placeholder(self) -> None:
        source = _read_authored(INDEX_PATH)
        self.assertTrue({"AppStore", "FeedScreen", "BottomNav"}.issubset(_named_imports(source)))
        component = _component_body(source, "Index", exported=False)
        component_code = _mask_arkts_non_code(component)
        self.assertRegex(component_code, r"\bappStore\s*:\s*AppStore\s*=\s*new\s+AppStore\s*\(")

        build = _method_body(component, "build")
        build_code = _mask_arkts_non_code(build)
        feed_calls = _call_arguments(component, "FeedScreen")
        nav_calls = _call_arguments(component, "BottomNav")
        self.assertEqual(1, len(feed_calls), "Index must compose exactly one FeedScreen")
        self.assertEqual(1, len(nav_calls), "Index must compose exactly one BottomNav")
        self.assertIn("this.appStore", feed_calls[0])
        self.assertIn("this.appStore.currentRoute", nav_calls[0])
        self.assertIn("this.appStore.selectTab", nav_calls[0])
        self.assertLess(component_code.find("FeedScreen"), component_code.find("BottomNav"))
        self.assertNotRegex(build_code, r"\.justifyContent\s*\(\s*FlexAlign\.Center\s*\)")

    def test_08_collection_dividers_start_after_the_first_collection_only(self) -> None:
        feed = _component_body(_read_authored(FEED_SCREEN_PATH), "FeedScreen")
        feed_build = _mask_arkts_non_code(_method_body(feed, "build"))
        self.assertRegex(feed_build, r"\bif\s*\(\s*index\s*>\s*0\s*\)\s*\{\s*Divider\s*\(")

        collection = _component_body(
            _read_authored(COMPONENT_PATHS["SnackCollection"]),
            "SnackCollection",
        )
        collection_build = _mask_arkts_non_code(_method_body(collection, "build"))
        self.assertNotRegex(
            collection_build,
            r"\.border\s*\(\s*\{\s*width\s*:\s*\{\s*top\s*:",
            "SnackCollection must not add an unconditional top divider to the first collection",
        )

    def test_09_root_preserves_child_automation_nodes_and_filter_hit_target(self) -> None:
        for path, component_name in ((INDEX_PATH, "Index"), (FEED_SCREEN_PATH, "FeedScreen")):
            with self.subTest(component=component_name):
                component = _component_body(
                    _read_authored(path),
                    component_name,
                    exported=component_name != "Index",
                )
                self.assertNotRegex(
                    _mask_arkts_non_code(_method_body(component, "build")),
                    r"\.accessibilityGroup\s*\(\s*true\s*\)",
                    "grouping the complete screen hides child nav/filter/card automation nodes",
                )

        filter_source = _read_authored(COMPONENT_PATHS["FilterBar"])
        filter_build = _mask_arkts_non_code(
            _method_body(_component_body(filter_source, "FilterBar"), "build")
        )
        self.assertRegex(
            filter_build,
            r"Stack\s*\([^)]*\)\s*\{[\s\S]*?Stack\s*\([^)]*\)\s*\{"
            r"[\s\S]*?Image\s*\([^)]*\)[\s\S]*?\}[\s\S]*?\.width\s*\(\s*24\s*\)"
            r"[\s\S]*?\.height\s*\(\s*24\s*\)[\s\S]*?\.borderImage\s*\("
            r"[\s\S]*?\}[\s\S]*?\.width\s*\(\s*48\s*\)[\s\S]*?\.height\s*\(\s*48\s*\)",
            "Android uses a 24vp gradient-bordered filter icon inside a 48vp touch target",
        )

    def test_10_highlight_gradient_spans_six_cards_with_symmetric_stops(self) -> None:
        card_source = _read_authored(COMPONENT_PATHS["SnackCard"])
        card_component = _component_body(card_source, "SnackCard")
        card_code = _mask_arkts_non_code(card_source)
        self.assertRegex(card_code, r"\bGRADIENT_CARD_SLOT\s*:\s*number\s*=\s*186\b")
        self.assertRegex(card_code, r"\bGRADIENT_SPAN\s*:\s*number\s*=\s*1116\b")
        self.assertRegex(card_code, r"\bcardIndex\s*:\s*number\b")

        gradient_body = _mask_arkts_non_code(_method_body(card_component, "gradientColors"))
        expected_stops = (
            r"\[\s*this\.gradientStart\s*,\s*0\s*\]",
            r"\[\s*this\.gradientBridge\s*,\s*0\.25\s*\]",
            r"\[\s*this\.gradientMiddle\s*,\s*0\.5\s*\]",
            r"\[\s*this\.gradientBridge\s*,\s*0\.75\s*\]",
            r"\[\s*this\.gradientStart\s*,\s*1\s*\]",
        )
        cursor = 0
        for pattern in expected_stops:
            match = re.search(pattern, gradient_body[cursor:])
            self.assertIsNotNone(match, f"missing ordered symmetric gradient stop: {pattern}")
            cursor += match.end() if match is not None else 0

        build_code = _mask_arkts_non_code(_method_body(card_component, "build"))
        self.assertRegex(build_code, r"\.width\s*\(\s*GRADIENT_SPAN\s*\)")
        self.assertRegex(
            build_code,
            r"\.position\s*\(\s*\{\s*x\s*:\s*-this\.cardIndex\s*\*\s*GRADIENT_CARD_SLOT",
        )

        collection_source = _read_authored(COMPONENT_PATHS["SnackCollection"])
        collection_build = _mask_arkts_non_code(
            _method_body(_component_body(collection_source, "SnackCollection"), "build")
        )
        self.assertRegex(collection_build, r"\bcardIndex\s*:\s*index\b")

    def test_11_feed_svg_paths_are_exact_android_vector_assets(self) -> None:
        vector_pairs = (
            ("ic_home.xml", "ic_home.svg"),
            ("ic_search.xml", "ic_search.svg"),
            ("ic_shopping_cart.xml", "ic_shopping_cart.svg"),
            ("ic_account_circle.xml", "ic_account_circle.svg"),
            ("ic_filter_list.xml", "ic_filter_list.svg"),
            ("ic_expand_more.xml", "ic_expand_more.svg"),
            ("ic_arrow_back.xml", "ic_arrow_back.svg"),
        )
        android_ns = "{http://schemas.android.com/apk/res/android}"
        media_root = ROOT / "entry" / "src" / "main" / "resources" / "base" / "media"
        drawable_root = (
            ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "res" / "drawable"
        )
        svg_ns = "{http://www.w3.org/2000/svg}"

        for android_name, svg_name in vector_pairs:
            with self.subTest(vector=android_name):
                android_root = ET.parse(drawable_root / android_name).getroot()
                target_path = media_root / svg_name
                self.assertTrue(target_path.is_file(), f"missing converted vector: {svg_name}")
                svg_root = ET.parse(target_path).getroot()

                expected_view_box = "0 0 {} {}".format(
                    android_root.attrib[f"{android_ns}viewportWidth"],
                    android_root.attrib[f"{android_ns}viewportHeight"],
                )
                self.assertEqual(expected_view_box, svg_root.attrib.get("viewBox"))
                android_paths = [
                    child.attrib[f"{android_ns}pathData"]
                    for child in android_root.findall("path")
                ]
                svg_paths = [child.attrib.get("d") for child in svg_root.findall(f"{svg_ns}path")]
                self.assertEqual(android_paths, svg_paths)

        collection_source = _read_authored(COMPONENT_PATHS["SnackCollection"])
        self.assertIn("app.media.ic_arrow_back", collection_source)

    def test_12_bottom_nav_indicator_and_type_metrics_match_android(self) -> None:
        source = _read_authored(COMPONENT_PATHS["BottomNav"])
        component = _component_body(source, "BottomNav")
        component_code = _mask_arkts_non_code(component)
        self.assertRegex(component_code, r"\.lineHeight\s*\(\s*16\s*\)")
        self.assertRegex(component_code, r"\.letterSpacing\s*\(\s*1\.25\s*\)")
        self.assertIn("left: this.currentRoute === item.route ? 16 : 0", source)
        self.assertIn("right: this.currentRoute === item.route ? 16 : 0", source)

        root_build = _mask_arkts_non_code(_method_body(component, "build"))
        self.assertNotRegex(
            root_build,
            r"\.padding\s*\(\s*\{\s*left\s*:\s*8\s*,\s*right\s*:\s*8",
            "the Android nav slots use the full width; only the selected indicator is inset",
        )

    def test_13_feed_type_metrics_and_chip_shape_match_android_theme(self) -> None:
        android_filters = _read_authored(
            ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "java" /
            "com" / "example" / "jetsnack" / "ui" / "components" / "Filters.kt"
        )
        android_shapes = _read_authored(
            ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "java" /
            "com" / "example" / "jetsnack" / "ui" / "theme" / "Shape.kt"
        )
        self.assertIn("FilterChip(filter = filter, shape = MaterialTheme.shapes.small)", android_filters)
        self.assertIn("elevation = 2.dp", android_filters)
        self.assertIn("small = RoundedCornerShape(percent = 50)", android_shapes)

        destination = _mask_arkts_non_code(
            _method_body(
                _component_body(_read_authored(COMPONENT_PATHS["DestinationBar"]), "DestinationBar"),
                "build",
            )
        )
        self.assertRegex(destination, r"\.lineHeight\s*\(\s*24\s*\)")
        self.assertRegex(destination, r"\.letterSpacing\s*\(\s*0\.15\s*\)")
        self.assertRegex(destination, r"\.textAlign\s*\(\s*TextAlign\.Center\s*\)")

        filter_raw = _read_authored(COMPONENT_PATHS["FilterBar"])
        filter_source = _mask_arkts_non_code(filter_raw)
        self.assertRegex(filter_source, r"\.lineHeight\s*\(\s*16\s*\)")
        self.assertRegex(filter_source, r"\.letterSpacing\s*\(\s*0\.4\s*\)")
        self.assertIn(".borderRadius('50%')", filter_raw)
        self.assertIn(".shadow(ShadowStyle.OUTER_DEFAULT_XS)", filter_raw)
        self.assertIn("app.color.filter_elevated_background", filter_raw)
        self.assertIn("app.color.filter_elevated_selected", filter_raw)
        self.assertNotRegex(filter_source, r"\.borderRadius\s*\(\s*14\s*\)")

        base_colors = {
            item["name"]: item["value"]
            for item in json.loads(
                (ROOT / "entry/src/main/resources/base/element/color.json").read_text(encoding="utf-8")
            )["color"]
        }
        dark_colors = {
            item["name"]: item["value"]
            for item in json.loads(
                (ROOT / "entry/src/main/resources/dark/element/color.json").read_text(encoding="utf-8")
            )["color"]
        }
        self.assertEqual("#FFFFFF", base_colors.get("filter_elevated_background"))
        self.assertEqual("#8EF8FA", base_colors.get("filter_elevated_selected"))
        self.assertEqual("#222222", dark_colors.get("filter_elevated_background"))
        self.assertEqual("#C0FDFD", dark_colors.get("filter_elevated_selected"))

        journeys = (ROOT / "journeys/core.yaml").read_text(encoding="utf-8")
        self.assertIn('"quickFilter.shadow:OUTER_DEFAULT_XS"', journeys)
        self.assertIn('"quickFilter.selectedBackground:#8EF8FA"', journeys)
        self.assertIn('"quickFilter.selectedBackground:#C0FDFD"', journeys)

        card_source = _mask_arkts_non_code(_read_authored(COMPONENT_PATHS["SnackCard"]))
        self.assertRegex(card_source, r"\.lineHeight\s*\(\s*24\s*\)")
        self.assertRegex(card_source, r"\.lineHeight\s*\(\s*28\s*\)")
        self.assertRegex(card_source, r"\.letterSpacing\s*\(\s*0\.15\s*\)")

        collection_source = _mask_arkts_non_code(_read_authored(COMPONENT_PATHS["SnackCollection"]))
        self.assertGreaterEqual(len(re.findall(r"\.lineHeight\s*\(\s*24\s*\)", collection_source)), 2)

    def test_14_android_no_op_icon_buttons_remain_clickable_without_empty_handlers(self) -> None:
        destination_source = _read_authored(COMPONENT_PATHS["DestinationBar"])
        destination_code = _mask_arkts_non_code(destination_source)
        self.assertRegex(destination_code, r"\backnowledgeDeliveryAddressAction\s*\(\s*\)\s*:\s*void")
        self.assertRegex(
            destination_code,
            r"\.width\s*\(\s*48\s*\)[\s\S]*?\.height\s*\(\s*48\s*\)[\s\S]*?\.id\s*\([^)]*\)[\s\S]*?\.onClick\s*\(",
        )

    def test_15_bottom_nav_owns_navigation_inset_while_detail_uses_root_avoidance(self) -> None:
        bottom_nav = _read_authored(COMPONENT_PATHS["BottomNav"])
        self.assertIn("@Prop bottomInset: number", bottom_nav)
        self.assertIn(".height(56 + this.bottomInset)", bottom_nav)
        self.assertIn(".padding({ bottom: this.bottomInset })", bottom_nav)
        self.assertIn(".backgroundColor(BRAND_COLOR)", bottom_nav)

        index = _read_authored(INDEX_PATH)
        self.assertIn("bottomInset: this.bottomInset()", index)
        self.assertIn("this.appStore.currentRoute === ROUTE_DETAIL ? this.bottomInset() : 0", index)
        self.assertNotIn("bottom: this.bottomInset(),", index)

        collection_source = _read_authored(COMPONENT_PATHS["SnackCollection"])
        collection_code = _mask_arkts_non_code(collection_source)
        self.assertRegex(collection_code, r"\backnowledgeCollectionAction\s*\(\s*\)\s*:\s*void")
        self.assertRegex(
            collection_code,
            r"\.width\s*\(\s*48\s*\)[\s\S]*?\.height\s*\(\s*48\s*\)[\s\S]*?\.id\s*\(\s*this\.collectionActionId\s*\(\s*\)\s*\)[\s\S]*?\.onClick\s*\(",
        )

    def test_15_user_facing_feed_literals_are_string_resources(self) -> None:
        ui_paths = (
            INDEX_PATH,
            FEED_SCREEN_PATH,
            COMPONENT_PATHS["DestinationBar"],
            COMPONENT_PATHS["FilterBar"],
            COMPONENT_PATHS["BottomNav"],
        )
        for path in ui_paths:
            source = _read_authored(path)
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                for method in ("Text", "accessibilityText"):
                    literal_arguments = [
                        argument
                        for argument in _call_arguments(source, method, member=method != "Text")
                        if argument.startswith(("'", '"'))
                    ]
                    self.assertEqual([], literal_arguments, f"{method} must use app string resources")

        nav_objects = _exported_array_objects(_read_authored(COMPONENT_PATHS["BottomNav"]), "BOTTOM_NAV_ITEMS")
        for item in nav_objects:
            self.assertTrue(_object_property(item, "label").lstrip().startswith("$r("))

        filter_source = _read_authored(COMPONENT_PATHS["FilterBar"])
        self.assertNotRegex(_mask_arkts_non_code(filter_source), r"\bFEED_FILTERS\s*:\s*string\s*\[\s*\]")
        self.assertGreaterEqual(filter_source.count("$r('app.string.filter_"), 5)

    def test_16_highlight_gradient_tracks_horizontal_scroll_with_android_parallax(self) -> None:
        collection = _read_authored(COMPONENT_PATHS["SnackCollection"])
        card = _read_authored(COMPONENT_PATHS["SnackCard"])
        self.assertIn("@State highlightScrollOffset: number = 0", collection)
        self.assertIn("private highlightScroller: Scroller = new Scroller()", collection)
        self.assertIn("List({ space: 16, scroller: this.highlightScroller })", collection)
        self.assertIn("this.highlightScroller.currentOffset().xOffset", collection)
        self.assertIn("gradientScrollOffset: this.highlightScrollOffset", collection)
        self.assertIn("@Prop gradientScrollOffset: number", card)
        self.assertIn("-this.cardIndex * GRADIENT_CARD_SLOT + this.gradientScrollOffset / 3", card)

    def test_17_destination_bar_matches_material3_container_insets_and_overlay_alpha(self) -> None:
        source = _read_authored(COMPONENT_PATHS["DestinationBar"])
        component = _component_body(source, "DestinationBar")
        build = _mask_arkts_non_code(_method_body(component, "build"))

        self.assertRegex(build, r"\.height\s*\(\s*64\s*\)")
        self.assertRegex(build, r"\.padding\s*\(\s*\{\s*left\s*:\s*16\s*,\s*right\s*:\s*4\s*\}\s*\)")
        self.assertRegex(build, r"Divider\s*\(\s*\)[\s\S]*?\.strokeWidth\s*\(\s*1\s*\)")
        self.assertRegex(build, r"\.height\s*\(\s*65\s*\)")
        self.assertIn("app.color.destination_overlay", source)
        self.assertNotIn(".backgroundColor(BACKGROUND_COLOR)", build)

        for theme, expected in (("base", "#F2FFFFFF"), ("dark", "#F2121212")):
            colors = json.loads(
                (ROOT / "entry/src/main/resources" / theme / "element/color.json").read_text(encoding="utf-8")
            )["color"]
            values = {item["name"]: item["value"] for item in colors}
            self.assertEqual(expected, values.get("destination_overlay"))

    def test_17_repeated_snacks_have_unique_ids_and_decorative_images_are_hidden(self) -> None:
        image_source = _read_authored(COMPONENT_PATHS["SnackImage"])
        image_code = _mask_arkts_non_code(image_source)
        self.assertRegex(image_code, r"\bcollectionId\s*:\s*number\b")
        self.assertRegex(image_source, r"\.accessibilityLevel\s*\(\s*['\"]no['\"]\s*\)")
        self.assertIn("`snack.image.${this.collectionId}.${this.stableId}`", image_source)

        card_source = _read_authored(COMPONENT_PATHS["SnackCard"])
        self.assertIn("`snack.card.${this.collectionId}.${this.snack.stableId}`", card_source)
        self.assertIn("this.collectionId <= 2", card_source)

        collection_source = _read_authored(COMPONENT_PATHS["SnackCollection"])
        self.assertIn("`snack.card.${this.collection.stableId}.${snack.stableId}`", collection_source)
        self.assertIn("this.collection.stableId <= 2", collection_source)
        self.assertNotIn("this.collectionSnacks().length", collection_source)

    def test_18_snack_text_keeps_source_wrap_content_instead_of_forced_ellipsis(self) -> None:
        collection_source = _read_authored(COMPONENT_PATHS["SnackCollection"])
        normal_start = collection_source.find("private normalSnack")
        normal_end = collection_source.find("build()", normal_start)
        self.assertGreater(normal_start, 0)
        self.assertGreater(normal_end, normal_start)
        normal = collection_source[normal_start:normal_end]

        self.assertIn("imageSize: 120", normal)
        self.assertIn(".padding(8)", normal)
        self.assertIn(".margin({ top: 8 })", normal)
        self.assertNotIn(".width(136)", normal)
        self.assertNotIn(".height(168)", normal)
        self.assertNotIn(".maxLines(1)", normal)
        self.assertNotIn("TextOverflow.Ellipsis", normal)

        build_start = collection_source.find("build()")
        self.assertGreater(build_start, normal_end - 1)
        build = collection_source[build_start:]
        normal_list = build[build.find("} else {") :]
        self.assertNotIn(".height(176)", normal_list)
        self.assertIn(".constraintSize({ minHeight: 176 })", normal_list)

        card_source = _read_authored(COMPONENT_PATHS["SnackCard"])
        tagline_start = card_source.find("Text(this.snack.tagline)")
        self.assertGreater(tagline_start, 0)
        tagline = card_source[tagline_start:]
        self.assertNotIn(".maxLines(1)", tagline)
        self.assertNotIn("TextOverflow.Ellipsis", tagline)

    def test_19_collection_header_and_filter_bar_use_source_minimum_height(self) -> None:
        collection = _read_authored(COMPONENT_PATHS["SnackCollection"])
        header_start = collection.find("Text(this.collection.name)")
        list_start = collection.find("if (this.collection.type", header_start)
        self.assertGreater(header_start, 0)
        self.assertGreater(list_start, header_start)
        header = collection[header_start:list_start]
        self.assertIn(".constraintSize({ minHeight: 56 })", header)
        self.assertNotIn(".height(56)", header)

        filter_bar = _read_authored(COMPONENT_PATHS["FilterBar"])
        build = _method_body(_component_body(filter_bar, "FilterBar"), "build")
        self.assertIn(".constraintSize({ minHeight: 56 })", build)
        self.assertNotIn(".height(56)", build)

    def test_20_quick_filter_uses_process_lifetime_store_like_global_android_filters(self) -> None:
        store = _read_authored(ETS_ROOT / "state" / "AppStore.ets")
        filter_bar = _read_authored(COMPONENT_PATHS["FilterBar"])
        feed = _read_authored(ETS_ROOT / "screens" / "FeedScreen.ets")

        self.assertIn("quickFilterSelections: string[] = []", store)
        self.assertIn("toggleQuickFilterSelection(name: string): void", store)
        self.assertIn("isQuickFilterSelected(name: string): boolean", store)
        self.assertIn("@ObjectLink appStore: AppStore", filter_bar)
        self.assertIn("@Prop value: string", filter_bar)
        self.assertNotIn("@State selected: boolean", filter_bar)
        self.assertIn("this.appStore.isQuickFilterSelected(this.value)", filter_bar)
        self.assertIn("this.appStore.toggleQuickFilterSelection(this.value)", filter_bar)
        self.assertIn("FilterBar({", feed)
        self.assertIn("appStore: this.appStore", feed)
        self.assertIn("@State renderedHeight: number = 28", filter_bar)
        self.assertIn("private touchHeight(): number", filter_bar)
        self.assertIn("return Math.max(48, this.renderedHeight)", filter_bar)
        self.assertIn("private touchTop(): number", filter_bar)
        self.assertIn("(this.renderedHeight - this.touchHeight()) / 2", filter_bar)
        self.assertIn(".responseRegion({", filter_bar)
        self.assertIn("height: this.touchHeight()", filter_bar)
        self.assertIn("this.renderedHeight = height", filter_bar)

    def test_21_only_normal_feed_snack_images_keep_the_source_one_dp_elevation(self) -> None:
        image = _read_authored(ETS_ROOT / "components" / "SnackImage.ets")
        collection = _read_authored(COMPONENT_PATHS["SnackCollection"])
        card = _read_authored(COMPONENT_PATHS["SnackCard"])

        self.assertIn("@Prop hasMiniShadow: boolean = false", image)
        self.assertIn("ShadowStyle.OUTER_DEFAULT_XS", image)

        normal_start = collection.find("private normalSnack(snack: Snack)")
        normal_end = collection.find("build()", normal_start)
        self.assertGreater(normal_end, normal_start)
        normal = collection[normal_start:normal_end]
        self.assertIn("hasMiniShadow: true", normal)

        self.assertNotIn("hasMiniShadow: true", card)


class ParserGuardTests(unittest.TestCase):
    def test_comments_and_string_decoys_cannot_fake_components_or_arrays(self) -> None:
        fake = """
          // @Component export struct FeedScreen { build() { Column() {} } }
          const componentDecoy: string = '@Component export struct FeedScreen { build() { Column() {} } }';
          const arrayDecoy: string = 'export const BOTTOM_NAV_ITEMS = [{ route: ROUTE_FEED }]';
        """
        with self.assertRaisesRegex(AssertionError, "missing @Component"):
            _component_body(fake, "FeedScreen")
        with self.assertRaisesRegex(AssertionError, "missing exported object array"):
            _exported_array_objects(fake, "BOTTOM_NAV_ITEMS")

    def test_structural_helpers_accept_real_code_and_ignore_literal_braces(self) -> None:
        source = """
          @Component
          export struct Demo {
            private message: string = 'not code: } ] //';
            build() { Column() { Text(this.message) } }
          }
          export const ITEMS: Item[] = [
            { route: ROUTE_FEED, label: 'HOME', stableId: 'nav.feed' }
          ];
        """
        self.assertIn("Text(this.message)", _component_body(source, "Demo"))
        objects = _exported_array_objects(source, "ITEMS")
        self.assertEqual(1, len(objects))
        self.assertEqual("HOME", _quoted_value(_object_property(objects[0], "label")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
