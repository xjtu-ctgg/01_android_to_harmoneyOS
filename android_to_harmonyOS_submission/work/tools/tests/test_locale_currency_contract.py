#!/usr/bin/env python3
"""Contracts for Android-equivalent locale currency and navigation casing."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ETS = ROOT / "entry/src/main/ets"
FACTS = ROOT / "source-facts/android-facts.json"
CURRENCY_SOURCE = ROOT / (
    "source-facts/android-source/app/src/main/java/"
    "com/example/jetsnack/ui/utils/Currency.kt"
)
HOME_SOURCE = ROOT / (
    "source-facts/android-source/app/src/main/java/"
    "com/example/jetsnack/ui/home/Home.kt"
)
FORMATTER = ETS / "utils/CurrencyFormatter.ets"
BOTTOM_NAV = ETS / "components/BottomNav.ets"
STRINGS = ROOT / "entry/src/main/resources/base/element/string.json"
JOURNEYS = ROOT / "journeys/core.yaml"
EXPECTED_REGION_CODES = set(
    "AC AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG "
    "BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK "
    "CL CM CN CO CP CR CU CV CW CX CY CZ DE DG DJ DK DM DO DZ EA EC EE EG "
    "EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ "
    "GR GS GT GU GW GY HK HM HN HR HT HU IC ID IE IL IM IN IO IQ IR IS IT "
    "JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT "
    "LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW "
    "MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL "
    "PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK "
    "SL SM SN SO SR SS ST SV SX SY SZ TA TC TD TF TG TH TJ TK TL TM TN TO "
    "TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT "
    "ZA ZM ZW"
    .split()
)


def formatter_region_codes(source: str) -> set[str]:
    return set(re.findall(r"case '([A-Z]{2})':", source))


class LocaleCurrencyContractTests(unittest.TestCase):
    def test_01_android_currency_and_uppercase_sources_are_frozen(self) -> None:
        self.assertTrue(CURRENCY_SOURCE.is_file(), "missing frozen Android Currency.kt")
        currency = CURRENCY_SOURCE.read_text(encoding="utf-8")
        home = HOME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("NumberFormat.getCurrencyInstance().format(", currency)
        self.assertIn("BigDecimal(price).movePointLeft(2)", currency)
        self.assertIn("uppercase(currentLocale)", home)

    def test_02_cldr_49_locale_contract_is_frozen(self) -> None:
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        self.assertIn("localeContract", facts)
        locale = facts["localeContract"]
        self.assertEqual("CLDR 49", locale["currencyDataVersion"])
        self.assertEqual(
            "https://unicode.org/cldr/charts/49/supplemental/"
            "detailed_territory_currency_information.html",
            locale["currencyDataSource"],
        )
        self.assertEqual("XXX", locale["unknownCurrency"])
        self.assertEqual(
            {
                "AC": "SHP",
                "AQ": "XXX",
                "BG": "EUR",
                "CP": "XXX",
                "CW": "XCG",
                "DG": "USD",
                "EA": "EUR",
                "IC": "EUR",
                "SX": "XCG",
                "TA": "GBP",
                "XK": "EUR",
                "ZW": "ZWG",
            },
            locale["specialTerritories"],
        )

    def test_03_formatter_uses_api20_global_intl_and_system_locale(self) -> None:
        self.assertTrue(FORMATTER.is_file(), "missing shared CurrencyFormatter.ets")
        source = FORMATTER.read_text(encoding="utf-8")
        self.assertIn("import { i18n } from '@kit.LocalizationKit';", source)
        self.assertIn("i18n.System.getSystemLocaleInstance().toString()", source)
        self.assertIn("new Intl.Locale(", source)
        self.assertIn(".maximize()", source)
        self.assertIn("new Intl.NumberFormat(", source)
        self.assertIn("style: 'currency'", source)
        self.assertIn("currency: currency", source)
        self.assertNotIn("intl.NumberFormat", source)
        self.assertNotIn("@ohos.intl", source)

    def test_04_formatter_has_complete_cldr_region_domain(self) -> None:
        self.assertTrue(FORMATTER.is_file(), "missing shared CurrencyFormatter.ets")
        source = FORMATTER.read_text(encoding="utf-8")
        self.assertEqual(EXPECTED_REGION_CODES, formatter_region_codes(source))
        self.assertIn("default:\n      return 'XXX';", source)

    def test_05_formatter_supports_unicode_currency_override(self) -> None:
        self.assertTrue(FORMATTER.is_file(), "missing shared CurrencyFormatter.ets")
        source = FORMATTER.read_text(encoding="utf-8")
        self.assertIn("extensionParts.indexOf('cu')", source)
        self.assertIn("unicodeParts.findIndex(", source)
        self.assertIn("isAsciiLowercaseCurrencyCode(candidate)", source)
        self.assertIn("candidate.length !== 3", source)
        self.assertEqual(3, source.count("candidate.charCodeAt("))
        self.assertIn("candidate.toUpperCase()", source)

    def test_06_screens_use_only_the_shared_formatter(self) -> None:
        expected_calls = {
            "CartScreen.ets": 4,
            "SearchScreen.ets": 1,
            "DetailScreen.ets": 1,
        }
        for filename, minimum_calls in expected_calls.items():
            with self.subTest(filename=filename):
                source = (ETS / "screens" / filename).read_text(encoding="utf-8")
                self.assertIn(
                    "import { formatPrice } from '../utils/CurrencyFormatter';",
                    source,
                )
                self.assertNotRegex(source, r"private\s+formatPrice\s*\(")
                self.assertNotIn("return `$${dollars}.${cents}`", source)
                self.assertGreaterEqual(source.count("formatPrice("), minimum_calls)

    def test_07_only_formatter_constructs_currency_number_format(self) -> None:
        owners = []
        for path in ETS.rglob("*.ets"):
            if "new Intl.NumberFormat(" in path.read_text(encoding="utf-8"):
                owners.append(path.relative_to(ETS).as_posix())
        self.assertEqual(["utils/CurrencyFormatter.ets"], owners)

    def test_08_navigation_keeps_source_case_and_uppercases_current_locale(self) -> None:
        values = {
            item["name"]: item["value"]
            for item in json.loads(STRINGS.read_text(encoding="utf-8"))["string"]
        }
        self.assertEqual("Home", values["home_feed_navigation"])
        self.assertEqual("Search", values["home_search_navigation"])
        self.assertEqual("My Cart", values["home_cart_navigation"])
        self.assertEqual("Profile", values["home_profile_navigation"])
        source = BOTTOM_NAV.read_text(encoding="utf-8")
        self.assertIn("i18n.System.getSystemLocaleInstance().toString()", source)
        self.assertIn("getStringSync(item.label.id)", source)
        self.assertIn("toLocaleUpperCase(localeTag)", source)
        self.assertIn("Text(this.localizedLabel(item))", source)
        self.assertIn(".accessibilityText(this.localizedLabel(item))", source)
        self.assertEqual(1, source.count("private localizedLabel("))

    def test_09_locale_journeys_cover_prices_navigation_and_state(self) -> None:
        text = JOURNEYS.read_text(encoding="utf-8")
        required = (
            "locale.currency.en_us.all_surfaces",
            "locale.currency.en_gb.all_surfaces",
            "locale.currency.de_de.cart",
            "locale.currency.ja_jp.detail",
            "locale.currency.ar_eg.rtl",
            "locale.currency.tr_tr.navigation",
            "locale.currency.language_only_ar",
            "locale.currency.unknown_territory",
            "locale.currency.runtime_switch_preserves_state",
        )
        for journey_id in required:
            with self.subTest(journey_id=journey_id):
                self.assertIn(f"id: {journey_id}", text)
        self.assertIn("set_locale", text)
        self.assertIn("PROFİLE", text)
        self.assertIn("quantity.5:3", text)
        self.assertIn("currency:XXX", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
