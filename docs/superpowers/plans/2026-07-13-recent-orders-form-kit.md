# RecentOrders Widget → HarmonyOS Form Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 `work/entry` 中补齐 Android `RecentOrdersWidgetReceiver` 对应的 HarmonyOS Form Kit 服务卡片，保持五组订单、三档尺寸和 Cart 跳转语义，并通过静态合同、API 20 编译、HAP 组装与全新解压交付复验。

**Architecture:** 继续使用单 `entry` Stage HAP；`RecentOrdersFormData` 保存只读订单映射，`RecentOrdersFormAbility` 负责 Form 生命周期和尺寸绑定，`RecentOrdersForm` 负责响应式 ArkUI 卡片及 `postCardAction`，现有 `EntryAbility` 统一消费网页深链与受限 `targetRoute` 参数。迁移台账、Journey 和 Skill 门禁同步覆盖该功能。

**Tech Stack:** HarmonyOS/OpenHarmony API 20、Stage、ArkTS、ArkUI、Form Kit、Hvigor、Python 3 `unittest`、POSIX shell。

---

## 实施约束

- 用户已批准 `docs/superpowers/specs/2026-07-13-recent-orders-form-kit-design.md`；本计划不得扩展为网络刷新、持久化加购或独立模块。
- Android 冻结事实来自提交 `23e1421b72b602d80486777efbf24dd248abf3bb`：五组索引为 `(0,20)`、`(1,21)`、`(2,22)`、`(3,23)`、`(4,24)`。
- 只有标题栏购物车与可见行尾按钮可点击；订单整行不得绑定 Cart 动作。
- 静态 `Resource` 图片只留在 ArkTS 卡片进程内，不放入 `FormBindingData`。
- 每个生产变更必须先出现可解释的失败测试，再写最小实现并转绿。
- 当前目录属于外层未跟踪/脏工作区；不执行 Git commit、push 或上传。检查点由测试结果和 ZIP 新鲜解压复验承担。
- 无 HarmonyOS 桌面设备时，只能报告静态与构建证据，不得宣称桌面卡片截图或交互 Journey 已真机通过。

### Task 1: 固化 Widget 源事实并建立红色合同测试

**Files:**
- Create: `work/source-facts/android-widget.json`
- Create: `work/tools/tests/test_form_contract.py`

- [x] **Step 1: 写 Form Kit 文件与冻结事实合同**

创建 `test_form_contract.py`，首批测试精确断言：

```python
FORM_ABILITY = ROOT / "entry/src/main/ets/entryformability/RecentOrdersFormAbility.ets"
FORM_PAGE = ROOT / "entry/src/main/ets/form/RecentOrdersForm.ets"
FORM_DATA = ROOT / "entry/src/main/ets/form/RecentOrdersFormData.ets"
FORM_CONFIG = ROOT / "entry/src/main/resources/base/profile/form_config.json"
WIDGET_FACTS = ROOT / "source-facts/android-widget.json"

def test_form_files_exist(self) -> None:
    for path in (FORM_ABILITY, FORM_PAGE, FORM_DATA, FORM_CONFIG):
        self.assertTrue(path.is_file(), path)

def test_android_widget_facts_are_frozen(self) -> None:
    facts = json.loads(WIDGET_FACTS.read_text(encoding="utf-8"))
    self.assertEqual("23e1421b72b602d80486777efbf24dd248abf3bb", facts["sourceCommit"])
    self.assertEqual([[0, 20], [1, 21], [2, 22], [3, 23], [4, 24]], facts["demoItemIndices"])
    self.assertEqual(["2*2", "2*4", "4*4"], facts["targetDimensions"])
    self.assertEqual(["titleCart", "trailingCart"], facts["clickTargets"])
    self.assertFalse(facts["wholeRowClickable"])
```

