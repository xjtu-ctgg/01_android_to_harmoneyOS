# Locale Currency Parity and Five-Executor Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 复刻 Android Jetsnack 的系统地区货币格式和 locale-aware 导航大写，并用与平台真实轨迹一致的五个独立 Executor 验证交付复现、产物和完整本地代理用例集的稳定性。

**Architecture:** 新建一个无状态 `CurrencyFormatter.ets`，以 HarmonyOS API 20 全局 `Intl`、系统 locale 和冻结 CLDR 49 territory→currency 表生成价格文本；Cart、Search、Detail 只依赖该入口。`BottomNav` 在资源解析后按系统 locale 大写。Python 合同冻结 Android/CLDR 事实并检查单一接线，`five_executor_verify.py` 从只读提交包创建五个独立工作目录，逐裁判执行同一验证并汇总交集/最佳结果。

**Tech Stack:** ArkTS、ArkUI、Localization Kit、ECMAScript Intl、HarmonyOS/OpenHarmony API 20、Python 3.10+ `unittest`/`zipfile`/`subprocess`、YAML Journey、Hvigor 6.20.0。

---

## 文件职责

- `work/source-facts/android-source/app/src/main/java/com/example/jetsnack/ui/utils/Currency.kt`：保存固定 Android 节点的原始价格格式化源码。
- `work/source-facts/android-facts.json`：冻结 Android locale 语义和 CLDR 49 货币数据版本、来源、特殊地区。
- `work/tools/tests/test_locale_currency_contract.py`：验证源事实、完整映射、单一 formatter、三屏接线、导航、配置更新和 Journey。
- `work/entry/src/main/ets/utils/CurrencyFormatter.ets`：唯一运行时货币格式化实现。
- `work/entry/src/main/ets/screens/{CartScreen,SearchScreen,DetailScreen}.ets`：移除局部美元拼接，统一调用 formatter。
- `work/entry/src/main/ets/components/BottomNav.ets`：解析资源并按当前 locale 大写显示/无障碍标签。
- `work/entry/src/main/resources/base/element/string.json`：导航资源恢复为 Android 源 title case。
- `work/journeys/core.yaml`：补充多 locale、动态切换和状态保持的设备合同。
- `work/tools/five_executor_verify.py`：模拟只读 package root、五个独立 Executor、复现审查和结果汇总。
- `work/tools/tests/test_five_executor_verify.py`：验证安全解压、只读输入、五次独立执行、失败传播和汇总公式。
- `INSTRUCTION.md`：明确平台每个 Executor 的幂等复现协议、完成判定和仓位置。
- `docs/鸿蒙化实现方法与进展.md`：记录本轮红—绿、五裁判、构建和证据边界。

## 约束

- 用户已批准 `docs/superpowers/specs/2026-07-13-locale-currency-parity-design.md`，并要求后续自行审批推进。
- 平台模型以 `/Users/ctgg/master/code/learn/ICT_software/log7_9.md` 为实证：五个 `executor_1..5` 各自复现并各跑完整 case 集，不是五个质量维度。
- 不 commit、不 push、不上传；所有交付改动只在当前目录和 `work/`。
- 不引入网络、OHPM 三方包、汇率换算或废弃 `@ohos.intl.NumberFormat`。
- 每个生产改动先出现针对性失败，再最小转绿；不得先写实现后补测试。

### Task 1: 冻结 Android/CLDR 事实并建立红色合同

**Files:**
- Create: `work/source-facts/android-source/app/src/main/java/com/example/jetsnack/ui/utils/Currency.kt`
- Modify: `work/source-facts/android-facts.json`
- Create: `work/tools/tests/test_locale_currency_contract.py`

- [x] **Step 1: 先创建失败合同测试**

创建测试常量和首批测试：

