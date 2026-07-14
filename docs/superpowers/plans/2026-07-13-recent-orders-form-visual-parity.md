# RecentOrders Form 视觉同源修订 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已完成的 RecentOrders Form Kit 卡片进一步对齐固定 Android 源码与 Glance 1.2.0-rc01 的标题栏、矢量图标、内容间距、双列 gutter 和确定性浅/深色回退调色板，并保持现有功能、构建与交付合同不退化。

**Architecture:** 继续保留单 `entry` 模块和既有 Form 生命周期/路由；只在 Form 页面引用五个卡片专用颜色资源和一个精确标题购物车矢量，不影响主应用主题。Android 源视觉事实冻结在 `android-widget.json`，由 Python 合同、现有设备 Journey、API 20 编译和全新 ZIP 解压构建共同约束。

**Tech Stack:** ArkTS、ArkUI、HarmonyOS/OpenHarmony API 20、Form Kit、JSON 资源、SVG、Python 3 `unittest`、Hvigor 6.20.0。

---

## 文件职责

- `work/source-facts/android-widget.json`：冻结 Android 提交节点和 Glance 1.2.0-rc01 的视觉常量。
- `work/tools/tests/test_form_contract.py`：对源事实、资源角色、精确矢量和 ArkUI 结构做可执行合同检查。
- `work/entry/src/main/resources/base|dark/element/color.json`：仅新增 Form 专用浅/深色资源。
- `work/entry/src/main/resources/base/media/shopping_cart.svg`：保存 Android Widget 标题动作的原始 24×24 路径。
- `work/entry/src/main/ets/form/RecentOrdersForm.ets`：应用标题栏、条目间距、网格 gutter 与颜色映射。
- `work/journeys/core.yaml`：在既有 Form Journey 上冻结截图可观测的颜色与几何，不伪造设备执行。
- `work/tools/tests/test_workflow_contract.py`：保证 Journey 确实包含新增视觉断言。
- `docs/鸿蒙化实现方法与进展.md`：记录证据、限制和交付包复验结果。

## 实施约束

- 用户已书面确认 `docs/superpowers/specs/2026-07-13-recent-orders-form-kit-design.md` 第 11 节方案 A。
- 不修改主应用 `page_background`、`ui_floated`、`text_*` 或 `icon_*` 的既有值。
- 不尝试在 HarmonyOS 猜测 Android 12 壁纸动态色；采用冻结 AAR 的确定性 fallback palette。
- 不改变五组订单、断点、Form 生命周期、Cart 路由或点击区域语义。
- 当前外层工作区有用户未提交改动；不 commit、不 push、不上传。
- 每项生产变更遵循红色测试→最小实现→聚焦转绿；最终再跑全量测试与构建。

### Task 1: 冻结视觉源事实并建立红色合同

**Files:**
- Modify: `work/source-facts/android-widget.json`
- Modify: `work/tools/tests/test_form_contract.py`

- [x] **Step 1: 先写源事实和资源失败测试**

在测试常量中加入：

```python
BASE_COLORS = ROOT / "entry/src/main/resources/base/element/color.json"
DARK_COLORS = ROOT / "entry/src/main/resources/dark/element/color.json"
SHOPPING_CART = ROOT / "entry/src/main/resources/base/media/shopping_cart.svg"
```

新增测试，精确要求冻结版本与视觉常量：

