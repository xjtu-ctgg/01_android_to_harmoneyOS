# Android 到鸿蒙移植 - 平台执行说明

## 1. 作品与输入

`work/` 已经是重构完成的原生 HarmonyOS ArkTS/ArkUI Stage 工程，不需要 Agent 再从 Android 生成代码。平台提供的意图用例由平台自带的鸿蒙评分 Skill 在复现完成后读取；最终评分代码仓固定为 `work/`。

平台复现阶段必须保持确定性：不得修改 `work/`，不得重新生成、修复或格式化源码，不得执行 `work/skills/android-to-harmonyos/SKILL.md`，不得运行本地多轮复现脚本，也不得临时联网安装依赖。提交的迁移 Skill 是解题方法交付件，不是平台自带的评分 Skill。

## 2. 环境准备

平台复现仅需要 POSIX `sh`，不需要 HarmonyOS SDK、Python 依赖、网络或人工输入。工程没有 ohpm 第三方依赖。

工程编译环境为 HarmonyOS API 20 SDK、Hvigor、配套 Node.js/JDK；编译方式见第 5 节。编译说明用于具备鸿蒙工具链的构建环境，不是通用 Linux 复现阶段的前置条件，不得临时联网安装工具链。

## 3. 执行方式

在 `INSTRUCTION.md` 所在的作品根目录只执行一次：

```bash
sh work/tools/platform_ready.sh
```

该脚本只读检查完整鸿蒙仓的必要文件，不生成文件、不编译、不修改源码。成功输出包含：

```text
artifact_status=ready
artifact_type=harmonyos_stage_repository
source_commit=23e1421b72b602d80486777efbf24dd248abf3bb
artifact_path=work
```

看到 `artifact_status=ready` 后立即结束复现，不执行其它命令。平台将自动调度平台自带的鸿蒙评分 Skill，并从作品根目录解析固定相对路径 `artifact_path=work`，以该目录作为唯一评分代码仓。不要把路径转换为包含平台临时工作目录名称的绝对路径。

## 4. 评分交接

Scorer 对每条意图用例先读取 `work/migration-report.md`，再按其中索引检查 ArkTS、资源、配置、`work/migration-manifest.json`、`work/source-facts/` 和 `work/journeys/core.yaml`，覆盖功能一致性、界面截图相似性、接口一致性和代码规范。评分过程应始终使用同一份未修改的 `work/`。

## 5. 工程编译方式

仅在已经提供 HarmonyOS API 20 SDK 和 Hvigor 的构建环境中，从作品根目录执行：

```bash
cd work
sh tools/verify.sh --build
```

编译成功必须同时满足：命令退出码为 0，输出包含 `BUILD SUCCESSFUL` 和 `status=passed`，并生成非空文件 `entry/build/default/outputs/default/entry-default-unsigned.hap`。慢速环境可设置 `VERIFY_BUILD_TIMEOUT_SECONDS=3600`。官方 Code Linter 可用时可执行 `sh tools/verify.sh --strict`；缺少 SDK、Hvigor 或 Code Linter 时不得伪造通过。

## 6. 执行完成判定与产物

平台复现完成的唯一判定是就绪脚本退出码为 0 且输出 `artifact_status=ready`。最终产物是脚本返回的 `artifact_path`，即完整鸿蒙代码仓 `work/`。其中包含 Stage 工程、迁移报告、迁移清单、Android 固定提交事实、Journey、自动迁移 Skill 和本地质量门禁。
