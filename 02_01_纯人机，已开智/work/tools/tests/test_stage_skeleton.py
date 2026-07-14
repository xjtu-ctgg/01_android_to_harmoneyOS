#!/usr/bin/env python3
"""Contract tests for the API 20 HarmonyOS Stage project skeleton."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(relative_path: str) -> dict[str, object]:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"missing project file: {relative_path}")
    return json.loads(path.read_text(encoding="utf-8"))


class StageSkeletonTests(unittest.TestCase):
    def test_app_identity_is_stable(self) -> None:
        app = load_json("AppScope/app.json5")["app"]

        self.assertEqual("com.example.jetsnack", app["bundleName"])
        self.assertEqual("$media:app_icon", app["icon"])
        self.assertEqual("$string:app_name", app["label"])
        self.assertEqual(1_000_000, app["versionCode"])
        self.assertEqual("1.0.0", app["versionName"])

    def test_formal_product_targets_and_requires_harmonyos_api_20(self) -> None:
        profile = load_json("build-profile.json5")
        app = profile["app"]
        products = app["products"]

        self.assertEqual(1, len(products))
        self.assertEqual(
            {
                "name": "default",
                "signingConfig": "default",
                "compatibleSdkVersion": "6.0.0(20)",
                "targetSdkVersion": "6.0.0(20)",
                "runtimeOS": "HarmonyOS",
            },
            products[0],
        )
        self.assertEqual([], app["signingConfigs"])
        self.assertNotIn("compileSdkVersion", products[0])

    def test_project_declares_one_entry_module_and_no_external_dependencies(self) -> None:
        profile = load_json("build-profile.json5")
        self.assertEqual(
            [
                {
                    "name": "entry",
                    "srcPath": "./entry",
                    "targets": [
                        {
                            "name": "default",
                            "applyToProducts": ["default"],
                        }
                    ],
                }
            ],
            profile["modules"],
        )

        for relative_path in ("oh-package.json5", "entry/oh-package.json5"):
            package = load_json(relative_path)
            self.assertEqual({}, package["dependencies"], relative_path)
            self.assertEqual({}, package["devDependencies"], relative_path)
            self.assertEqual({}, package["dynamicDependencies"], relative_path)

    def test_entry_is_a_stage_hap_for_phone_and_tablet(self) -> None:
        module_profile = load_json("entry/build-profile.json5")
        self.assertEqual("stageMode", module_profile["apiType"])
        self.assertEqual([{"name": "default"}], module_profile["targets"])

        module = load_json("entry/src/main/module.json5")["module"]
        self.assertEqual("entry", module["name"])
        self.assertEqual("entry", module["type"])
        self.assertEqual("EntryAbility", module["mainElement"])
        self.assertEqual(["phone", "tablet"], module["deviceTypes"])
        self.assertEqual("$profile:main_pages", module["pages"])
        self.assertTrue(module["deliveryWithInstall"])
        self.assertFalse(module["installationFree"])

        self.assertEqual(1, len(module["abilities"]))
        ability = module["abilities"][0]
        self.assertEqual("EntryAbility", ability["name"])
        self.assertEqual("./ets/entryability/EntryAbility.ets", ability["srcEntry"])
        self.assertEqual("$media:app_icon", ability["icon"])
        self.assertEqual("$media:app_icon", ability["startWindowIcon"])
        self.assertEqual("$color:start_window_background", ability["startWindowBackground"])
        self.assertTrue(ability["exported"])
        self.assertEqual("auto_rotation", ability.get("orientation"))
        self.assertEqual("singleton", ability.get("launchType"))

    def test_entry_explicitly_supports_fullscreen_split_and_floating_windows(self) -> None:
        module = load_json("entry/src/main/module.json5")["module"]
        ability = module["abilities"][0]

        self.assertEqual(
            ["fullscreen", "split", "floating"],
            ability.get("supportWindowMode"),
        )

    def test_start_window_matches_android_icon_and_content_theme_backgrounds(self) -> None:
        expected_android_icon_hash = "828319b46fbc1e1d51b05f0e258394ea3b3f1ae253b970c3bb6f2032d8da2f63"
        for relative_path in (
            "AppScope/resources/base/media/app_icon.png",
            "entry/src/main/resources/base/media/app_icon.png",
        ):
            digest = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected_android_icon_hash, digest, relative_path)

        expected_backgrounds = {"base": "#FFFFFF", "dark": "#121212"}
        for theme, expected in expected_backgrounds.items():
            colors = load_json(f"entry/src/main/resources/{theme}/element/color.json")["color"]
            values = {item["name"]: item["value"] for item in colors}
            self.assertEqual(expected, values["start_window_background"], theme)
            self.assertEqual(values["page_background"], values["start_window_background"], theme)

    def test_hvigor_uses_official_app_and_hap_task_plugins(self) -> None:
        root_hvigor = (ROOT / "hvigorfile.ts").read_text(encoding="utf-8")
        entry_hvigor = (ROOT / "entry/hvigorfile.ts").read_text(encoding="utf-8")
        hvigor_config = load_json("hvigor/hvigor-config.json5")

        self.assertIn("import { appTasks } from '@ohos/hvigor-ohos-plugin';", root_hvigor)
        self.assertIn("system: appTasks", root_hvigor)
        self.assertIn("import { hapTasks } from '@ohos/hvigor-ohos-plugin';", entry_hvigor)
        self.assertIn("system: hapTasks", entry_hvigor)
        self.assertEqual("5.0.0", hvigor_config["modelVersion"])

    def test_required_resources_and_page_registry_are_complete(self) -> None:
        required_files = (
            "AppScope/resources/base/element/string.json",
            "AppScope/resources/base/media/app_icon.png",
            "entry/src/main/resources/base/element/string.json",
            "entry/src/main/resources/base/element/color.json",
            "entry/src/main/resources/base/element/float.json",
            "entry/src/main/resources/base/media/app_icon.png",
            "entry/src/main/resources/base/profile/main_pages.json",
        )
        for relative_path in required_files:
            with self.subTest(path=relative_path):
                path = ROOT / relative_path
                self.assertTrue(path.is_file(), f"missing resource: {relative_path}")
                self.assertGreater(path.stat().st_size, 0, f"empty resource: {relative_path}")

        self.assertEqual(
            ["pages/Index"],
            load_json("entry/src/main/resources/base/profile/main_pages.json")["src"],
        )
        colors = load_json("entry/src/main/resources/base/element/color.json")["color"]
        self.assertIn(
            {"name": "start_window_background", "value": "#FFFFFF"},
            colors,
        )

    def test_entry_ability_loads_index_defensively_and_sets_theme_aware_system_bars(self) -> None:
        source = (ROOT / "entry/src/main/ets/entryability/EntryAbility.ets").read_text(
            encoding="utf-8"
        )

        self.assertRegex(source, r"import \{[^}]*\bUIAbility\b[^}]*\} from '@kit\.AbilityKit';")
        self.assertRegex(
            source,
            r"import \{[^}]*\bKeyboardAvoidMode\b[^}]*\bwindow\b[^}]*\} from '@kit\.ArkUI';",
        )
        self.assertIn("import { hilog } from '@kit.PerformanceAnalysisKit';", source)
        self.assertIn("onWindowStageCreate(windowStage: window.WindowStage): void", source)
        self.assertIn("try {", source)
        self.assertIn("windowStage.loadContent('pages/Index')", source)
        self.assertIn("catch", source)
        self.assertIn("hilog.error", source)
        self.assertIn("setWindowLayoutFullScreen(true)", source)
        self.assertIn("getUIContext().setKeyboardAvoidMode(KeyboardAvoidMode.RESIZE)", source)
        self.assertIn("setWindowSystemBarProperties", source)
        self.assertIn("statusBarContentColor: contentColor", source)
        self.assertIn("'#FFFFFF' : '#000000'", source)
        self.assertIn("onConfigurationUpdate(newConfig: Configuration)", source)

    def test_cart_deep_link_is_declared_and_routed_on_cold_launch(self) -> None:
        module = load_json("entry/src/main/module.json5")["module"]
        skills = module["abilities"][0]["skills"]
        deep_links = [
            uri
            for skill in skills
            for uri in skill.get("uris", [])
            if uri.get("scheme") == "https"
        ]
        self.assertIn(
            {"scheme": "https", "host": "jetsnack.example.com", "path": "home/cart"},
            deep_links,
        )
        ability = (ROOT / "entry/src/main/ets/entryability/EntryAbility.ets").read_text(
            encoding="utf-8"
        )
        index = (ROOT / "entry/src/main/ets/pages/Index.ets").read_text(encoding="utf-8")
        self.assertIn("https://jetsnack.example.com/home/cart", ability)
        self.assertIn("AppStorage.setOrCreate", ability)
        self.assertIn("@StorageProp('initialRoute')", index)
        self.assertIn("this.appStore.selectTab(this.initialRoute)", index)

    def test_index_exposes_stable_root_contract(self) -> None:
        source = (ROOT / "entry/src/main/ets/pages/Index.ets").read_text(encoding="utf-8")

        self.assertIn("@Entry", source)
        self.assertIn("@Component", source)
        self.assertIn("FeedScreen({ appStore: this.appStore })", source)
        self.assertIn("BottomNav({", source)
        self.assertIn(".id('screen.root')", source)
        self.assertIn(".accessibilityText($r('app.string.app_name'))", source)
        self.assertNotIn(": any", source)
        self.assertNotIn("=> {}", source)

    def test_deep_link_routing_accepts_suffixes_and_replays_identical_warm_wants(self) -> None:
        ability = (ROOT / "entry/src/main/ets/entryability/EntryAbility.ets").read_text(
            encoding="utf-8"
        )
        index = (ROOT / "entry/src/main/ets/pages/Index.ets").read_text(encoding="utf-8")

        self.assertIn("private publishRoute(want: Want): void", ability)
        self.assertIn("want.uri", ability)
        self.assertIn("indexOf('?')", ability)
        self.assertIn("indexOf('#')", ability)
        self.assertIn("substring(0, routeEnd)", ability)
        self.assertNotIn("want.uri === CART_DEEP_LINK", ability)
        self.assertGreaterEqual(ability.count("this.publishRoute(want);"), 2)
        self.assertIn("AppStorage.setOrCreate<string>('initialRoute'", ability)
        self.assertIn("AppStorage.setOrCreate<number>('navigationRequestId'", ability)

        self.assertIn("@StorageProp('navigationRequestId')", index)
        self.assertIn("@Watch('onNavigationRequestChanged')", index)
        watcher_start = index.find("private onNavigationRequestChanged(): void")
        watcher_end = index.find("aboutToAppear(): void", watcher_start)
        self.assertGreater(watcher_start, 0)
        self.assertGreater(watcher_end, watcher_start)
        self.assertIn("this.appStore.selectTab(this.initialRoute);", index[watcher_start:watcher_end])

    def test_empty_warm_launcher_want_preserves_the_existing_navigation_task(self) -> None:
        ability = (ROOT / "entry/src/main/ets/entryability/EntryAbility.ets").read_text(
            encoding="utf-8"
        )
        self.assertIn("private publishWarmRoute(want: Want): void", ability)
        warm_start = ability.index("private publishWarmRoute(want: Want): void")
        warm_end = ability.index("onCreate(want: Want", warm_start)
        warm_route = ability[warm_start:warm_end]
        self.assertIn("if (this.routeForWant(want) !== ROUTE_CART)", warm_route)
        self.assertIn("return;", warm_route)
        self.assertIn("this.publishRoute(want);", warm_route)
        new_want_start = ability.index("onNewWant(want: Want")
        new_want_end = ability.index("onConfigurationUpdate", new_want_start)
        new_want = ability[new_want_start:new_want_end]
        self.assertIn("this.publishWarmRoute(want);", new_want)
        self.assertNotIn("this.publishRoute(want);", new_want)

    def test_system_back_handles_overlay_detail_and_secondary_tabs_in_order(self) -> None:
        source = (ROOT / "entry/src/main/ets/pages/Index.ets").read_text(encoding="utf-8")
        start = source.find("onBackPress(): boolean")
        end = source.find("@Builder", start)
        self.assertGreater(start, 0, "missing typed @Entry back handler")
        self.assertGreater(end, start)
        handler = source[start:end]

        ordered_tokens = (
            "this.appStore.filterVisible",
            "this.appStore.hideFilters();",
            "this.appStore.currentRoute === ROUTE_DETAIL",
            "this.appStore.goBack();",
            "this.appStore.currentRoute !== ROUTE_FEED",
            "this.appStore.selectTab(ROUTE_FEED);",
            "return false;",
        )
        cursor = 0
        for token in ordered_tokens:
            with self.subTest(token=token):
                token_index = handler.find(token, cursor)
                self.assertGreaterEqual(token_index, cursor, f"missing/out-of-order back branch: {token}")
                cursor = token_index + len(token)
        self.assertEqual(3, handler.count("return true;"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