```python
def test_glance_visual_contract_is_frozen(self) -> None:
    facts = json.loads(WIDGET_FACTS.read_text(encoding="utf-8"))
    visual = facts["visualContract"]
    self.assertEqual("1.2.0-rc01", visual["glanceAppWidgetVersion"])
    self.assertEqual(
        {"height": 48, "horizontalPadding": 4, "startSlot": 48,
         "startPadding": 2, "iconSize": 24, "titleMaxLines": 1},
        visual["titleBarVp"],
    )
    self.assertEqual(16, visual["contentSpacingVp"])
    self.assertEqual(4, visual["gridGutterVp"])
    self.assertEqual("shopping_cart", visual["titleActionVector"])
    self.assertEqual(
        {
            "light": {"widgetBackground": "#E0F3FF", "secondaryContainer": "#E8DEF8",
                      "primary": "#6750A4", "secondary": "#625B71", "onSurface": "#1C1B1F"},
            "dark": {"widgetBackground": "#20333D", "secondaryContainer": "#4A4458",
                     "primary": "#D0BCFF", "secondary": "#CCC2DC", "onSurface": "#E6E1E5"},
        },
        visual["fallbackPalette"],
    )

def test_form_has_dedicated_glance_palette_resources(self) -> None:
    expected = {
        "base": {"form_widget_background": "#E0F3FF", "form_secondary_container": "#E8DEF8",
                 "form_primary": "#6750A4", "form_secondary": "#625B71",
                 "form_on_surface": "#1C1B1F"},
        "dark": {"form_widget_background": "#20333D", "form_secondary_container": "#4A4458",
                 "form_primary": "#D0BCFF", "form_secondary": "#CCC2DC",
                 "form_on_surface": "#E6E1E5"},
    }
    for mode, path in (("base", BASE_COLORS), ("dark", DARK_COLORS)):
        colors = {item["name"]: item["value"] for item in json.loads(path.read_text())["color"]}
        for name, value in expected[mode].items():
            self.assertEqual(value, colors[name])

def test_title_cart_uses_exact_android_widget_vector(self) -> None:
    svg = SHOPPING_CART.read_text(encoding="utf-8")
    self.assertIn('viewBox="0 0 24 24"', svg)
    self.assertIn("M7,18c-1.1,0 -1.99,0.9 -1.99,2", svg)
    self.assertIn("M1,2v2h2l3.6,7.59", svg)
    self.assertIn("M17,18c-1.1,0 -1.99,0.9", svg)
```

- [x] **Step 2: 运行聚焦测试并确认红色原因**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest work.tools.tests.test_form_contract -v
```

Expected: 新测试因 `visualContract`、五个 Form 颜色资源或 `shopping_cart.svg` 缺失而失败；既有测试继续通过。

- [x] **Step 3: 写入冻结视觉事实**

在 `android-widget.json` 添加：

```json
"visualContract": {
  "glanceAppWidgetVersion": "1.2.0-rc01",
  "titleBarVp": {
    "height": 48,
    "horizontalPadding": 4,
    "startSlot": 48,
    "startPadding": 2,
    "iconSize": 24,
    "titleMaxLines": 1
  },
  "contentSpacingVp": 16,
  "gridGutterVp": 4,
  "titleActionVector": "shopping_cart",
  "fallbackPalette": {
    "light": {
      "widgetBackground": "#E0F3FF",
      "secondaryContainer": "#E8DEF8",
      "primary": "#6750A4",
      "secondary": "#625B71",
      "onSurface": "#1C1B1F"
    },
    "dark": {
      "widgetBackground": "#20333D",
      "secondaryContainer": "#4A4458",
      "primary": "#D0BCFF",
      "secondary": "#CCC2DC",
      "onSurface": "#E6E1E5"
    }
  }
}
```

- [x] **Step 4: 重跑聚焦测试**

Expected: 源事实测试转绿；资源测试仍明确因资源尚未实现而红。

### Task 2: 添加精确矢量与 Form 专用调色板

**Files:**
- Create: `work/entry/src/main/resources/base/media/shopping_cart.svg`
- Modify: `work/entry/src/main/resources/base/element/color.json`
- Modify: `work/entry/src/main/resources/dark/element/color.json`

- [x] **Step 1: 添加 Android 标题购物车矢量**

创建 24×24 SVG，path 必须保持 Android `shopping_cart.xml` 原语义：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <path fill="#000000" d="M7,18c-1.1,0 -1.99,0.9 -1.99,2S5.9,22 7,22s2,-0.9 2,-2 -0.9,-2 -2,-2zM1,2v2h2l3.6,7.59 -1.35,2.45c-0.16,0.28 -0.25,0.61 -0.25,0.96 0,1.1 0.9,2 2,2h12v-2L7.42,15c-0.14,0 -0.25,-0.11 -0.25,-0.25l0.03,-0.12 0.9,-1.63h7.45c0.75,0 1.41,-0.41 1.75,-1.03l3.58,-6.49c0.08,-0.14 0.12,-0.31 0.12,-0.48 0,-0.55 -0.45,-1 -1,-1L5.21,4l-0.94,-2L1,2zM17,18c-1.1,0 -1.99,0.9 -1.99,2s0.89,2 1.99,2 2,-0.9 2,-2 -0.9,-2 -2,-2z"/>
</svg>
```

