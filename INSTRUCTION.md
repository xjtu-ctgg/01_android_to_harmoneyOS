# Android 到鸿蒙移植 - 参赛作品说明

## 1. 作品概述

本作品将固定版本的 Jetsnack Android 应用移植为可编译的 HarmonyOS ArkTS/ArkUI Stage 工程。完整结果已经放在 `work/`，评测时直接读取、检查并构建该代码仓。

## 2. 输入与环境

本作品没有运行时业务输入；`work/` 就是待评测的完整鸿蒙代码仓。`work/source-facts/` 保存 Android 固定提交的事实快照，`work/migration-manifest.json` 保存迁移映射，供功能和接口核对使用。

评测环境准备：

| 项目 | 要求 |
| --- | --- |
| HarmonyOS 工具链 | DevEco Studio 或 Command Line Tools，含 API 20 SDK |
| 构建工具 | Hvigor 5.x/6.x、工具链配套 Node.js、Hvigor 自带或已初始化的 pnpm |
| Java | JDK 17 或 21 |
| 合同测试 | Python 3.10+；只使用标准库 |
| 依赖 | 工程本身没有 ohpm 第三方依赖 |
| 严格规范门禁 | 评分环境提供官方 Code Linter 时使用；不得在评测过程中临时联网安装 |

可选地设置 `DEVECO_SDK_HOME`、`HVIGORW`、`DEVECO_NODE_HOME`、`JAVA_HOME`、`CODELINTER` 和已初始化的 `HVIGOR_USER_HOME`。工具已在标准目录或 `PATH` 时无需设置。所有执行均应为非交互方式。

## 3. 执行工作流

### Step 1：运行统一门禁

从交付件根目录执行：

```bash
cd work
sh tools/verify.sh --build
```

这是唯一必需的执行入口。它依次完成迁移事实校验、Python 合同测试、SDK/Hvigor 探测和 `assembleHap` 构建；构建在临时副本中进行，不要求也不会修改只读交付目录。不要先执行 `chmod`。

成功标志：输出 `status=passed`，并生成非空的未签名 HAP。构建默认有 1800 秒上限，适配慢速评测机和工具链初始化；仍需更长时间时可设置正整数 `VERIFY_BUILD_TIMEOUT_SECONDS`（例如 `3600`）。超时会输出 `reason=build_timeout` 并失败，避免真正卡死的进程无限占用 Executor。

### Step 2：严格规范门禁（评分环境可用时）

```bash
cd work
sh tools/verify.sh --strict
```

该模式在相同合同和构建基础上调用官方 Code Linter。若评测镜像未提供其后端，`preflight` 会明确返回 `reason=missing_codelinter`；不得用替代脚本冒充官方扫描通过。仅做仓内合同检查时可使用 `sh tools/verify.sh --static`。

### Step 3：交给鸿蒙评分 Skill

验证通过后，将 `work/` 作为最终鸿蒙代码仓交给评分 Skill，读取 `work/journeys/core.yaml`、稳定 ID、迁移清单和 ArkTS 源码，执行公开及隐藏的功能、界面、接口和规范用例。验证通过后不做随机重写；只有真实环境暴露确定的编译或规范错误时，才在当前 Executor 的可写副本中做最小修复并重跑 Step 1。

平台可能把解压后的 `package_root` 标为只读，并建立 `executor_1` 至 `executor_5` 五个各自独立的可写工作目录。每个 Executor 在自己的可写副本中独立运行完整用例集，不共享构建状态，也不修改只读输入。

## 4. 完成判定

执行完成需同时满足：

1. 主命令退出码为 0，末尾包含 `status=passed`；
2. `work/entry/build/default/outputs/default/entry-default-unsigned.hap` 存在且非空；
3. `work/AppScope/app.json5`、`work/entry/src/main/module.json5`、`work/entry/src/main/ets/pages/Index.ets` 存在；
4. `--strict` 被调用时，官方 Code Linter 也返回 0，并生成非空 `work/build/reports/codelinter.json`。

## 5. 产物清单

| 产物 | 位置 | 用途 |
| --- | --- | --- |
| 完整鸿蒙代码仓 | `work/` | 评分 Skill 的主输入；包含 ArkTS、资源、配置和构建入口 |
| 自动迁移 Skill | `work/skills/android-to-harmonyos/SKILL.md` | 迁移事实、修复边界和质量门禁说明 |
| 迁移清单 | `work/migration-manifest.json` | Android→HarmonyOS 文件和行为映射 |
| Journey 用例 | `work/journeys/core.yaml` | 公开行为、界面和接口检查点 |
| 统一验证入口 | `work/tools/verify.sh` | 合同测试和 HAP 构建 |
| 构建 HAP | `work/entry/build/default/outputs/default/entry-default-unsigned.hap` | 构建成功后的非签名验证产物 |
| 自验证结果 | `result/output.md` | 最近一次本地复现结果和环境边界 |
| 交互与验证轨迹 | `logs/interaction.md`、`logs/trace/` | 人工交互摘要及可复核的实现、验证记录 |
