# Jetsnack Android → HarmonyOS 移植说明

## 评测入口

`work/` 是已经完成的原生 HarmonyOS Stage 工程。Scorer 对每条意图用例先在下表定位功能，再读取对应 ArkTS、资源或配置文件判定；不需要重新生成、编译或运行项目。

- 应用入口和页面装配：`entry/src/main/ets/pages/Index.ets`
- 路由与返回：`entry/src/main/ets/state/AppRoute.ets`、`entry/src/main/ets/state/AppStore.ets`
- 公共组件：`entry/src/main/ets/components/`
- 图片、字符串、颜色、尺寸与字体：`entry/src/main/resources/`
- Android→HarmonyOS 逐项映射：`migration-manifest.json`
- Android 固定提交事实：`source-facts/`

## 功能对照

| Android 功能 | HarmonyOS 实现证据 | 已实现行为 |
| --- | --- | --- |
| Feed 首页 | `entry/src/main/ets/screens/FeedScreen.ets`、`components/SnackCollection.ets`、`data/SnackData.ets` | 配送地址、筛选入口、多组横向商品、商品详情跳转、稳定选择器 |
| Search 搜索 | `entry/src/main/ets/screens/SearchScreen.ets`、`data/SearchData.ets`、`state/AppStore.ets` | 聚焦态、查询、建议词、延迟结果、大小写/区域匹配、清空、分类与结果交互 |
| Cart 购物车 | `entry/src/main/ets/screens/CartScreen.ets`、`components/QuantitySelector.ets`、`state/AppStore.ets` | 数量增减、归零移除、滑动隐藏、金额汇总、配送与结账、错误 Snackbar 队列 |
| Profile 资料页 | `entry/src/main/ets/screens/ProfileScreen.ets` | 与 Android 基线一致的静态占位内容 |
| Snack 详情 | `entry/src/main/ets/screens/DetailScreen.ets`、`state/AppStore.ets` | 返回、说明展开/收起、数量边界、加入购物车、关联集合入口；详情页隐藏底栏 |
| Filter 筛选层 | `entry/src/main/ets/screens/FilterOverlay.ets`、`components/FilterBar.ets` | 排序、价格/类别选择、卡路里滑块、重置、应用、遮罩/返回关闭 |
| 底部导航 | `entry/src/main/ets/components/BottomNav.ets`、`pages/Index.ets` | Feed/Search/Cart/Profile 四 Tab、选中态、Tab 状态保持、返回 Feed |
| Recent orders 卡片 | `entry/src/main/ets/form/RecentOrdersForm.ets`、`entryformability/RecentOrdersFormAbility.ets`、`resources/base/profile/form_config.json` | Form Kit 注册、2×2/2×4/4×4 响应式布局、购物车路由动作 |
| 外部购物车链接 | `entry/src/main/module.json5`、`entry/src/main/ets/entryability/EntryAbility.ets` | `https://jetsnack.example.com/home/cart` 深链解析到 Cart |

## 状态、交互与接口证据

- `state/AppStore.ets` 是唯一业务状态源，集中实现 Tab、搜索、购物车、详情和筛选动作；状态与 UI 通过强类型字段绑定，不依赖网络、随机数或当前时间。
- 页面和关键动作均提供稳定 `.id(...)` 与无障碍文本，例如 `screen.feed`、`screen.search`、`screen.cart`、`screen.profile`、`screen.detail`、`action.detail.addToCart`、`action.cart.checkout`。
- Android 中本来没有状态变化的按钮仍保持可点击且不虚构业务结果；相关映射在 `migration-manifest.json` 中标为 `implemented`，实现中使用显式 acknowledge 方法保留可观察交互。
- 公开 Android 测试路径、页面/动作清单和期望状态保存在 `source-facts/`；完整可机读 Journey 位于 `journeys/core.yaml`。

## 界面一致性

- `theme/JetsnackTheme.ets` 和 `entry/src/main/resources/base/element/` 统一保存颜色、字号、间距与可见文案；Karla、Montserrat 字体保存在 `resources/rawfile/fonts/`。
- Android 商品图、图标和矢量资源均为本地资源，位于 `resources/base/media/`；深色模式替换资源位于 `resources/dark/`，无运行时网络图片。
- `pages/Index.ets` 与 `entryability/EntryAbility.ets` 读取并监听系统栏、导航指示器和刘海避让区，像素转换为 vp 后传给页面；支持手机、平板、分屏、浮窗和旋转。
- `BottomNav.ets`、`DetailScreen.ets`、`FilterOverlay.ets` 与 Form 页面使用显式布局尺寸、触控热区、选中/禁用状态，保证截图几何和交互命中稳定。
- `utils/CurrencyFormatter.ets` 使用系统区域和 `Intl.NumberFormat` 输出金额；配置变化时刷新区域派生显示并按 Android 边界重置瞬态状态。

## 代码规范

- 工程入口：`AppScope/app.json5`、`entry/src/main/module.json5`、`build-profile.json5`、`oh-package.json5`。
- ArkTS 业务代码位于 `entry/src/main/ets/`，采用 Stage 模型、声明式 ArkUI、强类型模型和资源引用；工程没有 ohpm 第三方依赖。
- FormExtensionAbility、Form 配置、页面清单、深链和权限边界均在 HarmonyOS 标准配置位置声明。
- 迁移合同、资源完整性、稳定 ID、ArkTS 规则和构建前检查位于 `tools/`；它们是本地质量保障材料，不是 Scorer 必须执行的步骤。

## 原始基线

Android 来源仓库为 `fuxi-artifacts/demo-Jetsnack-android`，固定提交 `23e1421b72b602d80486777efbf24dd248abf3bb`。`migration-manifest.json` 中所有页面、路由、动作、数据、主题、资源和组件映射均指向实际 HarmonyOS 目标文件。