- [x] **Step 2: 添加浅色与深色资源**

分别在 base/dark 的 `color` 数组追加 `form_widget_background`、`form_secondary_container`、
`form_primary`、`form_secondary`、`form_on_surface`，值严格采用 Task 1 冻结表；不得覆盖主应用同名主题角色。

- [x] **Step 3: 重跑资源聚焦测试**

Expected: 调色板与 SVG 测试转绿；尚未修改 UI 的结构合同保持红色。

### Task 3: 以最小 ArkUI 变更对齐标题栏、间距、颜色和 gutter

**Files:**
- Modify: `work/tools/tests/test_form_contract.py`
- Modify: `work/entry/src/main/ets/form/RecentOrdersForm.ets`

- [x] **Step 1: 写 UI 结构失败测试**

在 `test_form_contract.py` 新增或强化：

```python
def test_form_matches_glance_title_spacing_palette_and_grid(self) -> None:
    source = FORM_PAGE.read_text(encoding="utf-8")
    for marker in (
        "app.media.shopping_cart",
        ".height(48)",
        ".padding({ left: 4, right: 4 })",
        ".padding({ left: 2 })",
        ".maxLines(1)",
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
    self.assertNotIn("app.media.ic_shopping_cart", source)
    self.assertNotIn("app.color.page_background", source)
    self.assertNotIn("app.color.ui_floated", source)
```

同时把既有 marker `.lanes(this.isLarge() ? 2 : 1)` 更新为带 gutter 的完整调用，并让标题栏单行测试
定位在 `titleBar()` 片段内，避免把条目标题的 `maxLines(2)` 误当标题栏。

- [x] **Step 2: 运行聚焦测试并确认结构红色**

Expected: 失败点为旧 `ic_shopping_cart`、56vp 标题栏、12vp 内容间距、无横向 gutter 或旧主题资源。

- [x] **Step 3: 修改标题栏**

将 `titleBar()` 的布局收敛为：

```typescript
Row() {
  Stack() {
    Image($r('app.media.widget_logo'))
      .width(24)
      .height(24)
      .fillColor($r('app.color.form_primary'))
      .accessibilityLevel('no')
  }
  .width(48)
  .height(48)
  .padding({ left: 2 })

  if (!this.isSmall()) {
    Text($r('app.string.recent_orders_form_title'))
      .fontSize(16)
      .fontWeight(FontWeight.Medium)
      .fontColor($r('app.color.form_on_surface'))
      .maxLines(1)
      .textOverflow({ overflow: TextOverflow.Ellipsis })
      .layoutWeight(1)
  } else {
    Blank().layoutWeight(1)
  }

  Stack() {
    Image($r('app.media.shopping_cart'))
      .width(24)
      .height(24)
      .fillColor($r('app.color.form_secondary'))
      .accessibilityLevel('no')
  }
  .width(48)
  .height(48)
  .id('form.action.cart.title')
  .accessibilityText($r('app.string.recent_orders_form_cart'))
  .onClick(() => { this.openCart(''); })
}
.width('100%')
.height(48)
.alignItems(VerticalAlign.Center)
.padding({ left: 4, right: 4 })
```

- [x] **Step 4: 修改条目、网格和颜色映射**

生产代码必须满足：

```typescript
// leading → center
.margin({ left: this.isSmall() ? 0 : 16 })

// trailing builder root
.margin({ left: 16 })

// grid/list
.lanes(this.isLarge() ? 2 : 1, this.isLarge() ? 4 : 0)

// palette roles
.backgroundColor($r('app.color.form_secondary_container'))
.backgroundColor($r('app.color.form_widget_background'))
```

条目标题使用 `form_on_surface`，辅助文本使用 `form_secondary`，行尾动作图标使用 `form_primary`。

