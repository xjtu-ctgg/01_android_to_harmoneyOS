# 迁移实现与架构证据

## 1. 目标工程骨架

`work/` 是原生 HarmonyOS Stage 工程：

- `AppScope/` 和 `entry/` 提供应用与 Entry HAP 配置；
- `entry/src/main/ets/pages/Index.ets` 装配窗口安全区、Tab、Detail 和 Filter 层级；
- `state/AppStore.ets` 是共享业务状态源，`AppRoute.ets` 处理路由与返回语义；
- `screens/`、`components/`、`data/`、`utils/` 按页面、公共组件、事实数据和平台适配分层；
- `resources/` 保存可审计的颜色、文字、尺寸、图片、字体、向量和深色覆盖；
- `form/` 与 `entryformability/` 实现 Recent Orders Form Kit；
- `skills/`、`journeys/` 和 `tools/` 提供自动化迁移、验证和评审材料。

## 2. Android→HarmonyOS 映射

| Android 来源能力 | ArkUI 目标 | 关键验证证据 |
| --- | --- | --- |
| Feed / Search / Cart / Profile | 六个页面/覆盖层中的四个主 Tab 页面 | `screens/*.ets`、`screen.*` 稳定 ID、核心 Journey |
| Snack Detail | DetailScreen + AppRoute | 返回栈、数量、展开态、关联集合、隐藏 BottomNav |
| FilterScreen | FilterOverlay + FilterBar | 450vp 上限/窄屏可用高度、Chip、Slider、Scrim、返回 |
| Navigation Compose | AppRoute + Index 状态装配 | Tab 状态、详情来源、无效冷暖 URI、系统返回 |
| Glance AppWidget | FormExtensionAbility + RecentOrdersForm | Form 配置、尺寸断点、订单数据、Cart router |
| Compose State/Flow | AppStore 与局部状态 | 搜索延迟/取消、Filter 进程期状态、Detail 配置重建重置 |
| Material/自定义组件 | ArkUI 原生组件和资源 token | JetsnackTheme、渐变、阴影、圆角、最小高度与触控热区 |

清单中的 34 项映射全部指向仓内真实文件，状态为 `implemented`；这避免只提交说明书而没有可追溯目标实现。

## 3. 功能与生命周期的关键实现

### 搜索

保留 Android 的 `contains(query, ignoreCase=true)`，不擅自 trim；空查询、聚焦建议、Loading、结果、NoResults 和清空形成可测试状态。延迟请求采用 generation 语义，旧查询不能覆盖最新结果；离开 Search、进入 Detail 或配置重建时按源 `remember` 生命周期重置。

### 购物车

购物车状态集中在 AppStore，支持增减、归零删除、侧滑、失败周期、Subtotal/Shipping/Total、单数复数和 Snackbar FIFO。Snackbar 采用 4000ms 短时提示及 generation 隔离，跨 Tab 共享 Host，进入 Detail 时隐藏当前提示，返回后恢复队列。

### 详情与导航

Detail Hero 根据真实视口宽度从 300vp 收缩到 150vp；标题、SEE MORE/LESS 和底部余量使用最小尺寸，允许大字体自然增长。Cart 深链在 Ability 冷启动和暖启动均同步到根路由；系统返回优先关闭 Filter，再按来源返回 Cart/Feed。

### Form Kit

Recent Orders 卡片不是装饰性附加项，而是 Android Manifest 中注册的公开能力。Harmony 实现注册 FormExtensionAbility，按尺寸提供无图单列、有图单列和双列布局，标题/行尾动作可打开 Cart；所有媒体留在资源中，绑定数据保持轻量和可序列化。

## 4. 截图一致性策略

视觉实现按“源 token → 资源 → 组件几何 → 状态截图”逐层固定：

- 36 张商品图片和 6 种字体保留本地快照；
- 颜色、字号、间距、阴影、渐变和圆角进入资源或共享主题；
- 普通卡、精选卡、SearchResult、CartItem、Detail Hero 按 Compose 的自然测量、Cover 裁切和最小高度实现；
- BottomNav 的品牌色 Surface 延伸到导航指示条，Detail 隐藏 BottomNav 时按页面背景独立避让；
- 系统栏、刘海/挖孔、导航指示条和横屏侧边避让区由 EntryAbility 动态读取得到，不再把上下 24vp 当作通用安全区；
- Journey 固定视口、方向、主题、字体比例和截图点；`tools/screenshot_compare.py` 拒绝尺寸不一致和静默缩放。

## 5. 接口与规范策略

- 页面、Tab、商品卡、动作、按钮、Filter 和 Form 具备稳定且唯一的 ID；动态列表用业务身份而非索引作为 key；
- 叶子可点击控件显式暴露 Button 角色，Sort/Chip 等控件暴露 selected/checked 语义；
- 用户可见文案、颜色、错误和集合说明均资源化；货币走系统区域与 `Intl.NumberFormat`；
- 生产 ArkTS 避免 `any`、空事件、Tab、经典 `for`、非严格比较、正则字面量等已覆盖风险；
- 清单目标限制在仓内，归档拒绝凭据、个人路径、缓存、构建产物和符号链接。

## 6. 评审入口

评委可从 `work/migration-report.md` 进入页面、状态、资源、Form Kit、深链、安全区和规范证据，再用 `migration-manifest.json` 追踪源文件与 Journey，最后在 `work/entry/src/main/ets/` 抽查实际代码。这样能够把实现工作量与可运行交付件直接对应起来。
