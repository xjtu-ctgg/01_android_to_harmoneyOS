# 人工交互与项目决策记录

> 本文件是提交件的人工交互摘要，供评委了解目标、取舍、验证边界和最终交付定位。记录的是可审计的输入、决定与行动，不包含模型私有推理过程。

## 1. 参赛者目标

参赛者将本题目标确定为：以比赛指定 Android 基线为事实来源，交付一个完整、可构建、原生的 HarmonyOS Stage/ArkTS/ArkUI 工程，并尽量同时满足功能、截图、接口和规范四类隐藏验证。

固定输入基线为：

- 仓库：`fuxi-artifacts/demo-Jetsnack-android`
- 提交：`23e1421b72b602d80486777efbf24dd248abf3bb`
- 最终代码仓：`work/`
- 交付形式：同名作品根目录中的 `INSTRUCTION.md`、`work/`、`result/` 和 `logs/`

参赛者特别确认：`work/` 是最终鸿蒙代码仓，不再嵌套 `demo-Jetsnack-android/`；作品通过 ZIP 提交，不需要向源 GitHub 仓库回传代码。

## 2. 评分与交付合同的理解

根据比赛说明，平台通过根目录 `INSTRUCTION.md` 启动作品，随后读取 `work/` 中的 Skill/Agent/代码；`result/` 和 `logs/` 是选手自验证及人工过程材料，主要供评委进行主观评价。

本题解题要求被拆为四个工程目标：

1. 功能一致：页面、路由、交互、状态、错误/空状态和外部入口可触发并符合 Android 行为。
2. 截图一致：布局、字体、颜色、资源、系统栏、安全区、主题、方向和大字体状态可复现。
3. 接口一致：稳定组件 ID、无障碍语义、深链、Form Kit、资源和配置契约可被自动化用例定位。
4. 规范一致：使用原生 Stage/ArkUI/ArkTS，避免静态检查对应的高风险写法，并保留官方 Code Linter 在评分环境执行的入口。

因此没有把“能生成一个 HAP”当作唯一完成标准，而是建立了源码事实、映射台账、Journey 和静态合同四层证据。

## 3. 参赛者确认的关键决策

| 决策 | 参赛者要求/确认 | 实施结果 |
| --- | --- | --- |
| 交付根目录 | `work/` 直接作为完整鸿蒙仓，不再包一层 Android 仓库目录 | `work/AppScope`、`work/entry`、`work/build-profile.json5` 等构成 Stage 工程 |
| 技术路线 | 采用原生 HarmonyOS Stage + ArkTS + ArkUI | 未使用 Web、Flutter 或跨端壳替代原生页面 |
| 自动化方式 | 提供 Skill/工作流，但最终评分优先验证预先完成的最佳仓 | `work/skills/android-to-harmonyos/SKILL.md`、`migration-manifest.json`、`journeys/core.yaml` 和 `tools/` 均随仓交付 |
| 基线事实 | 所有迁移结论以指定提交为准 | `work/source-facts/` 保存离线源码/资源/公开测试事实，清单记录 34 项映射 |
| UI 重点 | 不能只做页面静态截图，要覆盖状态、手势、返回栈和隐藏边界 | Feed/Search/Cart/Profile/Detail/Filter、导航、深链、Form Kit 和错误路径均有实现及 Journey |
| 多设备 | 批准按窗口避让区处理刘海、挖孔、导航指示条、横屏和平板 | `EntryAbility.ets` 读取系统避让区，`Index.ets` 将像素转换为 vp 并动态布局 |
| 小组件 | 批准将 Android Glance 小组件迁移为 HarmonyOS Form Kit | `RecentOrdersForm.ets`、`RecentOrdersFormAbility.ets` 和 `form_config.json` 提供 2×2/2×4/4×4 及购物车跳转 |
| 说明书 | `INSTRUCTION.md` 面向平台 Agent，只保留输入、执行、完成判定和产物 | 当前主路径为只读 `sh work/tools/platform_ready.sh`，编译命令只作为工具链环境下的工程说明 |
| 结构材料 | 根据平台结构门禁补齐 `result/output.md`、`logs/interaction.md` 和 `logs/trace/` | 当前提交包包含完整过程材料，且不把这些材料替代 `work/` 成品仓 |
| 稳定性 | 发现平台复现成功但稳定性交集为零后，优先消除执行路径差异 | 固定相对 `artifact_path=work`，禁止运行时重生成/联网安装/递归复现，入口脚本只读幂等 |

## 4. 实施过程摘要

### 4.1 调研与方案裁定

先对赛题、平台合同、FAQ、HarmonyOS 官方开发规范、UiTest/arkXtest、截图测试和 Android→ArkUI 迁移研究进行调研。调研结论是：通用“整仓一次性 LLM 翻译”难以保证编译、截图和重复运行；更稳妥的方式是“确定性事实抽取 + 迁移台账/轻量 IR + 原生代码实现 + 有边界 Agent + 编译/静态/旅程门禁”。

参考 ArkTrans、UITrans、GUIMigrator、ArkAnalyzer 和 HarmonyOS-App-Test 的可迁移思想，但没有将外部仓库未经审计地复制进提交件。外部模型、网络检索和 VLM 只作为开发期辅助，平台主路径不依赖它们。

### 4.2 基线审计与目标建模

固定 Android 提交被整理为 `android-facts.json`、源码快照、资源事实和公开测试契约。事实层覆盖：

