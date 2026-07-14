# Jetsnack 鸿蒙化交付设计

> 日期：2026-07-11  
> 状态：已批准实施；用户已明确要求按照《安卓APP鸿蒙化自动迁移调研与解题路线》持续执行直至可交付。

## 1. 目标与边界

在提交根目录直接交付：

- `work/`：可独立打开、命令行构建的 Stage 模型 HarmonyOS 工程；
- `INSTRUCTION.md`：平台唯一正式入口，描述非交互构建、验证、完成判定和最终仓位置；
- `introduction.md`：满足用户字面命名需求，但只作为兼容说明，不能替代大写正式入口；
- `work/skills/android-to-harmonyos/SKILL.md`、迁移台账、Journey 和验证脚本：证明重构过程可自动编排、可追溯、可重复；
- `docs/鸿蒙化实现方法与进展.md`：持续记录方法、实现状态、验证证据与剩余风险；
- `result/`、`logs/`：按大赛较严格口径提供主观评审证据。

公开验证工程固定为 `demo-Jetsnack-android` 的 `23e1421b72b602d80486777efbf24dd248abf3bb`。最终交付以原生 ArkTS/ArkUI 成品为主，不在裁判阶段从零随机生成，也不依赖外网、模型密钥、人工登录或 GUI 点击。

## 2. 方案比较与选择

### 方案 A：原生成品仓 + 确定性迁移/验证工作流（采用）

先完整迁移当前 Jetsnack，再用事实清单、映射台账、Skill 和脚本保存迁移过程。优势是页面、交互、截图和 Code Linter 能逐项优化，五次运行稳定；代价是通用转换能力采用渐进式规则，而非一次覆盖任意 Android 应用。

### 方案 B：先实现通用 Compose→ArkUI 编译器（暂缓）

泛用性更强，但 Kotlin 语义、Modifier、状态、动画和组件映射工作量会阻塞固定 Jetsnack 得分。只保留轻量事实提取和显式映射清单，后续按隐藏材料合同扩展。

### 方案 C：Web/Flutter/截图壳或纯 VLM 复刻（拒绝）

开发快，但接口、状态、无障碍、静态检查和原生规范风险高，且 VLM 操作不适合五次无人值守评测。

## 3. 技术架构

### 3.1 工程

- Stage 模型；一个 `entry` HAP 模块；ArkTS + ArkUI 声明式 UI。
- `bundleName` 保持 `com.example.jetsnack`，入口为 `EntryAbility`。
- 新应用以 HarmonyOS 6.0.0 API 20 为目标，最低兼容 API 12；所有业务代码限制在通用 API 范围。若裁判声明其他 SDK，以正式环境合同为准调整构建配置。
- 不引入运行时三方 OHPM 依赖；图片、字体、字符串和静态数据全部随仓提供。
- 开发期优先安装 DevEco Studio 6.0.1 与配套 SDK；真实构建、Code Linter 和设备结论必须来自实际命令，不能以语法目测替代。

### 3.2 模块边界

```text
entry/src/main/ets/
├── entryability/EntryAbility.ets   # Ability 生命周期与深链入口
├── pages/Index.ets                 # 根页面、路由状态和底栏
├── model/                          # Snack、OrderLine、筛选与稳定 ID
├── data/                           # 静态商品、集合、搜索和购物车初值
├── state/                          # AppStore、搜索状态、购物车动作
├── theme/                          # 色板、字体、尺寸、渐变
├── components/                     # 商品卡、底栏、数量器、筛选控件
└── screens/                        # Feed/Search/Cart/Profile/Detail/Filter
```

每个文件只承担一个职责。根页面维护当前 Tab、详情来源和返回关系；业务状态集中在 `AppStore`，页面只渲染状态并发出动作。关键组件暴露稳定 `.id()` 和无障碍文本。

### 3.3 状态与导航

- 主 Tab：`home/feed`、`home/search`、`home/cart`、`home/profile`。
- 详情逻辑路由：`snack/{stableSnackId}?origin={route}`。
- Feed/Search/Cart 各自保存滚动或输入状态；从详情返回恢复来源页面。
- Search 保持 Android 四态：Categories、Suggestions、Results、NoResults；匹配为大小写不敏感的本地 `contains`。
- Cart 初值、价格单位、运费和第五次数量操作失败行为与 Android 一致。
- 原 Android 明确为空操作的按钮保持 no-op；不凭空改变业务语义。
- 内部 ID 改为固定顺序 ID，避免 Android `Random.nextLong()` 导致五次运行不一致。