- [x] **Step 5: 运行 Form 合同与 API 20 编译**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest work.tools.tests.test_form_contract -v
work/tools/verify.sh --build
```

Expected: Form 合同全绿；`CompileArkTS`、`PackageHap`、`assembleHap` 成功并输出 `status=passed`。

### Task 4: 强化截图 Journey 与工作流合同

**Files:**
- Modify: `work/journeys/core.yaml`
- Modify: `work/tools/tests/test_workflow_contract.py`

- [x] **Step 1: 写 Journey 失败合同**

要求既有 Journey 包含以下断言：

```python
expected = {
    "core.form.recent-orders": ("background:#E0F3FF", "item.background:#E8DEF8",
                                "titleBar.height:48vp", "titleBar.paddingX:4vp"),
    "visual.form.2x4": ("contentSpacing:16vp", "titleBar.maxLines:1"),
    "visual.form.4x4": ("grid.gutter:4vp",),
    "visual.dark.form.2x4": ("background:#20333D", "item.background:#4A4458",
                                     "title:#E6E1E5", "supporting:#CCC2DC"),
    "visual.large-font.form.4x4": ("titleBar.maxLines:1", "itemTitle.maxLines:2"),
}
```

逐个截取 Journey 段并断言 marker，先运行 `test_workflow_contract` 确认红色。

- [x] **Step 2: 更新既有 Journey**

只强化断言，不增加不可执行动作：浅色卡片冻结 `#E0F3FF/#E8DEF8`，深色卡片由旧的 `#121212`
修正为 `#20333D/#4A4458`，双列冻结 4vp gutter，标题栏冻结 48vp/4vp/单行；大字体将
`title.maxLines:2` 明确拆成 `titleBar.maxLines:1` 和 `itemTitle.maxLines:2`。

- [x] **Step 3: 重跑工作流与 YAML 解析合同**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest work.tools.tests.test_workflow_contract -v
ruby -e 'require "yaml"; YAML.load_file("work/journeys/core.yaml"); puts "yaml=passed"'
```

Expected: 工作流合同通过，Ruby 输出 `yaml=passed`。

### Task 5: 全量回归、文档和交付 ZIP

**Files:**
- Modify: `docs/鸿蒙化实现方法与进展.md`
- Replace: `android_to_harmonyOS_submission.zip`

- [x] **Step 1: 全量静态与构建回归**

Run:

```bash
work/tools/verify.sh --static
work/tools/verify.sh --build
```

Expected: 全部合同通过；API 20 `CompileArkTS`、`PackageHap` 和 `assembleHap` 退出码均为 0。

- [x] **Step 2: 更新进展证据**

在进展文档新增一条，记录五项视觉修订、最终测试/Journey 数量和构建结果；同时继续注明：
Android 动态壁纸色不可跨系统确定性复刻，正式 Code Linter 与设备截图仍需评分环境执行。

- [x] **Step 3: 重新生成仅含两个顶层条目的 ZIP**

使用临时 staging 目录复制 `INSTRUCTION.md` 和排除以下内容后的 `work/`：`.git`、`.hvigor`、
`build`、`oh_modules`、`__pycache__`、`*.pyc`、`*.hap`。在 staging 根运行：

```bash
zip -q -r android_to_harmonyOS_submission.zip INSTRUCTION.md work
```

然后原子替换根目录旧 ZIP。不得包含 `docs/` 或 `introduction.md`。

- [x] **Step 4: 全新解压副本复验**

在 `mktemp -d` 下解压新 ZIP，并从解压根运行：

```bash
work/tools/verify.sh --static
work/tools/verify.sh --build
```

Expected: 解压副本测试和构建均通过。

- [x] **Step 5: 最终结构与禁止项审计**

Run:

```bash
unzip -t android_to_harmonyOS_submission.zip
unzip -Z1 android_to_harmonyOS_submission.zip
```

Expected: 顶层严格只有 `INSTRUCTION.md`、`work/`；禁止项为 0；ZIP 内说明和源码与当前交付源一致。

## 完成条件

1. 新视觉合同经历可解释红—绿过程；
2. 标题图标、48vp TitleBar、两处 16vp 间距、4vp gutter 和专用浅/深色角色均被自动合同锁定；
3. 既有五组数据、物理断点、Cart 冷/热启动和仅两个点击目标不退化；
4. 全量静态测试与 API 20 HAP 构建通过；
5. 新 ZIP 只含 `INSTRUCTION.md` 与 `work/`，全新解压副本再次测试/构建通过；
6. 未执行的专有 Code Linter 和真机截图继续如实披露，不承诺未经证明的隐藏用例满分。
