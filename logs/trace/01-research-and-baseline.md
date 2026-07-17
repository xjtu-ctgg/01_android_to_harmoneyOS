# 研究与基线冻结

## 1. 赛题问题的工程化解释

题目不是把 Kotlin 文本换成 ArkTS，而是要在隐藏验证下同时保留：

- 页面与交互可达性；
- 状态和数据的行为语义；
- 截图中的几何、文字、颜色、资源和系统窗口关系；
- 路由、深链、Widget/Form、稳定 ID 和无障碍接口；
- ArkTS/ArkUI 工程结构与静态规范。

平台文档还明确：`INSTRUCTION.md` 是 Agent 的运行入口，`work/` 是可运行交付件，`result/` 和 `logs/` 是评委参考材料。由此将“运行时随机迁移”和“交付前完成成品”区分开：平台主路径交付已完成的最佳仓，Skill 负责展示可复用迁移方法和审计流程。

## 2. 研究结论

调研了 HarmonyOS Stage/ArkUI/ArkTS、arkXtest/UiTest、官方 Code Linter、Android Compose 截图测试和多类 Android→ArkUI 迁移研究：

| 资料/工具 | 借鉴点 | 本项目采用方式 |
| --- | --- | --- |
| ArkTrans | 事实抽取、骨架生成、局部模型补全、编译/视觉反馈 | 采用“事实→台账→原生实现→门禁”的主链，不把整仓提示词翻译当主链 |
| UITrans | 分层转换、文档检索、编译错误回灌 | 只借鉴编排和错误反馈，不直接引入其 XML 主链、外部依赖或未审计代码 |
| GUIMigrator | 源 UI 与目标渲染器解耦、显式组件注册表 | 用 `migration-manifest.json` 保存源/目标/状态/Journey 映射 |
| ArkAnalyzer / ArkTS 规则 | ArkTS AST/数据流和规范扫描思路 | 仓内合同补充官方 Linter；不把本地规则冒充官方报告 |
| HarmonyOS-App-Test / arkXtest | 页面转换图、组件 ID、边界回放和截图采集 | 生成 `journeys/core.yaml`，提供设备证据和 PNG 比较工具 |
| Android golden / Compose Semantics | 同尺寸截图、语义节点和状态序列比较 | 用稳定 ID、资源合同、视觉 Journey 和可执行比较器形成交付证据 |

## 3. 方案裁定

最终采用两条相互约束的轨道：

```text
主得分轨：固定提交 → Android 事实快照 → 完整原生 HarmonyOS 仓 → 平台评分
泛化支撑轨：Skill → 迁移台账 → Journey → 静态/构建/归档工具 → 可复核报告
```

放弃作为比赛主线的做法包括：整仓一次性 LLM 翻译、只做 XML 转换、只用截图/VLM 复刻、依赖在线模型或把 Web/跨端壳伪装成原生鸿蒙。这些方法可能在单次演示中有效，但难以同时满足状态、接口、静态规则和稳定性。

## 4. 基线冻结结果

`work/source-facts/android-facts.json` 保存固定提交事实：

- 6 个页面、6 条路由；
- 28 个商品、5 个集合；
- 搜索匹配、延迟、空结果和最新查询规则；
- 购物车初始行、金额、失败周期和归零删除边界；
- 主题、字体、位图、向量、字符串、区域/货币和窗口避让契约；
- Manifest 中 Recent Orders Widget、公开 Android 测试路径和 no-op 合同。

完整源码快照位于 `work/source-facts/android-source/`，迁移清单位于 `work/migration-manifest.json`。冻结之后的 ArkTS 改动都要求能回指源事实和 Journey，而不是凭截图猜测。

## 5. 评审可核查的来源

提交包中的实现材料不依赖外部网络，但研究阶段参考了官方和公开资料，包括 HarmonyOS 开发者文档、OpenHarmony ArkTS 规范、UiTest API、Android Compose/Material 源码，以及 ArkTrans、UITrans、GUIMigrator 等公开研究。它们的作用是确定工程方法和验证指标，不是声称外部项目已经被直接集成。