- 6 个页面、6 条路由、10 个 no-op/业务动作边界；
- 28 个商品、5 个 Feed 集合、初始购物车行及金额/失败周期；
- 搜索四态、200ms 延迟与最新查询胜出规则；
- 颜色、字体、图片、向量 path、尺寸、主题和本地化/货币格式化；
- Manifest 中的 Recent Orders Widget、深链、窗口键盘模式和返回语义。

每项目标都在 `migration-manifest.json` 中记录源文件、目标文件、稳定 ID、Journey 和 `implemented` 状态，避免模型或人工修复时静默删除难处理功能。

### 4.3 原生迁移与视觉/交互对齐

迁移优先实现共享状态和公共组件，再实现页面切片。重点对齐内容包括：

- `AppStore.ets` 集中管理 Tab、搜索、购物车、详情和筛选状态，冷启动使用工厂复制，避免跨用例共享可变数据；
- Feed、Search、Cart、Profile、Detail、FilterOverlay 使用原生 ArkUI，保留源代码中的 no-op，不擅自发明状态变化；
- 字体、图片和向量资源本地化，颜色/字符串进入资源文件，货币通过系统区域和 `Intl.NumberFormat` 格式化；
- Cart 侧滑删除阈值、速度边界、Snackbar FIFO/4000ms 生命周期、数量归零删除和金额汇总与 Android 源码逐项对齐；
- Detail Hero、标题吸顶、Filter 面板、Cart 底栏、Search 网格、长标题和大字体均使用最小尺寸/自然测量，而不是把默认尺寸误写成不可增长的固定高度；
- 系统避让区按 TYPE_SYSTEM、TYPE_NAVIGATION_INDICATOR 和 cutout 处理，BottomNav 在 Tab 页面延伸到品牌色安全区，Detail 隐藏 BottomNav 后单独避让；
- 关键叶子控件补充稳定 `.id()`、无障碍文本、Button/selected/checked 语义，避免“可点击但自动化无法定位”。

### 4.4 对抗验证与持续修正

采用“先新增失败合同，再修改最小生产代码，最后完整回归”的方式。对抗覆盖搜索空格/大小写/延迟、Cart 失败与删除边界、Filter 重开、深链冷暖启动、系统返回、RTL、主题、大字体、窄屏/平板、横屏挖孔、Form Kit 尺寸、触控热区、资源解析、ArkTS 规则和缓存污染。

每次修正都要求同时通过：合同检查、仓内 Python 测试、ArkTS/API 20 构建（在工具链可用时）、归档审计和独立只读复现。没有真机、官方 Code Linter 或隐藏平台用例时，日志明确标记为“待评分环境提供证据”，不把代理测试写成官方满分。

## 5. 平台结果复盘与稳定性修复

`docs/log_7_16.txt` 的旧结果是交付审查通过，237 个用例准确性 230、稳定性 103，且复现阶段出现失败。由于日志没有失败用例名称，不能把它武断归因于某一个按钮；复核发现旧说明把构建/工具链准备放在平台 Agent 主路径，并混入了较多开发者上下文，给不同执行留下了不同分支。

`docs/log_7_17.txt` 中交付审查和复现均成功，准确性达到 262/262，但稳定性为 0。这表明至少有一次完整评分能够读取和评估当前工程，风险集中在独立运行之间的交接一致性，而不是 ZIP 结构缺失。

为此执行了以下修复：

1. 新增 `work/tools/platform_ready.sh`，只检查必要文件是否存在，不写入、不构建、不联网、不依赖 Python 或 HarmonyOS SDK。
2. 将成功标记和 `artifact_path=work` 固定为相同文本，避免临时执行目录绝对路径进入后续解析。
3. 将迁移 Skill 的完成仓规则和 Agent 元数据改为“审计既有仓”，禁止评分时从 Android 重新生成或覆盖 `work/`。
4. 把本地构建、合同测试和多轮归档预演降为交付前自检，不让平台 Agent 递归启动本地复现工具。
5. 重新做独立解压、只读权限、输出逐字节比较、结构审计和压缩完整性检查。

## 6. 证据边界

当前日志可证明：交付仓完整、源码映射可追溯、静态合同通过、平台入口确定、归档可解压、只读复现输出一致。以下证据仍必须由评分环境提供：正式 HarmonyOS 专有 SDK/签名构建、官方 Code Linter 全量报告、真实设备/模拟器组件树和 PNG、平台非公开用例最终通过数。

这一区分是有意保留的：它既向评委展示完整工程工作量，也避免把本地代理或研究结论冒充不可获得的官方评分结果。

## 7. 评委阅读路径

建议按以下顺序审阅：

1. 先看本目录 `trace/README.md` 了解证据索引；
2. 看 `trace/01-research-and-baseline.md` 了解为什么采用确定性混合路线；
3. 看 `trace/02-migration-and-architecture.md` 对照 `work/migration-report.md` 和 `work/migration-manifest.json`；
4. 看 `trace/03-hidden-case-and-quality.md` 了解功能、截图、接口和规范的覆盖方式；
5. 看 `trace/04-delivery-and-stability.md` 了解平台结果复盘、稳定性修复和最终归档证据；
6. 最后直接打开 `work/entry/src/main/ets/`、`work/journeys/core.yaml` 和 `work/tools/tests/` 抽查实现与门禁。
