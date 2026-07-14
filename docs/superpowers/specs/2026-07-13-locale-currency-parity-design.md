# Jetsnack 地区化货币与五裁判稳定性设计

> 日期：2026-07-13  
> 状态：用户已明确批准，并授权后续同类设计由执行者书面化后自审推进。

## 1. 背景与目标

固定 Android 节点 `23e1421b72b602d80486777efbf24dd248abf3bb` 的
`Currency.kt` 使用 `NumberFormat.getCurrencyInstance()` 显示价格；`Home.kt` 使用当前
`Locale` 对底部导航标题执行 `uppercase(currentLocale)`。当前鸿蒙实现却在 Cart、Search、Detail
分别拼接固定 `$dollars.cents`，导航资源也预先写成英文大写。这会在英国、欧元区、日本、阿拉伯语和
土耳其语等隐藏用例中同时影响文本、截图、无障碍接口和源行为一致性。

本设计的目标是：

- 以一个 ArkTS 货币格式化边界替换三份美元拼接实现；
- 让系统 locale 决定货币、数字、分隔符、小数位、符号位置和双向文本；
- 恢复 Android 的 locale-aware 导航大写语义；
- 保持运行时配置变更、路由和业务状态不退化；
- 以平台 5 个独立裁判（Executor）分别复现并执行完整隐藏用例集的模型验证确定性，而不是只验证一次幸运运行；
- 不引入网络、第三方 OHPM 包、运行时汇率或废弃国际化 API。

## 2. 平台执行模型

根据 `docs/打分平台使用指导.md` 和另一赛题真实评分轨迹
`/Users/ctgg/master/code/learn/ICT_software/log7_9.md`，平台使用选手选择的 Agent 框架与模型启动
`executor_1..executor_5` 五个独立裁判。平台文档中的“5 个用例集”在实际轨迹中体现为五个裁判各自完成
一次完整复现，并各自运行同一完整隐藏 case 集；示例中每个裁判均报告 `case_count=24`：

- 用例通过率看五个裁判的整体表现；
- 稳定性看五个裁判共同通过的用例交集；
- 准确性看单个裁判的最佳通过数；
- 最终得分同时依赖稳定性和准确性。

根据 `docs/PLATFORM赛题提交指导.md`，每次裁判执行都从顶层 `INSTRUCTION.md` 得到环境准备、执行命令、
完成判定和最终仓位置，并把 `work/` 交给鸿蒙打分 Skill。真实轨迹还表明：解压后的 `package_root` 被标记为
只读，每个 Executor 在自己的工作目录中复现；交付审查会检查 `INSTRUCTION.md` 是否已归档、是否为有效复现
指导以及 Skill 路径是否合法；复现阶段再检查 `artifact_valid=True`。

因而本项目的本地同构验收定义为：从同一只读提交 ZIP 建立五个互不共享构建缓存和生成文件的
`executor_1..executor_5` 工作目录，每个裁判都遵循同一 `INSTRUCTION.md`，独立复现完整 `work/` 结果，
独立验证必要产物，然后各自执行相同的完整本地代理用例集。正式 SDK 构建在资源允许时五个裁判都执行；至少
还要保留一次全新解压后的完整 API 20 构建。五次结果不得依赖随机数、网络、时钟、Git 状态或其他裁判留下的
产物。

这五个本地裁判用于发现 Agent 复现不确定性、只读输入兼容性和交付协议问题，不宣称拥有平台未公开用例，也不
把本地合同冒充平台满分证明。

## 3. 方案比较与选择

### 方案 A：完整地区化语义（采用）

集中使用 API 20 全局 `Intl.NumberFormat`，由系统 locale 和冻结的 CLDR territory→currency 数据确定默认
货币；导航先解析资源，再按当前 locale 大写。它最接近 Android 源行为，能覆盖非美国隐藏用例，代价是需要
维护一份可审计的地区货币映射和边界测试。

### 方案 B：固定 USD，仅地区化数字（不采用）

可得到本地化分隔符和数字，但 `en-GB`、`de-DE`、`ja-JP` 等仍错误显示美元，不能复刻
`NumberFormat.getCurrencyInstance()`。

### 方案 C：继续拼接 `$`（不采用）

只对现有 `en-US` 快照偶然正确；小数位、符号位置、RTL 和地区敏感大写均不正确。

## 4. 工程结构与职责

```text
work/
├── entry/src/main/ets/
│   ├── utils/CurrencyFormatter.ets
│   ├── components/BottomNav.ets
│   └── screens/{CartScreen,SearchScreen,DetailScreen}.ets
├── entry/src/main/resources/base/element/string.json
├── source-facts/
│   ├── android-facts.json
│   └── android-source/.../Currency.kt
├── tools/tests/test_locale_currency_contract.py
├── tools/five_executor_verify.py
└── journeys/core.yaml
```