```python
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


class LocaleCurrencyContractTests(unittest.TestCase):
    def test_01_android_currency_and_uppercase_sources_are_frozen(self) -> None:
        currency = CURRENCY_SOURCE.read_text(encoding="utf-8")
        home = HOME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("NumberFormat.getCurrencyInstance().format(", currency)
        self.assertIn("BigDecimal(price).movePointLeft(2)", currency)
        self.assertIn("uppercase(currentLocale)", home)

    def test_02_cldr_49_locale_contract_is_frozen(self) -> None:
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        locale = facts["localeContract"]
        self.assertEqual("CLDR 49", locale["currencyDataVersion"])
        self.assertEqual(
            "https://unicode.org/cldr/charts/49/supplemental/"
            "detailed_territory_currency_information.html",
            locale["currencyDataSource"],
        )
        self.assertEqual("XXX", locale["unknownCurrency"])
        self.assertEqual(
            {"AC": "SHP", "AQ": "XXX", "BG": "EUR", "CP": "XXX",
             "CW": "XCG", "DG": "USD", "EA": "EUR", "IC": "EUR",
             "SX": "XCG", "TA": "GBP", "XK": "EUR", "ZW": "ZWG"},
            locale["specialTerritories"],
        )
```

- [x] **Step 2: 运行测试确认因事实缺失而失败**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_locale_currency_contract -v
```

Expected: FAIL，原因只应是 `Currency.kt` 或 `localeContract` 尚不存在。

- [x] **Step 3: 保存 Android 原始 Currency.kt**

写入固定节点的完整源码：

```kotlin
package com.example.jetsnack.ui.utils

import java.math.BigDecimal
import java.text.NumberFormat

fun formatPrice(price: Long): String {
    return NumberFormat.getCurrencyInstance().format(
        BigDecimal(price).movePointLeft(2),
    )
}
```

- [x] **Step 4: 在 android-facts.json 冻结 localeContract**

在根对象加入：

```json
"localeContract": {
  "androidCurrencySource": "source-facts/android-source/app/src/main/java/com/example/jetsnack/ui/utils/Currency.kt",
  "androidNavigationSource": "source-facts/android-source/app/src/main/java/com/example/jetsnack/ui/home/Home.kt",
  "currencyDataVersion": "CLDR 49",
  "currencyDataSource": "https://unicode.org/cldr/charts/49/supplemental/detailed_territory_currency_information.html",
  "amountSemantics": "price cents are divided by 100 without exchange-rate conversion",
  "languageOnlyLocale": "maximize to likely region",
  "unknownCurrency": "XXX",
  "specialTerritories": {
    "AC": "SHP", "AQ": "XXX", "BG": "EUR", "CP": "XXX",
    "CW": "XCG", "DG": "USD", "EA": "EUR", "IC": "EUR",
    "SX": "XCG", "TA": "GBP", "XK": "EUR", "ZW": "ZWG"
  }
}
```

- [x] **Step 5: 重跑聚焦测试**

Expected: `test_01`、`test_02` PASS；后续 formatter 测试尚未加入。

### Task 2: 为唯一 CurrencyFormatter 建立完整失败合同

**Files:**
- Modify: `work/tools/tests/test_locale_currency_contract.py`
- Create: `work/entry/src/main/ets/utils/CurrencyFormatter.ets`

- [x] **Step 1: 增加 formatter 结构和地区覆盖失败测试**

加入完整当前地区集合和测试：

```python
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

def test_03_formatter_uses_api20_global_intl_and_system_locale(self) -> None:
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
    source = FORMATTER.read_text(encoding="utf-8")
    self.assertEqual(EXPECTED_REGION_CODES, formatter_region_codes(source))
    self.assertIn("default:\n      return 'XXX';", source)

def test_05_formatter_supports_unicode_currency_override(self) -> None:
    source = FORMATTER.read_text(encoding="utf-8")
    self.assertIn("parts[index] === 'cu'", source)
    self.assertIn("candidate.length === 3", source)
    self.assertIn("candidate.toUpperCase()", source)
```

- [x] **Step 2: 运行并确认红色原因**

Expected: FAIL，因为 `CurrencyFormatter.ets` 尚不存在。

- [x] **Step 3: 创建 formatter 的解析与格式化骨架**

写入：

```ts
import { i18n } from '@kit.LocalizationKit';

function localeOrFallback(localeTag: string): Intl.Locale {
  try {
    return new Intl.Locale(localeTag);
  } catch {
  }
  try {
    return i18n.System.getSystemLocaleInstance();
  } catch {
    return new Intl.Locale('en-US');
  }
}

