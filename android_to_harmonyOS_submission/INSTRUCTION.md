# Jetsnack HarmonyOS 交付执行说明

## 1. 交付结果位置

完整的 HarmonyOS Stage 工程已生成在 `work/`。该目录本身就是最终鸿蒙代码仓，不需要再执行随机代码生成，也不需要 Git 上传、外网服务或人工确认。

关键入口：

- 工程根：`work/`
- Entry HAP：`work/entry/`
- Recent Orders 服务卡片：`work/entry/src/main/ets/form/RecentOrdersForm.ets`
- 自动迁移 Skill：`work/skills/android-to-harmonyos/SKILL.md`
- 迁移清单：`work/migration-manifest.json`
- 核心用例：`work/journeys/core.yaml`
- 唯一验证命令：`work/tools/verify.sh`

## 2. 环境准备

评测环境需预装以下标准工具：

- HarmonyOS Command Line Tools 或 DevEco Studio，包含 HarmonyOS API 20 SDK；
- Hvigor（工程模型版本 5.0.0，当前验证使用 Hvigor 6.20.0），且该工具链包含 Hvigor 自带或已初始化的 pnpm；
- 工具链配套 Node.js；
- 与所装 HarmonyOS 工具链配套的 JDK 17 或 21（本工程已用 JDK 21 验证）；
- Python 3.10 或更高版本（只用于仓内零第三方依赖的合同测试）；
- 官方 Code Linter（执行严格规范门禁时需要）。

工程本身没有 ohpm 第三方依赖，应用构建不执行 `ohpm install`。Hvigor 包装器首次运行可能初始化其内部 pnpm；评测镜像应预装完整 DevEco/Command Line Tools，或提供已经初始化的 `HVIGOR_USER_HOME`，不得在评测过程中临时联网安装。工具发现顺序为：显式环境变量、仓相邻工具目录、`PATH`、DevEco 标准安装目录。

可按评测环境设置：

```bash
export DEVECO_SDK_HOME=/path/to/HarmonyOS/sdk
export HVIGORW=/path/to/hvigorw
export DEVECO_NODE_HOME=/path/to/node/home
export JAVA_HOME=/path/to/jdk-21
export CODELINTER=/path/to/codelinter
export HVIGOR_USER_HOME=/path/to/initialized/hvigor-user-home
```

除 `DEVECO_SDK_HOME` 外，其余变量在工具已位于标准目录、`PATH` 或默认用户缓存位置时可以省略。若独立命令行版 `hvigorw` 首次运行提示 `Installing pnpm`，说明该工具安装尚未完成；应在制作评测镜像时完成初始化，而不是由参赛工程联网补齐。所有命令均非交互执行，不修改 shell profile。

## 3. 自动执行方式

### 3.1 平台 Agent 执行协议

平台可能把解压后的 `package_root` 标记为只读，并建立 `executor_1` 至 `executor_5` 五个独立任务。五个 Executor 各自运行完整用例集，而不是分别代表五种评分维度。每个裁判 Agent 按以下顺序执行，整个过程幂等且不需要人工输入：

1. 在平台分配给当前 Executor 的各自独立的可写工作目录中使用交付件副本；不得尝试修改只读 `package_root`，也不得与其他 Executor 共享运行时状态或构建输出。
2. 读取 `work/skills/android-to-harmonyos/SKILL.md`，将其作为迁移与修复工作流；该 Skill 已位于平台要求的标准路径，无需复制或安装到用户目录。
3. 将 `work/` 视为针对指定 Android 基线提交 `23e1421b72b602d80486777efbf24dd248abf3bb` 已生成的最佳鸿蒙结果仓。平台提供的 Android 材料只用于核对，不覆盖已有 ArkTS、资源或迁移事实。
4. 在自己的任务目录运行同一条 `tools/verify.sh --build`。验证通过后不做随机重写；只有平台环境暴露真实编译或规范错误时，才依据 Skill、`migration-manifest.json` 和 `source-facts/` 在自己的可写副本中做最小、确定性修复并重跑同一命令。
5. 命令成功退出即表示当前 Executor 复现完成。把当前可写任务目录中的 `work/` 交给鸿蒙打分 Skill；不执行 Git push，不等待后台服务，也不读取其他 Executor 的输出。

`work/tools/five_executor_verify.py` 只用于参赛者提交前在本地模拟上述五次独立复现。真实平台已经负责建立五个 Executor，因此不得在单个 Executor 内再次启动五重模拟，避免递归执行和资源竞争。

### 3.2 主执行命令

从交付件根目录运行：

```bash
cd work
sh tools/verify.sh --build
```

`--build` 会依次执行：

1. 校验冻结 Android 事实和 34 项迁移映射；
2. 运行全部 Python 合同测试；
3. 探测 SDK、Hvigor 和版本；
4. 执行 `assembleHap`；
5. 检查生成的 HAP 非空。

若当前机器只有仓相邻的公共 OpenHarmony API 20 SDK，脚本会在临时副本中完成公共 API 兼容编译，并输出 `build_scope=public_api_compatibility`；正式工程配置不会被修改。评分环境提供 HarmonyOS SDK 时应输出 `build_scope=harmonyos`。两者均不要求、也不会执行 Git 上传。

Hvigor 构建默认最多运行 600 秒，并会在超时后回收整个构建进程组，输出 `reason=build_timeout` 后失败退出，避免裁判无限等待。仅当评测机器确实较慢时才可通过正整数环境变量（例如 `VERIFY_BUILD_TIMEOUT_SECONDS=900`）提高上限；不得以取消时限掩盖工具链初始化或构建卡死。

