# 安卓 APP 鸿蒙化：自动迁移调研与解题路线

> 调研日期：2026-07-11  
> 二次复核：2026-07-11  
> 适用对象：ICT 软件大赛“安卓 APP 鸿蒙化”赛题  
> 当前阶段：方案调研，不代表已完成鸿蒙重构；本轮未向 `work/` 引入任何第三方代码

## 0. 二次调研后的可行性结论

### 0.1 总体判断

原方案的核心方向——“确定性抽取/生成 + 有边界的 Agent + 编译/静态检查/双端验证”——**技术上可行，且仍是目前证据最充分的路线**。但原文把“通用 Compose→ArkUI 迁移编译器”放得过重，对本赛题固定验证工程而言，投入产出比不够高；部分验收门禁也过于绝对，可能导致本可获得部分用例分数的工程因为单个未覆盖能力而整体失败。

二次复核后的正式策略调整为：

```text
主得分轨：预生成并持续完善固定 Jetsnack 的完整原生鸿蒙仓
  ├── 编译、Code Linter、页面/交互/API、截图逐项闭环
  └── 裁判运行时只做幂等检查、必要的有限修复和结果定位

泛化支撑轨：轻量事实清单 + 迁移映射表 + Skill/脚本
  ├── 证明迁移过程可自动化、可追溯
  ├── 对公开工程可重复生成/校验关键文件
  └── 为可能变化的隐藏材料保留有限适应能力
```

不建议在比赛主线一开始就实现完整的 Kotlin 语义编译器、全组件 ArkUI 后端和任意 Android 项目迁移。该目标长期可行，但会显著挤压当前 Jetsnack 页面、交互、截图和规范对齐的时间。

### 0.2 对原方案的逐项裁定

| 原策略 | 二次结论 | 调整 |
|---|---|---|
| Stage + ArkTS + ArkUI 原生重构 | 保留 | 最符合静态检查与原生用例预期 |
| 确定性规则 + 局部 LLM | 保留 | 模型只做局部补全/修复，不负责最终验收 |
| App IR | 缩减后保留 | 先做迁移台账和测试契约，不先造通用编译器 |
| Kotlin Analysis API 作为主解析器 | 降为可选增强 | 其命令行 Standalone 模式仍在开发；主路径改为 tree-sitter/结构化扫描 + 运行时事实 |
| 所有未支持项使构建失败 | 否决 | 只对编译、交付合同和目标静态告警设硬门禁；功能覆盖按项报告并持续补齐 |
| 运行时由 Agent 从零生成完整仓库 | 降为兜底 | 最终 ZIP 应预置完整可构建仓，裁判阶段避免高随机、长耗时重生成 |
| VLM/视觉 Agent 自动操作 | 降为开发期探索工具 | 发现路径后固化成确定性 HDC/arkXtest 脚本，不放进五次评分主链 |
| 双端截图 + 交互回放 | 强化 | 增加统一 Journey DSL、稳定组件 ID、语义树和状态快照 |