function currencyOverride(localeTag: string): string | undefined {
  const parts: string[] = localeTag.toLowerCase().split('-');
  const unicodeIndex: number = parts.indexOf('u');
  if (unicodeIndex < 0) {
    return undefined;
  }
  for (let index: number = unicodeIndex + 1; index < parts.length - 1; index += 1) {
    if (parts[index] === 'cu') {
      const candidate: string = parts[index + 1];
      if (candidate.length === 3 && /^[a-z]{3}$/.test(candidate)) {
        return candidate.toUpperCase();
      }
      return undefined;
    }
  }
  return undefined;
}

function currencyForRegion(region: string): string {
  switch (region.toUpperCase()) {
    default:
      return 'XXX';
  }
}

export function formatPriceForLocale(priceCents: number, localeTag: string): string {
  const locale: Intl.Locale = localeOrFallback(localeTag);
  const canonicalTag: string = locale.toString();
  let region: string = locale.region ?? '';
  if (region.length === 0) {
    region = locale.maximize().region ?? '';
  }
  const currency: string = currencyOverride(canonicalTag) ?? currencyForRegion(region);
  try {
    return new Intl.NumberFormat(canonicalTag, {
      style: 'currency',
      currency: currency
    }).format(priceCents / 100);
  } catch {
    return new Intl.NumberFormat(canonicalTag, {
      style: 'currency',
      currency: 'XXX'
    }).format(priceCents / 100);
  }
}