- [x] **Step 2: 运行并确认正确失败**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_form_contract -v
```

Expected: `FAIL`，原因是 `android-widget.json` 或 Form Kit 文件缺失，而不是 Python 语法错误。

- [x] **Step 3: 写冻结源事实 JSON**

创建以下确定性事实：

```json
{
  "schemaVersion": 1,
  "sourceCommit": "23e1421b72b602d80486777efbf24dd248abf3bb",
  "manifestReceiver": "com.example.jetsnack.widget.RecentOrdersWidgetReceiver",
  "sourceWidget": "app/src/main/java/com/example/jetsnack/widget/RecentOrdersWidget.kt",
  "sourceRepository": "app/src/main/java/com/example/jetsnack/widget/RecentOrdersDataRepository.kt",
  "demoItemIndices": [[0, 20], [1, 21], [2, 22], [3, 23], [4, 24]],
  "demoItems": [
    ["Cupcake", "Apples"],
    ["Donut", "Apple sauce"],
    ["Eclair", "Apple chips"],
    ["Froyo", "Apple juice"],
    ["Gingerbread", "Apple pie"]
  ],
  "targetDimensions": ["2*2", "2*4", "4*4"],
  "clickTargets": ["titleCart", "trailingCart"],
  "wholeRowClickable": false,
  "actionResult": "openCartOnly"
}
```

- [x] **Step 4: 重跑聚焦测试**

Expected: 源事实测试通过；Form 文件存在性测试继续因目标文件缺失而失败。

### Task 2: 注册 FormExtensionAbility 与三档卡片配置

**Files:**
- Modify: `work/entry/src/main/module.json5`
- Modify: `work/entry/src/main/resources/base/element/string.json`
- Create: `work/entry/src/main/resources/base/profile/form_config.json`
- Create: `work/entry/src/main/ets/entryformability/RecentOrdersFormAbility.ets`

- [x] **Step 1: 扩充失败测试**

在 `test_form_contract.py` 增加：

```python
def test_module_registers_form_extension(self) -> None:
    module = json.loads(MODULE.read_text(encoding="utf-8"))["module"]
    extension = next(item for item in module["extensionAbilities"]
                     if item["name"] == "RecentOrdersFormAbility")
    self.assertEqual("form", extension["type"])
    self.assertEqual("./ets/entryformability/RecentOrdersFormAbility.ets", extension["srcEntry"])
    self.assertEqual("ohos.extension.form", extension["metadata"][0]["name"])
    self.assertEqual("$profile:form_config", extension["metadata"][0]["resource"])

def test_form_profile_declares_resizable_dimensions(self) -> None:
    forms = json.loads(FORM_CONFIG.read_text(encoding="utf-8"))["forms"]
    form = forms[0]
    self.assertEqual("arkts", form["uiSyntax"])
    self.assertEqual("auto", form["colorMode"])
    self.assertTrue(form["isDynamic"])
    self.assertTrue(form["resizable"])
    self.assertEqual(["2*2", "2*4", "4*4"], form["supportDimensions"])
    self.assertEqual("2*4", form["defaultDimension"])
```

并断言 Ability 源码包含 `FormExtensionAbility`、`createFormBindingData`、`DIMENSION_KEY`、`onSizeChanged`、`updateForm` 和 `FormState.READY`。

- [x] **Step 2: 运行并确认因清单/Ability 缺失失败**

Expected: 源事实测试绿；注册与生命周期测试红。

- [x] **Step 3: 添加清单与 profile**

在 `module.json5` 的 `module` 下增加：

```json
"extensionAbilities": [
  {
    "name": "RecentOrdersFormAbility",
    "srcEntry": "./ets/entryformability/RecentOrdersFormAbility.ets",
    "label": "$string:recent_orders_form_name",
    "description": "$string:recent_orders_form_description",
    "type": "form",
    "exported": true,
    "metadata": [
      {
        "name": "ohos.extension.form",
        "resource": "$profile:form_config"
      }
    ]
  }
]
```

`form_config.json` 使用一个 `RecentOrdersForm`，入口为 `./ets/form/RecentOrdersForm.ets`，`uiSyntax` 为 `arkts`，`isDynamic` 和 `resizable` 为 `true`，尺寸按测试声明，更新周期关闭，默认 `2*4`。

- [x] **Step 4: 实现最小类型安全生命周期**

`RecentOrdersFormAbility.ets` 使用名义类型作为绑定对象：

```typescript
class RecentOrdersFormBinding {
  formId: string;
  formDimension: number;
  formWidth: number;
  formHeight: number;

