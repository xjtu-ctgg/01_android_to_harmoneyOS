#!/usr/bin/env python3
"""Contracts for the submitted migration Skill, journeys, and verifier."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "android-to-harmonyos" / "SKILL.md"
AGENT = ROOT / "skills" / "android-to-harmonyos" / "agents" / "openai.yaml"
JOURNEYS = ROOT / "journeys" / "core.yaml"
VERIFY = ROOT / "tools" / "verify.sh"
CROSS_BUILD = ROOT / "tools" / "cross_build_openharmony.sh"
DEVICE_EVIDENCE = ROOT / "tools" / "device_evidence.py"
SCREENSHOT_COMPARE = ROOT / "tools" / "screenshot_compare.py"
PROJECT_GATE = ROOT / "skills" / "android-to-harmonyos" / "scripts" / "run-project-gates.sh"
QUALITY_GATES = ROOT / "skills" / "android-to-harmonyos" / "references" / "quality-gates.md"
MANIFEST = ROOT / "migration-manifest.json"
ETS_ROOT = ROOT / "entry" / "src" / "main" / "ets"


class WorkflowContractTests(unittest.TestCase):
    def test_skill_is_actionable_and_contains_no_template_markers(self) -> None:
        source = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("TODO", source)
        self.assertRegex(source, r"(?m)^name: android-to-harmonyos$")
        for phase in (
            "Freeze source facts",
            "Build the Harmony project",
            "Verify behavior and visuals",
            "Package the result",
        ):
            self.assertIn(phase, source)
        self.assertIn("migration-manifest.json", source)
        self.assertIn("journeys/core.yaml", source)
        self.assertIn("tools/verify.sh", source)

    def test_skill_packaging_matches_the_platform_delivery_contract(self) -> None:
        source = SKILL.read_text(encoding="utf-8")
        for marker in (
            "single root directory",
            "INSTRUCTION.md",
            "work/",
            "result/output.md",
            "logs/interaction.md",
            "logs/trace/",
            "migration-report.md",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, source)
        self.assertNotIn(
            "Package the contents so `INSTRUCTION.md` and `work/` are top-level entries",
            source,
        )

    def test_submitted_migration_skill_is_not_confused_with_platform_scorer(self) -> None:
        source = SKILL.read_text(encoding="utf-8")
        self.assertIn("not the platform scoring Skill", source)
        self.assertIn("do not execute this migration Skill during reproduction", source)

    def test_contract_suite_avoids_python_310_only_zip_strict(self) -> None:
        violations = []
        for path in sorted((ROOT / "tools").rglob("*.py")):
            if path.resolve() == Path(__file__).resolve():
                continue
            source = path.read_text(encoding="utf-8")
            if re.search(r"zip\([^)]*strict\s*=\s*True", source, re.DOTALL):
                violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], violations, f"Python 3.10-only zip(strict=True) found: {violations}")

    def test_agent_metadata_invokes_the_exact_skill(self) -> None:
        source = AGENT.read_text(encoding="utf-8")
        self.assertIn("$android-to-harmonyos", source)
        self.assertIn('display_name: "Android to HarmonyOS Migrator"', source)

    def test_agent_metadata_does_not_regenerate_a_completed_delivery(self) -> None:
        source = AGENT.read_text(encoding="utf-8")
        self.assertIn("already completed", source)
        self.assertIn("do not regenerate", source)

    def test_journeys_cover_every_page_and_action_mapping(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expected = {
            item["journey"]
            for item in manifest["mappings"]
            if item["kind"] in {"page", "route", "action"}
        }
        actual = set(re.findall(r"(?m)^  - id: ([a-zA-Z0-9_.-]+)$", source))
        self.assertTrue(expected.issubset(actual), sorted(expected - actual))
        for marker in ("stable_id:", "steps:", "assert:", "screenshot:"):
            self.assertIn(marker, source)

    def test_public_android_instrumentation_paths_are_replayed(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        for marker in (
            "core.public-app-test.navigate-all-screens",
            "core.public-app-test.open-chips-detail",
            '"tap:nav.search", "tap:nav.cart", "tap:nav.profile"',
            '"tap:snack.card.15"',
            '"This is currently work in progress"',
            '"Lorem ipsum"',
        ):
            self.assertIn(marker, source)

    def test_skill_requires_a_complete_offline_fixed_commit_text_snapshot(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        migration_contract = (
            ROOT / "skills/android-to-harmonyos/references/migration-contract.md"
        ).read_text(encoding="utf-8")
        for source in (skill, migration_contract):
            self.assertIn("complete fixed-commit text snapshot", source)
            self.assertIn("production Kotlin", source)
            self.assertIn("build configuration", source)
            self.assertIn("exclude credentials", source)

    def test_verifier_is_portable_and_has_all_hard_gates(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        self.assertTrue(VERIFY.stat().st_mode & 0o111)
        self.assertNotIn("/Users/", source)
        for gate in (
            "contract_check.py",
            "unittest discover",
            "preflight.sh",
            "assembleHap",
            "codelinter",
            "entry/build/default/outputs/default/entry-default-unsigned.hap",
        ):
            self.assertIn(gate, source)

    def test_public_api_cross_build_never_mutates_the_formal_profile(self) -> None:
        source = CROSS_BUILD.read_text(encoding="utf-8")
        self.assertTrue(CROSS_BUILD.stat().st_mode & 0o111)
        self.assertNotIn("/Users/", source)
        for marker in (
            "mktemp -d",
            "runtimeOS",
            "OpenHarmony",
            "deviceTypes",
            "assembleHap",
            "build/cross/entry-default-unsigned.hap",
            "status=passed",
            "scope=public_api_cross_build",
        ):
            self.assertIn(marker, source)
        self.assertNotRegex(source, r"(?:sed|perl)[^\n]*\"\$PROJECT_ROOT/build-profile\.json5\"")

    def test_skill_project_gate_defaults_to_a_real_build(self) -> None:
        source = PROJECT_GATE.read_text(encoding="utf-8")
        self.assertIn('${1:---build}', source)
        self.assertNotIn('${1:---static}', source)

    def test_device_evidence_gate_is_executable_and_selector_driven(self) -> None:
        self.assertTrue(DEVICE_EVIDENCE.is_file())
        self.assertTrue(DEVICE_EVIDENCE.stat().st_mode & 0o111)
        source = QUALITY_GATES.read_text(encoding="utf-8") + DEVICE_EVIDENCE.read_text(encoding="utf-8")
        for marker in (
            "hdc list targets",
            "uitest dumpLayout",
            "uitest screenCap",
            "stable_id",
            "five cold-start repetitions",
            "raw PNG",
            "expected_exactly_one_target",
            "stable_id_not_found",
            "allPngHashesEqual",
        ):
            self.assertIn(marker, source)

    def test_screenshot_comparison_gate_is_executable_and_skill_driven(self) -> None:
        self.assertTrue(SCREENSHOT_COMPARE.is_file())
        self.assertTrue(SCREENSHOT_COMPARE.stat().st_mode & 0o111)
        source = (
            SKILL.read_text(encoding="utf-8")
            + QUALITY_GATES.read_text(encoding="utf-8")
            + SCREENSHOT_COMPARE.read_text(encoding="utf-8")
        )
        for marker in (
            "tools/screenshot_compare.py",
            "--reference",
            "--actual",
            "raw PNG",
            "meanAbsoluteError",
            "pixelMismatchRate",
            "ssim",
            "dimension_mismatch",
        ):
            self.assertIn(marker, source)

    def test_every_journey_anchor_is_exposed_by_an_arkts_ui_node(self) -> None:
        journey_source = JOURNEYS.read_text(encoding="utf-8")
        journey_anchors = set(re.findall(r"(?m)^    stable_id: ([a-zA-Z0-9_.-]+)$", journey_source))
        arkts_source = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(ETS_ROOT.rglob("*.ets"))
        )
        dynamic_anchors = {
            "action.feed.collection.3": ("return `action.feed.collection.${this.collection.stableId}`",),
            "action.search.result.add.25": ("return `action.search.result.add.${this.snack.stableId}`",),
            "cart.quantity.increase.5": ("cart.quantity.increase.${", "stableIdPrefix"),
            "cart.quantity.decrease.9": ("cart.quantity.decrease.${", "stableIdPrefix"),
            "detail.quantity.decrease": ("stableIdPrefix: 'detail.quantity'", "`${this.stableIdPrefix}.decrease`"),
            "detail.quantity.increase": ("stableIdPrefix: 'detail.quantity'", "`${this.stableIdPrefix}.increase`"),
            "feed.collection.1": ("`feed.collection.${this.collection.stableId}`",),
            "search.suggestion.Cheese": ("`search.suggestion.${suggestion}`", "items: ['Cheese'"),
            "form.action.cart.1": ("`form.action.cart.${item.stableKey}`", "stableKey"),
        }
        missing = sorted(
            anchor
            for anchor in journey_anchors
            if anchor not in arkts_source
            and not all(marker in arkts_source for marker in dynamic_anchors.get(anchor, ("<missing>",)))
        )
        self.assertEqual([], missing, f"journey anchors missing from ArkTS UI: {missing}")

        filter_bar = (ETS_ROOT / "components/FilterBar.ets").read_text(encoding="utf-8")
        self.assertIn("@Prop stableId: string", filter_bar)
        self.assertIn(".id(this.stableId)", filter_bar)
        self.assertIn("FeedFilterChip({", filter_bar)
        self.assertIn("stableId: filter.stableId", filter_bar)

    def test_adversarial_journeys_cover_state_edges_and_visual_variants(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        actual = set(re.findall(r"(?m)^  - id: ([a-zA-Z0-9_.-]+)$", source))
        expected = {
            "edge.search.suggestions",
            "edge.search.no-results",
            "edge.search.clear",
            "edge.search.clear-expanded-top-hit-target",
            "edge.search.case-insensitive",
            "edge.search.whitespace-is-query",
            "edge.cart.increment",
            "edge.cart.quantity-persists-across-tabs",
            "edge.cart.quantity-persists-after-rotation",
            "edge.process-restart.resets-cart-view-model",
            "edge.cart.checkout-expanded-top-hit-target",
            "edge.cart.fifth-request-failure",
            "edge.cart.snackbar-auto-dismiss",
            "visual.cart.snackbar-source-geometry",
            "visual.dark.cart-snackbar-source-geometry",
            "edge.cart.snackbar-tap-does-not-dismiss",
            "edge.cart.snackbar-fifo-queue",
            "edge.cart.snackbar-fifo-advances",
            "edge.cart.snackbar-shared-across-tabs",
            "edge.detail.current-snackbar-host-disposed",
            "edge.detail.pending-snackbar-resumes-on-return",
            "edge.cart.decrement-removes-line",
            "edge.cart.remove-all-lines",
            "edge.cart.single-line-plural",
            "edge.detail.quantity-zero-floor",
            "edge.detail.add-expanded-bottom-hit-target",
            "edge.detail.expand-collapse",
            "edge.detail.see-more-expanded-bottom-hit-target",
            "edge.detail.back-expanded-left-hit-target",
            "edge.detail.collapsed-hero",
            "edge.filter.reopen-preserves-global-chips",
            "edge.filter.overlay-chip-persists-across-tabs",
            "edge.process-restart.resets-global-overlay-chip",
            "edge.filter.overlay-chip-expanded-bottom-hit-target",
            "edge.filter.sort-expanded-bottom-hit-target",
            "edge.configuration.filter-overlay-closes-global-chip-persists",
            "visual.dark.feed",
            "visual.large-font.detail",
            "visual.narrow.detail",
            "visual.narrow.search-no-results",
            "visual.narrow.profile",
            "visual.rtl.quantity",
            "edge.navigation.repeated-deep-link",
            "edge.navigation.cart-deep-link-query-fragment",
            "edge.back.filter-priority",
            "visual.feed.horizontal-parallax",
            "visual.feed.normal-snack-source-elevation",
            "edge.feed.quick-filter-toggle",
            "edge.quick-filter.persists-across-tabs",
            "edge.quick-filter.expanded-top-hit-target",
            "edge.quick-filter.persists-after-detail",
            "edge.process-restart.resets-global-quick-filter",
            "edge.feed.pinned-destination",
            "edge.feed.repeated-product-collection-id",
            "edge.search.latest-query-wins",
            "edge.search.loading-during-source-delay",
            "edge.search.results-after-source-delay",
            "edge.search.pending-query-cancelled-on-tab-disposal",
            "edge.search.pending-query-cancelled-by-clear",
            "edge.search.result-add-expanded-hit-target-no-navigation",
            "edge.search.result-return-resets-plain-remember",
            "visual.tablet.search-categories",
            "visual.large-font.search-suggestions",
            "visual.safe-area.cutout",
            "visual.safe-area.no-navigation-indicator",
            "visual.safe-area.landscape-cutout",
            "edge.navigation.same-tab-preserves-state",
            "edge.navigation.search-resets-after-other-tab",
            "edge.detail.bottom-nav-absent",
            "edge.detail.return-to-cart-preserves-state",
            "visual.cart.checkout-source-height",
            "visual.cart.summary-source-geometry",
            "visual.filter.source-spacing",
            "edge.cart.swipe-below-threshold",
            "edge.cart.swipe-at-threshold",
            "edge.cart.swipe-fast-fling",
            "visual.rtl.cart-swipe-progress",
            "edge.rtl.cart-swipe-at-threshold",
            "edge.rtl.cart-swipe-opposite-direction",
            "visual.large-font.search-source-min-heights",
            "visual.search.result-button-gradient",
            "visual.cart.checkout-gradient",
            "visual.dark.detail-button-gradient",
            "visual.feed.quick-filter-gradient-border",
            "visual.dark.filter-chip-gradient-border",
            "visual.feed.quick-filter-selected-black",
            "visual.dark.filter-chip-selected-black",
            "visual.safe-area.bottom-nav-brand-inset",
            "visual.safe-area.detail-bottom-inset",
            "visual.safe-area.detail-gradient-under-status",
            "visual.safe-area.filter-overlay-content-bounds",
            "visual.cart.quantity-source-geometry",
            "visual.dark.detail-quantity-source-geometry",
            "visual.dark.profile",
            "visual.compact-large-font.profile",
            "visual.feed.destination-overlay-source-geometry",
            "visual.dark.cart-destination-overlay",
            "visual.dark.bottom-navigation-selected",
            "visual.rtl.bottom-navigation-order",
            "visual.detail.related-long-title-wrap-content",
            "visual.cart.inspired-long-title-wrap-content",
            "visual.search.long-result-title-wrap",
            "visual.compact-large-font.search-results",
            "visual.compact-large-font.detail-long-title",
            "visual.detail.expand-control-source-height",
            "visual.compact.filter-panel-max-height",
            "visual.large-font.filter-scroll-reachability",
            "visual.cart.long-item-title-wrap",
            "visual.compact-large-font.cart-item-growth",
            "visual.large-font.cart-order-header",
            "visual.large-font.cart-summary-growth",
            "visual.large-font.cart-checkout-growth",
            "visual.large-font.detail-bottom-bar-growth",
            "visual.large-font.feed-collection-header",
            "visual.extra-large-font.feed-filter-bar-growth",
            "visual.dark.extra-large-font.quick-filter-selected-pill",
            "visual.large-font.filter-header-growth",
            "visual.large-font.filter-sort-row-growth",
            "visual.large-font.search-category-text-measurement",
            "visual.rtl.search-category-placement",
            "visual.combined.rtl-large-font-cutout-feed",
            "edge.configuration.rotation-resets-plain-remember-search",
            "edge.configuration.rotation-restarts-empty-search-effect",
            "edge.configuration.quick-filter-global-state-persists",
            "visual.dark.safe-area.no-navigation-indicator-detail",
            "edge.configuration.theme-change-preserves-cart-state",
            "edge.configuration.rotation-resets-detail-plain-remember-state",
            "visual.detail.bottom-scroll-source-clearance",
            "visual.rtl.cart-checkout-physical-left-text",
            "visual.rtl.detail-collapsed-image-logical-end",
            "edge.safe-area.runtime-avoid-area-change",
            "edge.navigation.hot-deep-link-detail-to-cart",
            "edge.process-restart.cart-deep-link-resets-state",
            "edge.window-resize.cart-state-persists",
            "edge.window-mode.split-cart-state-persists",
            "edge.window-mode.floating-cart-state-persists",
            "edge.filter.scrim-dismisses-and-reopen-resets-local-state",
            "edge.filter.panel-captures-tap-without-dismiss",
            "edge.search.suggestion-click-loading",
            "edge.search.suggestion-click-results",
            "visual.startup.light-theme-no-flash",
            "visual.startup.dark-theme-no-flash",
            "visual.startup.cart-deep-link-first-content-no-feed-flash",
            "visual.combined.dark-rtl-large-font-safe-area-cart",
            "visual.combined.dark-rtl-large-font-safe-area-detail",
            "visual.image.crop.portrait-gingerbread-cart-to-detail",
            "visual.image.crop.landscape-froyo-feed-to-detail",
            "edge.filter.category-chip-persists-across-reopen",
            "edge.feed.normal-collection-action-no-navigation",
            "edge.search.non-first-result-add-no-navigation",
        }
        self.assertTrue(expected.issubset(actual), sorted(expected - actual))

    def test_latest_query_wins_journey_asserts_the_real_no_results_state(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        start = source.index("  - id: edge.search.latest-query-wins")
        end = source.index("\n  - id:", start + 1)
        journey = source[start:end]
        self.assertIn('"No matches for “Zucchini”"', journey)
        self.assertIn('"Try broadening your search"', journey)
        self.assertIn("Apples:absent", journey)
        self.assertIn("wait:250ms", journey)
        self.assertNotIn("wait:300ms", journey)
        self.assertNotRegex(journey, r"assert:\s*\[[^\n]*,\s*Zucchini\s*,")

    def test_cross_page_image_journeys_use_the_rendered_collection_qualified_ids(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        portrait_start = source.index("  - id: visual.image.crop.portrait-gingerbread-cart-to-detail")
        portrait_end = source.index("\n  - id:", portrait_start + 1)
        portrait = source[portrait_start:portrait_end]
        self.assertIn('"capture_region:snack.image.90.5:cartCrop"', portrait)
        self.assertIn('"capture_region:snack.image.5:detailCrop"', portrait)

        cart = (ETS_ROOT / "screens/CartScreen.ets").read_text(encoding="utf-8")
        self.assertIn("collectionId: 90", cart)
        snack_image = (ETS_ROOT / "components/SnackImage.ets").read_text(encoding="utf-8")
        self.assertIn("`snack.image.${this.collectionId}.${this.stableId}`", snack_image)

    def test_filter_reset_journey_enables_the_todo_action_before_clicking_it(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        start = source.index("  - id: core.filter.reset.noop")
        end = source.index("\n  - id:", start + 1)
        journey = source[start:end]
        rating_step = '"tap:filter.sort.rating"'
        reset_step = '"tap:action.filter.reset"'
        self.assertIn(rating_step, journey)
        self.assertIn(reset_step, journey)
        rating = journey.index(rating_step)
        reset = journey.index(reset_step)
        self.assertLess(rating, reset)
        self.assertIn('"filter.sort.rating:selected"', journey)
        self.assertIn('"action.filter.reset:enabled"', journey)

        filter_overlay = (ETS_ROOT / "screens/FilterOverlay.ets").read_text(encoding="utf-8")
        self.assertIn(".enabled(this.appStore.filterSort !== DEFAULT_FILTER_SORT)", filter_overlay)

    def test_every_action_mapping_executes_its_stable_id_in_the_named_journey(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        source = JOURNEYS.read_text(encoding="utf-8")
        missing: list[str] = []
        for mapping in manifest["mappings"]:
            if mapping["kind"] != "action":
                continue
            start = source.index(f"  - id: {mapping['journey']}")
            end = source.find("\n  - id:", start + 1)
            journey = source[start:] if end < 0 else source[start:end]
            steps = re.search(r"(?m)^    steps: \[(.*)\]$", journey)
            self.assertIsNotNone(steps, mapping["journey"])
            if mapping["stableId"] not in steps.group(1):
                missing.append(f"{mapping['id']}->{mapping['journey']}")
        self.assertEqual([], missing)

    def test_form_kit_migration_is_traceable_and_device_ready(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mappings = {mapping["id"]: mapping for mapping in manifest["mappings"]}
        expected = {
            "recent-orders-widget": ("component", "form.recentOrders", "core.form.recent-orders"),
            "recent-orders-title-cart": ("action", "form.action.cart.title", "core.form.title-cart"),
            "recent-orders-trailing-cart": ("action", "form.action.cart.1", "core.form.trailing-cart"),
        }
        for mapping_id, contract in expected.items():
            with self.subTest(mapping_id=mapping_id):
                mapping = mappings[mapping_id]
                self.assertEqual(contract, (mapping["kind"], mapping["stableId"], mapping["journey"]))
                self.assertEqual("implemented", mapping["status"])
                self.assertEqual("source-facts/android-widget.json", mapping["source"])

        journeys = set(
            re.findall(r"(?m)^  - id: ([a-zA-Z0-9_.-]+)$", JOURNEYS.read_text(encoding="utf-8"))
        )
        self.assertTrue(
            {
                "core.form.recent-orders",
                "core.form.title-cart",
                "core.form.trailing-cart",
                "edge.form.cart-cold-start",
                "edge.form.cart-warm-start",
                "edge.form.cart-repeated",
                "visual.form.2x2",
                "visual.form.2x4",
                "visual.form.4x4",
                "visual.dark.form.2x4",
                "visual.large-font.form.4x4",
                "visual.form.breakpoint.259x179",
                "visual.form.breakpoint.259x180",
                "visual.form.breakpoint.260x179",
                "visual.form.breakpoint.339x180",
                "visual.form.breakpoint.340x180",
                "visual.form.breakpoint.478x180",
                "visual.form.breakpoint.479x180",
                "visual.form.breakpoint.480x180",
                "visual.form.breakpoint.620x180",
                "visual.form.breakpoint.621x180",
            }.issubset(journeys)
        )

    def test_form_geometry_journeys_freeze_every_android_breakpoint_edge(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        expected = {
            "visual.form.breakpoint.259x179": ("layout:small", "titleBar:absent", "trailingCart:absent"),
            "visual.form.breakpoint.259x180": ("layout:small", "titleBar:visible", "titleText:empty"),
            "visual.form.breakpoint.260x179": ("layout:medium", "titleBar:absent", "images:visible"),
            "visual.form.breakpoint.339x180": ("layout:medium", "titleBar:visible", "trailingCart:absent"),
            "visual.form.breakpoint.340x180": ("layout:medium", "titleBar:visible", "trailingCart:visible"),
            "visual.form.breakpoint.478x180": ("layout:medium", "lanes:1", "trailingCart:visible"),
            "visual.form.breakpoint.479x180": ("layout:large", "lanes:2", "trailingCart:visible"),
            "visual.form.breakpoint.480x180": ("layout:large", "lanes:2", "trailingCart:absent"),
            "visual.form.breakpoint.620x180": ("layout:large", "lanes:2", "trailingCart:absent"),
            "visual.form.breakpoint.621x180": ("layout:large", "lanes:2", "trailingCart:visible"),
        }
        for journey_id, markers in expected.items():
            with self.subTest(journey_id=journey_id):
                start = source.index(f"  - id: {journey_id}")
                end = source.find("\n  - id:", start + 1)
                journey = source[start:] if end < 0 else source[start:end]
                width_height = journey_id.rsplit(".", 1)[1]
                self.assertIn(f'"form_size:{width_height}vp"', journey)
                for marker in markers:
                    self.assertIn(marker, journey)

    def test_every_form_journey_declares_physical_vp_geometry(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        starts = [match.start() for match in re.finditer(r"(?m)^  - id: ", source)]
        starts.append(len(source))
        missing: list[str] = []
        for index in range(len(starts) - 1):
            journey = source[starts[index]:starts[index + 1]]
            if "add_form:RecentOrdersForm" not in journey:
                continue
            journey_id = re.search(r"(?m)^  - id: ([a-zA-Z0-9_.-]+)$", journey)
            self.assertIsNotNone(journey_id)
            if re.search(r'"form_size:[0-9]+x[0-9]+vp"', journey) is None:
                missing.append(journey_id.group(1))
        self.assertEqual([], missing)

    def test_form_visual_journeys_freeze_glance_palette_and_geometry(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        expected = {
            "core.form.recent-orders": (
                "background:#E0F3FF",
                "item.background:#E8DEF8",
                "titleBar.height:48vp",
                "titleBar.paddingX:4vp",
            ),
            "visual.form.2x4": (
                "contentSpacing:16vp",
                "titleBar.maxLines:1",
            ),
            "visual.form.4x4": ("grid.gutter:4vp",),
            "visual.dark.form.2x4": (
                "background:#20333D",
                "item.background:#4A4458",
                "title:#E6E1E5",
                "supporting:#CCC2DC",
            ),
            "visual.large-font.form.4x4": (
                "titleBar.maxLines:1",
                "itemTitle.maxLines:2",
            ),
        }
        for journey_id, markers in expected.items():
            with self.subTest(journey_id=journey_id):
                start = source.index(f"  - id: {journey_id}")
                end = source.find("\n  - id:", start + 1)
                journey = source[start:] if end < 0 else source[start:end]
                for marker in markers:
                    self.assertIn(marker, journey)

        skill = SKILL.read_text(encoding="utf-8")
        quality_gates = QUALITY_GATES.read_text(encoding="utf-8")
        for marker in ("Android widgets", "Form Kit", "form_config.json"):
            self.assertIn(marker, skill)
        for marker in ("FormParam.WIDTH_KEY", "FormParam.HEIGHT_KEY", "onSizeChanged", "breakpoint - 1"):
            self.assertIn(marker, skill)
        for marker in (
            "Launcher",
            "resize",
            "title cart",
            "trailing cart",
            "physical width/height in vp",
            "one vp below, exactly at, and one vp above",
        ):
            self.assertIn(marker, quality_gates)

    def test_rtl_cart_swipe_journeys_change_the_runtime_locale_signal(self) -> None:
        source = JOURNEYS.read_text(encoding="utf-8")
        for journey_id in (
            "visual.rtl.cart-swipe-progress",
            "edge.rtl.cart-swipe-at-threshold",
            "edge.rtl.cart-swipe-opposite-direction",
        ):
            start = source.index(f"  - id: {journey_id}")
            end = source.find("\n  - id:", start + 1)
            journey = source[start:] if end < 0 else source[start:end]
            self.assertIn('"locale:ar"', journey)
            self.assertIn('"layout_direction:rtl"', journey)

    def test_journey_flow_tokens_with_colons_are_yaml_quoted(self) -> None:
        violations: list[str] = []
        for line_number, line in enumerate(JOURNEYS.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"\s+(?:setup|steps|assert):\s*\[(.*)\]\s*$", line)
            if match is None:
                continue
            items = re.findall(r'"(?:[^"\\]|\\.)*"|[^,]+', match.group(1))
            for item in items:
                token = item.strip()
                quoted = (
                    (token.startswith('"') and token.endswith('"')) or
                    (token.startswith("'") and token.endswith("'"))
                )
                if ":" in token and not quoted:
                    violations.append(f"line {line_number}: {token}")
        self.assertEqual([], violations)

    def test_skill_and_quality_gates_cover_locale_and_five_executor_determinism(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        for marker in (
            "system locale",
            "Intl.NumberFormat",
            "toLocaleUpperCase",
            "configuration change",
            "five independent Executor",
        ):
            with self.subTest(document="skill", marker=marker):
                self.assertIn(marker, skill)
        for marker in (
            "Unicode bidirectional",
            "currency symbol",
            "five independent Executor",
            "local five-Executor proxy",
            "hidden-case full score",
        ):
            with self.subTest(document="quality-gates", marker=marker):
                self.assertIn(marker, quality)


if __name__ == "__main__":
    unittest.main(verbosity=2)
