# Jetsnack HarmonyOS Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将指定 Jetsnack Android 基线重构为 `work/` 内完整、可编译、可自动验证的原生 HarmonyOS 应用，并补齐平台入口与过程资产。

**Architecture:** Stage 模型单 `entry` HAP，ArkTS/ArkUI 原生 UI；`AppStore` 集中管理搜索、购物车和详情状态，页面组件通过稳定 ID 暴露测试契约。预置成品仓负责稳定评分，Skill、迁移台账、Journey 和验证脚本负责自动化过程与泛化证据。

**Tech Stack:** HarmonyOS 6.0 API 20（最低兼容 API 12）、Stage、ArkTS、ArkUI、Hvigor、Code Linter、Hypium/arkXtest、POSIX shell、Python 3 标准库。

---

## 文件结构锁定

```text
INSTRUCTION.md
introduction.md
docs/鸿蒙化实现方法与进展.md
work/
├── AppScope/app.json5
├── build-profile.json5
├── hvigorfile.ts
├── hvigor/hvigor-config.json5
├── oh-package.json5
├── migration-manifest.json
├── source-facts/android-facts.json
├── journeys/core.yaml
├── entry/
│   ├── build-profile.json5
│   ├── hvigorfile.ts
│   ├── oh-package.json5
│   └── src/main/
│       ├── module.json5
│       ├── ets/{entryability,pages,model,data,state,theme,components,screens}/
│       └── resources/{base,dark,en_US}/
├── skills/android-to-harmonyos/{SKILL.md,references/}
└── tools/{verify.sh,preflight.sh,contract_check.py,tests/}
```

Android Gradle 文件在 Harmony 工程完成且源事实已固化后从最终交付树移除；删除前用 `git archive` 在 `/tmp` 保存只读基线快照，最终 ZIP 不包含该临时文件或 `.git`。

### Task 1: 建立失败的交付合同测试

**Files:**
- Create: `work/tools/tests/test_delivery_contract.py`
- Create: `work/tools/contract_check.py`
- Create: `work/source-facts/android-facts.json`
- Create: `work/migration-manifest.json`

- [ ] **Step 1: 写结构测试，声明 Harmony 工程必须存在**

测试逐项断言 `AppScope/app.json5`、根/模块 `build-profile.json5`、`module.json5`、`EntryAbility.ets`、`Index.ets`、`migration-manifest.json`、Skill 和 Journey 存在；扫描个人绝对路径、密钥特征、`any`、空事件占位和 Android 构建产物。

- [ ] **Step 2: 运行测试并确认因 Harmony 文件缺失而失败**

Run:

```bash
python3 work/tools/tests/test_delivery_contract.py
```

Expected: `FAIL`，首个原因是 `work/AppScope/app.json5` 或其他 Harmony 标记缺失，而不是测试脚本语法错误。

- [ ] **Step 3: 固化源事实与映射 Schema**

`android-facts.json` 写入源提交、模块、六个页面、六条逻辑路由、28 个商品、三条 Cart 初值、资源、关键文本和 no-op 契约；`migration-manifest.json` 每项包含：

```json
{
  "source": "ui/home/Feed.kt",
  "target": "entry/src/main/ets/screens/FeedScreen.ets",
  "stableId": "screen.feed",
  "status": "planned",
  "journey": "core.feed"
}
```

- [ ] **Step 4: 实现只读合同检查器**

`contract_check.py` 读取 JSON，验证路径、唯一 ID、合法状态、映射重复、必需文本和文件存在；只输出稳定排序结果，不写业务源码。

- [ ] **Step 5: 重跑测试，预期仍只因工程文件缺失而失败**

Run: `python3 work/tools/tests/test_delivery_contract.py`  
Expected: 源事实和 JSON Schema 相关断言通过，Harmony 骨架断言仍失败。

### Task 2: 安装和锁定真实 Harmony 工具链

**Files:**
- Modify: `docs/鸿蒙化实现方法与进展.md`
- Create: `work/tools/preflight.sh`

- [ ] **Step 1: 获取官方 Apple Silicon DevEco Studio/Command Line Tools**

优先版本为 DevEco Studio 6.0.1 Release + API 20/21 SDK。下载安装包后核验官方 SHA-256；若官方下载必须人工登录，记录该真实阻塞并使用 OpenHarmony 6.0 API 20 公共 SDK做公共 API 编译交叉检查，但不把 OpenHarmony 结果冒充 HarmonyOS 最终验证。

- [ ] **Step 2: 探测工具实际路径和版本**

运行实际 `hvigorw --help/--version`、`ohpm --version`、`codelinter --help`、`hdc --version`；记录 SDK、Node 和 JDK 配套，不使用系统 Node 25 猜测兼容性。

