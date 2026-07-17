# 隐藏用例对抗与质量门禁

## 1. 验证设计原则

赛题不提供完整公开自验证用例，因此不能只凭“页面能打开”宣布完成。本项目把非公开评测拆成四类代理目标，并为每类建立事实、Journey、静态检查和代码证据：

| 评测维度 | 代理问题 | 主要证据 |
| --- | --- | --- |
| 功能一致性 | 操作后页面、状态、数量、金额、错误和返回栈是否与 Android 相同 | `source-facts/`、`AppStore.ets`、`journeys/core.yaml` |
| 截图相似性 | 同一状态下尺寸、资源、文字、主题和系统窗口是否相同 | `resources/`、组件几何合同、视觉 Journey、PNG 比较器 |
| 接口一致性 | 自动化能否定位并理解页面、动作、深链和 Form | `.id()`、无障碍角色、module/Ability/Form 配置、manifest |
| 代码规范 | 是否为原生 ArkTS/ArkUI，是否命中高风险静态规则 | `tools/tests/`、contract checker、preflight、官方 Linter 入口 |

## 2. 对抗用例族

### 功能和状态

- 搜索空查询、聚焦建议、大小写、单个空格、NoResults、清空、连续输入和 200ms 延迟取消；
- 购物车增减、数量归零删除、第 5 次失败、Snackbar 短时消失、FIFO 队列、总价和单数复数；
- Filter 选择、Apply/Reset no-op、重开、跨 Tab、详情往返和配置重建；
- Detail 展开/收起、数量下限、加入购物车、Cart→Detail→系统返回；
- Feed/搜索分类/商品动态入口、无效冷暖深链、重复 URI 和系统返回优先级。

### 截图和窗口

- 320/360/720vp 窄屏、平板和横屏侧边挖孔；
- 2.0/3.0 字体比例下长标题、分类、Cart Summary、Filter SortOption 和底栏自然增长；
- Light/Dark、阿拉伯语 RTL、Feed/Cart/Detail/Profile/Form 的主题资源和物理/逻辑方向；
- Hero 折叠、普通图片 Cover 裁切、Cart 侧滑进度、Snackbar 表面、Pressed 渐变和 BottomNav 安全区；
- 刘海顶部、无导航指示条、手势底栏和横屏侧避让区，不依赖固定上下 24vp。

### 接口和可访问性

- 生产 ID 反向覆盖动态 Feed、Search、Filter、Cart、Detail 和 Form 节点；
- 叶子点击节点的 Button 角色、Filter/Sort 的 selected/checked 状态和无障碍文本；
- Form Kit 尺寸断点、router 参数、冷暖启动、模块声明和外部 Cart URI；
- 资源引用、主题 key 对称性、唯一 ID、仓内路径和无凭据/无 WebView 壳检查。

### ArkTS/工程规范

- 无 `any`、空事件、错误类型导入、经典 `for`、Tab、非严格比较、正则字面量和其他已登记 ArkTS 2.0 高风险模式；
- 生产代码与测试/报告范围分离，用户可见文字和颜色资源化；
- Manifest 映射状态合法、目标为文件且位于仓内，迁移报告和事实快照完整；
- 提交归档不含 `.git`、`.gradle`、`.hvigor`、构建/依赖缓存、HAP/pyc、个人绝对路径或符号链接。

## 3. 先失败后修复的闭环

每次对抗修正遵循以下记录方式：

```text
固定 Android 事实
  → 添加可复现的失败合同或 Journey
  → 修改最小 ArkTS/资源/配置范围
  → 运行静态合同、映射检查和相关 Journey
  → 在可用工具链中编译
  → 归档审计并记录剩余环境边界
```

该流程避免为了某一张截图硬编码答案，也避免模型“认为完成”但没有可定位证据。所有已实现映射均回指真实目标文件，未知隐藏用例仍可从同一状态和接口契约扩展。

## 4. 当前本地质量结果

- 仓内静态合同：272/272 通过；
- Journey：228 条，覆盖功能、视觉、接口、窗口和配置边界；
- API 20 构建入口：`sh tools/verify.sh --build`，成功判定包含 `BUILD SUCCESSFUL`、`status=passed` 和非空 HAP；
- 官方 Code Linter：交付件保留 `--strict` 入口，但本机缺少后端，不虚构通过；
- 真机/模拟器截图：交付件保留设备取证和 PNG 比较工具，本机没有可用设备，不虚构截图成绩。

## 5. 泛化性说明

本仓针对公开 Jetsnack 基线做了高密度事实和状态对齐，但没有把未知答案写进裁判协议，也没有把某一套设备坐标作为唯一实现。泛化能力来自：

- Skill 中的事实抽取、映射台账、局部补全、编译反馈和失败策略；
- stable ID、Journey、资源合同、窗口避让和 ArkTS 规则可以迁移到同类应用；
- 平台主路径使用已完成仓，避免每次模型随机重写导致结果漂移。

## 6. 评委可抽查的代表案例

| 案例 | 代码/数据位置 | 可观察结果 |
| --- | --- | --- |
| 搜索最新查询胜出 | `SearchData.ets`、`AppStore.ets`、`edge.search.*` Journey | 旧请求不能覆盖新请求，空格不被擅自 trim |
| 购物车失败与 Snackbar | `AppStore.ets`、`CartScreen.ets`、Snackbar Journey | 失败消息、FIFO、4 秒生命周期和金额保持 |
| 多设备安全区 | `EntryAbility.ets`、`Index.ets`、`visual.safe-area.*` Journey | 刘海/导航条/横屏挖孔使用动态避让 |
| Form Kit | `form/RecentOrdersForm.ets`、`form_config.json` | 尺寸变化和 Cart router 均有目标实现 |
| 规范门禁 | `tools/tests/test_hidden_score_adversarial.py`、`preflight.sh` | 稳定 ID、无障碍、资源/路径和 ArkTS 风险可自动检查 |