export function formatPrice(priceCents: number): string {
  return formatPriceForLocale(
    priceCents,
    i18n.System.getSystemLocaleInstance().toString()
  );
}
```

- [x] **Step 4: 补全 currencyForRegion 的 CLDR 49 switch**

将空 switch 替换为以下完整分组；每个地区必须保留独立 `case`，以便合同精确核对：

```ts
function currencyForRegion(region: string): string {
  switch (region.toUpperCase()) {
    case 'AE': return 'AED';
    case 'AF': return 'AFN';
    case 'AL': return 'ALL';
    case 'AM': return 'AMD';
    case 'AO': return 'AOA';
    case 'AR': return 'ARS';
    case 'AU': case 'CC': case 'CX': case 'HM': case 'KI': case 'NF': case 'NR': case 'TV': return 'AUD';
    case 'AW': return 'AWG';
    case 'AZ': return 'AZN';
    case 'BA': return 'BAM';
    case 'BB': return 'BBD';
    case 'BD': return 'BDT';
    case 'BH': return 'BHD';
    case 'BI': return 'BIF';
    case 'BM': return 'BMD';
    case 'BN': return 'BND';
    case 'BO': return 'BOB';
    case 'BR': return 'BRL';
    case 'BS': return 'BSD';
    case 'BT': return 'BTN';
    case 'BW': return 'BWP';
    case 'BY': return 'BYN';
    case 'BZ': return 'BZD';
    case 'CA': return 'CAD';
    case 'CD': return 'CDF';
    case 'CH': case 'LI': return 'CHF';
    case 'CL': return 'CLP';
    case 'CN': return 'CNY';
    case 'CO': return 'COP';
    case 'CR': return 'CRC';
    case 'CU': return 'CUP';
    case 'CV': return 'CVE';
    case 'CZ': return 'CZK';
    case 'DJ': return 'DJF';
    case 'DK': case 'FO': case 'GL': return 'DKK';
    case 'DO': return 'DOP';
    case 'DZ': return 'DZD';
    case 'EG': return 'EGP';
    case 'ER': return 'ERN';
    case 'ET': return 'ETB';
    case 'AD': case 'AT': case 'AX': case 'BE': case 'BG': case 'BL': case 'CY': case 'DE': case 'EA':
    case 'EE': case 'ES': case 'FI': case 'FR': case 'GF': case 'GP': case 'GR': case 'HR': case 'IC': case 'IE':
    case 'IT': case 'LT': case 'LU': case 'LV': case 'MC': case 'ME': case 'MF': case 'MQ': case 'MT': case 'NL':
    case 'PM': case 'PT': case 'RE': case 'SI': case 'SK': case 'SM': case 'TF': case 'VA': case 'XK': case 'YT':
      return 'EUR';
    case 'FJ': return 'FJD';
    case 'FK': return 'FKP';
    case 'GB': case 'GG': case 'GS': case 'IM': case 'JE': case 'TA': return 'GBP';
    case 'GE': return 'GEL';
    case 'GH': return 'GHS';
    case 'GI': return 'GIP';
    case 'GM': return 'GMD';
    case 'GN': return 'GNF';
    case 'GT': return 'GTQ';
    case 'GY': return 'GYD';
    case 'HK': return 'HKD';
    case 'HN': return 'HNL';
    case 'HT': return 'HTG';
    case 'HU': return 'HUF';
    case 'ID': return 'IDR';
    case 'IL': case 'PS': return 'ILS';
    case 'IN': return 'INR';
    case 'IQ': return 'IQD';
    case 'IR': return 'IRR';
    case 'IS': return 'ISK';
    case 'JM': return 'JMD';
    case 'JO': return 'JOD';
    case 'JP': return 'JPY';
    case 'KE': return 'KES';
    case 'KG': return 'KGS';
    case 'KH': return 'KHR';
    case 'KM': return 'KMF';
    case 'KP': return 'KPW';
    case 'KR': return 'KRW';
    case 'KW': return 'KWD';
    case 'KY': return 'KYD';
    case 'KZ': return 'KZT';
    case 'LA': return 'LAK';
    case 'LB': return 'LBP';
    case 'LK': return 'LKR';
    case 'LR': return 'LRD';
    case 'LS': return 'LSL';
    case 'LY': return 'LYD';
    case 'EH': case 'MA': return 'MAD';
    case 'MD': return 'MDL';
    case 'MG': return 'MGA';
    case 'MK': return 'MKD';
    case 'MM': return 'MMK';
    case 'MN': return 'MNT';
    case 'MO': return 'MOP';
    case 'MR': return 'MRU';
    case 'MU': return 'MUR';
    case 'MV': return 'MVR';
    case 'MW': return 'MWK';
    case 'MX': return 'MXN';
    case 'MY': return 'MYR';
    case 'MZ': return 'MZN';
    case 'NA': return 'NAD';
    case 'NG': return 'NGN';
    case 'NI': return 'NIO';
    case 'BV': case 'NO': case 'SJ': return 'NOK';
    case 'NP': return 'NPR';
    case 'CK': case 'NU': case 'NZ': case 'PN': case 'TK': return 'NZD';
    case 'OM': return 'OMR';
    case 'PA': return 'PAB';
    case 'PE': return 'PEN';
    case 'PG': return 'PGK';
    case 'PH': return 'PHP';
    case 'PK': return 'PKR';
    case 'PL': return 'PLN';
    case 'PY': return 'PYG';
    case 'QA': return 'QAR';
    case 'RO': return 'RON';
    case 'RS': return 'RSD';
    case 'RU': return 'RUB';
    case 'RW': return 'RWF';
    case 'SA': return 'SAR';
    case 'SB': return 'SBD';
    case 'SC': return 'SCR';
    case 'SD': return 'SDG';
    case 'SE': return 'SEK';
    case 'SG': return 'SGD';
    case 'AC': case 'SH': return 'SHP';
    case 'SL': return 'SLE';
    case 'SO': return 'SOS';
    case 'SR': return 'SRD';
    case 'SS': return 'SSP';
    case 'ST': return 'STN';
    case 'SV': return 'SVC';
    case 'SY': return 'SYP';
    case 'SZ': return 'SZL';
    case 'TH': return 'THB';
    case 'TJ': return 'TJS';
    case 'TM': return 'TMT';
    case 'TN': return 'TND';
    case 'TO': return 'TOP';
    case 'TR': return 'TRY';
    case 'TT': return 'TTD';
    case 'TW': return 'TWD';
    case 'TZ': return 'TZS';
    case 'UA': return 'UAH';
    case 'UG': return 'UGX';
    case 'AS': case 'BQ': case 'DG': case 'EC': case 'FM': case 'GU': case 'IO': case 'MH': case 'MP': case 'PR':
    case 'PW': case 'TC': case 'TL': case 'UM': case 'US': case 'VG': case 'VI': return 'USD';
    case 'UY': return 'UYU';
    case 'UZ': return 'UZS';
    case 'VE': return 'VES';
    case 'VN': return 'VND';
    case 'VU': return 'VUV';
    case 'WS': return 'WST';
    case 'CF': case 'CG': case 'CM': case 'GA': case 'GQ': case 'TD': return 'XAF';
    case 'AG': case 'AI': case 'DM': case 'GD': case 'KN': case 'LC': case 'MS': case 'VC': return 'XCD';
    case 'CW': case 'SX': return 'XCG';
    case 'BF': case 'BJ': case 'CI': case 'GW': case 'ML': case 'NE': case 'SN': case 'TG': return 'XOF';
    case 'NC': case 'PF': case 'WF': return 'XPF';
    case 'AQ': case 'CP': return 'XXX';
    case 'YE': return 'YER';
    case 'ZA': return 'ZAR';
    case 'ZM': return 'ZMW';
    case 'ZW': return 'ZWG';
    default:
      return 'XXX';
  }
}
```

- [x] **Step 5: 运行聚焦合同并修正纯类型/格式问题**

Expected: `test_03..05` PASS，地区集合无缺失、无多余。

- [x] **Step 6: 运行 API 20 聚焦编译**

Run:

```bash
cd work
tools/verify.sh --build
```

Expected: ArkTS 编译和 HAP assemble PASS；若编译器对 `Intl.Locale` 类型或正则语法有正式限制，只调整类型表达，不改变 locale/货币语义，并同步合同。

### Task 3: 将 Cart、Search、Detail 全部接到统一 formatter

**Files:**
- Modify: `work/tools/tests/test_locale_currency_contract.py`
- Modify: `work/entry/src/main/ets/screens/CartScreen.ets`
- Modify: `work/entry/src/main/ets/screens/SearchScreen.ets`
- Modify: `work/entry/src/main/ets/screens/DetailScreen.ets`
- Modify: `work/tools/tests/test_cart_detail_filter_contract.py`
- Modify: `work/tools/tests/test_search_contract.py`

- [x] **Step 1: 先增加单一实现与全调用点失败测试**

```python
def test_06_screens_use_only_the_shared_formatter(self) -> None:
    expected_calls = {"CartScreen.ets": 4, "SearchScreen.ets": 1, "DetailScreen.ets": 1}
    for filename, minimum_calls in expected_calls.items():
        source = (ETS / "screens" / filename).read_text(encoding="utf-8")
        self.assertIn("import { formatPrice } from '../utils/CurrencyFormatter';", source)
        self.assertNotRegex(source, r"private\s+formatPrice\s*\(")
        self.assertNotIn("return `$${dollars}.${cents}`", source)
        self.assertGreaterEqual(source.count("formatPrice("), minimum_calls)

