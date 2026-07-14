#!/usr/bin/env python3
"""Validate the frozen Android facts and Android-to-Harmony migration ledger.

The checker is read-only, deterministic, and uses only the Python standard
library so it can run before the Harmony SDK is discovered.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_COMMIT = "23e1421b72b602d80486777efbf24dd248abf3bb"
EXPECTED_ROUTES = (
    "home/feed",
    "home/search",
    "home/cart",
    "home/profile",
    "snack/{snackId}?origin={origin}",
    "overlay/filter",
)
EXPECTED_ROUTE_IDS = (
    "route.feed",
    "route.search",
    "route.cart",
    "route.profile",
    "route.detail",
    "route.filter",
)
EXPECTED_ROUTE_KINDS = ("tab", "tab", "tab", "tab", "detail", "overlay")
CART_DEEP_LINK = "https://jetsnack.example.com/home/cart"
EXPECTED_PAGE_IDS = {"feed", "search", "cart", "profile", "detail", "filter"}
EXPECTED_REQUIRED_TEXTS = {
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
EXPECTED_NO_OP_IDS = {
    "delivery.address.expand",
    "feed.collection.action",
    "filter.reset",
    "filter.applyToFeed",
    "search.category.select",
    "search.result.add",
    "cart.checkout",
    "cart.swipeDismiss.persistence",
    "detail.addToCart",
    "detail.related.select",
}
ROUTE_KINDS = {"tab", "detail", "overlay"}
COLLECTION_TYPES = {"Normal", "Highlight"}
LEGAL_STATUSES = {"planned", "in_progress", "implemented", "verified", "not_applicable"}
LEGAL_MAPPING_KINDS = {"page", "route", "action", "data", "state", "theme", "resource", "component"}
REQUIRED_MAPPING_KEYS = {"id", "kind", "source", "target", "stableId", "status", "journey"}


JsonObject = dict[str, Any]


def _is_object(value: object) -> bool:
    return isinstance(value, dict)


def _is_array(value: object) -> bool:
    return isinstance(value, list)


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _duplicates(values: list[object]) -> list[str]:
    counts = Counter(str(value) for value in values)
    return sorted(value for value, count in counts.items() if count > 1)


def _require_keys(record: JsonObject, keys: set[str], label: str, errors: list[str]) -> None:
    for key in sorted(keys - set(record)):
        errors.append(f"{label} missing key: {key}")


def _nonempty_string(record: JsonObject, key: str, label: str, errors: list[str]) -> str | None:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.{key} must be a non-empty string")
        return None
    return value


def _integer(
    record: JsonObject,
    key: str,
    label: str,
    errors: list[str],
    minimum: int | None = None,
) -> int | None:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or (minimum is not None and value < minimum):
        qualifier = f" >= {minimum}" if minimum is not None else ""
        errors.append(f"{label}.{key} must be an integer{qualifier}")
        return None
    return value


def _boolean(record: JsonObject, key: str, label: str, errors: list[str]) -> bool | None:
    value = record.get(key)
    if not isinstance(value, bool):
        errors.append(f"{label}.{key} must be a boolean")
        return None
    return value


def _object_field(record: JsonObject, key: str, label: str, errors: list[str]) -> JsonObject:
    value = record.get(key)
    if not _is_object(value):
        errors.append(f"{label}.{key} must be an object")
        return {}
    return value


def _array_field(record: JsonObject, key: str, label: str, errors: list[str]) -> list[Any]:
    value = record.get(key)
    if not _is_array(value):
        errors.append(f"{label}.{key} must be an array")
        return []
    return value


def _string_array(value: object, label: str, errors: list[str]) -> list[str]:
    if not _is_array(value):
        errors.append(f"{label} must be an array")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}] must be a non-empty string")
        else:
            result.append(item)
    return result


def _integer_array(value: object, label: str, errors: list[str]) -> list[int]:
    if not _is_array(value):
        errors.append(f"{label} must be an array")
        return []
    result: list[int] = []
    for index, item in enumerate(value):
        if not isinstance(item, int) or isinstance(item, bool):
            errors.append(f"{label}[{index}] must be an integer")
        else:
            result.append(item)
    return result


def _validate_existing_source(root: Path, value: object, label: str, errors: list[str]) -> None:
    if not _safe_relative_path(value):
        errors.append(f"{label} must be a safe relative path")
        return
    if not (root / str(value)).is_file():
        errors.append(f"{label} does not exist: {value}")


def _read_json(path: Path, label: str, errors: list[str]) -> JsonObject:
    if not path.is_file():
        errors.append(f"missing {label}: {path.as_posix()}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"invalid {label} JSON: {type(error).__name__}")
        return {}
    if not _is_object(payload):
        errors.append(f"{label} root must be an object")
        return {}
    return payload


def _validate_source(facts: JsonObject, errors: list[str]) -> None:
    source = _object_field(facts, "source", "facts", errors)
    required = {"repository", "commit", "branch", "module", "applicationId", "framework"}
    _require_keys(source, required, "facts source", errors)
    for key in sorted(required):
        _nonempty_string(source, key, "facts source", errors)
    if source.get("commit") != EXPECTED_COMMIT:
        errors.append("facts source commit does not match the competition baseline")
    if source.get("module") != "app":
        errors.append("facts source module must equal app")


def _validate_pages(root: Path, facts: JsonObject, errors: list[str]) -> list[JsonObject]:
    pages = _array_field(facts, "pages", "facts", errors)
    if len(pages) != 6:
        errors.append(f"facts pages must contain 6 entries, found {len(pages)}")
    records: list[JsonObject] = []
    ids: list[object] = []
    stable_ids: list[object] = []
    routes: list[object] = []
    required = {"id", "name", "source", "target", "route", "stableId", "journey"}
    for index, value in enumerate(pages):
        label = f"facts pages[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        record = value
        records.append(record)
        _require_keys(record, required, label, errors)
        for key in sorted(required):
            _nonempty_string(record, key, label, errors)
        ids.append(record.get("id"))
        stable_ids.append(record.get("stableId"))
        routes.append(record.get("route"))
        _validate_existing_source(root, record.get("source"), f"{label}.source", errors)
        if not _safe_relative_path(record.get("target")):
            errors.append(f"{label}.target must be a safe relative path")
    if {value for value in ids if isinstance(value, str)} != EXPECTED_PAGE_IDS:
        errors.append("facts page ids do not cover feed/search/cart/profile/detail/filter")
    for duplicate in _duplicates(ids):
        errors.append(f"duplicate page id: {duplicate}")
    for duplicate in _duplicates(stable_ids):
        errors.append(f"duplicate page stableId: {duplicate}")
    if tuple(routes) != EXPECTED_ROUTES:
        errors.append("facts page route order does not match the six-route contract")
    return records


def _validate_routes(root: Path, facts: JsonObject, errors: list[str]) -> list[JsonObject]:
    routes = _array_field(facts, "routes", "facts", errors)
    if len(routes) != 6:
        errors.append(f"facts routes must contain 6 entries, found {len(routes)}")
    records: list[JsonObject] = []
    ids: list[object] = []
    patterns: list[object] = []
    route_kind_values: list[object] = []
    stable_ids: list[object] = []
    required = {"id", "pattern", "kind", "source", "target", "stableId", "journey"}
    kinds = ",".join(sorted(ROUTE_KINDS))
    for index, value in enumerate(routes):
        label = f"facts routes[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        record = value
        records.append(record)
        _require_keys(record, required, label, errors)
        for key in ("id", "pattern", "source", "target", "stableId", "journey"):
            _nonempty_string(record, key, label, errors)
        route_kind = record.get("kind")
        if not isinstance(route_kind, str) or route_kind not in ROUTE_KINDS:
            errors.append(f"{label}.kind must be one of: {kinds}")
        if "deepLink" in record and (not isinstance(record["deepLink"], str) or not record["deepLink"].strip()):
            errors.append(f"{label}.deepLink must be a non-empty string")
        ids.append(record.get("id"))
        patterns.append(record.get("pattern"))
        route_kind_values.append(record.get("kind"))
        stable_ids.append(record.get("stableId"))
        _validate_existing_source(root, record.get("source"), f"{label}.source", errors)
        if not _safe_relative_path(record.get("target")):
            errors.append(f"{label}.target must be a safe relative path")
    if tuple(patterns) != EXPECTED_ROUTES:
        errors.append("facts routes do not match the six-route contract")
    if tuple(ids) != EXPECTED_ROUTE_IDS:
        errors.append("facts route ids do not match the six-route contract")
    if tuple(route_kind_values) != EXPECTED_ROUTE_KINDS:
        errors.append("facts route kinds do not match the six-route contract")
    if len(records) < 3 or records[2].get("deepLink") != CART_DEEP_LINK:
        errors.append("facts cart route deepLink does not match the Android baseline")
    for label, values in (("route id", ids), ("route pattern", patterns), ("route stableId", stable_ids)):
        for duplicate in _duplicates(values):
            errors.append(f"duplicate {label}: {duplicate}")
    return records


def _validate_snacks(facts: JsonObject, errors: list[str]) -> list[JsonObject]:
    snacks = _array_field(facts, "snacks", "facts", errors)
    if len(snacks) != 28:
        errors.append(f"facts snacks must contain 28 entries, found {len(snacks)}")
    records: list[JsonObject] = []
    ids: list[object] = []
    source_indices: list[object] = []
    required = {"stableId", "sourceIndex", "name", "image", "priceCents", "tagline"}
    for index, value in enumerate(snacks):
        label = f"facts snacks[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        record = value
        records.append(record)
        _require_keys(record, required, label, errors)
        ids.append(_integer(record, "stableId", label, errors, 1))
        source_indices.append(_integer(record, "sourceIndex", label, errors, 0))
        _nonempty_string(record, "name", label, errors)
        _nonempty_string(record, "image", label, errors)
        if not isinstance(record.get("tagline"), str):
            errors.append(f"{label}.tagline must be a string")
        _integer(record, "priceCents", label, errors, 0)
    if ids != list(range(1, 29)):
        errors.append("facts snack stableIds must be the deterministic sequence 1..28")
    if source_indices != list(range(28)):
        errors.append("facts snack sourceIndex values must be the sequence 0..27")
    for duplicate in _duplicates(ids):
        errors.append(f"duplicate snack stableId: {duplicate}")
    return records


def _validate_collections(facts: JsonObject, snack_ids: set[int], errors: list[str]) -> None:
    collections = _array_field(facts, "collections", "facts", errors)
    if len(collections) != 5:
        errors.append(f"facts collections must contain 5 entries, found {len(collections)}")
    ids: list[object] = []
    required = {"stableId", "name", "type", "snackStableIds"}
    for index, value in enumerate(collections):
        label = f"facts collections[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        record = value
        _require_keys(record, required, label, errors)
        ids.append(_integer(record, "stableId", label, errors, 1))
        _nonempty_string(record, "name", label, errors)
        collection_type = record.get("type")
        if not isinstance(collection_type, str) or collection_type not in COLLECTION_TYPES:
            errors.append(f"{label}.type must be one of: Highlight,Normal")
        references = _integer_array(record.get("snackStableIds"), f"{label}.snackStableIds", errors)
        unknown = sorted(set(references) - snack_ids)
        if unknown:
            errors.append(f"{label}.snackStableIds contains unknown ids: {','.join(map(str, unknown))}")
    for duplicate in _duplicates(ids):
        errors.append(f"duplicate collection stableId: {duplicate}")


def _validate_search(facts: JsonObject, snack_ids: set[int], errors: list[str]) -> None:
    search = _object_field(facts, "search", "facts", errors)
    required = {"states", "matchRule", "simulatedDelayMs", "queryExpectations", "categoryGroups", "suggestionGroups"}
    _require_keys(search, required, "facts search", errors)
    states = _string_array(search.get("states"), "facts search.states", errors)
    if states != ["Categories", "Suggestions", "Results", "NoResults"]:
        errors.append("facts search states do not match the four-state contract")
    if search.get("matchRule") != "case-insensitive contains":
        errors.append("facts search.matchRule must equal case-insensitive contains")
    _integer(search, "simulatedDelayMs", "facts search", errors, 0)
    if search.get("simulatedDelayMs") != 200:
        errors.append("facts search.simulatedDelayMs must equal the source SearchRepo delay of 200ms")
    expectations = _object_field(search, "queryExpectations", "facts search", errors)
    expected_queries = {
        "Apple": [21, 22, 23, 24, 25],
        "Cheese": [20],
        "NoSuchSnack": [],
        "": list(range(1, 29)),
        " ": [7, 22, 23, 24, 25],
        " Apple ": [],
    }
    if set(expectations) != set(expected_queries):
        errors.append("facts search.queryExpectations do not match the frozen interface query set")
    for query, expected in expected_queries.items():
        actual = _integer_array(expectations.get(query), f"facts search.queryExpectations.{query}", errors)
        if actual != expected:
            errors.append(f"facts search query expectation is wrong: {query}")
        unknown = sorted(set(actual) - snack_ids)
        if unknown:
            errors.append(f"facts search query {query} contains unknown snack ids: {','.join(map(str, unknown))}")
    for group_key in ("categoryGroups", "suggestionGroups"):
        groups = _array_field(search, group_key, "facts search", errors)
        for index, value in enumerate(groups):
            label = f"facts search.{group_key}[{index}]"
            if not _is_object(value):
                errors.append(f"{label} must be an object")
                continue
            _require_keys(value, {"name", "items"}, label, errors)
            _nonempty_string(value, "name", label, errors)
            _string_array(value.get("items"), f"{label}.items", errors)


def _validate_cart(facts: JsonObject, snack_ids: set[int], errors: list[str]) -> None:
    cart = _object_field(facts, "cart", "facts", errors)
    required = {
        "initialLines",
        "orderLineCount",
        "subtotalCents",
        "shippingCents",
        "totalCents",
        "quantityFailureInterval",
        "decrementAtOneRemoves",
        "orderHeaderCountsLinesNotUnits",
    }
    _require_keys(cart, required, "facts cart", errors)
    lines = _array_field(cart, "initialLines", "facts cart", errors)
    actual_lines: list[tuple[int | None, int | None]] = []
    for index, value in enumerate(lines):
        label = f"facts cart.initialLines[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        _require_keys(value, {"snackStableId", "quantity"}, label, errors)
        snack_id = _integer(value, "snackStableId", label, errors, 1)
        quantity = _integer(value, "quantity", label, errors, 1)
        actual_lines.append((snack_id, quantity))
        if snack_id is not None and snack_id not in snack_ids:
            errors.append(f"{label}.snackStableId is unknown: {snack_id}")
    if actual_lines != [(5, 2), (7, 3), (9, 1)]:
        errors.append("facts cart initialLines do not match the Android baseline")
    expected_integer_values = {
        "orderLineCount": 3,
        "subtotalCents": 5444,
        "shippingCents": 369,
        "totalCents": 5813,
        "quantityFailureInterval": 5,
    }
    for key, expected in expected_integer_values.items():
        value = _integer(cart, key, "facts cart", errors, 0)
        if value != expected:
            errors.append(f"facts cart {key} must equal {expected}")
    for key in ("decrementAtOneRemoves", "orderHeaderCountsLinesNotUnits"):
        value = _boolean(cart, key, "facts cart", errors)
        if value is not True:
            errors.append(f"facts cart {key} must equal True")


def _validate_resources(root: Path, facts: JsonObject, snack_images: set[str], errors: list[str]) -> None:
    resources = _object_field(facts, "resources", "facts", errors)
    required = {"images", "fonts", "theme", "license"}
    _require_keys(resources, required, "facts resources", errors)
    image_paths = _string_array(resources.get("images"), "facts resources.images", errors)
    font_paths = _string_array(resources.get("fonts"), "facts resources.fonts", errors)
    if len(image_paths) != 36:
        errors.append(f"facts resources images must contain 36 paths, found {len(image_paths)}")
    if len(font_paths) != 6:
        errors.append(f"facts resources fonts must contain 6 paths, found {len(font_paths)}")
    for key, paths in (("images", image_paths), ("fonts", font_paths)):
        for index, path in enumerate(paths):
            _validate_existing_source(root, path, f"facts resources.{key}[{index}]", errors)
        for duplicate in _duplicates(paths):
            errors.append(f"duplicate resource {key} path: {duplicate}")
    missing_snack_images = sorted(snack_images - {Path(path).name for path in image_paths})
    if missing_snack_images:
        errors.append(f"facts resources images miss snack images: {','.join(missing_snack_images)}")
    theme = _object_field(resources, "theme", "facts resources", errors)
    _require_keys(theme, {"brand", "secondary", "background"}, "facts resources.theme", errors)
    for key in ("brand", "secondary", "background"):
        _nonempty_string(theme, key, "facts resources.theme", errors)
    if theme.get("brand") != "#4B30ED" or theme.get("secondary") != "#86F7FA" or theme.get("background") != "#FFFFFF":
        errors.append("facts theme colors do not match the Android baseline")
    _validate_existing_source(root, resources.get("license"), "facts resources.license", errors)


def _validate_public_copy(facts: JsonObject, errors: list[str]) -> None:
    copy = _object_field(facts, "publicCopy", "facts", errors)
    expected = {
        "detailDescription": DETAIL_DESCRIPTION,
        "noResultsTitleTemplate": NO_RESULTS_TITLE_TEMPLATE,
        "noResultsRetry": NO_RESULTS_RETRY,
    }
    _require_keys(copy, set(expected), "facts publicCopy", errors)
    for key, value in expected.items():
        _nonempty_string(copy, key, "facts publicCopy", errors)
        if copy.get(key) != value:
            errors.append(f"facts publicCopy.{key} does not match Android strings.xml")
    required_texts = _string_array(facts.get("requiredTexts"), "facts requiredTexts", errors)
    for duplicate in _duplicates(required_texts):
        errors.append(f"duplicate required text: {duplicate}")
    missing = sorted((EXPECTED_REQUIRED_TEXTS | set(expected.values())) - set(required_texts))
    for text in missing:
        errors.append(f"missing required text: {text}")
    if "NoResults" in required_texts:
        errors.append("internal state name NoResults must not be recorded as public copy")


def _validate_no_ops(root: Path, facts: JsonObject, errors: list[str]) -> list[JsonObject]:
    no_ops = _array_field(facts, "noOpContracts", "facts", errors)
    records: list[JsonObject] = []
    ids: list[object] = []
    stable_ids: list[object] = []
    required = {"id", "source", "target", "stableId", "journey", "description"}
    for index, value in enumerate(no_ops):
        label = f"facts noOpContracts[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        record = value
        records.append(record)
        _require_keys(record, required, label, errors)
        for key in sorted(required):
            _nonempty_string(record, key, label, errors)
        ids.append(record.get("id"))
        stable_ids.append(record.get("stableId"))
        _validate_existing_source(root, record.get("source"), f"{label}.source", errors)
        if not _safe_relative_path(record.get("target")):
            errors.append(f"{label}.target must be a safe relative path")
    if {value for value in ids if isinstance(value, str)} != EXPECTED_NO_OP_IDS:
        errors.append("facts noOpContracts do not cover the frozen no-op contract")
    for duplicate in _duplicates(ids):
        errors.append(f"duplicate no-op id: {duplicate}")
    for duplicate in _duplicates(stable_ids):
        errors.append(f"duplicate no-op stableId: {duplicate}")
    return records


def _validate_facts(root: Path, facts: JsonObject) -> tuple[list[str], dict[str, list[JsonObject]]]:
    errors: list[str] = []
    root_keys = {
        "schemaVersion",
        "source",
        "pages",
        "routes",
        "snacks",
        "collections",
        "search",
        "cart",
        "resources",
        "publicCopy",
        "requiredTexts",
        "noOpContracts",
    }
    _require_keys(facts, root_keys, "facts", errors)
    if facts.get("schemaVersion") != 1 or isinstance(facts.get("schemaVersion"), bool):
        errors.append("facts schemaVersion must equal integer 1")
    _validate_source(facts, errors)
    pages = _validate_pages(root, facts, errors)
    routes = _validate_routes(root, facts, errors)
    snacks = _validate_snacks(facts, errors)
    snack_ids = {record["stableId"] for record in snacks if isinstance(record.get("stableId"), int) and not isinstance(record.get("stableId"), bool)}
    snack_images = {record["image"] for record in snacks if isinstance(record.get("image"), str)}
    _validate_collections(facts, snack_ids, errors)
    _validate_search(facts, snack_ids, errors)
    _validate_cart(facts, snack_ids, errors)
    _validate_resources(root, facts, snack_images, errors)
    _validate_public_copy(facts, errors)
    no_ops = _validate_no_ops(root, facts, errors)
    return sorted(set(errors)), {"page": pages, "route": routes, "action": no_ops}


def _validate_manifest_target(manifest: JsonObject, errors: list[str]) -> None:
    target = _object_field(manifest, "target", "manifest", errors)
    expected = {
        "platform": "HarmonyOS",
        "model": "Stage",
        "language": "ArkTS",
        "uiFramework": "ArkUI",
        "module": "entry",
    }
    _require_keys(target, set(expected), "manifest target", errors)
    for key, value in expected.items():
        _nonempty_string(target, key, "manifest target", errors)
        if target.get(key) != value:
            errors.append(f"manifest target {key} must equal {value}")


def _cross_validate_mappings(
    facts_by_kind: dict[str, list[JsonObject]],
    mappings: list[JsonObject],
    errors: list[str],
) -> None:
    for kind in ("page", "route", "action"):
        expected = {
            record["id"]: record
            for record in facts_by_kind[kind]
            if isinstance(record.get("id"), str)
        }
        actual = {
            record["id"]: record
            for record in mappings
            if record.get("kind") == kind and isinstance(record.get("id"), str)
        }
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        if missing:
            errors.append(f"manifest is missing {kind} mappings: {','.join(missing)}")
        if extra and kind != "action":
            errors.append(f"manifest has unknown {kind} mappings: {','.join(extra)}")
        for item_id in sorted(set(expected) & set(actual)):
            for field in ("source", "target", "stableId", "journey"):
                if actual[item_id].get(field) != expected[item_id].get(field):
                    errors.append(f"manifest {kind} mapping {item_id}.{field} does not match facts")


def _validate_manifest(
    root: Path,
    manifest: JsonObject,
    facts_by_kind: dict[str, list[JsonObject]],
) -> list[str]:
    errors: list[str] = []
    _require_keys(manifest, {"schemaVersion", "sourceCommit", "target", "mappings"}, "manifest", errors)
    if manifest.get("schemaVersion") != 1 or isinstance(manifest.get("schemaVersion"), bool):
        errors.append("manifest schemaVersion must equal integer 1")
    if not isinstance(manifest.get("sourceCommit"), str) or manifest.get("sourceCommit") != EXPECTED_COMMIT:
        errors.append("manifest sourceCommit does not match the competition baseline")
    _validate_manifest_target(manifest, errors)

    raw_mappings = _array_field(manifest, "mappings", "manifest", errors)
    if not raw_mappings:
        errors.append("manifest mappings must not be empty")
    mappings: list[JsonObject] = []
    ids: list[object] = []
    stable_ids: list[object] = []
    for index, value in enumerate(raw_mappings):
        label = f"manifest mappings[{index}]"
        if not _is_object(value):
            errors.append(f"{label} must be an object")
            continue
        mapping = value
        mappings.append(mapping)
        _require_keys(mapping, REQUIRED_MAPPING_KEYS, label, errors)
        for key in ("id", "source", "target", "stableId", "journey"):
            _nonempty_string(mapping, key, label, errors)
        kind = mapping.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            errors.append(f"{label}.kind must be a non-empty string")
        elif kind not in LEGAL_MAPPING_KINDS:
            errors.append(f"invalid mapping kind at mappings[{index}]: {kind}")
        status = mapping.get("status")
        if not isinstance(status, str) or not status.strip():
            errors.append(f"{label}.status must be a non-empty string")
        elif status not in LEGAL_STATUSES:
            errors.append(f"invalid migration status at mappings[{index}]: {status}")
        ids.append(mapping.get("id"))
        stable_ids.append(mapping.get("stableId"))
        _validate_existing_source(root, mapping.get("source"), f"{label}.source", errors)
        if not _safe_relative_path(mapping.get("target")):
            errors.append(f"{label}.target must be a safe relative path")
        elif isinstance(status, str) and status in {"implemented", "verified"} and not (root / str(mapping["target"])).is_file():
            errors.append(f"{status} target must be a file: {mapping['target']}")
    for duplicate in _duplicates(ids):
        errors.append(f"duplicate mapping id: {duplicate}")
    for duplicate in _duplicates(stable_ids):
        errors.append(f"duplicate mapping stableId: {duplicate}")
    _cross_validate_mappings(facts_by_kind, mappings, errors)
    return sorted(set(errors))


def validate_contract(root: Path, facts: JsonObject, manifest: JsonObject) -> list[str]:
    """Return deterministic contract errors without changing the worktree."""

    fact_errors, facts_by_kind = _validate_facts(root, facts)
    manifest_errors = _validate_manifest(root, manifest, facts_by_kind)
    return sorted(set(fact_errors + manifest_errors))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root, help="work/ project root")
    parser.add_argument("--facts", type=Path, default=None, help="override Android facts JSON")
    parser.add_argument("--manifest", type=Path, default=None, help="override migration manifest JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    facts_path = args.facts.resolve() if args.facts else root / "source-facts" / "android-facts.json"
    manifest_path = args.manifest.resolve() if args.manifest else root / "migration-manifest.json"
    read_errors: list[str] = []
    facts = _read_json(facts_path, "facts", read_errors)
    manifest = _read_json(manifest_path, "manifest", read_errors)
    errors = sorted(set(read_errors + validate_contract(root, facts, manifest)))

    if errors:
        print("status=failed")
        print(f"error_count={len(errors)}")
        for error in errors:
            print(f"error={error}")
        return 1

    print("status=passed")
    print(f"facts={_display_path(facts_path, root)}")
    print(f"manifest={_display_path(manifest_path, root)}")
    print(f"source_commit={facts['source']['commit']}")
    print(f"pages={len(facts['pages'])}")
    print(f"routes={len(facts['routes'])}")
    print(f"actions={len(facts['noOpContracts'])}")
    print(f"snacks={len(facts['snacks'])}")
    print(f"mappings={len(manifest['mappings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