如需额外验证 release 模式（不替代上述正式 HarmonyOS 门禁），可从交付件根目录运行：

```bash
work/tools/cross_build_openharmony.sh --release
```

该命令仍只修改临时副本，成功时输出 `build_mode=release`，并将公共 API 兼容产物写入 `work/build/cross/release/entry-default-unsigned.hap`。

若评测环境提供官方 Code Linter，使用完整严格门禁：

```bash
cd work
sh tools/verify.sh --strict
```

只检查交付结构、行为合同、资源哈希和 ArkTS 策略时：

```bash
cd work
sh tools/verify.sh --static
```

若评测或复核环境连接了官方 HarmonyOS 设备/等价模拟器，可在手动准备好某个 Journey 检查点后采集五次原始组件树和截图（这不是无设备构建的必需步骤）：

```bash
cd work
tools/device_evidence.py \
  --journey-id core.feed \
  --stable-id screen.feed \
  --expected-text "Android's picks" \
  --output-dir device-evidence/core.feed
```

脚本要求 `hdc list targets` 中恰好一个设备；输出目录包含原始 JSON、原始 PNG 和 `checkpoint.json`。它只采集当前已准备的界面检查点，不会假装自动回放 Journey，也不会把本地 PNG 哈希冒充 Android/HarmonyOS 截图相似度。

若同时具有相同视口、密度、字体缩放、语言、布局方向、主题和系统栏条件下的 Android 原始参考 PNG，可执行量化对比：

```bash
cd work
tools/screenshot_compare.py \
  --reference device-evidence/android/core.feed.png \
  --actual device-evidence/harmony/core.feed.png \
  --output device-evidence/comparison/core.feed.json
```

对比器不依赖第三方 Python 包，输出 MAE、像素差异率和窗口化 SSIM；尺寸不一致会直接拒绝，不会通过静默缩放制造高相似度。默认阈值仅用于仓内回归，不代表未知平台评分阈值。

提交前可从交付件根目录对最终 ZIP 做平台轨迹预演：

```bash
python3 work/tools/five_executor_verify.py \
  --archive android_to_harmonyOS_submission.zip \
  --mode build
```

该命令安全解压 ZIP、将输入包设为只读、创建五个可写工作目录并在每个目录执行相同验证。默认按 `--jobs 1` 顺序执行，避免完整合同中的子验证在普通机器上资源争用；资源充足时可显式传入 `--jobs 5`。并发度不改变五次独立结果的汇总语义。它是本地可复现性代理，不等同于平台隐藏用例得分。

也可直接构建：

```bash
cd work
"${HVIGORW:-hvigorw}" clean assembleHap --mode module \
  -p product=default \
  -p module=entry@default \
  -p buildMode=debug \
  --no-daemon
```

## 4. 执行完成判定

满足以下全部条件即执行完成：

- 命令退出码为 0；
- 末尾输出 `status=passed`；
- 文件 `work/entry/build/default/outputs/default/entry-default-unsigned.hap` 存在且非空；
- 严格模式下 Code Linter 退出码为 0。
- 严格模式生成的 `work/build/reports/codelinter.json` 存在且非空；若官方 Code Linter 不可用，命令必须失败，不得把兼容编译冒充规范扫描通过。
- `work/AppScope/app.json5`、`work/entry/src/main/module.json5` 与 `work/entry/src/main/ets/pages/Index.ets` 均存在；这三个文件共同判定完整鸿蒙仓已经生成，而不是仅生成单个 HAP。

构建产物为未签名调试 HAP，评测安装时可按平台证书流程签名；签名不改变源码评测结果。

提交平台只需要本说明和 `work/`。SHA-256 不是赛题要求，也不是平台执行参数；如在本地显示，它仅用于人工确认某个压缩包在传输前后是否为同一文件。

## 5. 评分输入与功能入口

最终评分代码仓位置固定为：

```text
work/
```

Bundle 名为 `com.example.jetsnack`，启动 Ability 为 `EntryAbility`。主页含 Feed、Search、My Cart、Profile 四个 Tab；商品卡进入 Detail；Feed 筛选按钮打开 Filter 浮层。Cart 同时声明并处理：

```text
https://jetsnack.example.com/home/cart
```

Android `RecentOrdersWidgetReceiver` 已迁移为同一 `entry` 模块内的原生 Form Kit 服务卡片 `RecentOrdersForm`，支持 `2*2`、`2*4`、`4*4` 和尺寸调整。标题购物车与可见行尾加购图标均只打开 Cart，不修改 Cart 数据；冷启动由 `onCreate`、热启动由 singleton `onNewWant` 处理。卡片 profile 位于 `work/entry/src/main/resources/base/profile/form_config.json`，生命周期入口为 `RecentOrdersFormAbility`。

卡片布局读取初次添加参数中的真实宽高，并在 `onSizeChanged` 后按新的 vp 矩形刷新；不会只按 `2*2/2*4/4*4` 枚举猜测布局。评分设备应重点执行 `work/journeys/core.yaml` 中 `visual.form.breakpoint.*` 用例，核对 Android 原实现的 `260/479vp` 列布局、`180vp` 标题栏以及 `340..479/>620vp` 行尾动作断点。

自动化节点和预期 Journey 见 `work/journeys/core.yaml`。评分程序可直接读取完整工程，无需从 `work/` 外复制任何源码。