def test_07_only_formatter_constructs_currency_number_format(self) -> None:
    owners = []
    for path in ETS.rglob("*.ets"):
        if "new Intl.NumberFormat(" in path.read_text(encoding="utf-8"):
            owners.append(path.relative_to(ETS).as_posix())
    self.assertEqual(["utils/CurrencyFormatter.ets"], owners)
```

- [x] **Step 2: 运行并确认因三屏仍有局部实现而失败**

Expected: FAIL，显示三个 Screen 缺共享 import 且仍有 private formatter。

- [x] **Step 3: 最小替换三屏实现**

每个 Screen 加入：

```ts
import { formatPrice } from '../utils/CurrencyFormatter';
```

删除各自 `private formatPrice()`，并将所有 `this.formatPrice(...)` 改为 `formatPrice(...)`。Cart 必须覆盖行价、
subtotal、shipping、total；Search 覆盖结果行；Detail 覆盖主价格。

- [x] **Step 4: 更新旧测试的调用点断言**

把旧测试中 `Text(this.formatPrice` 改为 `Text(formatPrice`，保持原先相对顺序和全部价格位置断言。

- [x] **Step 5: 运行聚焦测试**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_locale_currency_contract \
  work.tools.tests.test_cart_detail_filter_contract \
  work.tools.tests.test_search_contract -v
```

Expected: PASS。

### Task 4: 恢复 locale-aware BottomNav 大写

**Files:**
- Modify: `work/tools/tests/test_locale_currency_contract.py`
- Modify: `work/entry/src/main/ets/components/BottomNav.ets`
- Modify: `work/entry/src/main/resources/base/element/string.json`
- Modify: `work/tools/tests/test_resource_data.py`

- [x] **Step 1: 先增加资源、土耳其语和无障碍失败合同**

```python
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
    self.assertIn("Text(localizedLabel)", source)
    self.assertIn(".accessibilityText(localizedLabel)", source)
    self.assertEqual(1, source.count("private localizedLabel("))
```

- [x] **Step 2: 运行并确认当前全大写资源导致失败**

Expected: FAIL，当前资源仍为 `HOME/SEARCH/MY CART/PROFILE` 且组件未读取 locale。

- [x] **Step 3: 修改导航项和标签函数**

给 `BottomNavItem` 增加 `fallbackLabel: string`，四项分别为 `Home`、`Search`、`My Cart`、`Profile`；引入：

```ts
import { i18n } from '@kit.LocalizationKit';
```

增加：

```ts
private localizedLabel(item: BottomNavItem): string {
  const localeTag: string = i18n.System.getSystemLocaleInstance().toString();
  let label: string = item.fallbackLabel;
  const hostContext = this.getUIContext().getHostContext();
  if (hostContext !== undefined) {
    try {
      label = hostContext.resourceManager.getStringSync(item.label.id);
    } catch {
    }
  }
  return label.toLocaleUpperCase(localeTag);
}
```

在 `navItem()` 顶部计算：

```ts
const localizedLabel: string = this.localizedLabel(item);
```

把可见 `Text(item.label)` 和 `.accessibilityText(item.label)` 都替换为 `localizedLabel`。

- [x] **Step 4: 将四个资源恢复 title case**

```json
{"name": "home_feed_navigation", "value": "Home"},
{"name": "home_search_navigation", "value": "Search"},
{"name": "home_cart_navigation", "value": "My Cart"},
{"name": "home_profile_navigation", "value": "Profile"}
```

同步旧资源测试，使它断言资源保持 source case、运行时负责 uppercase，而不是直接要求资源全大写。

- [x] **Step 5: 运行 locale、resource、root-tab 聚焦测试**

Expected: PASS，且英文渲染合同仍为大写，土耳其语路径可生成 `PROFİLE`。

- [x] **Step 6: 运行 API 20 构建验证 ResourceManager 调用非废弃**

Expected: 编译 PASS；源码不得使用 API 20 已废弃的 `getStringSync(Resource)` 重载，只传 `item.label.id`。

### Task 5: 增加多 locale 与配置切换 Journey

**Files:**
- Modify: `work/tools/tests/test_locale_currency_contract.py`
- Modify: `work/journeys/core.yaml`
- Modify: `work/tools/tests/test_workflow_contract.py`

- [x] **Step 1: 先增加 Journey ID 和关键动作失败测试**

```python
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
        self.assertIn(f"id: {journey_id}", text)
    self.assertIn("set_locale", text)
    self.assertIn("PROFİLE", text)
    self.assertIn("quantity.5:3", text)
    self.assertIn("currency:XXX", text)
```

- [x] **Step 2: 运行并确认 Journey 缺失**

Expected: FAIL，九个 Journey 尚不存在。

- [x] **Step 3: 添加九个 Journey**

每个 Journey 使用现有 schema 的 `setup`、`steps`、`assert` 和 `screenshot` 字段，在步骤中使用
`launch`、`tap:*`、`set_locale:*` 等动作；分别覆盖三屏金额、德国符号后置、日本零小数、阿拉伯 RTL、土耳其 `PROFİLE`、
language-only likely region、`XXX` fallback，以及 locale 切换前后的 currentRoute/cart quantities/detail selection。
所有 locale/theme/fontScale/viewport 必须显式声明；截图 checkpoint 等待本地字体和图片稳定，不使用时钟或随机 ID。

- [x] **Step 4: 更新 workflow 合同并运行标准 YAML 解析**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
payload = yaml.safe_load(Path('work/journeys/core.yaml').read_text())
assert isinstance(payload, dict)
print(len(payload['journeys']))
PY
```

Expected: YAML 可解析，Journey 数量增加 9；相关 unittest PASS。

### Task 6: 实现真实平台轨迹的五 Executor 模拟器

**Files:**
- Create: `work/tools/five_executor_verify.py`
- Create: `work/tools/tests/test_five_executor_verify.py`

- [x] **Step 1: 先写安全解压与五裁判失败测试**

测试以临时 ZIP 和假的 `verify.sh` 建立最小交付，要求：

```python
class FiveExecutorVerifyTests(unittest.TestCase):
    def test_success_runs_same_case_suite_in_five_isolated_directories(self) -> None:
        result = run_harness(self.make_archive(exit_code=0), "--static")
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(5, len(summary["executors"]))
        self.assertTrue(all(item["success"] for item in summary["executors"]))
        self.assertTrue(all(item["artifact_valid"] for item in summary["executors"]))
        self.assertEqual(5, summary["stability_passed_cases"])
        self.assertEqual(5, summary["accuracy_passed_cases"])

    def test_failure_in_one_executor_fails_stability_and_process(self) -> None:
        result = run_harness(self.make_archive(fail_executor=3), "--static")
        self.assertNotEqual(0, result.returncode)
        self.assertIn('"name": "executor_3"', result.stdout)

    def test_rejects_zip_slip_and_wrong_top_level_entries(self) -> None:
        self.assertRejected("../escape")
        self.assertRejected("extra.txt")
```

- [x] **Step 2: 运行并确认脚本缺失导致失败**

Expected: FAIL，`five_executor_verify.py` 尚不存在。

- [x] **Step 3: 实现 CLI 与安全解压**

CLI：

```text
python3 work/tools/five_executor_verify.py \
  --archive android_to_harmonyOS_submission.zip \
  --mode static|build \
  [--keep-workdirs PATH]
```

实现必须使用 `zipfile.Path`/`ZipInfo` 逐项拒绝绝对路径、`..`、符号链接和顶层非
`INSTRUCTION.md`/`work/` 条目；解压到 `TemporaryDirectory`，把 `package_root` 权限改为只读，然后为
`executor_1..5` 各自复制一份可写工作目录。

- [x] **Step 4: 实现交付审查和每裁判复现**

每个 Executor 必须验证：

```python
REQUIRED_ARTIFACTS = (
    "INSTRUCTION.md",
    "work/AppScope/app.json5",
    "work/entry/src/main/module.json5",
    "work/entry/src/main/ets/pages/Index.ets",
    "work/skills/android-to-harmonyos/SKILL.md",
    "work/tools/verify.sh",
)
```

并从自己的工作目录执行 `work/tools/verify.sh --static` 或 `--build`。解析 unittest 输出的
`Ran N tests` 和 Journey `id:` 数，保存退出码、`artifact_valid`、`case_count`、stdout 摘要、源码树摘要；
build 模式还要求非空 HAP。

- [x] **Step 5: 实现五裁判汇总**

脚本最后输出单行 JSON，字段固定为：

```json
{
  "executor_count": 5,
  "case_count": 0,
  "stability_passed_cases": 0,
  "accuracy_passed_cases": 0,
  "all_artifacts_valid": false,
  "all_source_trees_equal": false,
  "executors": []
}
```

本地代理 case 全部由同一 `verify.sh` 给出，因此某裁判退出 0 时该裁判通过 `case_count`，否则为 0；稳定值
是五个通过集合的交集，准确值是最大通过数。任一裁判失败、产物无效、case_count 不一致或源码摘要不一致时
CLI 退出非 0。

- [x] **Step 6: 运行聚焦测试和一份真实 ZIP 静态五裁判演练**

Expected: unit tests PASS；真实 ZIP 的五个 Executor 全部 success、artifact_valid、相同 case_count。

### Task 7: 更新平台执行说明、Skill 与进展文档

**Files:**
- Modify: `INSTRUCTION.md`
- Modify: `work/skills/android-to-harmonyos/SKILL.md`
- Modify: `work/skills/android-to-harmonyos/references/quality-gates.md`
- Modify: `docs/鸿蒙化实现方法与进展.md`
- Modify: `work/tools/tests/test_delivery_contract.py`
- Modify: `work/tools/tests/test_workflow_contract.py`

- [x] **Step 1: 先增加平台轨迹合同**

测试要求 INSTRUCTION 同时包含：只读输入包、每个 Executor 在自己的目录工作、验证通过不随机重写、
`work/` 最终仓、退出码/HAP/必要源码完成判定、Skill 标准路径，以及五次执行不共享缓存/状态。

- [x] **Step 2: 运行并确认现有说明缺少五 Executor/只读语义**

Expected: FAIL，但原有环境、执行、完成判定、结果路径测试继续通过。

- [x] **Step 3: 修改 INSTRUCTION**

在“平台 Agent 执行协议”明确：

1. `package_root` 可能只读，绝不原地写顶层输入包；
2. 每个 Executor 在自己的可写任务目录使用 `work/`；
3. 已完成仓先验证，成功则不随机重写；
4. 只有真实平台环境暴露编译/规范错误时才做最小确定性修复；
5. 每次都用相同 `tools/verify.sh --build` 完成判定；
6. 不让单个 Executor 再启动五重模拟器，`five_executor_verify.py` 仅供参赛者本地交付预演。

- [x] **Step 4: 更新 Skill/quality-gates**

增加系统 locale、货币、Unicode 双向文本、locale-aware case mapping、运行时配置更新和五 Executor
确定性规则；禁止把本地五裁判代理运行称为真实平台满分。

- [x] **Step 5: 更新进展文档**

记录 Android 源事实、CLDR 49 来源、红—绿测试数、五 Executor 结果、API20 构建/HAP、ZIP 复验和仍缺的
正式 HarmonyOS Code Linter/设备截图/真实隐藏用例证据。

### Task 8: 全量回归、五裁判冷构建与最终 ZIP

**Files:**
- Modify: `docs/superpowers/plans/2026-07-13-locale-currency-five-executor.md`
- Regenerate: `android_to_harmonyOS_submission.zip`

- [x] **Step 1: 运行全量静态门禁**

```bash
cd work
tools/verify.sh --static
```

Expected: 所有合同 PASS；记录准确的 test count 与 Journey count。

- [x] **Step 2: 运行 API 20 完整构建**

```bash
cd work
tools/verify.sh --build
```

Expected: `status=passed`、非空 `entry-default-unsigned.hap`、`build_scope` 明确。

- [x] **Step 3: 做规范负面扫描**

扫描新增 ArkTS，不得有 `any`、`unknown`、`ESObject`、`export *`、废弃 intl、硬编码美元、局部 formatter、
绝对个人路径、网络或随机逻辑。若官方 Code Linter 不存在，只能记录“未验证”，不能宣称严格扫描通过。

- [x] **Step 4: 清理交付副本并重建 ZIP**

ZIP 顶层严格只有 `INSTRUCTION.md` 和 `work/`；排除 `.git`、`.hvigor`、`oh_modules`、`build/`、
`__pycache__`、`.DS_Store`、工具链和旧 ZIP。不得多包 `demo-Jetsnack-android/` 层。

- [x] **Step 5: 将 ZIP 标记只读并运行五 Executor build 模式**

```bash
python3 work/tools/five_executor_verify.py \
  --archive android_to_harmonyOS_submission.zip \
  --mode build
```

Expected: `executor_count=5`，五个 success，五个 `artifact_valid=true`，相同非零 `case_count`，稳定与准确代理
通过数均等于 case_count，五份源码树摘要相同。

- [x] **Step 6: 再做一份全新解压人工审计**

检查 ZIP 条目、banned files、INSTRUCTION 四段、Skill 路径、必要工程文件、HAP 构建结果；从解压目录运行
`tools/verify.sh --build`，不得复用当前 work 的产物。

- [x] **Step 7: 自审计划完成情况并勾选所有任务**

逐项对照设计第 1–10 节；搜索计划中的未勾选框、占位词和签名不一致。只有全部证据存在时才报告本地可交付；
隐藏用例满分仍等待平台五个真实裁判返回。
