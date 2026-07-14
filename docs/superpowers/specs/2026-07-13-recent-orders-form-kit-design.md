# RecentOrders Widget → HarmonyOS Form Kit 迁移设计

> 日期：2026-07-13  
> 状态：书面设计已获用户确认，进入 TDD 实施阶段。

## 1. 背景与目标

比赛指定 Android 节点 `23e1421b72b602d80486777efbf24dd248abf3bb` 的
`AndroidManifest.xml` 注册了 `RecentOrdersWidgetReceiver`。该 Glance AppWidget 是用户可见功能，
支持最近订单展示、尺寸变化和跳转购物车。当前鸿蒙工程只迁移了主应用，没有对应 Form Kit 服务卡片，
因此在功能完备度、接口一致性或桌面卡片隐藏用例中存在明确缺口。

本设计在现有 `entry` 模块内新增原生 ArkTS 服务卡片，目标是：

- 保留 Android 卡片的五组静态最近订单；
- 覆盖小、中、大三类尺寸，并支持系统卡片尺寸调整；
- 标题栏购物车和订单行操作均打开 Jetsnack Cart；
- 不引入网络、三方 OHPM 依赖或第二个 HAP/HAR 模块；
- 保持主应用现有路由、状态、截图和离线构建能力不退化；
- 将 Widget → Form Kit 纳入迁移台账、自动化 Skill、Journey 和验证门禁。

## 2. 方案比较与选择

### 方案 A：在现有 entry 模块完整实现 Form Kit（采用）

新增一个 `FormExtensionAbility`、一份 `form_config.json` 和一个 ArkTS 卡片入口页面。
它复用现有商品媒体资源，通过 `postCardAction` 跳转现有 `EntryAbility`。优点是原生、离线、
构建链最短，且能覆盖功能、接口、截图和规范四类评分；代价是需要维护卡片专用 UI 限制和尺寸测试。

### 方案 B：独立卡片模块（不采用）

卡片与主应用隔离更强，但会增加模块依赖、产物定位、资源共享和平台打包复杂度。
本项目只有一个卡片，收益不足以抵消评测环境风险。

### 方案 C：仅注册空卡片或继续忽略 Widget（不采用）

空卡片只能通过部分清单检查，无法通过截图、数据和交互用例；忽略则保留已经确认的功能缺口，
均不符合满分导向。

## 3. 迁移边界

### 3.1 必须实现

1. `RecentOrdersFormAbility` 生命周期入口。
2. 一个默认 ArkTS 动态卡片，支持 `2*2`、`2*4`、`4*4`，并声明可调整尺寸。
3. 五组订单，数据严格来自 Android `RecentOrdersDataRepository.demoItems`：
   `(0,20)`、`(1,21)`、`(2,22)`、`(3,23)`、`(4,24)`。
4. 每组标题为第一件商品名称，辅助文本为该组两件商品名称，图片为第一件商品图片。
5. 标题栏购物车动作和可见的行尾操作均打开 Cart。
6. 小尺寸不显示商品图片和行尾操作；中尺寸显示图片；空间足够时显示行尾操作；大尺寸使用双列。
7. 浅色、深色、字体缩放、无障碍文本和资源化字符串。
8. 冷启动与 singleton 热启动两种卡片跳转路径。

### 3.2 明确不实现

- 不把卡片操作改造成真实持久化加购。Android 卡片虽然携带 `CART_ITEMS_KEY`，但 `MainActivity`
  没有消费该参数，实际行为只是打开 Cart；鸿蒙必须保持这一语义。
- 不引入远程图片、网络刷新或后台定时业务数据。
- 不迁移仅供 Android Glance 预览演示使用、且未注册到 Manifest 的
  `ActionDemonstrationActivity`。
- 不增加独立模块、数据库或账号能力。

## 4. 工程结构

```text
work/entry/src/main/
├── ets/
│   ├── entryformability/
│   │   └── RecentOrdersFormAbility.ets
│   ├── form/
│   │   ├── RecentOrdersForm.ets
│   │   └── RecentOrdersFormData.ets
│   └── entryability/EntryAbility.ets
├── module.json5
└── resources/base/
    ├── element/string.json
    └── profile/form_config.json
```

职责划分：

- `RecentOrdersFormData.ets`：只保存不可变订单映射和卡片数据类型；
- `RecentOrdersFormAbility.ets`：只负责 Form 生命周期和初始绑定数据；
- `RecentOrdersForm.ets`：只负责响应式渲染与 `postCardAction`；
- `EntryAbility.ets`：统一解析网页深链和卡片路由参数；
- `form_config.json`：声明卡片名称、入口、尺寸、颜色模式和调整能力。

## 5. 数据与生命周期