- [ ] **Step 3: 写失败的预检测试**

`preflight.sh` 在缺少 SDK/Hvigor 时非零退出并输出机器可读键：

```text
status=failed
reason=missing_hvigor
```

先用清空 PATH 的子进程确认该行为。

- [ ] **Step 4: 实现多路径、无硬编码的工具探测**

顺序：环境变量 → 仓内 wrapper → PATH → DevEco 标准安装路径。只接受可执行文件并打印版本，不修改用户 shell profile。

- [ ] **Step 5: 在真实环境运行预检**

Expected: `status=passed` 且列出 SDK/API/Hvigor/Code Linter；HDC/设备可以标为 optional，但不能把未安装写成 passed。

### Task 3: 创建最小可编译 Stage 工程

**Files:**
- Create: `work/AppScope/app.json5`
- Create: `work/build-profile.json5`
- Create: `work/hvigorfile.ts`
- Create: `work/hvigor/hvigor-config.json5`
- Create: `work/oh-package.json5`
- Create: `work/entry/build-profile.json5`
- Create: `work/entry/hvigorfile.ts`
- Create: `work/entry/oh-package.json5`
- Create: `work/entry/src/main/module.json5`
- Create: `work/entry/src/main/ets/entryability/EntryAbility.ets`
- Create: `work/entry/src/main/ets/pages/Index.ets`
- Create: `work/entry/src/main/resources/base/element/{string,color,float}.json`
- Create: `work/entry/src/main/resources/base/profile/main_pages.json`

- [ ] **Step 1: 运行 Task 1 合同测试，保存骨架缺失失败**

Run: `python3 work/tools/tests/test_delivery_contract.py`  
Expected: FAIL，缺少 Stage 工程文件。

- [ ] **Step 2: 从官方 API 20 Empty Ability 配置最小工程**

`bundleName` 为 `com.example.jetsnack`，产品为 `default`，`compatibleSdkVersion` 为 `5.0.0(12)`，`targetSdkVersion` 为 `6.0.0(20)`，`runtimeOS` 为 `HarmonyOS`。入口只显示 `Jetsnack` 文本，且 Ability 设置沉浸式浅色系统栏。

- [ ] **Step 3: 运行合同测试到结构通过**

Run: `python3 work/tools/tests/test_delivery_contract.py`  
Expected: 工程结构断言通过；资源/页面覆盖项可继续失败。

- [ ] **Step 4: 首次真实 Hvigor 构建**

先从实际 `--help` 选择任务，候选命令：

```bash
hvigorw assembleHap --mode module \
  -p product=default -p module=entry@default -p buildMode=debug --no-daemon
```

Expected: exit 0 且找到 `entry/build/**/outputs/**/*.hap`。失败时按诊断写最小修复测试，不跳过编译器。

### Task 4: 迁移主题、字体、图片与确定性数据

**Files:**
- Create: `work/entry/src/main/ets/model/Snack.ets`
- Create: `work/entry/src/main/ets/model/OrderLine.ets`
- Create: `work/entry/src/main/ets/data/SnackData.ets`
- Create: `work/entry/src/main/ets/data/SearchData.ets`
- Create: `work/entry/src/main/ets/theme/JetsnackTheme.ets`
- Create: `work/entry/src/main/resources/base/media/*`
- Create: `work/entry/src/main/resources/base/profile/font_config.json`
- Create: `work/tools/tests/test_source_facts.py`

- [ ] **Step 1: 写失败的数据一致性测试**

断言 28 个稳定 ID/名称/价格/图片、5 个 Feed 集合、分类、建议、Cart 初值和主题 token 与 Android facts 一致；在 ArkTS 数据文件尚不存在时失败。

- [ ] **Step 2: 运行并确认失败原因是目标数据缺失**

Run: `python3 work/tools/tests/test_source_facts.py`  
Expected: FAIL `SnackData.ets missing`。

- [ ] **Step 3: 实现静态类型数据模型**

只使用显式 `class/interface` 和 `number/string/boolean`，禁用 `any`。固定商品 ID 为 1..28，保持 Android 显示顺序；价格继续使用 cents。

- [ ] **Step 4: 迁移资源**

图片和 TTF 从指定 Android 提交复制并保留 `ASSETS_LICENSE`；ArkUI 图片统一 `ImageFit.Cover`，不使用网络 URL。

- [ ] **Step 5: 运行数据测试和 Hvigor 构建**

Run: `python3 work/tools/tests/test_source_facts.py` 后运行实际 assembleHap。  
Expected: 全部通过，HAP 更新。

### Task 5: 实现 AppStore、Feed、底栏和通用组件

