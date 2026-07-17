# 评委证据映射表

本表把主观评分关注点映射到提交包内可直接打开的文件，减少评委在大量实现文件中搜索的成本。

| 评委关注 | 首选证据 | 建议抽查内容 |
| --- | --- | --- |
| 迁移是否真实完成 | `work/migration-report.md`、`work/migration-manifest.json` | 源路径、目标路径、稳定 ID、Journey 和 `implemented` 状态是否互相对应 |
| 原生鸿蒙规范 | `work/build-profile.json5`、`work/AppScope/`、`work/entry/src/main/module.json5` | Stage 模型、Entry HAP、API 20、phone/tablet、Form/Ability 配置 |
| 页面与功能 | `work/entry/src/main/ets/screens/`、`components/`、`state/AppStore.ets` | 六页面/覆盖层、Tab、搜索、购物车、详情、筛选和共享状态 |
| 视觉还原 | `work/entry/src/main/resources/`、`theme/JetsnackTheme.ets`、视觉 Journey | 字体、位图、向量、明暗资源、渐变、尺寸、裁切和安全区 |
| 交互可测性 | `work/journeys/core.yaml`、各页面 `.id()` 和 accessibility 属性 | 稳定 ID 唯一、动态列表 key、Button/selected/checked 角色、动作结果 |
| Widget/Form | `work/entry/src/main/ets/form/RecentOrdersForm.ets`、`entryformability/`、`resources/base/profile/form_config.json` | 尺寸断点、订单内容和 Cart 跳转 |
| 深链和生命周期 | `EntryAbility.ets`、`AppRoute.ets`、`AppStore.ets` | 冷/暖 URI、系统返回、Filter 优先级、Tab/Detail 状态边界 |
| 自动化方法 | `work/skills/android-to-harmonyos/SKILL.md`、`agents/openai.yaml`、`tools/` | 事实抽取、映射、局部修复、质量门禁和完成仓交接 |
| 隐藏用例思路 | `logs/trace/03-hidden-case-and-quality.md`、`work/tools/tests/test_hidden_score_adversarial.py` | 空/错/边界输入、视口、字体、RTL、主题、触控和规范风险 |
| 稳定交付 | `INSTRUCTION.md`、`work/tools/platform_ready.sh`、`logs/trace/04-delivery-and-stability.md` | 只读、固定相对路径、完成标记、归档审计和不重生成策略 |
| 结果真实性 | `result/output.md`、`logs/trace/validation.md` | 本地通过项与评分环境待验证项是否明确区分 |

## 评审建议

先以 `migration-report.md` 建立总览，再抽查 `AppStore.ets`、`Index.ets`、一个页面、一个视觉资源、一个 Journey 和一条静态合同。这样能够同时验证“文档说了什么”和“代码实际上做了什么”，也能看出该作品不是只用长文档包装空仓。
