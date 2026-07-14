# Task Plan: ICT 安卓 APP 鸿蒙化赛题调研

## Goal
系统掌握当前仓库赛题要求，并从 `ICT_software` 已完成赛道、评分平台文档及 Codex 对话记录中提炼可复用的交付方法。

## Current Phase
Phase 9

## Phases

### Phase 1: 资料盘点与范围确认
- [x] 盘点当前项目 `docs/` 与仓库结构
- [x] 盘点 `ICT_software` 的需求、交付文档及会话记录
- **Status:** complete

### Phase 2: 当前赛题要求抽取
- [x] 提炼任务、功能、技术、材料、验收和评分要求
- [x] 区分明确要求、推断项和缺失信息
- **Status:** complete

### Phase 3: 已完成赛道交付模式研究
- [x] 解析 LLM-Wiki 交付定位与 AI 依托方案
- [x] 检查 requirement、产物目录和实际执行入口
- [x] 提炼评分平台上的交付/运行闭环
- **Status:** complete

### Phase 4: Codex 上下文与迁移价值分析
- [x] 定位并阅读相关 Codex 会话/上下文
- [x] 判断哪些经验可直接迁移、哪些不可照搬
- **Status:** complete

### Phase 5: 综合结论与后续建议
- [x] 建立当前赛题到可交付形式的映射
- [x] 给出风险、缺口和下一步调查/实施建议
- [x] 核对所有结论的文件证据
- **Status:** complete

### Phase 6: 安卓验证工程部署设计确认
- [x] 复核用户指定的交付目录定位
- [x] 盘点本机 JDK、Android SDK、Docker、Conda 和磁盘环境
- [x] 向用户呈现落位与构建环境方案并取得确认
- **Status:** complete

### Phase 7: 仓库获取与版本固定
- [x] 创建 `work/`
- [x] clone `fuxi-artifacts/demo-Jetsnack-android`
- [x] 创建并切换 `competition` 分支到指定 commit
- [x] 核验 remote、HEAD、分支与工作树
- **Status:** complete

### Phase 8: Android 构建环境配置
- [x] 根据仓库 Gradle/AGP 配置选择兼容 JDK
- [x] 安装并配置 Android command-line SDK 与所需 platform/build-tools
- [x] 记录可复用的本地环境路径与命令
- **Status:** complete

### Phase 9: 原工程构建验证与交付约定
- [x] 运行仓库规定的构建任务
- [x] 诊断并解决环境/依赖问题
- [x] 记录构建产物和验证证据
- [x] 固化 `work/` 与未来根目录 `INSTRUCTION.md` 的边界
- **Status:** complete

## Key Questions
1. 当前赛题要求选手最终实现和提交什么？
2. 评分平台如何获取、启动、调用和验证作品？
3. 已完成赛道的交付结构和 AI 依托方式，哪些适用于安卓 APP 鸿蒙化？
4. 当前仓库距离可评分交付闭环还缺什么？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 本轮只调研，不修改业务代码 | 用户明确要求先熟悉调研 |
| 结论分为“文档明确”“仓库证据”“合理推断” | 避免把其他赛道经验误当作本赛题硬性规则 |
| 原始 Android 仓只做本地 clone/checkout/build，不 push | 用户最终以 ZIP 交付打分平台，GitHub 仅作为公开基线来源 |
| 后续直接在仓库根 `work/` 进行完整鸿蒙化重构 | 最终 ZIP 不再额外包装 `demo-Jetsnack-android/` 目录，鸿蒙仓位置更直接 |
| 正式根 `INSTRUCTION.md` 留到解题交付阶段创建 | 本轮只部署基线；避免把本地构建说明误当成最终裁判执行剧本 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| 参考仓库全量隐藏文件清单包含 `.git/objects`，输出截断 | 1 | 后续排除 `.git/**` 并分目录精读 |
| 计划记录组合补丁定位失败 | 1 | 确认未写入后拆分为精确补丁 |
| 综合记录组合补丁逆序定位失败 | 1 | 按文件从上到下拆分补丁 |
| 最终记录组合补丁空表行定位失败 | 1 | 读取实际文件后定点更新 |
| GitHub 页面直接打开返回 cache miss，raw URL未返回内容 | 1 | 不依赖网页猜测版本；clone 后读取指定 commit 的 Gradle 配置再安装环境 |
| 沙箱 clone 无法连接本地代理端口 | 1 | 使用获准网络执行公开仓 clone |
| clone 后台未结束时误判为不完整仓库 | 1 | 轮询 exec session 到 exit 0 后重新核验 |
| 部署记录组合补丁逆序定位失败 | 1 | 拆分文件并按文档顺序更新 |
| Homebrew 沙箱内缓存更新权限失败 | 1 | 安装/状态检查改用获准外部执行 |
| Gradle Wrapper 沙箱内无法创建 `~/.gradle` lock | 1 | 使用获准执行下载并验证 Gradle 9.4.1 |
| 系统进程二次只读检查因工具额度限制被拒 | 1 | 未绕过；改用安装文件增长与原会话输出判断进度 |
| 首次 assembleDebug 在 Google Maven TLS handshake 失败 | 1 | 检查代理环境后，以一次性 JVM proxy properties 验证根因 |
| 外部 curl 诊断因工具额度限制未获批 | 1 | 不绕过；基于既有 Git/Homebrew 成功下载与 Gradle异常链继续最小验证 |
| 带 JVM proxy 的第二次 Gradle 构建在启动前被工具额度拒绝 | 1 | 等待 19:51 额度恢复后重跑，不修改工程版本 |
| 首次正式构建的依赖解析错误被 Gradle 9.4.1 异常格式化 NPE 遮蔽 | 1 | 以 `--info` 单独重跑失败任务，恢复真实依赖坐标与 TLS 根因 |
| 并发下载中 `androidx.activity:activity:1.13.0` AAR 出现瞬时 TLS EOF | 1 | 保留代理并在命令行关闭并行、限制单 worker 串行补齐缓存 |