**Files:**
- Create: `work/entry/src/main/ets/state/AppStore.ets`
- Create: `work/entry/src/main/ets/components/{SnackImage,SnackCard,QuantitySelector,BottomNav,FilterBar}.ets`
- Create: `work/entry/src/main/ets/screens/FeedScreen.ets`
- Modify: `work/entry/src/main/ets/pages/Index.ets`
- Create: `work/entry/src/ohosTest/ets/test/AppStore.test.ets`

- [ ] **Step 1: 写失败的状态/导航测试**

断言初始路由 `home/feed`、四 Tab、详情来源和返回；断言 Feed 五组集合顺序。运行 Hypium 或在工具未就绪时先由结构测试确认测试存在且生产符号缺失。

- [ ] **Step 2: 实现最小 AppStore 与根路由**

使用确定性枚举和显式方法：`selectTab(route)`、`openDetail(id, origin)`、`goBack()`；不引入通用路由框架依赖。

- [ ] **Step 3: 实现 Feed 和底栏**

精确关键文本、尺寸、颜色、圆图和横向列表；添加 `screen.feed`、`nav.*`、`snack.card.*`、`feed.filters.open` ID 与 accessibilityText。

- [ ] **Step 4: 测试和构建**

运行合同/状态测试、Hvigor 和 Code Linter；修复后不得新增告警。

### Task 6: 实现 Search 与 Profile

**Files:**
- Create: `work/entry/src/main/ets/screens/{SearchScreen,ProfileScreen}.ets`
- Modify: `work/entry/src/main/ets/state/AppStore.ets`
- Modify: `work/entry/src/ohosTest/ets/test/AppStore.test.ets`
- Create: `work/journeys/core.yaml`

- [ ] **Step 1: 写失败的搜索状态测试**

覆盖空且未聚焦、空且聚焦、`Apple` 五条、`Cheese` 一条、不存在查询零条；清空按钮只清查询。

- [ ] **Step 2: 实现搜索纯函数和状态**

大小写不敏感本地 contains；加载延迟只影响状态，不依赖真实 I/O；分类点击和结果加号保持 no-op。

- [ ] **Step 3: 实现 Search/Profile UI 与稳定 ID**

保持公开文本、两列分类卡、建议、NoResults 和 Profile 固定文案。

- [ ] **Step 4: 添加 Journey**

`core.yaml` 覆盖启动、四 Tab、搜索四态和稳定 ID；同一动作声明 Android/Harmony 逻辑 ID。

- [ ] **Step 5: 运行测试、构建和规范扫描**

所有硬门禁 exit 0，Journey 在无设备时只做 schema 校验并明确 skipped 原因。

### Task 7: 实现 Detail、Cart 与 Filter

**Files:**
- Create: `work/entry/src/main/ets/screens/{DetailScreen,CartScreen,FilterOverlay}.ets`
- Modify: `work/entry/src/main/ets/state/AppStore.ets`
- Modify: `work/entry/src/ohosTest/ets/test/AppStore.test.ets`
- Modify: `work/journeys/core.yaml`

- [ ] **Step 1: 写失败的 Cart/Detail/Filter 状态测试**

断言 Cart 初值、subtotal 5444、shipping 369、total 5813、数量 1 时减少即删除、第五次增减失败；Detail 数量可到 0；Filter 只改状态不改变 Feed。

- [ ] **Step 2: 实现最小状态行为**

金额计算使用整数 cents；第五次失败计数每次冷启动重置；原版 ADD TO CART、Checkout、Reset 保持 no-op。

- [ ] **Step 3: 实现三个 UI**

Detail 使用稳定渐变首帧、圆图、SEE MORE/LESS、关联区和固定底栏；Cart 使用 100vp 图片、数量器、删除和 Summary；Filter 使用 50% 遮罩、20vp 面板、Chip/Slider。

- [ ] **Step 4: 补充 Journey 与深链入口**

覆盖 Chips→详情→返回、Cart 增减/删除、Filter 开关；`EntryAbility` 识别 Cart URI 并选择 `home/cart`。

- [ ] **Step 5: 完整测试、构建和 Code Linter**

任何编译或目标告警必须修复；不通过禁用规则、删除测试或更改断言逃逸。

### Task 8: 自动化 Skill、验证入口和平台文档

**Files:**
- Create: `work/skills/android-to-harmonyos/SKILL.md`
- Create: `work/skills/android-to-harmonyos/references/{delivery-contract,compose-arkui-map,diagnostic-playbook}.md`
- Create: `work/tools/verify.sh`
- Create: `INSTRUCTION.md`
- Create: `introduction.md`
- Create: `result/output.md`
- Create: `logs/interaction.md`
- Create: `logs/trace/.gitkeep`

- [ ] **Step 1: 扩展失败的交付合同测试**

