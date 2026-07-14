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
- 265 项仓内测试全部通过；
- API 20 ArkTS 编译和 HAP 打包通过；
- 五个隔离 Executor 的本地复现代理均通过相同 265 项检查；
- 最终源码树在五次复现中保持一致；
- 输入交付包按只读方式复现。

## 交付边界

提交包不包含 `.git`、`.gradle`、`.hvigor`、`build`、`node_modules`、`oh_modules`、`__pycache__`、`.hap`、`.pyc`、`.DS_Store` 或符号链接。官方 Code Linter、真实设备截图相似度和平台隐藏用例仍由评分平台给出最终结果。