  constructor(formId: string, formDimension: number, formWidth: number, formHeight: number) {
    this.formId = formId;
    this.formDimension = formDimension;
    this.formWidth = formWidth;
    this.formHeight = formHeight;
  }
}
```

`onAddForm()` 从 `IDENTITY_KEY`、`DIMENSION_KEY`、`WIDTH_KEY` 与 `HEIGHT_KEY` 安全读取；`onSizeChanged()` 使用 `newRect` 的 vp 宽高和 `formProvider.updateForm()` 发布相同名义类型；`onAcquireFormState()` 返回 `READY`。几何缺失时使用冻结的参考设备回退值。错误只用固定 tag 记录，不抛出到提供方。

- [x] **Step 5: 重跑聚焦测试**

Expected: 清单、profile、生命周期合同全部通过；UI/data 测试尚未添加。

### Task 3: 实现确定性订单数据与响应式卡片 UI

**Files:**
- Create: `work/entry/src/main/ets/form/RecentOrdersFormData.ets`
- Create: `work/entry/src/main/ets/form/RecentOrdersForm.ets`
- Modify: `work/entry/src/main/resources/base/element/string.json`

- [x] **Step 1: 写数据与交互失败测试**

测试逐项断言五个稳定 key、十个商品名称、首商品媒体名、三种尺寸分支、`postCardAction`、`targetRoute`、`home/cart`、标题与行尾稳定 ID，并加入负向断言：

```python
self.assertNotRegex(form_source, r"(?s)RecentOrderRow\([^)]*\).*?\.onClick\(")
self.assertNotIn("Resource", ability_source)
self.assertNotIn("any", form_source)
self.assertIn("ForEach", form_source)
self.assertRegex(form_source, r"item\.stableKey")
```

同时断言图片尺寸 `68`、图片圆角 `12`、条目圆角 `16`、最小动作触控区 `48`、标题和辅助文本最多两行。

- [x] **Step 2: 运行并确认因 data/UI 文件缺失失败**

Expected: `RecentOrdersFormData.ets missing` 或 `RecentOrdersForm.ets missing`。

- [x] **Step 3: 实现只读五组数据**

定义：

```typescript
export class RecentOrderFormItem {
  readonly stableKey: string;
  readonly title: string;
  readonly supportingText: string;
  readonly image: Resource;
  readonly orderKey: string;
}
```

数组严格为：

```typescript
new RecentOrderFormItem('cupcake-apples', 'Cupcake', 'Cupcake, Apples', $r('app.media.cupcake'), '0-20')
new RecentOrderFormItem('donut-apple-sauce', 'Donut', 'Donut, Apple sauce', $r('app.media.donut'), '1-21')
new RecentOrderFormItem('eclair-apple-chips', 'Eclair', 'Eclair, Apple chips', $r('app.media.eclair'), '2-22')
new RecentOrderFormItem('froyo-apple-juice', 'Froyo', 'Froyo, Apple juice', $r('app.media.froyo'), '3-23')
new RecentOrderFormItem('gingerbread-apple-pie', 'Gingerbread', 'Gingerbread, Apple pie', $r('app.media.gingerbread'), '4-24')
```

- [x] **Step 4: 实现尺寸分支与受限 router action**

`RecentOrdersForm.ets` 使用 `@Entry(formStorage)` 和 `@LocalStorageProp` 读取枚举及真实宽高。2026-07-13 经书面确认的几何修订以 Android `LocalSize` 为准：`width<260` 无图单列、`260<=width<479` 有图单列、`width>=479` 双列；`height>=180` 才显示标题栏；行尾动作只在 `340<=width<=479` 或 `width>620` 显示。标题购物车 ID 为 `form.action.cart.title`，动态行尾 ID 为 ``form.action.cart.${item.stableKey}``；订单内容容器不调用 `.onClick()`。

Router action 使用显式类而非未类型化 object literal：

```typescript
class CartRouteParams {
  targetRoute: string = 'home/cart';
  orderKey: string;
  constructor(orderKey: string) { this.orderKey = orderKey; }
}