- `CurrencyFormatter.ets`：只负责 locale、地区、货币和价格文本；提供系统入口和可注入 locale 的纯入口。
- 三个 Screen：只调用统一入口，不再知道美元、分值补零或 locale 规则。
- `BottomNav.ets`：解析当前资源并执行 locale-aware 大写，显示文本与无障碍文本共用结果。
- `android-facts.json`：冻结 Android `Currency.kt`、`Home.kt` 事实及采用的 CLDR 数据版本/规则。
- `test_locale_currency_contract.py`：验证源码事实、单一实现、映射覆盖、屏幕接线、导航和 Journey。
- `five_executor_verify.py`：只做五裁判隔离复现与确定性编排，不联网、不伪造平台结果。

## 5. 价格格式化合同

### 5.1 公共接口

```ts
export function formatPriceForLocale(priceCents: number, localeTag: string): string
export function formatPrice(priceCents: number): string
```

`formatPrice()` 使用 `i18n.System.getSystemLocaleInstance().toString()`，然后调用纯入口；所有页面只调用
`formatPrice()`。纯入口用于边界推理和静态合同，不需要模拟系统配置对象。

### 5.2 locale 与货币解析顺序

1. 用 `new Intl.Locale(localeTag)` 解析 locale；无效 tag 时改用当前系统 locale；若仍无效，使用 `en-US`，
   该路径只防止 UI 崩溃，正常系统配置不应进入。
2. 若 Unicode locale extension 明确包含 `-u-cu-xxx`，优先采用该 ISO 4217 货币码。
3. 否则先读取显式 `Locale.region`；缺少地区时调用 `maximize()` 获得 likely-region。
4. 通过冻结的 CLDR 当前法定 tender 映射得到货币。
5. 未知地区、无当前法定货币地区使用 `XXX`，不得静默回退 USD。
6. 使用全局 `Intl.NumberFormat(localeTag, { style: 'currency', currency })` 格式化
   `priceCents / 100`。

不做汇率换算。Android 同样只是把整数分值左移两位后交给 locale currency formatter。例如 `299` 在
`en-US` 为 `$2.99`，在 `en-GB` 为 `£2.99`，在 `de-DE` 为 `2,99 €`，在 `ja-JP` 按 JPY 默认精度为
`￥3`，在 `ar-EG` 使用阿拉伯数字、EGP 和运行时所需的双向控制字符。

### 5.3 数据边界

- 映射只保存 ISO 地区和 ISO 4217 代码，不复制符号、分隔符或小数位；这些由运行时 Intl/CLDR 决定。
- 覆盖 CLDR 中所有具有当前 tender currency 的地区，并显式覆盖无货币/未知地区回退。
- 映射使用确定性 `switch`/纯函数，避免 ArkTS 不允许的动态索引签名、`any` 或反射。
- 金额输入沿用现有非负整数 `priceCents` 数据合同；不为源应用不存在的负数、NaN 或无限值发明 UI。
- 不使用 API 20 已废弃的 `@ohos.intl.NumberFormat`。

## 6. 导航标题合同

Android 资源的源字符串为 `Home`、`Search`、`My cart`、`Profile`，显示时再按当前 locale 大写。鸿蒙资源
恢复为同义 title case，`BottomNav` 通过非废弃的 `ResourceManager.getStringSync(resource.id)` 解析当前
资源，再执行 `toLocaleUpperCase(systemLocaleTag)`。同一字符串同时用于可见选中标签和
`accessibilityText`。

该规则保持 `en-US` 的 `HOME / SEARCH / MY CART / PROFILE` 不变，同时允许 `tr-TR` 正确得到
`PROFİLE`。不得依赖已大写资源或未记录 locale 语义的视觉-only 转换属性。

如果宿主 Context 在极端生命周期瞬间不可用，组件使用资源对应的固定 title-case fallback 后按同一 locale
大写；fallback 只用于避免无障碍和渲染崩溃，正常 Ability 页面必须走 ResourceManager。fallback 由导航项
数据声明并受合同测试约束，不散落在渲染代码中。

## 7. 配置变化与状态

现有 `EntryAbility.onConfigurationUpdate()` 增加 `configurationRequestId`，`Index` 监听后重建页面。新格式化
入口每次渲染读取系统 locale，因此运行时 `en-US → tr-TR` 或 `en-US → ar-EG` 会更新价格、导航大写和 RTL。
配置更新不得改变当前 Tab、Cart 数量、隐藏行项目、Detail 商品或展开状态之外的业务数据；只重置已经明确
依赖布局方向/尺寸的瞬态视觉状态。

