# 自验证结果

## 作品

- 赛题：02_01 Android 到鸿蒙移植
- Android 基线提交：`23e1421b72b602d80486777efbf24dd248abf3bb`
- 最终鸿蒙代码仓：`work/`
- 工程类型：HarmonyOS Stage、ArkTS/ArkUI、Entry HAP
- Bundle 名：`com.example.jetsnack`

## 执行方式

本地交付前自检可从作品根目录执行（评分平台按根 `INSTRUCTION.md` 的源码评测流程，不要求先执行此命令）：

```bash
cd work
sh tools/verify.sh --build
```

## 最近一次自验证结果

| 检查项 | 结果 |
| --- | --- |
| Android 固定基线与迁移映射校验 | 通过；6 个页面、6 条路由、10 个动作、28 个商品、34 项映射 |
| 仓内合同测试 | 通过；269/269 |
| ArkTS/API 20 兼容构建 | 通过；`BUILD SUCCESSFUL` |
| HAP 产物 | 通过；`entry/build/default/outputs/default/entry-default-unsigned.hap` 非空 |
| 五个独立 Executor 本地复现代理 | 通过；5/5 均为同一份交付结构，源码树一致，输入包只读；完整 HAP 构建见统一验证结果 |
| 交付结构检查 | 通过；必选文件与目录齐全，压缩包无缓存、构建产物和符号链接 |

最近一次主验证输出末尾为：

```text
BUILD SUCCESSFUL
stage=completed
status=passed
mode=build
build_scope=public_api_compatibility
hap=entry/build/default/outputs/default/entry-default-unsigned.hap
```

## 平台结果复盘与本轮改进

`docs/log_7_16.txt` 记录的上一版平台结果为：交付审查通过，237 个用例中准确性 230、稳定性 103，3 个 Executor 的 reproduction 均 failed。该日志没有失败用例名称，无法据此证明某个业务功能缺失；本轮可复现的确定原因是旧说明强制在未保证 HarmonyOS SDK 的评分环境执行构建，并且合同测试含 Python 3.10 专属 `zip(strict=True)`。

参赛者向组委会再次确认后，本轮不采用 `INSTRUCTION说明与样例.md` 的具体执行内容，只参考其表达格式。根说明现以真实赛题和平台要求为准：先执行静态合同与规范门禁；具备 HarmonyOS API 20 SDK 和 Hvigor 时执行真实构建；无 SDK 时不伪造通过或临时联网安装，继续把完整 `work/` 交给 HarmonyOS 评分 Skill。Scorer 通过 `work/migration-report.md` 定位 ArkTS、资源、配置、稳定 ID、Form Kit、深链和响应式安全区证据。合同测试也已兼容平台常见 Python 3.9，并把迁移报告纳入归档必选件。

针对三个 Executor 均 `reproduction_status=failed` 的执行层风险，根说明进一步固定了 `work/skills/android-to-harmonyos/SKILL.md` 的调用路径，要求以已交付源码为唯一输入；缺少 SDK/Hvigor/Code Linter 时只记录一次环境边界并继续评分，不重试、不联网安装、不重新生成代码。构建等待可通过 `VERIFY_BUILD_TIMEOUT_SECONDS=3600` 延长，避免慢速工具链误触发超时。

## 环境边界

本地已完成公共 API 20 兼容编译和仓内规范门禁。官方 HarmonyOS Code Linter 后端、真实 HarmonyOS 设备截图及平台隐藏用例由评分环境执行；本文件不将本地代理结果表述为隐藏用例成绩。