class CartRouterAction {
  action: string = 'router';
  abilityName: string = 'EntryAbility';
  params: CartRouteParams;
  constructor(orderKey: string) { this.params = new CartRouteParams(orderKey); }
}
```

标题动作传空 `orderKey`，行尾动作传冻结索引键；两者都只导航，不修改购物车状态。

- [x] **Step 5: 运行聚焦测试并立即做一次 API 20 编译**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_form_contract -v
work/tools/verify.sh --build
```

Expected: Python 合同绿；`CompileArkTS` 与 `assembleHap` 退出码 0。若卡片支持组件或类型被 SDK 拒绝，只做保持语义的最小兼容修复并为该失败补合同。

### Task 4: 让卡片 Cart 动作覆盖冷启动与热启动

**Files:**
- Modify: `work/entry/src/main/ets/entryability/EntryAbility.ets`
- Modify: `work/tools/tests/test_deep_link_contract.py`
- Modify: `work/tools/tests/test_form_contract.py`

- [x] **Step 1: 写卡片参数路由失败测试**

断言 `EntryAbility`：

```python
self.assertIn("want.parameters", source)
self.assertIn("targetRoute", source)
self.assertIn("ROUTE_CART", source)
self.assertIn("onCreate", source)
self.assertIn("onNewWant", source)
```

并断言未知参数仍回 Feed，热启动空/无关 Want 不触发 `publishRoute()`。

- [x] **Step 2: 运行并确认旧实现因未读取 parameters 失败**

Expected: 失败原因明确为 `want.parameters`/`targetRoute` 缺失；现有网页深链测试仍通过。

- [x] **Step 3: 最小扩展白名单路由解析**

保留现有精确 URI 去 query/fragment 匹配；仅当 `want.parameters?.['targetRoute']` 是字符串且精确等于 `ROUTE_CART` 时返回 Cart，其他参数回 Feed。继续复用：

```typescript
onCreate(want: Want, _launchParam: AbilityConstant.LaunchParam): void {
  this.publishRoute(want);
}

onNewWant(want: Want, _launchParam: AbilityConstant.LaunchParam): void {
  this.publishWarmRoute(want);
}
```

- [x] **Step 4: 聚焦回归**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_deep_link_contract \
  work.tools.tests.test_form_contract -v
```

Expected: 网页深链与卡片路由合同均通过。

### Task 5: 将 Form Kit 纳入迁移台账、Journey 与自动化 Skill

**Files:**
- Modify: `work/migration-manifest.json`
- Modify: `work/journeys/core.yaml`
- Modify: `work/tools/tests/test_workflow_contract.py`
- Modify: `work/skills/android-to-harmonyos/SKILL.md`
- Modify: `work/skills/android-to-harmonyos/references/quality-gates.md`

- [x] **Step 1: 写台账与 Journey 失败测试**

要求存在三个映射：

```json
{
  "id": "recent-orders-widget",
  "kind": "component",
  "target": "entry/src/main/ets/form/RecentOrdersForm.ets",
  "stableId": "form.recentOrders",
  "journey": "core.form.recent-orders"
}
```

以及标题 Cart、行尾 Cart 两个 `action` 映射。Journey 必须覆盖 `2*2`、`2*4`、`4*4`、深色、大字体、标题跳转、行尾跳转、冷启动、热启动和重复点击。

- [x] **Step 2: 运行并确认映射/Journey 缺失失败**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  work.tools.tests.test_workflow_contract -v
```

Expected: 明确报告新映射或新 Journey 不存在。

- [x] **Step 3: 添加已实现映射与可审计 Journey**

Journey ID 固定为：

```text
core.form.recent-orders
core.form.title-cart
core.form.trailing-cart
edge.form.cart-cold-start
edge.form.cart-warm-start
edge.form.cart-repeated
visual.form.2x2
visual.form.2x4
visual.form.4x4
visual.dark.form.2x4
visual.large-font.form.4x4
```

每条 Journey 都包含 `stable_id`、`setup`（需要时）、`steps`、`assert`、`screenshot`；文字明确它是待设备执行的契约，不伪造 PNG。

- [x] **Step 4: 扩展 Skill 和质量门禁**