断言正式入口必须大写、唯一主命令存在、Skill 路径正确、结果/日志存在、无交互/联网安装指令。

- [ ] **Step 2: 运行并确认因交付文档缺失而失败**

Run: `python3 work/tools/tests/test_delivery_contract.py`。

- [ ] **Step 3: 实现短版 Skill 和渐进参考**

主 Skill 只写触发、输入输出、执行顺序、硬/软门禁、有限修复和禁止项；映射/诊断细节放 references。

- [ ] **Step 4: 实现幂等 verify.sh**

严格模式，顺序调用 preflight、contract_check、实际 Hvigor、Code Linter、可用测试；固定生成 `work/reports/verification.json`，成功标记 `status=passed`。

- [ ] **Step 5: 编写平台入口**

`INSTRUCTION.md` 明确 `cd work && ./tools/verify.sh --judge`、完成条件、HAP/仓路径、无设备退化和失败退出码；`introduction.md` 明确正式入口为大写文件，不复制一份可能漂移的说明。

- [ ] **Step 6: 重跑合同测试和主命令**

Expected: 合同测试 exit 0；主命令在完整环境 exit 0 并生成报告/HAP。

### Task 9: 视觉、设备和五轮稳定性验证

**Files:**
- Create: `work/tools/visual_compare.py`
- Create: `work/reports/.gitkeep`
- Modify: `docs/鸿蒙化实现方法与进展.md`
- Modify: `result/output.md`
- Modify: `logs/interaction.md`

- [ ] **Step 1: 在设备/模拟器安装并启动 HAP**

使用实际 HDC 帮助确认命令，安装 HAP，启动 `com.example.jetsnack/EntryAbility`，保存工具版本和设备规格。

- [ ] **Step 2: 回放核心 Journey**

每轮清应用数据，固定 en-US、Light、字体比例、分辨率与动画；逐项断言公开文本、状态、返回和金额。

- [ ] **Step 3: 采集双端关键截图并比较**

至少 Feed、Search Categories、Detail Donut/Chips、Cart、Profile；输出像素差、SSIM 可用指标、OCR/文本和元素几何，不通过模糊掩盖偏差。

- [ ] **Step 4: 连续执行五轮**

构建、Code Linter、状态测试、Journey 每轮从固定状态运行；报告最好通过项和五轮全通过项。任何间歇失败先写复现测试再修复。

- [ ] **Step 5: 更新真实证据**

进展/结果文档只写实际命令、退出码、产物哈希、告警数和设备结果；环境不可用项目明确未验证。

### Task 10: 清理 Android 构建树并审计最终 ZIP

**Files:**
- Delete from final tree: Android Gradle/IDE/缓存/源码文件及 APK
- Create: `work/tools/package_check.py`
- Modify: `migration-manifest.json`
- Modify: `INSTRUCTION.md`

- [ ] **Step 1: 在 `/tmp` 创建 Android 指定提交的只读归档**

Run: `git -C work archive 23e1421b72b602d80486777efbf24dd248abf3bb -o /tmp/jetsnack-android-baseline.tar`。  
Expected: tar 存在且可列出源文件；不放进提交 ZIP。

- [ ] **Step 2: 运行包检查并确认旧 Android/缓存导致失败**

检查 `.git`、`.gradle`、`.idea`、`app/build`、`local.properties`、APK、keystore、个人路径和超大文件。

- [ ] **Step 3: 从最终工作树移除旧 Android 与缓存**

仅在 Harmony HAP 已真实构建后执行；保留 `source-facts`、迁移台账、资源许可和必要对照证据。

- [ ] **Step 4: 从模拟解压目录执行正式入口**

按白名单复制 `INSTRUCTION.md`、`introduction.md`、`work/`、`docs/`、`result/`、`logs/` 到临时目录，执行原文命令并定位完整仓/HAP。

- [ ] **Step 5: 最终全量验证**

运行合同、状态、Hvigor、Code Linter、可用 UI Journey、五轮稳定性和包检查；逐条对照赛题与平台合同，所有硬门禁真实通过后才标记完成。

## 计划自审

- 规格覆盖：完整仓、正式入口、自动迁移过程、功能/视觉/接口/规范、五次稳定性、结果/日志与清洁打包均有对应任务。
- 无实现占位：所有 `未开始` 只存在进展记录，计划任务均有目标文件、命令和验收结果。
- 类型一致：全局状态统一称 `AppStore`，商品稳定 ID 为 `number`，价格统一为整数 cents，路由字符串与 Android facts 一致。
- 范围控制：Form Kit 卡片在核心应用通过后再评估；不让通用编译器、在线 RAG 或 VLM 阻塞 P0 得分。

