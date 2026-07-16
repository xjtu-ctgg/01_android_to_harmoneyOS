# Android 到鸿蒙移植 - 参赛作品说明

## 1. 作品概述

本作品将指定版本的 Jetsnack Android 应用重构为原生 HarmonyOS ArkTS/ArkUI Stage 工程，并提供可复用的迁移 Skill、源码事实快照、行为 Journey 和完整鸿蒙代码仓。最终代码仓位于 `work/`。

## 2. 输入与环境准备

| 输入项 | 说明 |
| --- | --- |
| 鸿蒙代码仓 | `work/` 中重构后的完整 HarmonyOS 工程与本地资源 |
| 意图用例文件 | 评分平台提供的功能、交互、界面、接口和规范验证用例 |

本地编译环境为 HarmonyOS API 20 SDK、Hvigor、配套 Node.js/JDK 和 Python 3；工程本身没有 ohpm 第三方依赖。优先使用评测环境或交付包旁的已存在工具链，不得临时联网安装依赖。平台 Agent 不需要重新生成鸿蒙代码仓，直接使用已交付的 `work/`；不得因为工具链缺失而反复重试、修改源码或重新下载工程。

## 3. 执行方式

### Step 1：静态合同与规范检查

```bash
cd work
sh tools/verify.sh --static
```

该步骤校验 Android 固定提交事实、迁移映射、资源、稳定 ID、Journey、ArkTS 规范和交付工程结构。输出末尾应包含 `status=passed`。

### Step 2：HarmonyOS 编译验证

仅在已有 HarmonyOS API 20 SDK 和 Hvigor 的环境中执行；构建是可验证项，不是评分 Skill 的前置条件：

```bash
cd work
sh tools/verify.sh --build
```

慢速工具链允许最多 1800 秒；必要时可在同一命令前设置 `VERIFY_BUILD_TIMEOUT_SECONDS=3600`。编译完成判定同时满足：输出包含 `BUILD SUCCESSFUL` 和 `status=passed`，并生成非空文件 `work/entry/build/default/outputs/default/entry-default-unsigned.hap`。若输出 `reason=missing_sdk`、`reason=missing_hvigor` 或其它工具链缺失，立即停止构建重试；不能伪造编译通过或联网安装，保留 Step 1 的真实静态结果并继续 Step 3。若官方 Code Linter 可用，再执行 `sh tools/verify.sh --strict`；`reason=missing_codelinter` 只记录环境边界，不得用替代脚本冒充官方扫描。

### Step 3：鸿蒙评分 Skill 评测

读取并按 `work/skills/android-to-harmonyos/SKILL.md` 执行鸿蒙评分 Skill，将 `work/` 作为唯一完整鸿蒙代码仓输入。Scorer/Skill 先读取 `work/migration-report.md`，再结合 `work/migration-manifest.json`、`work/source-facts/`、`work/journeys/core.yaml` 和 ArkTS/资源/配置源码，逐条执行公开及非公开用例，覆盖功能一致性、界面截图相似性、接口一致性和代码规范。已交付源码是最终答案：不得从 Android 重新生成或随机重写代码，不得为猜测隐藏用例添加硬编码；只有静态、编译或官方规范检查明确暴露真实错误时，才在当前 Executor 的可写副本中做最小修复，并重新执行受影响的检查。

## 4. 执行完成判定

作品执行完成需满足：

1. `work/` 存在且包含完整 HarmonyOS Stage 工程；
2. `work/migration-report.md`、`work/migration-manifest.json` 和迁移 Skill 存在；
3. 静态检查输出 `status=passed`；
4. 在提供 HarmonyOS 工具链时，构建输出 `BUILD SUCCESSFUL`、`status=passed` 和非空未签名 HAP；
5. 已读取 `work/skills/android-to-harmonyos/SKILL.md`，HarmonyOS 评分 Skill 已获得 `work/` 并可按 Journey 和源码索引评测隐藏用例。

## 5. 产物清单

| 产物 | 位置 | 格式 | 用途 |
| --- | --- | --- | --- |
| 完整鸿蒙项目 | `work/` | ArkTS/ArkUI Stage 工程 | 评分 Skill 的主输入 |
| 自动迁移 Skill | `work/skills/android-to-harmonyos/SKILL.md` | Skill | 迁移、审计、截图和规范工作流 |
| 移植说明 | `work/migration-report.md` | Markdown | 功能对照、关键实现和源码证据索引 |
| 迁移映射 | `work/migration-manifest.json` | JSON | Android 到 HarmonyOS 页面、路由、动作和资源映射 |
| Android 事实快照 | `work/source-facts/` | JSON/Markdown/源码快照 | 核对指定提交的原始行为与接口 |
| 行为与视觉 Journey | `work/journeys/core.yaml` | YAML | 公开行为、边界、稳定 ID 和截图检查点 |