`RecentOrdersFormData.ets` 直接保存五组确定性订单及其现有媒体资源引用。静态资源不经过
`FormBindingData` 序列化，避免把 `Resource` 对象转换为不稳定的跨进程数据。
`onAddForm()` 返回包含卡片实例 ID、枚举尺寸和真实宽高的有效 `FormBindingData`。初次添加从
`FormParam.WIDTH_KEY` / `HEIGHT_KEY` 读取几何；API 20 的 `onSizeChanged()` 再使用明确以 vp 表示的
`newRect.width/height` 实时发布。无效或缺失几何按 Android 参考设备预览确定性回退为
`2*2=172×224`、`2*4=360×224`、`4*4=480×359`，但系统真实几何始终优先。数据不使用时间、随机数或网络，
因此重复添加和五轮评测结果一致。

`onUpdateForm()` 无需发布可变业务数据；卡片重新渲染时仍读取同一静态映射。
`onRemoveForm()` 不需要清理业务数据，因为本实现不保存每个实例的可变状态。
`onAcquireFormState()` 返回 `READY`。所有生命周期签名使用 API 20
`@kit.FormKit` 和 `@kit.AbilityKit` 的正式类型，不使用旧版废弃导入。

卡片操作发送固定参数，例如 `targetRoute: 'home/cart'`。`EntryAbility` 的路由解析优先级为：

1. 精确 Cart 网页深链；
2. 精确卡片 `targetRoute`；
3. 冷启动默认 Feed；
4. 热启动的空 Want 或无关 Want 保持当前页面。

卡片参数不得把任意字符串直接当路由，避免外部输入进入未声明页面。

## 6. 响应式 UI

卡片页面使用 ArkTS 卡片允许的基础组件和属性，不使用 WebView、Canvas 截图壳或运行时反射。

枚举尺寸只决定宿主允许的规格，不再直接决定布局。布局严格使用 Android `LocalSize` 的物理断点：

| 条件（vp） | 结果 |
|---|---|
| `width < 260` | Small：单列、无图；标题栏若因高度显示，标题文字为空 |
| `260 <= width < 479` | Medium：单列、显示 68vp 图片 |
| `width >= 479` | Large：双列、显示图片 |
| `height < 180` / `>= 180` | 隐藏 / 显示标题栏 |
| `340 <= width <= 479` 或 `width > 620` | 显示 48vp 行尾购物车动作 |

这意味着 `479` 既是双列起点又仍显示行尾动作，`480..620` 为双列但隐藏行尾动作，`621` 再显示；
比较符不可被近似为枚举判断。滚动容器本身使用 16vp 圆角并裁剪，防止条目滚动到圆角外。

卡片以实际可用宽高决定布局，不依赖设备型号。条目容器保留 16vp 圆角、12vp 内边距、
4vp 间距；图片为 68vp、12vp 圆角，和 Android 源码一致。标题最多两行，辅助文本最多两行。
触控目标不小于 48vp。

颜色跟随系统模式，使用应用资源而非硬编码散落色值。图片只作视觉辅助，不重复播报；标题、
订单内容及购物车动作提供可读无障碍说明。大字体下允许条目增长或减少同屏条目，不裁剪动作。

## 7. 交互

标题栏购物车和行尾购物车按钮调用 `postCardAction` 的 `router` 动作，目标为现有
`EntryAbility`。冷启动直接显示 Cart，热启动通过 `onNewWant()` 切换到 Cart，不先闪 Feed。
重复点击为幂等导航，不重置当前 Cart ViewModel 等价状态。

订单条目非按钮区域保持不可点击；Android 源码只把 `shoppingCartActionIntent` 绑定到标题栏动作和
可见的行尾按钮。行尾操作参数中可保留订单键用于接口追踪，但主应用不据此修改数量。

## 8. 错误处理与兼容性

- `Want` 或参数缺失时仍返回有效空绑定数据，不能让卡片提供方崩溃；
- 未知卡片路由参数被忽略；
- Form 更新失败只记录规范化日志，不影响主应用；
- 卡片资源必须全部随 HAP 打包；
- 公共 OpenHarmony API 20 构建作为类型和配置兼容证据，正式 HarmonyOS SDK 仍是最终环境；
- 若公共 SDK 不支持某个 HarmonyOS 专有视觉属性，移除该非必要属性，而不降级核心数据和路由。

## 9. 测试策略

所有生产变更遵循失败测试 → 最小实现 → 全量回归：

1. **清单合同**：ExtensionAbility、`ohos.extension.form` metadata、profile 资源和三种尺寸完整。
2. **数据合同**：五组索引、标题/辅助文本/图片映射与 Android 源码逐项一致。
3. **交互合同**：标题、条目和行尾动作全部发送受限 Cart 路由；冷/热启动均可消费。
4. **响应式合同**：真实宽高绑定；`259/260`、`339/340`、`478/479/480`、`620/621` 和
   `179/180` 的比较符、列数、标题、图片与行尾动作逐点一致；触控目标、圆角、裁剪和文本行数一致。