## 8. 错误处理与规范

- locale 解析或 Intl 构造失败时返回确定性、可读的 `XXX` 货币文本，不向页面抛异常；
- 不捕获后静默返回硬编码美元；
- 不新增网络权限、第三方依赖或异步初始化；
- 不使用 `any`、`unknown`、`ESObject`、动态属性访问或废弃 Localization Kit API；
- 字符串继续资源化，currency code 映射属于标准数据而不是用户可见文案；
- 对 Unicode 空格、RTL 标记和地区数字不做 `.trim()`、正则替换或手工重排。

## 9. 测试矩阵

### 9.1 红—绿合同

先建立失败测试，再实现：

1. Android `Currency.kt` 与 `Home.kt` 的源码片段和哈希事实存在；
2. 只有 `CurrencyFormatter.ets` 包含 `Intl.NumberFormat`，三个 Screen 没有局部 `formatPrice` 或 `$` 拼接；
3. formatter 使用系统 locale、`Intl.Locale`、显式货币优先、likely-region、完整地区映射和 `XXX` 回退；
4. 三个 Screen 的所有价格位置均调用统一入口；
5. 导航资源为 title case，渲染与无障碍共用 locale-aware 大写结果；
6. 不出现废弃 `intl.NumberFormat`；
7. 配置更新链仍存在且 Journey 覆盖运行时 locale 切换。

### 9.2 Journey 代表集

- `en-US`：Cart 行价/小计/运费/总价、Search 行价、Detail 价格；
- `en-GB`：英镑符号及三页面接线；
- `de-DE`：逗号小数、符号后置和不可断空格；
- `ja-JP`：JPY 零小数位；
- `ar-EG`：RTL、阿拉伯数字、EGP、Cart 滑动方向和 Detail 布局；
- `tr-TR`：TRY 与 `PROFİLE`；
- 仅语言 `ar`：likely-region 路径；
- `en-AQ`/未知地区：`XXX` 通用货币回退；
- 运行时切换 locale：保留当前 Tab、Cart 数量和 Detail 选择；
- 浅色、深色、大字体和安全区组合继续覆盖，防止新文本宽度破坏截图布局。

Journey 文件是平台/设备执行合同；没有真实设备时不得把 YAML 声明误报为截图已执行。

### 9.3 五裁判同构稳定性验收

`five_executor_verify.py` 接收提交 ZIP，建立只读 `package_root` 和 `executor_1..executor_5` 五个隔离工作
目录。每个裁判独立执行：

1. 下载后等价的 ZIP 完整性与安全解压检查；
2. 交付审查：归档且非空的 `INSTRUCTION.md`、四段复现指导、合法 Skill 路径；
3. 从只读 `package_root` 复制到自己的工作目录，不能原地写输入包；
4. Executor 复现：依照 INSTRUCTION 得到完整 `work/`，验证必要工程文件和预期 HAP/源码产物；
5. 独立执行相同的本地代理 case 集，包括功能、截图合同、接口、规范和打包边界；
6. 输出每个 Executor 的 `success`、`artifact_valid`、`case_count`、逐 case 状态和摘要；
7. 汇总五次用例交集（稳定性代理值）与单次最佳值（准确性代理值）。

五个裁判必须全部退出 0、`artifact_valid=True`、`case_count` 相同、所有本地代理 case 均通过，且源码输入、
Journey 数量与验证摘要一致。全量实现后执行 API 20 `verify.sh --build`；若机器资源允许则五个 Executor
均冷构建，否则明确记录“一次全新解压完整构建 + 五裁判静态/交付复现”，不能把后者描述为五次正式平台评分。

## 10. 交付与完成判定

只有同时满足以下条件才接受本修订：

1. 地区化合同测试经历可解释的红—绿过程；
2. 全量 Python 合同测试和迁移清单检查通过；
3. API 20 `CompileArkTS`、HAP assemble 和产物非空检查通过；
4. 五份隔离冷运行全部通过且结果一致；
5. 新 ZIP 顶层只有 `INSTRUCTION.md` 与 `work/`，无 `.git`、缓存、临时 SDK 或旧 build 产物；
6. 从新 ZIP 解压后独立运行验证和构建通过；
7. `INSTRUCTION.md` 明确平台 Agent 的幂等执行、完成判定和最终仓位置；
8. 进展文档准确记录证据边界：本地无法证明未公开用例满分，也不能替代正式 Code Linter 和真机截图。

本设计提升五组隐藏用例共同通过的概率，但“平台全部隐藏用例满分”只有平台真实返回结果才能证明；本地完成
判定必须基于可复现证据，不作不可验证承诺。
