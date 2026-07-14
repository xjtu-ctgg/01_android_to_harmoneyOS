#!/usr/bin/env python3
"""Resource and immutable-data contracts for the Jetsnack migration.

These tests deliberately validate authored ArkTS object arrays rather than
looking for a bag of expected words.  The fixed SHA-256 baseline also keeps
the resource checks useful after the legacy Android source tree is removed
from the final delivery.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FACTS_PATH = ROOT / "source-facts" / "android-facts.json"
MEDIA_ROOT = ROOT / "entry" / "src" / "main" / "resources" / "base" / "media"
FONT_ROOT = ROOT / "entry" / "src" / "main" / "resources" / "rawfile" / "fonts"

SNACK_MODEL_PATH = ROOT / "entry" / "src" / "main" / "ets" / "model" / "Snack.ets"
ORDER_LINE_MODEL_PATH = ROOT / "entry" / "src" / "main" / "ets" / "model" / "OrderLine.ets"
SNACK_DATA_PATH = ROOT / "entry" / "src" / "main" / "ets" / "data" / "SnackData.ets"
SEARCH_DATA_PATH = ROOT / "entry" / "src" / "main" / "ets" / "data" / "SearchData.ets"
THEME_PATH = ROOT / "entry" / "src" / "main" / "ets" / "theme" / "JetsnackTheme.ets"
LIGHT_COLOR_PATH = ROOT / "entry" / "src" / "main" / "resources" / "base" / "element" / "color.json"
DARK_COLOR_PATH = ROOT / "entry" / "src" / "main" / "resources" / "dark" / "element" / "color.json"
LICENSE_PATH = ROOT / "ASSETS_LICENSE"
ANDROID_SNACKS_PATH = ROOT / "source-facts" / "android-source" / "app" / "src" / "main" / "java" / "com" / "example" / "jetsnack" / "ui" / "components" / "Snacks.kt"
SNACK_IMAGE_PATH = ROOT / "entry" / "src" / "main" / "ets" / "components" / "SnackImage.ets"
DETAIL_SCREEN_PATH = ROOT / "entry" / "src" / "main" / "ets" / "screens" / "DetailScreen.ets"
SEARCH_SCREEN_PATH = ROOT / "entry" / "src" / "main" / "ets" / "screens" / "SearchScreen.ets"

IMAGE_SHA256 = {
    "almonds.jpg": "6f178821216e348d39c7b66b4d9fe09ef77da8d76f5e7b609d8aa906f94bf9d0",
    "apple_chips.jpg": "5d7d8916fe6e3cadfc54d93e2ecc29b99b4b88a75fc34ee64ae943c6511f6891",
    "apple_juice.jpg": "7fc548e03cce586c52a8407a96b64c971a5a1676754614afc87d89a5e3176abd",
    "apple_pie.jpg": "28cd40c17dd642697a2153746aa62e643b85a89fad1a4936d70e7ddd5ecdab82",
    "apple_sauce.jpg": "f76fd70130e31ec7205fbe4264b4c237f3f31b83c600f104bd78f06766329711",
    "apples.jpg": "4f64dc7c2472365194e673e3cfd2e37364e581c08e2fe674464569732f36d580",
    "cheese.jpg": "ad9a3de7617f3438475daa67900208837e789a7bf91eda1a8983f5662944ac94",
    "chips.jpg": "63dcaa6c35bc7d997cdffecae22dad2cbfb2eda0df8fdcdac2e8b20c51e083fc",
    "cupcake.jpg": "dc2bb91937fa84732ff18d92be61f35d2856453c6dc6235045e1c785467d0551",
    "desserts.jpg": "53439f52090e3e622775d5821fcb0b9ce7b0c00ccfa0b9f670576329c15032bf",
    "donut.jpg": "adcb59b7b4b305d213192dcbe047642bff6d7d1dd24b2e908c1ea3807127222f",
    "eclair.jpg": "3a675db7c83b174e6eb018fd89af22ed5a08b41151df061ef2eded80f6eddaa5",
    "froyo.jpg": "7b24c55e44c8b5baec0cd94e8d03522bc6e708a4eac8ac0bb8727c02c532eb0c",
    "fruit.jpg": "a497fb3398867209c29c3c7a35ac77c866c02281f039bd46db9185680831f046",
    "gingerbread.jpg": "b96646f053e60fea70ea46561080d220deea6b133da263b81582d4b38e0b6e30",
    "gluten_free.jpg": "57d263d1693b0f68f5397776530dfe74ca0504db20609dd32c8e386463834ef6",
    "grapes.jpg": "fe0045831b2d40626a9e368fb145b5779c6f1dc35bbb7c0ab147d88d9d432a45",
    "honeycomb.jpg": "bd16e2b48715ac942629fdfcaf37bbaf2dc7e7b9e8cfa827dab77686323650ab",
    "ice_cream_sandwich.jpg": "99db9bf069742842360c00565b609e1c9843b3781dcf342382a3911c40c2249d",
    "jelly_bean.jpg": "b1bc07ff23efe1b0c725e8598c046782f2f987681a4a52a9d969a9b3dc559a9b",
    "kitkat.jpg": "0781c3d3e9bdc85a3135810a7aa676ace0982a5d0c3cadd026bf89a942adf8a2",
    "kiwi.jpg": "0f687c840e5f33f6442d0e79097a8986cba4ebe27210908d3972d2a196039ae5",
    "lollipop.jpg": "dfaa45dc256efde282231d80c852b5ee0d7b7b6bfbd030784891e4c89cef7adf",
    "mango.jpg": "f135cc13081d6e3708403d700c35f69d44b508b3137fca99361bde8089641d2c",
    "marshmallow.jpg": "7e629e0c823e6abde0090effaea1ef9456ea5c08237d1ebfcbc62a86020f36db",
    "nougat.jpg": "16fdb4fb6c33e2de1dee96079c42ec252c0b2196323f7aab03c29fd337bcc52e",
    "nuts.jpg": "712e85706a7ad66817a1a0a08b1415997fd1b82171b7d474e0d7d0735dc9c140",
    "oreo.jpg": "1b842600d7fe2fda3519d014707c92079ee2a798e7962e0d5df9adabe44280d9",
    "organic.jpg": "a641341435596a0a69e79c4061f72dbdec7c2f543bd11d892ed95328b6df3ba7",
    "paleo.jpg": "604d75ea7ae37721703f0ff97e118f59abaf30c9d51b272a96a2a580eaac574e",
    "pie.jpg": "cd36994067fb63df3cdaf9237ccc5337561c6bc651348bd6598c0cb8131e3ca8",
    "placeholder.jpg": "78b4bd18fd73e436a060fecd062577f5db89e8442c97f42ab21d515ae1bcc2ac",
    "popcorn.jpg": "8f4ebc52623b389fbc48d4f1b2706cade39dbcb2c7fad0457560ed8a3bcb03f1",
    "pretzels.jpg": "b91b12a5b1029ee3a3e968f5be6b6a2ce39c2bfb839b66191ffc58dd317b1fd4",
    "smoothies.jpg": "f3252f92c35b1af363881b4ed6e407ea8c435f67ca5bc6404ab6e413d758a6ac",
    "vegan.jpg": "1817472d58c4a76fdc64aece9ec778374e26b0c19c3e713c2c596e6823d0538a",
}

FONT_SHA256 = {
    "karla_bold.ttf": "7a61886119056f23bfb3ec3efa1d4678769e3794e205e60ca34136cc0f9008e7",
    "karla_regular.ttf": "b2754c00295b6eb895d8419cb3df993d74a0ed97e143ee98fcd83fdca94f932c",
    "montserrat_light.ttf": "e0feb97ab7fdca79ccdfcc7df7b629f86705e33b7687b7463b388b003ffef865",
    "montserrat_medium.ttf": "421f26b23e2be6b98373d32acd3cb2897b154d4bf0a77d26534ce476e4cbed53",
    "montserrat_regular.ttf": "077cdab15161232a9ba7124d2ddd7a9425145750788e9a966c156cc66274f525",
    "montserrat_semibold.ttf": "f227901ef48ac4d1fe4cc6ed0dbce99e6b38969babe5e05da2dfb33521b02944",
}


def _facts() -> dict[str, object]:
    return json.loads(FACTS_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_authored(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing authored file: {path.relative_to(ROOT).as_posix()}")
    source = path.read_text(encoding="utf-8")
    if len(source.strip()) < 80:
        raise AssertionError(f"authored file is an empty placeholder: {path.relative_to(ROOT).as_posix()}")
    return source


def _strip_comments(source: str) -> str:
    """Mask line/block comments without changing indexes or string literals."""

    output = list(source)
    index = 0
    quote = ""
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            index += 1
            continue
        if char == "/" and following == "/":
            end = source.find("\n", index + 2)
            if end < 0:
                end = len(source)
            for masked in range(index, end):
                output[masked] = " "
            index = end
            continue
        if char == "/" and following == "*":
            end_marker = source.find("*/", index + 2)
            end = len(source) if end_marker < 0 else end_marker + 2
            for masked in range(index, end):
                if output[masked] != "\n":
                    output[masked] = " "
            index = end
            continue
        index += 1
    return "".join(output)


def _mask_non_code(source: str) -> str:
    """Mask comments and literal contents, preserving code offsets/newlines."""

    comments_masked = _strip_comments(source)
    output = list(comments_masked)
    index = 0
    quote = ""
    while index < len(comments_masked):
        char = comments_masked[index]
        if quote:
            if char != "\n":
                output[index] = " "
            if char == "\\":
                if index + 1 < len(comments_masked) and comments_masked[index + 1] != "\n":
                    output[index + 1] = " "
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            output[index] = " "
        index += 1
    return "".join(output)


def _find_matching(source: str, start: int, opening: str, closing: str) -> int:
    if start >= len(source) or source[start] != opening:
        raise AssertionError(f"expected {opening!r} at offset {start}")
    depth = 0
    quote = ""
    index = start
    while index < len(source):
        char = source[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise AssertionError(f"unterminated {opening}{closing} expression")


def _named_array(source: str, symbol: str) -> str:
    authored = _strip_comments(source)
    code = _mask_non_code(source)
    declaration = re.search(rf"\bexport\s+const\s+{re.escape(symbol)}\b[^=]*=", code)
    if declaration is None:
        raise AssertionError(f"missing exported array: {symbol}")
    start = code.find("[", declaration.end())
    if start < 0:
        raise AssertionError(f"{symbol} is not initialized with an array literal")
    end = _find_matching(authored, start, "[", "]")
    return authored[start : end + 1]


def _top_level_objects(array_source: str) -> list[str]:
    objects: list[str] = []
    index = 1
    square_depth = 1
    quote = ""
    while index < len(array_source) - 1:
        char = array_source[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "[":
            square_depth += 1
        elif char == "]":
            square_depth -= 1
        elif char == "{" and square_depth == 1:
            end = _find_matching(array_source, index, "{", "}")
            objects.append(array_source[index : end + 1])
            index = end
        index += 1
    return objects


def _property_start(object_source: str, property_name: str) -> int:
    match = re.search(rf"\b{re.escape(property_name)}\s*:\s*", object_source)
    if match is None:
        raise AssertionError(f"object is missing property {property_name!r}: {object_source[:100]!r}")
    return match.end()


def _parse_string_at(source: str, start: int) -> tuple[str, int]:
    if start >= len(source) or source[start] not in ("'", '"'):
        raise AssertionError(f"expected quoted string near {source[start:start + 40]!r}")
    quote = source[start]
    index = start + 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == quote:
            literal = source[start : index + 1]
            return ast.literal_eval(literal), index + 1
        index += 1
    raise AssertionError("unterminated string literal")


def _string_property(object_source: str, property_name: str) -> str:
    value, _ = _parse_string_at(object_source, _property_start(object_source, property_name))
    return value


def _integer_property(object_source: str, property_name: str) -> int:
    start = _property_start(object_source, property_name)
    match = re.match(r"-?\d+", object_source[start:])
    if match is None:
        raise AssertionError(f"{property_name} must be an integer literal")
    return int(match.group(0))


def _array_property(object_source: str, property_name: str) -> str:
    start = _property_start(object_source, property_name)
    if start >= len(object_source) or object_source[start] != "[":
        raise AssertionError(f"{property_name} must be an array literal")
    end = _find_matching(object_source, start, "[", "]")
    return object_source[start : end + 1]


def _integer_array_property(object_source: str, property_name: str) -> tuple[int, ...]:
    array = _array_property(object_source, property_name)
    body = array[1:-1].strip()
    if not body:
        return ()
    values = [item.strip() for item in body.split(",") if item.strip()]
    if any(re.fullmatch(r"-?\d+", item) is None for item in values):
        raise AssertionError(f"{property_name} must contain only integer literals")
    return tuple(int(item) for item in values)


def _collection_type_property(object_source: str) -> str:
    start = _property_start(object_source, "type")
    if object_source[start] in ("'", '"'):
        value, _ = _parse_string_at(object_source, start)
        return value
    enum_value = re.match(r"CollectionType\.(NORMAL|HIGHLIGHT)\b", object_source[start:])
    if enum_value is None:
        raise AssertionError("type must be a CollectionType enum member")
    return {
        "NORMAL": "Normal",
        "HIGHLIGHT": "Highlight",
    }[enum_value.group(1)]


def _string_array_property(object_source: str, property_name: str) -> tuple[str, ...]:
    array = _array_property(object_source, property_name)
    values: list[str] = []
    index = 1
    while index < len(array) - 1:
        if array[index].isspace() or array[index] == ",":
            index += 1
            continue
        value, index = _parse_string_at(array, index)
        values.append(value)
    return tuple(values)


def _image_property_stem(object_source: str) -> str:
    property_names = ("imageResource", "image", "imageName")
    for property_name in property_names:
        match = re.search(rf"\b{property_name}\s*:\s*", object_source)
        if match is None:
            continue
        tail = object_source[match.end() :]
        if tail.startswith(("'", '"')):
            value, _ = _parse_string_at(tail, 0)
            return Path(value).stem
        resource = re.match(
            r"\$r\(\s*(['\"])app\.media\.([a-z0-9_]+)\1\s*\)",
            tail,
        )
        if resource is not None:
            return resource.group(2)
        raise AssertionError(f"{property_name} must name a migrated app.media resource")
    raise AssertionError("snack object is missing imageResource/image/imageName")


def _exported_scalar(source: str, symbol: str) -> str:
    authored = _strip_comments(source)
    code = _mask_non_code(source)
    declaration = re.search(
        rf"\bexport\s+const\s+{re.escape(symbol)}\b[^=]*=",
        code,
    )
    if declaration is None:
        raise AssertionError(f"missing exported constant: {symbol}")
    end = authored.find(";", declaration.end())
    newline = authored.find("\n", declaration.end())
    candidates = [position for position in (end, newline) if position >= 0]
    value_end = min(candidates) if candidates else len(authored)
    return authored[declaration.end() : value_end].strip()


def _assert_typed_array(test: unittest.TestCase, source: str, symbol: str, type_name: str) -> None:
    test.assertRegex(
        _mask_non_code(source),
        rf"\bexport\s+const\s+{re.escape(symbol)}\s*:\s*(?:ReadonlyArray\s*<\s*{type_name}\s*>|{type_name}\s*\[\s*\])\s*=",
        f"{symbol} must have an explicit {type_name} array type",
    )


class ResourceDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = _facts()

    def test_01_fixed_resource_baseline_matches_source_facts(self) -> None:
        resources = self.facts["resources"]
        fact_images = {Path(item).name for item in resources["images"]}
        fact_fonts = {Path(item).name for item in resources["fonts"]}

        self.assertEqual(36, len(IMAGE_SHA256))
        self.assertEqual(6, len(FONT_SHA256))
        self.assertEqual(set(IMAGE_SHA256), fact_images)
        self.assertEqual(set(FONT_SHA256), fact_fonts)

        # While the Android baseline is still present, guard the fixed digests
        # themselves against transcription mistakes.
        for relative_path in (*resources["images"], *resources["fonts"]):
            source = ROOT / relative_path
            if source.is_file():
                expected = (IMAGE_SHA256 | FONT_SHA256)[source.name]
                self.assertEqual(expected, _sha256(source), relative_path)

    def test_02_all_images_are_bit_identical_and_no_jpg_is_substituted(self) -> None:
        actual_names = {path.name for path in MEDIA_ROOT.glob("*.jpg")}
        self.assertEqual(set(IMAGE_SHA256), actual_names)
        for name, expected_digest in IMAGE_SHA256.items():
            with self.subTest(image=name):
                target = MEDIA_ROOT / name
                self.assertTrue(target.is_file(), f"missing migrated image: {name}")
                self.assertEqual(expected_digest, _sha256(target), name)

    def test_03_all_fonts_are_bit_identical_and_no_ttf_is_substituted(self) -> None:
        actual_names = {path.name for path in FONT_ROOT.glob("*.ttf")}
        self.assertEqual(set(FONT_SHA256), actual_names)
        for name, expected_digest in FONT_SHA256.items():
            with self.subTest(font=name):
                target = FONT_ROOT / name
                self.assertTrue(target.is_file(), f"missing migrated font: {name}")
                self.assertEqual(expected_digest, _sha256(target), name)

    def test_04_asset_provenance_and_licenses_are_explicit(self) -> None:
        self.assertTrue(LICENSE_PATH.is_file(), "missing ASSETS_LICENSE")
        text = LICENSE_PATH.read_text(encoding="utf-8")
        self.assertGreaterEqual(len(text.strip()), 300, "ASSETS_LICENSE is only a placeholder")
        required_evidence = (
            "https://github.com/fuxi-artifacts/demo-Jetsnack-android",
            "23e1421b72b602d80486777efbf24dd248abf3bb",
            "Unsplash",
            "https://unsplash.com",
            "Apache License",
            "2.0",
            "Montserrat",
            "Karla",
        )
        for evidence in required_evidence:
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, text)
        self.assertRegex(text, r"(?i)(SIL\s+Open\s+Font\s+License|\bOFL\b)")

    def test_05_models_are_explicitly_typed_and_non_placeholder(self) -> None:
        snack_model = _strip_comments(_read_authored(SNACK_MODEL_PATH))
        order_line_model = _strip_comments(_read_authored(ORDER_LINE_MODEL_PATH))

        self.assertRegex(snack_model, r"\bexport\s+(?:interface|class)\s+Snack\b")
        for name, type_name in (
            ("stableId", "number"),
            ("name", "string"),
            ("priceCents", "number"),
            ("tagline", "string"),
        ):
            self.assertRegex(snack_model, rf"\b{name}\s*:\s*{type_name}\b")
        self.assertRegex(snack_model, r"\bimage(?:Resource|Name)?\s*:\s*(?:Resource|string)\b")
        self.assertRegex(snack_model, r"\bexport\s+(?:interface|class)\s+SnackCollection\b")
        self.assertRegex(snack_model, r"\bexport\s+enum\s+CollectionType\b")
        self.assertRegex(snack_model, r"\bNORMAL\s*=\s*['\"]Normal['\"]")
        self.assertRegex(snack_model, r"\bHIGHLIGHT\s*=\s*['\"]Highlight['\"]")
        self.assertRegex(snack_model, r"\btype\s*:\s*CollectionType\b")
        self.assertRegex(snack_model, r"\bsnackStableIds\s*:\s*(?:ReadonlyArray\s*<\s*number\s*>|number\s*\[\s*\])")

        self.assertRegex(order_line_model, r"\bexport\s+(?:interface|class)\s+OrderLine\b")
        self.assertRegex(order_line_model, r"\bsnackStableId\s*:\s*number\b")
        self.assertRegex(order_line_model, r"\bquantity\s*:\s*number\b")
        for path, source in ((SNACK_MODEL_PATH, snack_model), (ORDER_LINE_MODEL_PATH, order_line_model)):
            self.assertNotRegex(source, r"\b(?:any|unknown)\b", path.name)
            self.assertNotRegex(source, r"\bTODO\b", path.name)

    def test_06_snacks_are_a_complete_structured_copy_of_the_facts(self) -> None:
        source = _read_authored(SNACK_DATA_PATH)
        _assert_typed_array(self, source, "SNACKS", "Snack")
        objects = _top_level_objects(_named_array(source, "SNACKS"))
        actual = tuple(
            (
                _integer_property(item, "stableId"),
                _string_property(item, "name"),
                f"{_image_property_stem(item)}.jpg",
                _integer_property(item, "priceCents"),
                _string_property(item, "tagline"),
            )
            for item in objects
        )
        expected = tuple(
            (
                item["stableId"],
                item["name"],
                item["image"],
                item["priceCents"],
                item["tagline"],
            )
            for item in self.facts["snacks"]
        )

        self.assertEqual(28, len(objects))
        self.assertEqual(expected, actual)
        self.assertEqual(28, len({item[0] for item in actual}), "stableId values must be unique")
        self.assertEqual(28, len({item[1] for item in actual}), "snack names must be unique")

    def test_07_feed_collections_preserve_order_type_and_membership(self) -> None:
        source = _read_authored(SNACK_DATA_PATH)
        _assert_typed_array(self, source, "SNACK_COLLECTIONS", "SnackCollection")
        objects = _top_level_objects(_named_array(source, "SNACK_COLLECTIONS"))
        actual = tuple(
            (
                _integer_property(item, "stableId"),
                _string_property(item, "name"),
                _collection_type_property(item),
                _integer_array_property(item, "snackStableIds"),
            )
            for item in objects
        )
        expected = tuple(
            (
                item["stableId"],
                item["name"],
                item["type"],
                tuple(item["snackStableIds"]),
            )
            for item in self.facts["collections"]
        )
        self.assertEqual(expected, actual)

    def test_08_initial_cart_and_mutation_constants_match_facts(self) -> None:
        source = _read_authored(SNACK_DATA_PATH)
        _assert_typed_array(self, source, "INITIAL_CART_LINES", "OrderLine")
        objects = _top_level_objects(_named_array(source, "INITIAL_CART_LINES"))
        actual_lines = tuple(
            (
                _integer_property(item, "snackStableId"),
                _integer_property(item, "quantity"),
            )
            for item in objects
        )
        cart = self.facts["cart"]
        expected_lines = tuple(
            (item["snackStableId"], item["quantity"]) for item in cart["initialLines"]
        )
        self.assertEqual(expected_lines, actual_lines)
        self.assertEqual(cart["orderLineCount"], len(actual_lines))

        shipping = _exported_scalar(source, "SHIPPING_CENTS")
        failure_interval = _exported_scalar(source, "QUANTITY_FAILURE_INTERVAL")
        decrement_removes = _exported_scalar(source, "DECREMENT_AT_ONE_REMOVES")
        header_counts_lines = _exported_scalar(source, "ORDER_HEADER_COUNTS_LINES_NOT_UNITS")
        self.assertEqual(cart["shippingCents"], int(shipping))
        self.assertEqual(cart["quantityFailureInterval"], int(failure_interval))
        self.assertEqual(str(cart["decrementAtOneRemoves"]).lower(), decrement_removes)
        self.assertEqual(str(cart["orderHeaderCountsLinesNotUnits"]).lower(), header_counts_lines)
        authored = _strip_comments(source)
        self.assertRegex(
            authored,
            r"\bexport\s+function\s+createInitialCartLines\s*\(\s*\)\s*:\s*OrderLine\s*\[\s*\]",
        )
        self.assertRegex(authored, r"\bcreateOrderLine\s*\(")

        prices = {item["stableId"]: item["priceCents"] for item in self.facts["snacks"]}
        subtotal = sum(prices[snack_id] * quantity for snack_id, quantity in actual_lines)
        self.assertEqual(cart["subtotalCents"], subtotal)
        self.assertEqual(cart["totalCents"], subtotal + int(shipping))

    def test_09_search_groups_states_delay_and_matching_rule_match_facts(self) -> None:
        source = _read_authored(SEARCH_DATA_PATH)
        search = self.facts["search"]

        states_array = _named_array(source, "SEARCH_STATES")
        state_holder = "{ items: " + states_array + " }"
        self.assertEqual(tuple(search["states"]), _string_array_property(state_holder, "items"))
        self.assertEqual(search["simulatedDelayMs"], int(_exported_scalar(source, "SEARCH_DELAY_MS")))
        self.assertEqual(
            search["matchRule"],
            ast.literal_eval(_exported_scalar(source, "SEARCH_MATCH_RULE")),
        )

        def groups(symbol: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
            return tuple(
                (_string_property(item, "name"), _string_array_property(item, "items"))
                for item in _top_level_objects(_named_array(source, symbol))
            )

        self.assertEqual(
            tuple((item["name"], tuple(item["items"])) for item in search["categoryGroups"]),
            groups("SEARCH_CATEGORY_GROUPS"),
        )
        self.assertEqual(
            tuple((item["name"], tuple(item["items"])) for item in search["suggestionGroups"]),
            groups("SEARCH_SUGGESTION_GROUPS"),
        )

        authored = _strip_comments(source)
        self.assertRegex(
            authored,
            r"\bexport\s+function\s+searchSnacks\s*\(\s*query\s*:\s*string\s*\)\s*:\s*(?:ReadonlyArray\s*<\s*Snack\s*>|Snack\s*\[\s*\])",
        )
        self.assertRegex(authored, r"\.toLowerCase\s*\(\s*\)")
        self.assertRegex(authored, r"\.includes\s*\(")
        self.assertNotRegex(authored, r"\.trim\s*\(", "Android SearchRepo does not trim queries")
        self.assertNotRegex(
            authored,
            r"normalizedQuery\.length\s*===\s*0",
            "the Android contains contract returns all snacks for an empty query",
        )

        expected_snacks = self.facts["snacks"]
        for query, expected_ids in search["queryExpectations"].items():
            with self.subTest(query=query):
                actual_ids = [
                    item["stableId"]
                    for item in expected_snacks
                    if query.lower() in item["name"].lower()
                ]
                self.assertEqual(expected_ids, actual_ids)

    def test_10_theme_exports_the_three_screenshot_critical_colors(self) -> None:
        source = _strip_comments(_read_authored(THEME_PATH))
        theme = self.facts["resources"]["theme"]
        expected = {
            "BRAND_COLOR": ("brand_primary", theme["brand"]),
            "SECONDARY_COLOR": ("brand_secondary", theme["secondary"]),
            "BACKGROUND_COLOR": ("page_background", theme["background"]),
        }
        light_colors = {
            item["name"]: item["value"]
            for item in json.loads(LIGHT_COLOR_PATH.read_text(encoding="utf-8"))["color"]
        }
        for symbol, (resource_name, value) in expected.items():
            with self.subTest(symbol=symbol):
                self.assertRegex(
                    source,
                    rf"\bexport\s+const\s+{symbol}\s*:\s*ResourceColor\s*=\s*\$r\(\s*['\"]app\.color\.{resource_name}['\"]\s*\)",
                )
                self.assertEqual(value, light_colors[resource_name])
        self.assertEqual("#4B30ED", light_colors["text_primary"])
        self.assertEqual("#DE000000", light_colors["text_secondary"])
        self.assertEqual("#99000000", light_colors["text_help"])

        dark_colors = {
            item["name"]: item["value"]
            for item in json.loads(DARK_COLOR_PATH.read_text(encoding="utf-8"))["color"]
        }
        self.assertEqual(set(light_colors), set(dark_colors))
        self.assertEqual("#DED6FE", dark_colors["brand_primary"])
        self.assertEqual("#121212", dark_colors["page_background"])
        self.assertEqual("#DED6FE", dark_colors["text_primary"])
        self.assertNotRegex(source, r"#[0-9A-Fa-f]{6,8}")
        self.assertNotRegex(source, r"\b(?:any|unknown)\b")
        self.assertNotRegex(source, r"\bTODO\b")

    def test_11_lookup_and_font_registration_do_not_leak_shared_state(self) -> None:
        snack_data = _strip_comments(_read_authored(SNACK_DATA_PATH))
        theme = _strip_comments(_read_authored(THEME_PATH))
        self.assertRegex(
            snack_data,
            r"\bexport\s+function\s+getSnackById\s*\(\s*stableId\s*:\s*number\s*\)\s*:\s*Snack\s*\|\s*undefined",
        )
        self.assertNotRegex(snack_data, r"return\s+SNACKS\s*\[\s*0\s*\]")
        self.assertRegex(theme, r"\bfontsRegistered\s*:\s*boolean\s*=\s*false")
        self.assertRegex(theme, r"if\s*\(\s*fontsRegistered\s*\)\s*\{\s*return\s*;")
        self.assertRegex(theme, r"fontsRegistered\s*=\s*true")

    def test_12_snack_images_preserve_the_android_center_crop_contract(self) -> None:
        android = _read_authored(ANDROID_SNACKS_PATH)
        snack_image = _read_authored(SNACK_IMAGE_PATH)
        detail = _read_authored(DETAIL_SCREEN_PATH)
        search = _read_authored(SEARCH_SCREEN_PATH)

        snack_image_start = android.index("fun SnackImage(")
        snack_image_end = android.index("@Preview", snack_image_start)
        android_snack_image = android[snack_image_start:snack_image_end]
        self.assertIn("contentScale = ContentScale.Crop", android_snack_image)
        self.assertNotIn("alignment =", android_snack_image)

        for marker in (
            ".width(this.imageSize)",
            ".height(this.imageSize)",
            ".borderRadius(this.imageSize / 2)",
            ".objectFit(ImageFit.Cover)",
        ):
            self.assertIn(marker, snack_image)

        detail_image_start = detail.index("private detailImage(snack: Snack)")
        detail_image_end = detail.index("private detailTitle(snack: Snack)", detail_image_start)
        detail_image = detail[detail_image_start:detail_image_end]
        for marker in (
            ".width(this.detailImageSize())",
            ".height(this.detailImageSize())",
            ".borderRadius(this.detailImageSize() / 2)",
            ".objectFit(ImageFit.Cover)",
        ):
            self.assertIn(marker, detail_image)

        category_start = search.index("struct SearchCategoryCard")
        category_end = search.index("struct SearchResultRow", category_start)
        category = search[category_start:category_end]
        self.assertIn(".aspectRatio(1)", category)
        self.assertIn(".borderRadius('50%')", category)
        self.assertIn(".objectFit(ImageFit.Cover)", category)


class ParserGuardTests(unittest.TestCase):
    def test_comments_and_unrelated_strings_cannot_fake_an_exported_array(self) -> None:
        fake = """
          // export const SNACKS: Snack[] = [{ stableId: 1 }];
          const message: string = 'export const SNACKS = [{ stableId: 1 }]';
        """
        with self.assertRaisesRegex(AssertionError, "missing exported array"):
            _named_array(fake, "SNACKS")

    def test_structured_parser_handles_apostrophes_and_nested_member_arrays(self) -> None:
        source = """
          export const SNACK_COLLECTIONS: SnackCollection[] = [
            {
              stableId: 1,
              name: "Android's picks",
              type: CollectionType.HIGHLIGHT,
              snackStableIds: [1, 2, 3]
            }
          ];
        """
        objects = _top_level_objects(_named_array(source, "SNACK_COLLECTIONS"))
        self.assertEqual(1, len(objects))
        self.assertEqual("Android's picks", _string_property(objects[0], "name"))
        self.assertEqual("Highlight", _collection_type_property(objects[0]))
        self.assertEqual((1, 2, 3), _integer_array_property(objects[0], "snackStableIds"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