Kotlin 官方说明：Analysis API 的命令行 Standalone 模式目前仍在开发并可能发生不兼容变化，官方唯一正式支持的场景仍是 IntelliJ IDEA 插件开发。因此它适合语义增强，不适合成为裁判运行时不可替代的单点依赖。[Kotlin Analysis API](https://kotlin.github.io/analysis-api/index_md.html)

### 0.3 比赛评分机制带来的关键调整

本地 [FAQ](FAQ.md) 明确说明：客观评测运行 5 次，“准确性”取最好一次通过数，“稳定性”看 5 次全部通过数；客观分 60 分（准确性 30、稳定性 30），主观分 40 分，其中性能参考 10 分；运行耗时和 Token 消耗会影响主观评价。平台当前以 CodeAgent/OpenCode 为主，模型包括 GLM 5.1、MiniMax M2.7，上下文窗口 200k，但不代表参赛 Python/Node 进程能直接获得模型 API。

由此得到以下硬原则：

1. 裁判主路径不得包含随机探索、无上限重试、人工确认、交互式覆盖询问或依赖网络临时下载。
2. 同一输入运行 5 次应产生相同文件、日志结论和退出码；时间、随机数、网络数据、设备状态均需固定或重置。
3. `INSTRUCTION.md` 是给平台主 Agent 的执行 Prompt，不是面向人的长篇 README；应短、命令化、路径明确、带完成判定和失败分支。
4. Skill 应使用渐进披露：主 `SKILL.md` 只负责路由，具体 ArkTS 规范、映射和诊断规则按需加载，避免一次占满 200k 上下文。
5. 平台 Agent 的模型能力用于理解说明和调用本地工具；作品内部模型 API只能是可选增强。

### 0.4 硬门禁与软门禁重新划分

**硬门禁**失败会导致整个作品无法评分，因此必须在交付前全部通过：

- `work/` 是完整鸿蒙仓且路径固定；
- 无人工交互，主命令有确定退出码和完成标记；
- 使用裁判同版本 SDK/Hvigor 可以编译；
- 目标 Code Linter 规则无告警；
- 必需配置、资源和入口 Ability 完整。

**软门禁**按隐藏用例逐项得分，不应因为一项失败阻断全部产物：

- 某个次要页面、动画、Widget 或异常状态尚未完全一致；
- 某张截图相似度低于内部目标；
- 某条非核心 Journey 失败；
- 某个长尾 API 尚未映射。

软门禁失败必须记录到机器可读报告并在本地开发阶段阻止“宣布完成”，但最终始终应保留可编译、可评分的最佳工程，而不是主动让整体构建失败。

## 1. 结论先行

本题最稳妥的解法不是让大模型一次性“翻译整个 Android 仓库”，而是建立一条可复现、可度量、可自动修复的混合流水线：

```text
Android 工程识别与基线运行
        ↓
Kotlin/Compose、资源、导航、状态、事件、接口的事实抽取
        ↓
轻量迁移台账与覆盖清单（按需扩展为 App IR）
        ↓
Stage 模型 + ArkTS + ArkUI 工程骨架和确定性代码生成
        ↓
检索官方文档/样例后进行“小范围、强约束”的模型补全
        ↓
编译错误驱动的有限轮自动修复
        ↓
Code Linter + 单元/UI 测试 + 双端截图差异 + 接口/路由覆盖检查
        ↓
始终保留可编译的 work/ 鸿蒙代码仓，并输出分级验收报告
```

这一判断有直接研究依据：面向 Jetpack Compose/SwiftUI 到 ArkUI 的 **ArkTrans** 采用“启发式元数据抽取、骨架生成、LLM 翻译、确定性后处理”组合；论文报告其直接提示基线没有生成任何可编译文件，而组合方案最高达到 90.67% 编译成功率，并以全局和局部视觉指标评估结果。[ArkTrans 论文](https://arxiv.org/abs/2606.07085)

因此，本项目建议：

1. 以确定性程序承担工程识别、轻量 IR/迁移台账、模板生成、映射规则、构建、静态扫描和验收；Agent/Skill 只负责编排与异常决策。
2. 模型一次只处理一个页面、组件或逻辑切片，输入输出都采用 Schema，并设置轮数和时间上限。
3. “编译成功”只是第一道门禁；必须同时量化页面、路由、交互、接口、资源、截图和规范覆盖。
4. 最终 `work/` 自身应预先包含完整、可独立编译的鸿蒙工程；自动化工具可放在 `work/tools/`，Skill 可放在 `work/skills/android-to-harmonyos/SKILL.md`。
5. 在裁判真实 SDK、API Version、设备分辨率和输入路径公开前，不应盲目锁死 SDK 版本或把网络模型服务作为唯一执行依赖。
6. 对固定 Jetsnack 工程优先完成真实页面和交互；通用迁移能力采用可渐进扩展的规则表证明，不让通用框架建设阻塞得分主线。

## 2. 赛题合同与本地基线

### 2.1 硬性要求

根据本地[赛题要求](android_to_harmoneyOS赛题要求.md)和[平台提交指导](PLATFORM赛题提交指导.md)，最终方案必须同时满足：

- 自动还原 Android APP 的界面、交互和功能；一致性直接影响隐藏用例通过率。
- 鸿蒙代码符合开发规范；静态扫描命中对应告警规则即可能丢分。
- `work/` 内提供重构后的完整鸿蒙代码仓。
- 项目根目录 `INSTRUCTION.md` 必须能指导裁判无人工交互地准备环境、执行、判断完成并获取最终仓库。
- 如果提交 Skill，其固定路径为 `work/skills/{skill-name}/SKILL.md`。
- 隐藏验证覆盖功能、截图、接口和代码规范；赛题不提供公开自验证用例。

这意味着“人工打开 DevEco Studio 后逐页调整”“运行中要求用户确认”“只交迁移说明或局部源码”“只证明 Android 基线能构建”都不构成完整交付。

### 2.2 当前验证工程不是 XML 老项目

当前 `work/` 已固定在比赛指定 Android 提交 `23e1421b72b602d80486777efbf24dd248abf3bb`。本地检查表明它是现代 Kotlin/Jetpack Compose 应用，包含：

- Compose、Material 3、Navigation Compose、Coil、Glance AppWidget；
- Feed、搜索/分类/筛选、商品详情、购物车、个人页等页面；
- 列表与网格、数量修改、滑动操作、折叠图片、动画、状态和导航；
- 图片、字体/颜色/字符串等资源以及桌面小组件能力。

因此，面向 Android XML 的转换器只能作为资源/XML 兼容支路，不能承担主迁移链。主链必须理解 `@Composable` 调用、Modifier、状态提升、ViewModel/Flow、Navigation、事件闭包、Lazy 容器、动画和 Glance。

## 3. 官方鸿蒙开发与质量约束

### 3.1 目标技术栈

建议以 HarmonyOS NEXT 推荐的 **Stage 模型 + ArkTS + ArkUI 声明式范式**为目标。Stage 模型以 UIAbility、WindowStage 等为核心，是官方推荐的长期应用模型；ArkUI 的声明式范式覆盖组件、布局、动画、状态与交互。[Stage 模型](https://developer.huawei.com/consumer/cn/arkui/arkui-stage/)、[ArkUI 开发入门](https://developer.huawei.com/consumer/cn/arkui/devstart/)

ArkTS 不是可以任意书写动态 TypeScript 的运行环境。其静态类型和对象布局约束会影响生成代码，例如应避免动态增删字段、宽泛 `any`、依赖结构类型兼容和不明确的对象字面量。迁移器应在代码生成和后处理阶段显式实施 ArkTS 规则，而不能等编译失败后全交给模型猜测。[ArkTS 官方入口](https://developer.huawei.com/consumer/cn/arkts/devstart/)、[ArkTS 英文概览](https://developer.huawei.com/consumer/en/arkts/)

### 3.2 构建、静态检查与测试必须都是流水线门禁

华为测试服务把下列能力列为应用质量链的一部分：

- Code Linter 静态扫描及自定义规则；
- Hypium/arkXtest 单元测试和 UI 测试；
- AppAnalyzer；
- 通过 Hvigor 命令行进行持续集成构建；
- codelinter 命令行接入 CI。[HarmonyOS 测试服务](https://developer.huawei.com/consumer/cn/testing/get-started/)

OpenHarmony 的 arkXtest 包括 JsUnit 和 UiTest，UiTest 可查找、操作 UI 组件，适合迁移后的关键路径回放。[arkXtest 指南](https://gitee.com/openharmony/docs/blob/ca4467409329c262b239693b7ba5e96185122ff6/en/application-dev/application-test/arkxtest-guidelines.md)、[arkXtest 源码仓](https://github.com/openharmony/testfwk_arkxtest)

正式实施时应以裁判环境实际安装的 SDK/Hvigor 为准，先探测版本和任务，再确定精确命令。`assembleHap` 等任务名可作为候选，但不应在尚未核验环境时写死为唯一命令。

### 3.3 编码规范策略

OpenHarmony ArkTS 编码规范区分强制要求与建议，并覆盖命名、类型、异常、并发、可维护性等内容。[OpenHarmony ArkTS 编码规范](https://gitee.com/openharmony/docs/blob/8e251bae7f55f10e36d7ce5bcb77bdf6b86e1bf1/zh-cn/contribute/OpenHarmony-ArkTS-coding-style-guide.md)

本题应把规范门禁设计为“默认零告警”，而不是只修已知规则：

1. 编译器错误必须为 0。
2. Code Linter 与项目配置启用的规则告警必须为 0；若存在无法消除的告警，需有机器可读白名单和充分理由，但不应假设裁判接受白名单。
3. 禁止使用 `any`、未使用导入、动态属性、空 catch、无处理 Promise、硬编码敏感信息、错误资源访问和不安全非空断言等高风险模式。
4. 生成器输出统一格式化，并保证同一输入重复运行不会持续改动文件。
5. 在每次自动修复后重新执行完整静态扫描，防止“修编译、添告警”。

## 4. 论文与方法调研

### 4.1 ArkTrans：与本题最贴合的研究路线

[ArkTrans](https://arxiv.org/abs/2606.07085)直接研究 Jetpack Compose/SwiftUI 到 HarmonyOS ArkUI 的声明式 UI 迁移，核心值得复用的是：

- 先通过启发式程序提取源 UI 元数据；
- 先生成 ArkUI 骨架，再让模型完成局部转换；
- 用确定性模式修复模型高频错误；
- 同时评估可编译性、全局视觉和元素级位置/尺寸/颜色/文本。

对本题的启示是：Compose 必须走“语义抽取 + 规则 + 模型”的混合方式；只比较整张图片也不够，局部组件偏移和文本错误应单独计分。论文页面表明存在复现实验包，但本次调研未找到可核验的公开仓库链接，因此当前只能复现其方法，不能把它当成可直接下载的工具。

### 4.2 UITrans：可借鉴的 ArkUI 生成与编译反馈实现

[UITrans 论文](https://arxiv.org/abs/2412.13693)和[UITrans 仓库](https://github.com/OpenSELab/UITrans)面向 Android XML 到 ArkUI，采用多 Agent 反思、检索和分层转换；论文报告组件、页面和项目级成功率分别为 90.1%、89.3% 和 89.2%。

本次对仓库提交 `b3775945a4e97b179b8c14664d75b1e8330bddc7` 做了代码级审阅，可借鉴：

- Android 页面拆解与 Harmony 页面组装的结构化提示；
- 使用 Harmony 组件文档/样例建立向量检索和重排；
- 通过 Hvigor 编译，解析 ArkTS 编译器错误并回灌修复；
- 对 `wrap_content`、`match_parent`、margin、行距等高频模式做确定性后处理；
- 使用空白 Harmony 工程模板进行最小组件编译验证。

但不建议原样纳入交付：

- 输入主链是 XML，不能理解本项目 Compose 状态与逻辑；
- 配置含 Windows 绝对路径以及硬编码凭据样式字段，不适合直接复制；
- 依赖外部模型、向量库、PyTorch，离线裁判部署成本较高；
- `pyproject.toml` 声明 MIT，但审阅提交未发现顶层 LICENSE 文件，直接复用代码前必须澄清许可证。

结论：参考其架构、提示 Schema、编译反馈和后处理规则；不要直接 vendor 整仓。

### 4.3 GUIMigrator：中间表示与确定性渲染器范式

[GUIMigrator 论文](https://arxiv.org/abs/2409.16656)与[Apache-2.0 仓库](https://github.com/testmigrator/guimigrator)采用“源 UI 解析 → 语义 IR → 平台渲染器”的结构，将 Android XML 转为 Compose/SwiftUI。论文在 31 个应用上的报告值为 Compose 81.9% SSIM、SwiftUI 78.2% SSIM，并显著降低人工工作量。

本次对提交 `0e2867079bee4c09040ee9cf0194f9f68846cbe7` 的解析器、IR、组件映射注册表和流水线实现做了审阅。值得复用的是：

- 将源解析和目标代码生成彻底解耦；
- 组件映射采用显式注册表，并记录 unsupported/fallback；
- 资源、样式和属性先规范化，再交给目标渲染器；
- 每阶段有计数、耗时和迁移覆盖指标。

它不支持 Compose，也没有 ArkUI 后端，因此更适合作为我们 `AppIR`、规则注册表、覆盖报告和 XML 兼容支路的设计参考。

### 4.4 ArkAnalyzer：ArkTS 结果仓的深层静态分析

[ArkAnalyzer 论文](https://arxiv.org/abs/2501.05798)针对 ArkTS/ArkUI 构建 AST/IR、控制流图、调用图和数据流分析，原因正是普通 JavaScript/TypeScript 分析器无法完整理解 ArkTS/ArkUI 扩展。当前项目仓位于 OpenHarmony SIG 的 [ArkAnalyzer](https://gitcode.com/openharmony-sig/arkanalyzer)。

它可用于：

- 检查页面、路由、事件处理器和接口方法是否可达；
- 生成迁移前后调用/依赖覆盖报告；
- 开发本题特定规则，如空事件、占位页面、永不触发的导航。

它不能代替裁判所用的官方 Code Linter；建议作为增强门禁，而不是唯一规范扫描器。

### 4.5 HarmonyOS-App-Test：模型化 GUI 遍历

[Model-based GUI Testing for HarmonyOS Apps](https://conf.researchr.org/details/ase-2024/ase-2024-artifact-evaluation-track/38/Model-based-GUI-Testing-For-HarmonyOS-Apps)及其[实验仓库](https://github.com/sqlab-sustech/HarmonyOS-App-Test)先从源码构建页面转换图，再通过 arkXtest 系统化探索 UI。

对仓库提交 `87a994446bdf9dcc4e5def9e244f34a122f9ba25` 的代码审阅表明，它可以抽取旧式 router 跳转，并以 DFS/随机策略点击组件。可借鉴页面转换图、可达性检查和系统化遍历；不能直接采用的原因包括：

- 基于较旧 DevEco/HarmonyOS 和 `@ohos.router` 假设；
- README 流程包含手工复制测试文件和打开模拟器；
- 随机行为难以复现；
- 需要扩展到现代 `Navigation`/`NavPathStack` 和当前 SDK。

### 4.6 Android/Harmony 双端截图与视觉指标

Android 官方建议为 Compose 使用截图测试，以参考图（golden）记录 UI，并以差异阈值或更智能的语义差异比较回归结果。[Android Compose 截图测试](https://developer.android.com/training/testing/ui-tests/screenshot)

可组合以下指标，而不是依赖单一 SSIM：

- 像素差：识别颜色、边距和细小绘制错误；
- SSIM：衡量结构相似；
- 全局感知指标：对整体布局和视觉风格更稳健；
- 元素级指标：组件位置、尺寸、颜色、文本内容；
- OCR/文本清单：避免图片看似相似但文案、数字或价格错误；
- 状态序列差异：同一操作前后分别截图，覆盖交互结果。

Android 基线候选工具：

- [Paparazzi](https://github.com/cashapp/paparazzi)：Apache-2.0，可在本机 JVM 渲染 Android/Compose 快照，适合稳定的组件和页面 golden。
- [Roborazzi](https://github.com/takahirom/roborazzi)：基于 Robolectric 的 record/compare/verify 和差异报告，适合 Compose 截图回归；正式引入前仍需核验目标版本许可证与兼容性。

Harmony 侧优先使用 arkXtest/HDC 驱动固定状态并截图。应固定设备分辨率、方向、字体缩放、语言、深浅色、状态栏/安全区和动画时钟，比较前只做明确定义的裁剪和色彩归一化，避免通过过度模糊掩盖偏差。

### 4.7 二次新增：ArkEval、APIKG4Syn 与 ArkTS-CodeSearch

第二轮调研又找到三项与“生成后能否编译、是否正确调用 HarmonyOS API”直接相关的研究：

- [ArkEval](https://arxiv.org/abs/2602.08866)从 400 余个官方应用中整理了 502 个可复现 ArkTS 问题，并研究检索增强的代码修复。它支持“按目标 SDK 检索相似官方代码 + 编译器诊断反馈”的做法，同时也说明单靠模型修复仍不足以形成可靠门禁。
- [APIKG4Syn](https://arxiv.org/abs/2512.00380)针对 HarmonyOS 低资源 API 使用构建知识增强生成；论文报告的最佳模型通过率仍明显有限。这进一步证明：官方 API、版本匹配样例和调用约束必须进入生成上下文，不能依赖模型记忆。
- [ArkTS-CodeSearch](https://arxiv.org/abs/2602.05550)使用 ArkTS 语法解析构建代码检索数据与模型，为“按组件/API 从已编译 ArkTS 代码中检索局部样例”提供了证据。

对本题的落地结论是：RAG 应检索同 API Version 的官方样例和本项目已验证代码；每次只修复一个诊断簇；修复是否接受必须由 Hvigor、官方 Code Linter 和回归测试决定。论文中的模型或数据集可以用于开发期实验，但不能成为裁判五次运行的在线依赖。

## 5. GitHub 工具与工作流适配结论

| 项目 | 可借鉴内容 | 与本题差距/风险 | 建议级别 |
|---|---|---|---|
| [UITrans](https://github.com/OpenSELab/UITrans) | ArkUI 模板、RAG、分层提示、编译错误反馈、确定性修复 | XML 主链、外部模型重、路径/凭据配置、许可证文件存疑 | 深度参考，选择性重写 |
| [GUIMigrator](https://github.com/testmigrator/guimigrator) | App IR、映射注册表、资源规范化、覆盖指标 | 无 Compose 输入、无 ArkUI 后端 | 架构复用优先 |
| [HarmonyOS-App-Test](https://github.com/sqlab-sustech/HarmonyOS-App-Test) | 页面转换图、DFS UI 探索 | API 偏旧、流程有人工步骤、随机性 | 改写测试思想 |
| [ArkAnalyzer](https://gitcode.com/openharmony-sig/arkanalyzer) | ArkTS CFG/调用图/数据流 | 不是官方 Code Linter | 可选增强门禁 |
| [arkXtest](https://github.com/openharmony/testfwk_arkxtest) | 官方单元与 UI 测试基础 | 需与裁判 SDK 对齐 | 应采用 |
| [OpenHarmony Samples](https://github.com/openharmony/applications_app_samples) | Navigation、布局、主题、网络、偏好、卡片等官方样例语料 | 样例是独立项目，需按 API Version 选择 | RAG/模板首选语料 |
| [Paparazzi](https://github.com/cashapp/paparazzi) | Android/Compose 本地 golden | 全应用动态状态仍需设备测试 | Android 视觉基线 |
| [Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM) | Apache-2.0；已有 HDC 启动、点击、滑动、截图封装 | 完整 Agent 依赖视觉模型；默认流程含交互式确认 | 只参考 HDC 封装 |
| [Kotlin Analysis API](https://kotlin.github.io/analysis-api/fundamentals.html) | 官方 PSI + 类型、符号、调用解析 | Standalone 模式仍在开发，集成和版本风险高 | 可选语义增强 |

官方 Kotlin Analysis API 建立在 Kotlin PSI 之上，可以解析调用目标、表达式类型、声明和诊断，比只看文本的 AST 更适合识别 Composable、扩展函数和间接调用；但其命令行 Standalone 模式尚不适合做比赛主链的单点依赖。[Analysis API](https://kotlin.github.io/analysis-api/index_md.html)、[Analysis API 文档仓](https://github.com/Kotlin/analysis-api)

### 5.1 二次新增工具的采用分级

| 工具/工作流 | 实际能力与证据 | 最终裁定 |
|---|---|---|
| [hmdriver2](https://github.com/codematrixer/hmdriver2) | MIT；封装 HDC 安装/启动/停止、截图、UI 树、选择器和输入，接口风格接近 uiautomator2 | **建议采用思想并固定版本**；为安全和可控性，主链宜只保留最小 argv 参数封装，避免其 `shell=True` 接收不可信参数 |
| [hmnextauto](https://github.com/ziguiway/hmnextauto) | hmdriver2 的活跃分支，增加图像匹配、OCR、性能采集 | **开发期候选**；项目很新、依赖较重，断言/报告仍不完整，不进入裁判硬依赖 |
| [Midscene Harmony](https://midscenejs.com/harmony-introduction) / [仓库](https://github.com/web-infra-dev/midscene) | MIT；可通过 HDC 和截图让 VLM 探索 Harmony 应用，支持 YAML/JS 与报告 | **仅本地探索**；发现旅程后转写为确定性脚本，禁止作为五次评分主链 |
| [DevEco CodeGenie MCP](https://www.npmjs.com/package/%40deveco-codegenie/mcp) | 可向 Agent 暴露 ArkTS 诊断、Hvigor 构建、启动、UI 树/操作和日志工具 | **本地 Agent 增强**；许可证未在包页明确，且部分能力需联网/VLM，暂不复制进交付件或设为必需依赖 |
| [tree-sitter-arkts](https://github.com/harmony-contrib/tree-sitter-arkts) | MIT；能解析 `.ets`、ArkUI `struct`、组件块、`@Extend` 等语法 | **建议开发期引入**；适合 AST、代码切片和自定义检查，但绝不能冒充类型检查器或官方 Code Linter |
| [tree-sitter-kotlin](https://github.com/tree-sitter-grammars/tree-sitter-kotlin) | MIT；轻量 Kotlin 语法树，便于扫描声明、调用和源码位置 | **建议作为事实清单主解析器之一**；无法确认符号解析的项标记为低置信度并由运行时/人工审阅补齐 |
| [arkts-patterns](https://github.com/OpeNopEn2007/arkts-patterns) | MIT；整理 ArkTS 状态、导航、网络等模式并提供 Skill/脚手架 | **只选用经目标 SDK 编译过的模式**；其模板版本和自报 benchmark 不等于本题隐藏用例，交互式覆盖询问也须移除 |
| [Dev-Assistant Harmony Skill](https://github.com/wwwyyyxl/Dev-Assistant) | MIT；强调证据收集、变更预算与验证闭环 | **参考 Skill 纪律**；不具备 Android→Harmony 迁移逻辑，不单独解决赛题 |
| [vscode-arkts](https://github.com/FadingLight9291117/vscode-arkts) | MIT；包含 ArkTS 编辑辅助和 HDC/MCP 封装 | **仅参考设备工具**；其部分诊断是正则近似，不能替代编译器/Code Linter |
| [test-harmonyos-apps](https://github.com/hu-qi/test-harmonyos-apps) | 提供 HDC 截图、UI dump、坐标选择等 Skill/脚本思路 | **只参考工作流**；未核验到许可证，不复制源码 |

上述工具没有一个能“一键”完成本题。最可用的组合是：`tree-sitter-kotlin` 做轻量源事实提取，规则/模板生成原生 ArkUI，`tree-sitter-arkts` 做结构检查，Hvigor + 官方 Code Linter 做最终裁决，arkXtest 或受控 HDC 驱动做确定性功能/截图回放。CodeGenie MCP、Midscene 和 VLM 只提高开发效率，不改变交付主链。

### 不建议作为主方案的做法

- **整仓一次性 LLM 翻译**：上下文、可编译性、可复现性和错误定位均不可控。
- **仅 XML 转换**：当前基线的主 UI 是 Compose。
- **仅截图/VLM 复刻**：可能外观相似，但导航、状态、接口和代码规范不可验证。
- **完整引入手机视觉 Agent**：常依赖外部服务和人工确认，违反无人值守要求。
- **把网页/Flutter/React Native 包装成鸿蒙应用**：若规则和隐藏静态检查期待原生 ArkTS/ArkUI，风险高于原生迁移。
- **使用来源不明的一键 linter/migration 脚本**：存在供应链、许可证和规则版本不一致风险。

## 6. 推荐的自动迁移架构

### 6.1 Android 事实提取层

先生成机器可读的 `android-facts.json`，至少包含：

- 工程模块、Gradle 插件、SDK、依赖、Manifest、权限、Activity/Service/Receiver/Widget；
- Composable 定义与调用树；
- `Row/Column/Box/LazyColumn/LazyGrid/Scaffold` 等布局和 Modifier 链；
- `remember`、State、Flow、ViewModel、参数和状态提升关系；
- NavHost、route、参数、deep link、返回行为；
- onClick、手势、滑动、输入、数量变更等事件和处理函数；
- 网络/本地接口、数据模型、错误/加载/空状态；
- drawable、图片、字符串、颜色、字体、尺寸和主题；
- 页面运行截图、组件语义树和关键用户旅程。

静态主路径采用 `tree-sitter-kotlin`、Gradle/Manifest/XML 专用解析器和有限结构化扫描，先得到可复现的语法事实；Kotlin Analysis API 只在可控的 IDE/版本环境中补充调用目标、类型和符号信息。动态运行的 Compose 语义树、截图和用户旅程用于补齐反射、条件分支、运行时尺寸和视觉事实。正则只做明确且有测试的小规则，不作为通用语义解析器。

### 6.2 渐进式平台无关台账 / App IR

第一阶段只需要 JSON/JSONL 迁移台账，覆盖源位置、目标位置、稳定 ID、状态和测试；确有自动生成需求时再扩展为以下版本化 IR，避免先为当前工程制造一套完整编译器：

```text
ProjectIR
├── ModuleIR / CapabilityIR / PermissionIR
├── ResourceIR / ThemeIR
├── ScreenIR
│   ├── ComponentIR（类型、属性、布局、样式、稳定 ID）
│   ├── StateIR
│   ├── InteractionIR
│   └── ApiBindingIR
├── NavigationGraphIR
└── TestJourneyIR
```

每个 IR 节点保留 Android 源文件和行号、目标 ArkTS 文件和符号、转换状态以及置信度。这样可生成“未迁移项清单”，也能防止模型悄悄删除难处理功能。

### 6.3 ArkUI 确定性映射层

首批规则可覆盖：

| Android/Compose | HarmonyOS/ArkUI 候选 | 验证重点 |
|---|---|---|
| Row / Column / Box | Row / Column / Stack | 排列、对齐、权重、层叠 |
| LazyColumn / LazyRow | List / ListItem | key、复用、滚动位置 |
| LazyVerticalGrid | Grid / GridItem | 列宽、间距、响应式 |
| NavHost / route | Navigation / NavPathStack | 参数、返回栈、深链 |
| remember / State / Flow | 对应 ArkUI 状态管理 | 所有权、双向更新、生命周期 |
| Modifier click/gesture/swipe | ArkUI 事件与手势 | 命中区域、冲突、反馈 |
| Coil/Image/resource | Image + 媒体/网络资源 | 裁剪、占位、失败图、缓存 |
| Dialog/Snackbar | ArkUI 弹窗/提示能力 | 时序、遮罩、可测试性 |
| Glance AppWidget | Form Kit/卡片能力 | 卡片声明、更新、跳转 |

卡片不是可忽略的外围功能：本项目包含 Glance AppWidget，应建立专门映射分支。HarmonyOS 的 Form Kit 支持卡片信息展示、轻量交互和页面跳转。[Form Kit](https://developer.huawei.com/consumer/cn/sdk/form-kit/)

所有组件规则都应有：输入 Schema、输出模板、资源转换、事件转换、兼容 API Version、单测和不支持时的显式错误。禁止无提示降级为空白组件。

### 6.4 受约束的模型补全层

模型仅处理规则难以覆盖的局部内容：复杂自定义布局、动画、业务逻辑重写和编译错误归因。建议约束：

- 输入包含单一 IR 切片、相关 Android 源码、目标 API Version、官方文档片段和允许 API 清单；
- 输出为 JSON Patch/文件补丁，而非自由文本；
- 禁止修改无关文件、构建配置和测试断言；
- 禁止联网获取不受控代码；
- 每类错误最多修复固定轮数，相同诊断不重复尝试；
- 模型不可用时，确定性规则仍能生成可诊断的工程和覆盖报告。

RAG 语料优先顺序：裁判 SDK API 文档 > 华为官方指南 > 与 API Version 匹配的 OpenHarmony 样例 > 已审计开源代码。不要把博客答案置于官方 API 之前。官方文档中心明确提供 ArkUI、ArkTS、Ability、资源和行业实践入口。[HarmonyOS 文档中心](https://developer.huawei.com/consumer/cn/doc/)

### 6.5 编译—修复闭环

```text
生成最小工程
→ 探测 Hvigor 版本/任务
→ 编译模块或最小组件
→ 结构化解析诊断（文件、行、规则、消息）
→ 先执行确定性修复器
→ 再调用局部模型修复
→ 格式化、静态扫描、重新编译
→ 达到轮数上限则失败并输出报告
```

完成状态必须由命令退出码和机器可读报告共同决定，不能以“Agent 认为完成”作为判定。

### 6.6 双端统一 Journey DSL 与可测试性契约

Android 和 Harmony 侧不应维护两套含义不同的自动化脚本。建议定义一个最小 Journey DSL：

```yaml
name: add_snack_to_cart
reset: clean
steps:
  - launch: app
  - tap: screen.feed.item.0
  - assertVisible: screen.detail
  - tap: detail.add_to_cart
  - assertText: { id: cart.badge, value: "1" }
  - screenshot: detail-added
```

同一 DSL 分别由 Android UIAutomator2/Compose 测试适配器与 Harmony arkXtest/HDC 适配器执行。每个关键组件使用跨端逻辑 ID，例如 `screen.feed`、`detail.add_to_cart`、`cart.qty.inc.<itemId>`；Android 通过 Compose semantics/`testTag` 暴露，Harmony 通过 ArkUI `.id()` 与无障碍文本暴露。[Compose Semantics](https://developer.android.com/develop/ui/compose/testing/semantics)、[Compose testTag](https://developer.android.com/reference/kotlin/androidx/compose/ui/platform/testTag.modifier)、[ArkUI 组件 ID](https://gitee.com/openharmony/docs/blob/3603a38ee6e0043b79dcf4ba42e4c806dca4f507/en/application-dev/reference/arkui-ts/ts-universal-attributes-component-id.md)、[ArkUI 无障碍属性](https://gitee.com/openharmony/docs/blob/7084dbcbc98086006a81c83224e0c45fa7f4d342/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-universal-attributes-accessibility.md)

稳定 ID 同时服务功能测试、截图元素对齐和无障碍规范，但不能改变视觉布局。无法设置 ID 的系统组件才退回文本/层级/坐标定位；坐标必须绑定固定设备规格，不能成为默认选择。

### 6.7 五次评分运行的确定性设计

根据比赛五次运行规则，裁判阶段应执行“验证优先、有限修复”，而不是每次从零迁移：

1. ZIP 内预置已经通过本地门禁的完整 Harmony 工程。
2. 主命令先检查 SDK/Hvigor/路径，再验证工程哈希、构建配置和依赖是否齐全。
3. 构建与 Code Linter 不需要网络安装依赖；尽量只使用 SDK 内置能力和已锁定依赖。
4. 若允许 Agent 修复，只能处理白名单诊断、固定轮数，并在失败时回退到本轮开始前的最佳可构建状态。
5. 每次测试前清除应用数据、固定语言/主题/字体/分辨率、关闭或等待动画、注入相同 fixture。
6. 报告排序、时间字段和临时路径归一化；相同输入产生相同产物与退出码。

这比“偶尔一次生成得更好”更贴合准确性与稳定性各占 30 分的计分方式，也能减少运行时长和 Token 消耗。

## 7. 面向隐藏评测的验证矩阵

| 隐藏评测维度 | 本地代理指标 | 验证信号 | 性质 |
|---|---|---|---|
| 功能完备度 | 页面、路由、按钮、手势、输入、状态、Widget 覆盖率 | Android 事实逐项有目标映射；检查 placeholder/empty handler | 软门禁，逐项得分 |
| 功能可用性 | 关键旅程的状态和输出一致 | 双端脚本回放；断言页面、文本、数量、列表和返回栈 | 软门禁，逐项得分 |
| 界面截图 | 像素差、SSIM、全局感知、元素位置/尺寸/颜色/文本 | 每个关键状态有 golden 和阈值；失败保存 diff | 软门禁，逐项得分 |
| 接口一致性 | 权限、路由参数、数据模型、网络/本地存储契约 | API 清单逐项映射；schema/fixture 测试 | 软门禁，逐项得分 |
| 代码规范 | 编译诊断、Code Linter、格式、ArkAnalyzer 增强规则 | 零编译错误、零目标告警、无禁用规则逃逸 | 硬门禁 |
| 工程交付 | 洁净环境构建、HAP 产物、固定输出路径 | 从 ZIP 解压后执行唯一命令；退出码 0；产物存在 | 硬门禁 |

### 建议的关键用户旅程

至少覆盖：

1. 启动 → Feed 页面正确显示。
2. Feed → 分类/搜索 → 结果和筛选。
3. 商品列表 → 商品详情 → 返回，滚动/折叠图片状态合理。
4. 商品详情 → 加入购物车。
5. 购物车数量增减、滑动操作和总计变化。
6. 底部导航切换，页面状态与返回栈符合 Android 基线。
7. 个人页展示和可触发入口。
8. 加载、空、错误等非快乐路径。
9. 桌面卡片展示、刷新和跳转（若评测设备支持）。

每一步都应保存“动作、前置状态、Android 截图/语义、Harmony 截图/语义、断言和差异”，便于定位是解析、映射、样式还是运行时问题。

## 8. 交付形态建议

在不改变“`work/` 就是完整鸿蒙仓库根目录”约定的前提下，推荐最终结构：

```text
INSTRUCTION.md
work/
├── AppScope/
├── entry/
├── build-profile.json5
├── hvigorfile.ts
├── oh-package.json5
├── migration-manifest.json
├── journeys/
│   └── *.yaml
├── tools/
│   ├── migrate...（开发期/有限兜底）
│   ├── verify...（裁判主入口，幂等）
│   └── schemas/...
├── skills/
│   └── android-to-harmonyos/
│       └── SKILL.md
└── reports/
    └── （运行时生成，不提交缓存/敏感信息）
```

其中：

- `work/` 打开即是鸿蒙项目，不能再套一层 `demo-Jetsnack-android/`。
- `work/` 在打包前就必须是最佳、完整、可构建的原生 Harmony 成品仓，不能等待裁判 Agent 从零生成。
- 自动迁移器和验证器是工程内的可选工具，不妨碍裁判直接构建；`verify` 是裁判主入口，`migrate` 只做开发期复现或受限兜底。
- Skill 只描述编排和失败策略，实际工作由可测试脚本执行。
- `INSTRUCTION.md` 作为平台主 Agent Prompt，应简短给出一条非交互主命令、环境探测、最终仓库路径、完成标记、构建命令和失败退出码，复杂知识下沉到 Skill/reference。
- `migration-manifest.json` 记录源提交、页面/路由/API/资源映射和未覆盖项；Journey 文件记录可重复的双端测试契约。
- 裁判主路径不得执行在线 `npm/pip/ohpm` 搜索安装，不得要求登录 DevEco、配置 VLM Key 或人工点击。
- 若平台后续给出隐藏 Android 输入路径，应先在临时目录生成，再把经过门禁的模块同步到固定 `work/` 工程；迁移脚本自身不能在覆盖输出时被删除。
- FAQ 所说的根目录 `result/`、`logs/` 可用于提交开发期执行证据和主观评审材料，但不能替代 `work/` 成品仓与 `INSTRUCTION.md`；其中不得包含密钥、个人路径或超大缓存。

当前平台指导中的材料路径仍是 `xxx` 占位符，这是交付合同风险。正式编写 `INSTRUCTION.md` 前必须以评测平台实际 README 为准确认：输入目录、是否联网、可用模型、时间/内存、Harmony SDK/API Version、模拟器/HDC、签名、最终路径和是否会对多个 Android 项目重复执行。不能凭空猜测这些参数。

## 9. 实施优先级

### P0：先保住可评测性

- 在 `work/` 直接创建并持续维护固定 Jetsnack 的完整 Stage/ArkTS/ArkUI 成品工程。
- 固化 SDK/Hvigor 探测与构建脚本。
- 接入 Code Linter，建立零告警门禁。
- 先实现启动、Feed、详情、购物车和底部导航等最高价值真实路径，始终保持可编译。
- 建立轻量事实清单、迁移台账和分级覆盖报告，不让通用 IR 框架阻塞页面实现。
- 写出幂等、离线、无人工步骤的验证入口和短版 `INSTRUCTION.md`。

### P1：提高功能与视觉通过率

- 完成 Jetsnack 业务状态、购物车、搜索/筛选和导航。
- 建立 Android golden 和 Harmony 截图采集。
- 实现像素、SSIM、文本和元素级差异。
- 加入关键旅程和页面转换图遍历。
- 迁移 Glance Widget 到 Form Kit 卡片。
- 为关键组件补齐跨端稳定 ID、语义和无障碍属性。
- 在同一环境连续执行五轮回归，统计最好通过数和五轮全通过数。

### P2：提高通用自动迁移能力

- 扩充 Compose/Modifier/状态/动画映射注册表和轻量 IR。
- 建立官方样例 RAG 索引和局部模型修复。
- 视需要接入 Kotlin Analysis API 语义增强，而非设为迁移器启动前提。
- 引入 ArkAnalyzer 增强检查。
- 支持 XML/View 混合项目、多个模块和更多 Android 能力。
- 统计每条规则的成功率，按失败类型迭代。

## 10. 可量化的阶段验收标准

下一阶段实施时建议以以下标准判断，而不是凭肉眼宣布完成：

- 洁净环境执行主命令无人工输入，退出码为 0。
- `work/` 是完整 Harmony 工程，能够由命令行生成 HAP。
- 编译错误为 0；目标 Code Linter 告警为 0。
- Android 页面、路由、事件、接口、资源映射以 100% 为开发目标；所有未覆盖项必须显式进入报告，但只有编译、交付合同和目标静态告警等硬门禁失败才使主命令失败。
- 所有关键旅程通过，且结果可重复。
- 同一环境连续执行五轮，核心旅程、构建和规范检查五轮全通过；每轮从固定状态开始。
- 所有关键截图都有差异报告，不以主观“看起来接近”代替指标。
- 不包含密钥、个人绝对路径、Gradle/DevEco 缓存、构建产物污染和未经许可的第三方源码。
- `INSTRUCTION.md` 在新目录中按原文执行可完成环境检查、迁移、验证和结果定位。

## 11. 风险与待确认项

1. **裁判环境**：HarmonyOS SDK/API Version、Hvigor、DevEco CLI、HDC/模拟器和签名条件未知。
2. **执行合同**：平台材料路径仍为占位符；是否会用其他隐藏 Android 仓检验迁移泛化能力尚未完全明确。
3. **联网/模型**：若裁判禁网或没有模型密钥，依赖在线 LLM 的方案会直接失败，必须有离线确定性主路径。
4. **视觉环境**：分辨率、字体、系统栏、语言、主题不固定会造成截图噪声，应由评测合同或脚本统一。
5. **API 差异**：Android 能力不一定有一对一 Harmony API，需要显式适配而非静默删除。
6. **第三方许可证**：UITrans 等候选项目在实际复制代码前需要逐文件确认许可证；目前只做方法参考。
7. **规则漂移**：官方 Code Linter/ArkTS 规则会随 SDK 更新，必须使用裁判同版本验证。

## 12. 最终建议

本题应实施为“预生成的固定成品仓 + 确定性迁移/验证工具 + 有边界的 Agent”，而非单一提示词项目或运行时从零翻译。近期最有价值的工作顺序是：

1. 从平台正式说明确认裁判 Harmony SDK/CLI、输入输出和网络合同；未知项用环境探测而非猜测处理。
2. 在 `work/` 建立可构建、零告警的原生 ArkUI 成品工程，先完成 Jetsnack 高价值真实路径。
3. 用 tree-sitter/专用解析器生成轻量事实清单、稳定 ID 表和迁移台账；运行时语义/截图作为事实真值。
4. 实现高频 Compose→ArkUI 映射和覆盖报告，Kotlin Analysis API 仅按需补充复杂符号语义。
5. 使用统一 Journey DSL 在 Android 与 Harmony 双端回放，逐项对齐状态、接口和截图。
6. 连续五轮执行构建、Code Linter、关键旅程和视觉回归，消除随机性与环境残留。
7. 最后才接入官方样例 RAG、CodeGenie MCP 或受约束模型补全，提高长尾覆盖；这些能力不得成为裁判硬依赖。

这条路线同时对应四类隐藏评分：IR/旅程保证功能和接口不遗漏，截图闭环提高视觉一致性，Stage/ArkTS/ArkUI 模板与 Code Linter 保证规范，固定构建和完成协议保证平台真正能够执行和取件。

## 参考资料索引

- HarmonyOS：[官方文档中心](https://developer.huawei.com/consumer/cn/doc/)、[ArkUI](https://developer.huawei.com/consumer/cn/arkui/)、[ArkTS](https://developer.huawei.com/consumer/cn/arkts/devstart/)、[测试服务](https://developer.huawei.com/consumer/cn/testing/get-started/)、[最佳实践](https://developer.huawei.com/consumer/cn/best-practices/)
- OpenHarmony：[应用样例](https://github.com/openharmony/applications_app_samples)、[arkXtest](https://github.com/openharmony/testfwk_arkxtest)、[ArkTS 编码规范](https://gitee.com/openharmony/docs/blob/8e251bae7f55f10e36d7ce5bcb77bdf6b86e1bf1/zh-cn/contribute/OpenHarmony-ArkTS-coding-style-guide.md)、[组件 ID](https://gitee.com/openharmony/docs/blob/3603a38ee6e0043b79dcf4ba42e4c806dca4f507/en/application-dev/reference/arkui-ts/ts-universal-attributes-component-id.md)、[无障碍属性](https://gitee.com/openharmony/docs/blob/7084dbcbc98086006a81c83224e0c45fa7f4d342/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-universal-attributes-accessibility.md)
- 迁移与代码生成研究：[ArkTrans](https://arxiv.org/abs/2606.07085)、[UITrans](https://arxiv.org/abs/2412.13693)、[GUIMigrator](https://arxiv.org/abs/2409.16656)、[ArkEval](https://arxiv.org/abs/2602.08866)、[APIKG4Syn](https://arxiv.org/abs/2512.00380)、[ArkTS-CodeSearch](https://arxiv.org/abs/2602.05550)
- 分析与测试：[ArkAnalyzer](https://arxiv.org/abs/2501.05798)、[HarmonyOS 模型化 GUI 测试](https://conf.researchr.org/details/ase-2024/ase-2024-artifact-evaluation-track/38/Model-based-GUI-Testing-For-HarmonyOS-Apps)、[Android Compose 截图测试](https://developer.android.com/training/testing/ui-tests/screenshot)、[Compose Semantics](https://developer.android.com/develop/ui/compose/testing/semantics)
- 解析与设备工具：[Kotlin Analysis API](https://kotlin.github.io/analysis-api/index_md.html)、[tree-sitter-kotlin](https://github.com/tree-sitter-grammars/tree-sitter-kotlin)、[tree-sitter-arkts](https://github.com/harmony-contrib/tree-sitter-arkts)、[hmdriver2](https://github.com/codematrixer/hmdriver2)、[Midscene Harmony](https://midscenejs.com/harmony-introduction)
- Agent/Skill 参考：[DevEco CodeGenie MCP](https://www.npmjs.com/package/%40deveco-codegenie/mcp)、[arkts-patterns](https://github.com/OpeNopEn2007/arkts-patterns)、[Dev-Assistant](https://github.com/wwwyyyxl/Dev-Assistant)