5. **规范合同**：资源化字符串、稳定 ForEach 键、无 `any/ESObject/export *`、无废弃 Form 导入。
6. **Journey**：三尺寸、浅色/深色、大字体、标题跳转、行尾跳转、冷/热启动、重复点击。
7. **回归**：现有全部静态测试、标准 YAML 解析、API20 `CompileArkTS`、HAP assemble。
8. **交付复验**：重新生成 ZIP，在全新目录解压后执行静态测试和构建，检查顶层仅
   `INSTRUCTION.md` 与 `work/`，并排除 `.git`、缓存和构建产物。

设备截图和真实桌面卡片操作只有在提供 HarmonyOS 设备或模拟器时才能形成强证据；没有设备时
不得把静态 Journey 误报为已执行截图。

## 10. 完成判定

本功能只有同时满足以下条件才视为实现完成：

1. 迁移台账新增 Widget → Form Kit 映射且状态为 `implemented`；
2. 服务卡片清单、Ability、数据、三尺寸 UI 和 Cart 跳转均存在；
3. 新增合同测试经历过可解释的红—绿过程；
4. 全量静态测试无失败；
5. API20 ArkTS 编译和 HAP 组装退出码为 0；
6. 新 ZIP 结构及新解压验证通过；
7. 进展文档准确区分静态/构建证据与尚缺的真机截图证据。

## 11. 书面确认后的像素同源修订

2026-07-13 二次对照固定 Android 节点、`androidx.glance:glance-appwidget:1.2.0-rc01`
实际依赖包和 ArkUI API 20 类型后，确认基础卡片的数据、路由和物理断点已经正确，但仍有五项会直接影响
截图相似度的差异。本节覆盖第 6 节中与这些差异冲突的旧近似值，并作为后续实现的唯一视觉基线。

### 11.1 标题栏

- Android `TitleBar` 的实际高度由 48dp 子项决定，不是 56dp；整行水平 padding 为 4dp。
- 左侧品牌图标位于 48dp 槽位内，槽位 start padding 为 2dp，内部图标保持 24dp。
- 标题为 16sp Medium、单行省略并占剩余宽度；小宽度仍保留图标和动作，但标题内容为空。
- 右侧动作继续使用 48dp 触控区。
- 标题动作必须使用 Android `R.drawable.shopping_cart` 的 24×24 原始 pathData，不能复用主应用
  `ic_shopping_cart` 的 960×960 Material 路径。行尾动作继续使用 `add_shopping_cart`。

### 11.2 条目与网格间距

- Android `ListItem` 默认在 leading→center 和 center→trailing 两处都插入 16dp；鸿蒙对应两处均为
  16vp。条目自身 12vp padding、68vp 图片、12vp 图片圆角和 16vp 容器圆角保持不变。
- 单列主轴间距保持 4vp。双列列表还必须向 `List.lanes` 传入 4vp gutter，不能只依赖
  `List({ space: 4 })`，以同时复现横向与纵向 cell spacing。

### 11.3 卡片专用颜色

采用已获确认的方案 A：新增 Form 专用颜色资源，不修改主应用主题。Android API 31+ 的 Glance
颜色会映射到 Android 壁纸动态色，HarmonyOS 无法确定性取得同一 Android 系统色，因此以冻结依赖包的
非动态回退色作为跨平台、跨评测环境可复验基线：

| 角色 | 浅色 | 深色 |
|---|---:|---:|
| `widgetBackground` | `#E0F3FF` | `#20333D` |
| `secondaryContainer` | `#E8DEF8` | `#4A4458` |
| `primary` | `#6750A4` | `#D0BCFF` |
| `secondary` | `#625B71` | `#CCC2DC` |
| `onSurface` | `#1C1B1F` | `#E6E1E5` |

映射固定为：卡片背景→`widgetBackground`，条目背景→`secondaryContainer`，品牌图标及默认行尾动作→
`primary`，标题文字和条目标题→`onSurface`，标题购物车及辅助文本→`secondary`。颜色必须放入
`base/element/color.json` 与 `dark/element/color.json`，禁止散落硬编码。

### 11.4 验证边界

- 静态合同冻结依赖版本、五个颜色角色、标题栏 48/4/48/2/24 几何、标题单行、两处 16vp 间距、
  4vp 双列 gutter 和精确标题购物车路径。
- 现有 260×180、479×180、480×180、浅色、深色与大字体 Journey 增加颜色和细部几何断言；
  不新增虚假的设备执行结论。
- 公共 API 20 ArkTS 编译、HAP 组装、全量静态合同和全新 ZIP 解压构建必须继续通过。
- 正式 HarmonyOS 桌面截图仍只能在有设备或评分平台时验证；确定性回退色的选择不能被表述为
  已证明与任意 Android 12 壁纸动态色逐像素相同。