在源事实阶段加入 Manifest receiver/Glance 数据冻结，在构建阶段加入 `extensionAbilities`/Form profile 检查，在设备阶段加入 Launcher 卡片添加、三尺寸调整、标题/行尾 Cart、冷/热启动截图采集。不得把卡片卡死为本题专有逻辑；说明这是发现 Android Widget 时的通用迁移分支。

- [x] **Step 5: 重跑 workflow 合同**

Expected: 所有映射的 Journey 都存在，所有 Journey 稳定 ID 能在 ArkTS 字面量或允许的动态模板中定位。

### Task 6: 全量静态、规范与构建回归

**Files:**
- Modify only when a failing test/compiler identifies a concrete defect.

- [x] **Step 1: 运行全部 Python 合同**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s work/tools/tests -p 'test_*.py' -v
```

Expected: 所有测试通过；测试总数比实施前 197 增加，不能通过删测试维持数字。

- [x] **Step 2: 运行统一静态门禁**

Run:

```bash
work/tools/verify.sh --static
```

Expected:

```text
status=passed
mode=static
```

- [x] **Step 3: 运行 API 20 公共 SDK 构建**

Run:

```bash
work/tools/verify.sh --build
```

Expected: `CompileArkTS`、HAP 组装成功，最后输出 `status=passed`；不把缺少专有 Code Linter 或设备写成已通过。

- [x] **Step 4: 扫描交付卫生与禁止模式**

Run:

```bash
rg -n '/Users/|\bany\b|ESObject|export \*' work INSTRUCTION.md
find work -name .git -o -name __pycache__ -o -name '*.hap' -o -name oh_modules -o -name build
```

Expected: 第一条仅出现测试自身允许的负向扫描字样或零结果；第二条不发现应进入 ZIP 的缓存/构建产物。

### Task 7: 更新进展、说明与最终 ZIP

**Files:**
- Modify: `docs/鸿蒙化实现方法与进展.md`
- Modify: `INSTRUCTION.md`
- Replace: `android_to_harmonyOS_submission.zip`

- [x] **Step 1: 更新进展证据边界**

记录源 Widget、Form Kit 架构、红—绿测试、最终测试数量、API 20 构建结果。未获得设备时明确列出：桌面添加、尺寸拖拽、真实截图和 HDC/UiTest 尚未形成强证据。

- [x] **Step 2: 校验 INSTRUCTION 构建方式**

确保 `INSTRUCTION.md` 仍以解压根目录为起点，说明 `cd work && tools/verify.sh --build` 或等价命令，不依赖本机绝对路径，不要求 Git 上传，也不引用不交付的 `docs/`。

- [x] **Step 3: 删除旧 ZIP 后只打包两个顶层条目**

使用排除 `.git`、缓存、构建产物的归档命令生成：

```text
INSTRUCTION.md
work/
```

ZIP 顶层不得包含 `docs/`、`introduction.md`、`demo-Jetsnack-android/` 或外层项目目录。

- [x] **Step 4: 在全新临时目录解压并复验**

在 `mktemp -d` 目录解压，运行：

```bash
python3 -m unittest discover -s work/tools/tests -p 'test_*.py' -v
work/tools/verify.sh --build
```

Expected: 全新解压副本测试与构建均通过。

- [x] **Step 5: 最终结构审计**

Run:

```bash
unzip -Z1 android_to_harmonyOS_submission.zip
```

Expected: 所有条目都以 `INSTRUCTION.md` 或 `work/` 开头；不含 `.git`、`docs/`、`introduction.md`、`__pycache__`、`.hvigor`、`oh_modules`、`build/`、`.hap`。

## 完成条件

只有以下事实同时成立，才可报告本轮实现及交付准备完成：

1. 新增合同测试经历了可解释的红—绿过程；
2. Form 清单、Ability、五组数据、三档响应式 UI、受限 Cart 路由均存在；
3. Android 整行不可点击和只导航不加购语义被负向合同锁定；
4. 全量静态测试、API 20 `CompileArkTS` 与 HAP 组装成功；
5. 新 ZIP 只含 `INSTRUCTION.md` 与 `work/`，且全新解压副本再次测试、构建成功；
6. 设备截图与专有 Code Linter 若仍不可用，必须继续作为证据缺口披露，不能据此承诺隐藏用例满分。
