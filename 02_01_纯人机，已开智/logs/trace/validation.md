# 实现与验证轨迹

## 输入基线

- 代码仓：`https://github.com/fuxi-artifacts/demo-Jetsnack-android`
- 固定节点：`23e1421b72b602d80486777efbf24dd248abf3bb`
- 离线事实快照：`work/source-facts/`
- 迁移映射：`work/migration-manifest.json`

## 主要实现产物

- HarmonyOS Stage 工程：`work/`
- ArkTS 页面与状态：`work/entry/src/main/ets/`
- 资源：`work/entry/src/main/resources/`
- Android→HarmonyOS 自动迁移 Skill：`work/skills/android-to-harmonyos/SKILL.md`
- 行为与界面 Journey：`work/journeys/core.yaml`
- 统一验证入口：`work/tools/verify.sh`

## 可复核验证

```bash
cd work
sh tools/verify.sh --static
sh tools/verify.sh --build
```

最近一次验证记录：

- 固定基线、迁移清单与资源合同通过；
- 269 项仓内测试全部通过，新增迁移报告必选件、Python 3.9 兼容回归和平台静态检查/编译/评分 Skill 交接契约；
- API 20 ArkTS 编译和 HAP 打包通过；
- 五个隔离 Executor 的本地复现代理均通过相同 269 项检查；
- 最终源码树在五次复现中保持一致；
- 输入交付包按只读方式复现。
- 上一版平台日志的 237/230/103 结果已记录在 `result/output.md`；本轮不把无用例名称的失败归因到具体业务功能，而修正可复现的构建前置条件和源码证据索引。
- 最新说明进一步固定评分 Skill 路径、缺失工具的一次性停止条件和慢速构建等待参数，减少 GLM/OpenCode 在五次独立执行中的自由发挥。

## 交付边界

提交包不包含 `.git`、`.gradle`、`.hvigor`、`build`、`node_modules`、`oh_modules`、`__pycache__`、`.hap`、`.pyc`、`.DS_Store` 或符号链接。官方 Code Linter、真实设备截图相似度和平台隐藏用例仍由评分平台给出最终结果。