## 4. UI 与资源还原

- 原样迁移 36 张食品 JPEG、Montserrat/Karla 字体及许可文件。
- Light 主题以 `#4B30ED` 品牌紫、`#86F7FA` 辅色、白色背景为核心；同时提供 Dark token，但先保证公开 Light 截图。
- Feed 保留 56vp 地址栏/筛选栏/底栏、170×250vp Highlight 卡、120vp 圆图、24vp 标题边距。
- Search 保留 2 列分类卡、56vp 搜索栏和建议/结果/空状态。
- Cart 保留 100vp 图片、三条初始订单、金额汇总、数量和删除操作。
- Detail 保留渐变头部、圆图、标题/价格、Details、SEE MORE、Ingredients、推荐区、数量器和底部按钮。
- 无限渐变和异步图片淡入改为确定性静态首帧或有限动画，减少隐藏截图漂移。
- 先适配常见手机宽度，再检查平板、大字体、深色和 RTL。

## 5. 自动化迁移与平台入口

`work/skills/android-to-harmonyos/SKILL.md` 负责：识别输入、读取迁移台账、调用事实检查、验证预置成品、有限诊断修复和完成判定。脚本负责机械动作，Agent 不直接自由覆盖全仓。

`migration-manifest.json` 逐项记录源页面/路由/动作/数据/资源、目标符号、稳定 ID、实现状态和 Journey。`tools/verify.sh` 是裁判唯一主命令，顺序为：

```text
预检 → 结构/台账契约 → Hvigor 构建 → Code Linter（若环境提供）
→ 单元/UI 测试（若设备提供）→ 产物/报告判定
```

构建或规范硬门禁失败必须非零退出；设备缺失应明确报告为环境不可用，不伪报 UI 通过。功能/截图软门禁逐项报告，不销毁当前最佳可构建工程。

## 6. 测试策略

### 6.1 测试先行

实现新行为前先增加契约或状态测试并确认失败，再写最小 ArkTS 实现。配置/资源等生成性内容以结构测试先行；设备 UI 以 Journey 断言先行。

### 6.2 测试层级

1. 静态交付测试：目录、配置、资源、稳定 ID、禁止模式和迁移台账完整性。
2. 纯状态测试：搜索匹配、Cart 增减/删除/金额、详情数量、第五次失败。
3. Hvigor/Hypium：编译与模型单元测试。
4. arkXtest/HDC：启动、四 Tab、搜索、详情、Cart、返回和截图。
5. 五轮稳定性：每轮清状态，固定语言/主题/字体/分辨率，输出相同退出码和核心结果。

关键公开文本必须保持精确：`HOME`、`Android's picks`、`SEARCH`、`Categories`、`MY CART`、`Order (3 items)`、`PROFILE`、`This is currently work in progress`、`Chips`、详情 Lorem ipsum。

## 7. 错误处理与回退

- SDK/Hvigor 缺失：预检给出发现路径和明确安装要求，非零退出。
- Code Linter 缺失：开发期不宣称零告警；裁判若提供则必须执行并接受其结论。
- 允许的自动修复只处理白名单编译诊断，固定轮数；重复诊断立即停止。
- 修复失败回到本轮开始前的最佳可构建文件，不能留下半生成仓。
- 不自动联网安装依赖，不要求 DevEco 登录，不向裁判提问。

## 8. 完成判定

完成需要同时满足：

1. `work/` 是完整 Harmony 工程且不存在交付必需项占位符；
2. 根 `INSTRUCTION.md` 可指导非交互执行，`introduction.md` 不与其冲突；
3. 实际 Hvigor 命令退出 0 并生成 HAP；
4. 实际 Code Linter 在目标规则下无告警，或明确记录裁判工具尚未提供而不虚报；
5. 核心状态测试通过，设备可用时核心 Journey 与截图完成；
6. 同一环境五轮硬门禁全部通过；
7. 受控打包不含 `.git`、缓存、个人绝对路径、Android APK、密钥或未经许可源码；
8. 进展文档、迁移台账、结果和日志与真实验证证据一致。

