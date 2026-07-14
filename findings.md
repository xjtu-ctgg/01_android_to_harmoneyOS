# Findings & Decisions: ICT 安卓 APP 鸿蒙化赛题

## Requirements
- 熟悉当前项目 `docs/` 中具体赛题任务要求。
- 调研 `/Users/ctgg/master/code/learn/ICT_software/` 其他赛道已完成作品。
- 重点理解 `docs/LLM-Wiki-交付定位与AI依托方案.md` 和 `requirement/`。
- 探索相关 Codex 模型对话上下文，判断对安卓 APP 鸿蒙化交付的帮助。
- 本轮输出调研认识，不修改业务实现。

## Research Findings
- 当前项目的官方/随题文档共 6 份：`android_to_harmoneyOS赛题要求.md`、`PLATFORM赛题提交指导.md`、`打分平台使用指导.md`、`参赛指导.md`、`FAQ.md`、`ICT_AI_ARENA - 概览.md`。
- 当前项目根目录除 `docs/` 外暂未发现业务源码目录；需在后续核实这是纯资料起点还是清单深度所限。
- 参考项目是已形成完整评分闭环的 LLM-Wiki 作品：包含 `requirement/` 原始要求、`docs/` 分析/方案、`work/llm_wiki_solver/` 实现、`tests/` 契约测试、`sample_llm_wiki/` 样例输入输出、`logs/` 执行轨迹、`result/` 结果以及打包 ZIP。
- 参考项目有明显的阶段性文档：`CHANGELOG_AND_STATUS.md`、`WORKSPACE_GUIDE.md`、`update.md`、`log7_7.md` 至 `log7_9.md`、`docs/last_v1/`、`docs/superpowers/plans/`。
- 参考项目存在 Codex turn-diff refs（`.git/refs/codex/turn-diffs/checkpoints/...`），说明至少可从 Git checkpoint/提交历史与日志追踪模型工作上下文。
- 两个项目共享的上层 Git 工作树目前有大量既有修改，尤其 `ICT_software` 仍是脏工作树；本轮严格只读参考项目，不能把工作树现状等同于稳定提交版本。

### 当前赛题：核心任务与评测闭环（首轮）
- 题目不是只手工重写 Jetsnack，而是要求提供 **Agent / Skill / 工作流**，自动把安卓 APP 迁移成鸿蒙 APP；目标是还原界面、交互与功能（`docs/android_to_harmoneyOS赛题要求.md:24-26`）。
- “成功翻译”分两层：功能完备度（功能入口都可触发，即使行为未完全正确）和功能可用性（功能实际实现且符合预期）（同文件 `:4-8`）。这意味着隐藏测试很可能先看覆盖，再看正确性。
- 基准安卓工程是 `demo-Jetsnack-android`，指定 Git commit 为 `23e1421b72b602d80486777efbf24dd248abf3bb`（同文件 `:10-21`）。
- 生成代码必须符合鸿蒙开发规范；静态扫描命中用例对应告警时，该项直接不通过（同文件 `:24-26`）。
- 官方不提供自验证用例；隐藏验证覆盖功能一致性、界面截图相似性、接口一致性、代码规范（同文件 `:32-34`）。
- 平台提交物统一放在 `work/`，作品形态不限；若用 Skill，强制路径为 `work/skills/{your-skill-name}/SKILL.md`（`docs/PLATFORM赛题提交指导.md:1-16,85-95`）。
- 作品根目录必须有 `INSTRUCTION.md`。自动裁判按其完成依赖/构建/安装、执行迁移工具、判断完成、获取“完整鸿蒙代码仓及其明确路径”，之后调度鸿蒙打分 Skill（同文件 `:27-83`）。全部步骤必须无人工交互。
- 平台拟从 `/app/code/judge-assets/02_01_android_to_harmoneyOS` 提供待迁移材料，但提交指导里的项目名/目录说明仍写成 `xxx` 占位符；因此输入发现方式和真实目录名尚未形成明确契约（同文件 `:18-25`）。
- 两份官方文档存在一个需要谨慎解释的表述差异：赛题要求说“`work/` 内提供重构后完整鸿蒙代码仓”，提交指导又把 `work/` 定义为自动迁移工具所在处，并要求运行后生成鸿蒙仓。合理交付应同时覆盖两层：`work/` 中有自动化迁移能力，并保证执行后产出完整可编译仓；是否还应预置 Jetsnack 成品需结合参赛指导、FAQ 和参考赛道确认。

### 当前赛题：大赛通用交付与评分规则
- 最终上传为 ZIP，命名 `{赛道ID}_{题号}_{队名}.zip`；必选结构是 `/INSTRUCTION.md`、`/work`、`/result/output.md`、`/logs/interaction.md`、`/logs/trace/`。`result` 是自验证证据，`logs` 是人工交互与推理轨迹（`docs/参赛指导.md:68-91`）。
- `INSTRUCTION.md` 在通用指导中被定义为平台“加载作品运行过程”的入口；打分平台使用指导又进一步说它应包含交给 Agent、让其长期稳定运行并最终实现作品的“原始提示词”（`docs/参赛指导.md:81-90`; `docs/打分平台使用指导.md:72-75`）。这说明它不是普通 README，而是 **裁判 Agent 的执行剧本/主提示词**，需要同时写明目标、资源、动作、命令、完成标准和输出位置。
- 平台允许选择 Agent 框架和模型，目前文档列出 CodeAgent 2.0、OpenCode；基础环境列出 Linux、GCC、POSIX、Python 3、Rust/Cargo，但未明确 DevEco Studio、HarmonyOS SDK 或 Android SDK 是否预装（`docs/打分平台使用指导.md:21-69`）。这是鸿蒙题的关键环境风险。
- 平台会清空上下文独立并行/重复运行 5 组（或 5 次）来衡量稳定性与准确性，且每日最多提交 5 次，只显示分数/通过比例，不给失败明细（`docs/打分平台使用指导.md:21-50`; `docs/参赛指导.md:63-66,126-149`）。因此作品必须可重复、幂等、无隐藏人工状态，并要本地建立代理验收。
- 通用积分结构是客观 60（准确性 30 + 稳定性 30）与主观 40（泛用性 20 + 规范性 10 + 性能 10）。针对验证工程硬编码会扣泛用性；性能看 5 次运行的时长和 Token 均值/极值（`docs/参赛指导.md:126-176`）。
- `打分平台使用指导.md` 另给了一个折算到 100 的客观最终分公式，而 `参赛指导.md` 明确总评为 60 客观 + 40 主观。更合理的解释是：前者是平台展示的客观评分口径，后者是竞赛总积分口径；后续应向组委会确认而不能混为一谈。
- 多次提交不是取历史最高，而是以“最后一次成功提交并完成打分”为准；同一赛道多题则取各题最高作品作为该赛道参赛作品（`docs/打分平台使用指导.md:9-19`）。最后一次提交必须做回归验证，不能用试验性版本覆盖高分稳定版。

### FAQ 对平台真实运行方式的补充
- 判题模型文档当前写明 GLM5.1、MiniMax-M2.7，上下文窗口 200k；Agent 是 CodeAgent 2.0 / OpenCode。工具不一致可能导致本地与平台分数异常（`docs/FAQ.md:72-101,159-161`）。
- 判题环境是黄区 Docker、Linux、**无外网**；第三方包建议随 `work/` 打包并在 `INSTRUCTION.md` 第一阶段安装，本地型数据库优先（同文件 `:273-287`）。安卓/鸿蒙迁移工具不能依赖运行时 GitHub、npm/pip 在线下载或远端服务。
- 平台实际输入会变化，部分 docs 不公开（同文件 `:87-90`）。这直接证明不能只针对公开 Jetsnack 写死转换；Agent 必须先发现输入仓、分析工程结构再迁移。
- `INSTRUCTION.md` 明确就是主 Agent 输入，人工交互也应预先写入；本地调试方式是把它整体作为 Prompt 运行、看 Agent 能否正确使用 `work/`（同文件 `:115-125,147-149`）。
- `/work + INSTRUCTION.md` 用于平台客观运行；`/logs + /result` 是选手提交的自验证/推理证据，主要供主观评审（同文件 `:103-105`）。因此这两套产物都不能缺，但用途不同。
- FAQ 对“重构类题目”的直接回答是：需提供重构 Prompt，同时验证“重构后的结果 + 重构的过程”（同文件 `:291-299`）。对本题而言，只交一个成品鸿蒙仓无法充分体现赛题核心；迁移过程资产是必要评分对象。
- 平台自动跑 5 个实例，不是选手手动跑五次；可见客观分、时长和 Token，手工提交每题每日最多 5 次（同文件 `:249-263`）。
- 题目仍可能细微调整，以最新下载版本为准（同文件 `:205-213`）。当前本地文档应视作调研基线，提交前需再核对平台最新版本。
- FAQ 说“作品要求和题目内交付件要一起提交”（同文件 `:66-68`），进一步支持本题最终 ZIP 应兼顾通用目录结构与赛题特定的完整鸿蒙代码仓要求。

### LLM-Wiki 已完成赛道：交付定位的核心经验
- 该作品最终定位不是离线脚本或一段提示词，而是“平台 Agent 可理解、可调用、可验证的 Tool / Skill / CLI”。平台 Agent + 模型负责理解/规划/调用，本地确定性工具负责解析、检索、执行、安全和格式校验（`ICT_software/docs/LLM-Wiki-交付定位与AI依托方案.md:3-19`）。
- 它明确区分两层 AI：① 必然存在的平台 Agent 模型；② 不保证暴露给参赛 Python 的模型 API。最终方案以第一层为主、第二层仅 optional enhancement，API 不可用必须可离线降级（同文件 `:47-65,609-624`）。这对鸿蒙题同样关键：不能假设迁移代码可直接获得判题模型 endpoint/key。
- 作品把职责拆为平台 Agent、模型语义层、本地安全/解析/检索/执行/校验层；LLM 不做权限最终判定、任意文件写入、任意代码执行和自由格式最终输出（同文件 `:81-105,226-244`）。可迁移原则是“Agent 做判断与编排，脚本做可重复机械动作，校验器做最终闸门”。
- 交付形态采用三层入口：`INSTRUCTION.md`（主 Agent 执行剧本）→ `work/skills/.../SKILL.md`（任务内操作手册）→ `work/.../main.py` CLI（确定性批处理入口），并让日志记录路由、安全判定、检索证据和规则/模型使用情况（同文件 `:87-93,109-120`）。
- 平台未知隐藏输入下，继续堆公开样例关键词导致泛化不足；已覆盖题型虽然稳定，未知表达/复杂语义大量失分。后续从“规则堆叠”转成“Agent 工具化 + 结构化索引 + 混合检索 + 安全确定性执行”（同文件 `:67-79,166-168`）。对应鸿蒙题应避免针对 Jetsnack 文件名/页面写死生成，改成可发现页面、资源、导航、状态和依赖的迁移流水线。
- 最终交付不依赖 `.opencode/` 或用户本地 Skill 路径，所有 Skill 严格放 `work/skills/{name}/SKILL.md`；重依赖和联网工具均 optional，零额外依赖时 CLI 仍能跑（同文件 `:500-534,567-574`）。
- LLM-Wiki 从早期 45.8/33.3 的不稳定评分，演进到 `log7_9` 客观正确性/稳定性 100；成功后仍继续修 WARN、补回归测试并为泛用性/规范性/性能 40 分优化（同文件 `:67-79,586-607`）。经验是平台满客观分并不等于交付完成，主观证据与性能仍需打磨。

### LLM-Wiki 原始要求到成品方案的映射
- 原始题目明确平台会把 `llm-wiki` 放在 `work` 同级，隐藏材料包含 200+ 多格式文件、20–30 个问题、动态目录/文件分类与 Permission 黑名单（`ICT_software/requirement/01_llm_wiki赛题要求.md:1-21,38-102`）。成品没有打包真实隐藏材料，而是让 CLI 接受 `--root` 并运行时发现输入。
- 输出契约非常具体：按题目 `answer_format` 产生 JSON；相对路径、固定拒答对象、修复副本目录都有硬约束（同文件 `:156-196`）。已完成作品据此建立了 normalize/validator 和 delivery-contract 测试，而不是把自然语言答案直接交给模型自由生成。
- 隐藏材料不完整公开，官方允许自行补充本地测试样本（同文件 `:198-200`）。对应实践是制作 `sample_llm_wiki/`，并把样例输入、预期输出、修复副本与权限场景一起纳入回归测试。
- 参考提交指导本身仍有 `{内容}` 占位、重复章节和未写完的自动评测流程（`ICT_software/requirement/难题赛道-01-大模型知识管理提交指导.md:18,73-85,131-140`）。作品团队没有等待文档完全规范，而是把明确的不变量（judge-assets 路径、无人工、输出位置、Skill 路径、完成判定）固化进自己的 `INSTRUCTION.md` 与测试。
- 该指导把“未提供方案说明/验证方案”“修复工程不可构建”“修改 REST API 契约”列为无法评测情形（同文件 `:143-155`）。虽然鸿蒙提交指导措辞不同，但可推导：方案说明、构建验证和接口不破坏应主动进入我们的自验证证据。

### 实际 `INSTRUCTION.md` / Skill 的可复用写法
- 成品 `INSTRUCTION.md` 首句就声明交付形态和主链，然后依次覆盖：环境/降级策略、Skill 位置、平台输入路径、唯一主命令与参数、完成判定、结果获取、输出 schema、安全、自验证、无人值守注意事项（`ICT_software/INSTRUCTION.md:1-194`）。它已经是一份可执行 Prompt，而非背景介绍。
- 它把必选路径与可选增强分得很清：标准库主链不需联网/安装/常驻服务；LibreOffice、MarkItDown、Docling、直连 LLM 全部“有则用、无则回退”，并对 API 调用设 12 次、8 秒、0 重试预算（同文件 `:5-21`）。这直接服务五次运行稳定性和性能。
- 主执行只有一条完整命令，并明确工作目录、平台根路径、全题组、日志目录、LLM 模式；还提供纯确定性和单组运行变体（同文件 `:49-76`）。完成条件可机器验证：exit code 0 + 每个输入题组都有输出 + 修复/trace 在固定目录（同文件 `:78-103`）。
- `INSTRUCTION.md` 同时复述关键输出格式和安全边界，避免平台 Agent 只读入口而未加载深层代码时产生误操作（同文件 `:137-173`）。末尾明确“若模型要求确认，也继续执行主命令、不向选手提问”（同文件 `:189-194`），这是处理自动 Agent 犹豫/确认行为的实用细节。
- 主 Skill 比 `INSTRUCTION.md` 短很多：YAML frontmatter 提供触发描述，正文只保留识别条件、平台/本地路径、必跑命令、行为清单和安全清单（`ICT_software/work/skills/llm-wiki-solver/SKILL.md:1-62`）。两者不是重复文档：入口负责完整编排，Skill 负责让 Agent 快速选对能力和守住不变量。
- 对鸿蒙题可直接迁移为：`INSTRUCTION.md` 指示找到 judge-assets 安卓仓 → 加载 `android-to-harmonyos` Skill → 运行迁移入口 → 编译/静态检查/测试 → 在固定路径返回完整鸿蒙仓；Skill 则描述何时触发、迁移阶段、禁止项和验收闸门。

### 开发工作台、提交包与自验证证据
- 参考项目刻意只维护一套根目录工作台，不再复制 `submission/` / `deliverable/` 两套代码；根目录同时组织入口、参赛代码、测试、样例、结果、日志、原始要求、方案和变更状态（`ICT_software/WORKSPACE_GUIDE.md:1-15`）。这样避免“开发版本已修、提交副本没同步”。
- 真正打包只取 `INSTRUCTION.md + work/ + result/ + logs/`；测试、样例、原始 requirement、评分脚本和历史日志默认不交（同文件 `:17-47`）。这是一套“开发仓丰富、提交包精简”的边界。
- `result/output.md` 不是一句“运行成功”，而是可审计的验证报告：记录日期、精确命令、测试数与耗时、离线/auto 两模式、样例输出、最小提交包模拟路径、trace 字段、修复输出、必需路径契约和平台 WARN 回归（`ICT_software/result/output.md:1-86`）。
- 最有价值的验证是“最小提交包模拟”：只复制将上传的四类内容，再额外创建仿真的 judge-assets 目录运行。这能发现开发仓里未显式声明的路径/依赖偶合（同文件 `:37-48`）。鸿蒙题也应在临时 Docker/目录里只用最终包 + 模拟安卓输入，跑迁移、编译、静态检查和产物定位。

### 平台评分实录与测试体系
- 三次平台实录揭示的实际阶段是：下载 → 解压并检测 `INSTRUCTION.md` → 建 5 个隔离执行目录 → 交付审查 → 5 个 executor/assistant judge 复现 → 用例评分 → 汇总。`log7_9` 还表明 **package_root 被设为只读**（`ICT_software/log7_9.md:9-38`）。鸿蒙迁移不能在提交包原地覆写，必须向允许的 judge-assets 输出位置或明确的工作目录生成仓库。
- 7 月 7 日版本出现 20/24、20/24、20/24、2/24、4/24 的巨大分叉；7 月 8 日版本收敛到 8/24–9/24；7 月 9 日五个 executor 都产出有效 artifact，24/24 accuracy/stability，最终客观 100。目标不仅是单次高通过，而是把不同 Agent 实例的执行路径收敛到同一条确定性命令。
- `log7_9` 的交付审查机器字段很具体：`instruction_archived`、`instruction_is_reproduction_guide`、`skill_path_valid`，之后每个 executor 验证 `artifact_valid`（同文件 `:26-45`）。说明入口说明和产物契约本身就是自动化打分前置项。
- 即使总分 100，模型评估仍报告 3 个 WARN（过度返回敏感信息、过度拦截安全脚本）；团队把 WARN 转成精确回归用例而非忽略。对鸿蒙题，截图偏差、规范告警、功能入口可触发但行为不对等 WARN 也应逐项固化为回归。
- 参考测试并非只有业务单测，而是分为：权限/安全、批注解析、CLI 端到端、混合索引、答案规范化、LLM schema/tool-call、LLM 降级/修复安全、以及 `test_delivery_contract.py` 的根目录/Skill/INSTRUCTION 契约检查。交付结构也被测试，这是很值得直接复用的方法。
- 鸿蒙题对应测试层应至少包含：提交目录契约、输入仓发现、迁移命令端到端、生成仓完整性、构建成功、静态规范扫描、页面/路由/交互清单覆盖、接口一致性、截图基准、重复五次输出稳定性、只读提交包与无网环境验证。

### Codex/迭代上下文：首轮定位
- 参考仓库内没有常规命名的 chat/session 转录；`logs/interaction.md` 只有空行，符合“平台运行全程无人工干预”的提交约定，而不是开发对话记录。
- 可用的模型工作上下文主要有四类：① 5696 行的 `update.md`（大量 patch/diff 与设计片段）；② 892 行 `CHANGELOG_AND_STATUS.md`（按阶段记录问题、修复、测试和待办）；③ `docs/superpowers/plans/` 的专项实现计划；④ Git 中两个 `refs/codex/turn-diffs/checkpoints/...` checkpoint。
- Git 主历史只有 `init`、`ok`、`7_9` 三个提交，粒度太粗；要理解 Codex 的决策过程，应优先读 changelog/专项计划/turn-diff，而不能只看 commit message。
- `update.md` 的关键词扫描显示它保存了成片的代码增删、测试设计和方案改写，形态更接近 Codex 轮次差异或汇总 diff，不是直接的 user/assistant 对话文本。后续会按“决策—实现—测试—评分反馈”抽取，而不逐行复述 5696 行补丁。

### 从 Codex 迭代记录提炼出的工作方式
- `CHANGELOG_AND_STATUS.md` 采用固定闭环：记录平台票型/得分 → 提出根因假设 → 标注 CRITICAL/HIGH/MEDIUM/LOW → 列具体文件改动 → 新增针对性测试 → 本地样例验证 → 再提交平台。这比单纯保留聊天记录更适合作为可执行上下文。
- 早期看到 AJ1–3 宽松、AJ4–5 严格，团队推断严格 schema/精确字符串/非确定性输出是稳定性根因，于是统一排序、int、路径分隔符、TODO 格式、合法字段，并缩小 LLM 路由（`ICT_software/CHANGELOG_AND_STATUS.md:129-166,232-244,502-511,658-685`）。这说明五次评测分叉首先要查 **输出确定性和 Agent 行为收敛**。
- 迭代记录保留了“问题—改动—涉及文件”，例如 OOXML 跨标签、权限语义、TODO 重复计数、多文件修复、LLM 盲路由、安全白名单过窄等。这种粒度让后续模型能接着做，而不是重新读全仓猜历史原因。
- 也能看到一次重要认知转变：前几轮主要补公开/已知题型规则，本地测试上升但平台 7_8 仍只有 33.3；第九轮才把交付整体重构为平台 Agent + 标准 Skill + 单 CLI + 混合索引 + validator，随后 7_9 达到 100。对鸿蒙题，优先把“平台如何稳定驱动迁移”架构做对，比一开始只补某个页面像素/某个 API 映射更高杠杆。
- 记录中也明确执行了“测试先失败再实现再通过”（同文件 `:105-113`），并在客观满分后继续对 WARN 加回归。对我们的迁移流水线，评分反馈应直接转成新的可自动验证检查，而不是只修改 Prompt 文案。
- 注意：这些文件是经过整理的工程上下文，并非完整原始 Codex 对话；能可靠复用的是决策链和结果证据，不应臆测未记录的具体对话措辞。

### Codex checkpoint / update / 专项计划的含义
- `update.md` 从 `diff --git` 开始，包含旧版到某一交付快照的广泛 patch，末尾还枚举新增样例文件与 Skill；因此它可用于恢复“某轮模型实际改了什么”，但内容有重复且不是当前真相。当前文件与测试应优先于这份旧 diff。
- 两个 Codex checkpoint ref 指向 Git **tree object**，没有 commit message/作者/对话文本。这类 ref 能重建某轮结束时的文件树、做差异对照，但本身不能还原用户和模型的语言交流。
- 四份专项计划都使用相同结构：Goal、Architecture、Tech Stack、按 Task 分解，并为每项指定测试先行、精确文件/函数、预期失败、最小实现、验证和记录更新。主题覆盖隐藏 TODO/修复/XLSX、受限 Python 执行、多条件表格和执行深度。
- 这些计划体现的可迁移做法是：针对隐藏评分缺口，不写“优化迁移效果”这种宽泛任务，而写成可验收的能力切片。例如鸿蒙题可拆为“Compose 页面识别 → ArkUI 页面骨架 → 资源转换 → 导航与交互 → 网络/数据层映射 → 构建与规范扫描 → 截图对比”，每片先有失败样例和验收命令。

### 原始 Codex 会话：真实演进脉络
- 已定位 6 个与 `ICT_software` 直接相关的 JSONL 会话（2026-06-25、06-27、07-08），来源为 Codex VS Code 0.142.x；部分 session 在 compact/resume 时重复写 `session_meta`，不是多次独立会话。
- 最初用户明确要求“先详尽分析赛题/提交要求与外部方法，先写技术方案和代码流程两份文档，再按文档实现”。随后把计划作为显式实施输入。这解释了仓库为何同时保存需求、方案、实现计划与代码，而不是模型直接无计划生成成品。
- v1 计划已经选择“确定性规则优先、LLM 复杂理解辅助”；v2 会话进一步限定 LLM 不直接访问文件、不执行命令、不决定安全，只输出 QueryPlan/Evidence/RepairPlan/AnswerDraft，最终由本地 Permission、写入、schema 和 validator 接管。
- 用户后来主动质疑为什么没有 Embedding + 余弦检索，并指出平台有 MiniMax/GLM。会话推动方案加入 SQLite + Embedding + Rerank 的混合架构；后续在读完平台规则后又修正为“平台一定有模型 ≠ Python 一定有 API”，因此向量/直连模型保持适配器和 optional，而不是强依赖。这是一次很重要的需求澄清与工程收敛。
- 后期用户连续追问 Skill 规范、`INSTRUCTION.md`、修复文件语义、logs/interaction/trace、最终打包内容和 `log7_9` WARN；模型工作随之从算法实现转向交付复现、评审解释和提交前审计。这说明比赛后半程的核心对象已从“代码功能”切换为“可评分交付闭环”。
- 原始会话也证实 `update.md` 是用户提供的“大幅更新代码变化集合”，之后由 Codex 整理回当前文件；它不是权威当前代码。使用参考仓时应以工作树 + 测试 + 最新评分记录为准。

## 面向安卓 APP 鸿蒙化的综合映射

### 当前仓库现状与缺口
- 当前项目实际只有 6 份赛题/平台 Markdown（另有本轮 3 个调研过程文件），没有文档声称的 `code/demo-Jetsnack-android`，也没有 `INSTRUCTION.md`、`work/`、`result/`、`logs/`、迁移代码、鸿蒙代码仓或测试。因此现在是“赛题资料起点”，尚不是可运行参赛作品。
- 最需要尽早确认的外部契约：① `/app/code/judge-assets/02_01_android_to_harmoneyOS` 下真实输入目录和结构；② 平台是否预装 Android SDK、HarmonyOS SDK、DevEco/hvigor、静态扫描 Skill；③ 允许的最长时长/Token/磁盘；④ 最终鸿蒙仓固定输出路径；⑤ `work/` 是否还需随包预置公开 Jetsnack 的成品鸿蒙仓。

### 建议的最终作品形态（由明确规则 + 参考实践推导）
- 根入口：`INSTRUCTION.md`，作为主 Agent Prompt，必须给出输入发现、Skill 加载、唯一主命令、环境检查、完成条件、失败/降级策略和生成仓位置。
- 自动化主体：`work/` 中的迁移 orchestrator/CLI 与平台规范 `work/skills/android-to-harmonyos/SKILL.md`；可按需再有 Android 工程分析、ArkUI 生成、构建/规范修复、UI 对比等专用 Skill，但不应无目的堆 Skill。
- 结果：运行后在固定可写路径生成 **完整、可编译** 的鸿蒙工程；考虑题目措辞差异，提交前最好同时保留对公开 Jetsnack 的完整迁移成果或明确由主命令生成，等待平台答疑确认最终放置方式。
- 主观证据：`result/output.md` 记录迁移命令、构建、静态检查、功能覆盖、接口检查、截图对比、五次重复运行和最小提交包模拟；`logs/interaction.md` 无人工则留空；`logs/trace/` 记录每阶段输入、识别清单、生成/映射决策、命令、错误、修复轮次、耗时/Token和最终产物。
- 开发仓应额外保留 `tests/`、公开/合成 Android 样例、预期 Harmony 工程、方案文档与状态记录，但像参考作品一样，最终 ZIP 只打包规则要求和题目特定交付件。

### 建议的确定性迁移主链
1. 输入发现与只读保护：定位平台安卓仓，复制/生成到可写目录，禁止修改只读 submission package。
2. Android 资产盘点：Gradle/module、Manifest、Compose/XML 页面、导航、资源、主题、状态、网络、存储、权限、第三方依赖和接口清单。
3. 迁移计划：建立 Android → HarmonyOS 映射清单与 unsupported/待补项，确保每个页面、入口、交互和接口都有目标。
4. 工程生成：创建完整 Stage 模型/Harmony 工程配置、ArkTS/ArkUI 页面、资源、导航、状态/data/network 层；机械映射由脚本/模板完成，复杂语义与修复由平台 Agent 处理。
5. 多闸门验证修复：目录完整性 → 编译 → 静态规范扫描 → 页面/路由/交互覆盖 → 接口一致性 → 截图相似性 → 关键功能行为；每轮失败定点修复并设上限。
6. 交付判定：命令 exit 0，固定路径存在完整鸿蒙仓，构建/扫描通过，所有识别到的 Android 功能均有迁移状态，trace/report 完整。

### 评分导向的优先级
- 第一优先：让五个 Agent 实例都走同一条主命令、同一输入发现和同一输出路径，保证 artifact 可生成且可编译；这是稳定性底座。
- 第二优先：页面/功能入口覆盖与代码规范。赛题把“可触发”与“符合预期”分层，先消除缺页、缺路由、缺按钮/交互，再逐步提高行为正确性。
- 第三优先：截图相似、接口一致、状态/数据行为正确；这些决定从“功能完备”走向“功能可用”。
- 第四优先：泛用性和性能。迁移规则应从工程结构和语义发现，不按 Jetsnack 名称硬编码；LLM/API 仅在可用时增强，设调用/修复预算，避免五次运行发散或超时。

### 可直接复用与不应照搬
- 直接复用：提交目录骨架、三层入口、平台 Agent/内部 API 边界、离线降级、只读包处理、固定产物、delivery-contract 测试、最小提交包模拟、trace/result 证据、评分反馈回归化。
- 方法论复用：先文档/方案，再能力切片；每片测试先行；明确问题—改动—文件—验证；客观满分后继续修主观 WARN。
- 不照搬：LLM-Wiki 的 Office Skill、SQLite/RAG、Permission/答案 JSON、Python AST 执行都属于题域实现，不是鸿蒙迁移核心。
- 需要替换为鸿蒙题域能力：Android/Gradle/Compose/XML 解析、ArkTS/ArkUI/Stage 模型代码生成、资源/导航/数据层映射、hvigor 构建、鸿蒙规范扫描、UI 自动化与截图差异。

## Final Verification Evidence (2026-07-10)
- 当前项目清单重新验证：业务/赛题文件确实只有 `docs/` 下 6 份 Markdown；`code/`、`INSTRUCTION.md`、`work/`、`result/`、`logs/`、`tests/` 均不存在。
- 当前赛题关键原文重新命中：Agent/Skill/工作流、完整鸿蒙代码仓、编译说明、四类隐藏评估、judge-assets 路径、无人值守、60/40 评分、无外网、主 Agent 输入和“重构结果 + 过程”。
- 参考项目关键证据重新命中：CLI + 规范 Skill、无网主链、明确完成判定、只读 package_root、合法 Skill 路径、`log7_9` 客观 100、48 项本地验证记录、最小提交包模拟、平台 Agent/内部 API 双层定位。
- 原始会话文件重新定位为 6 个与 `ICT_software` 匹配的 JSONL 文件。
- 所有验证命令 exit code 均为 0；本轮是文档调研，不声称当前鸿蒙工程可构建或测试通过，因为该工程尚不存在。

## Deployment Findings (2026-07-10)
- 用户已明确新的交付约定：`work/` 中直接放指定 Jetsnack 仓，后续在该仓基础上完成鸿蒙化；未来 `INSTRUCTION.md` 放当前项目根目录。
- 本机为 Apple Silicon (`arm64`) macOS 26.2，剩余磁盘约 151 GiB。
- 当前 `java` 是 OpenJDK 25.0.2；尚不能认定与目标仓的 Gradle/Android Gradle Plugin 兼容，必须 clone 后读取 wrapper/AGP 配置再选择 JDK 版本。
- 当前没有 Android Studio、`~/Library/Android/sdk`、`ANDROID_HOME`、`ANDROID_SDK_ROOT`、`sdkmanager` 或 `adb`。
- Docker CLI、Miniconda、Homebrew 已存在；对原生 Android Gradle 构建，推荐 Homebrew/JDK + Android command-line tools 作为主环境，Docker 只作为必要时的可复现备选，Conda 不适合管理 JDK/Android SDK 主链。
- 目标 GitHub 页面在网页工具中一次 cache miss，raw 文件请求未返回内容；为避免根据上游主分支误判，环境版本将在 clone 指定 commit 后从仓内配置确定。
- 仓库最初 clone 到 `work/demo-Jetsnack-android`，随后按最终交付结构去掉该包装层；当前仓库根目录为 `work/`，remote 仍为比赛指定公开仓。
- clone 默认 `main` 的 HEAD 已是指定 commit `23e1421b72b602d80486777efbf24dd248abf3bb`。
- clone 过程超过首次等待窗口后转入后台 session；过早检查曾看到临时 pack/无 HEAD，轮询真实 session 后 exit 0，仓库和工作树完整。根因是检查时机，不是仓库损坏。
- 已按题面创建本地 `competition` 分支，起点为指定 commit；这只是本地分支，没有上传行为。
- 指定 commit 的构建矩阵：Gradle Wrapper 9.4.1、Gradle daemon JVM 21、Android Gradle Plugin 9.1.0、Kotlin 2.3.21、compile/target SDK 36、min SDK 23、Java/Kotlin bytecode target 17。
- 环境主线据此确定为 JDK 21 + Android SDK Platform 36 + Build Tools 36.x + platform-tools；不使用 Conda 管理 Android/JDK，Docker留作必要时的第二验证环境。
- 仓库版本复核通过：当前分支 `competition`，HEAD 精确等于指定 commit，origin URL 正确，工作树无改动。
- Homebrew 在沙箱内检查包状态时尝试更新 `~/Library/Caches/Homebrew` 并因权限失败；环境安装需要按沙箱规范使用已获准的外部执行。
- OpenJDK 21.0.11 已安装在 `/opt/homebrew/opt/openjdk@21`，保持 keg-only，不覆盖系统默认 JDK 25。
- Android command-line tools 14742923 已安装；SDK 许可证已接受。
- Android SDK 已安装到 `/Users/ctgg/Library/Android/sdk`：Platform 36 rev 2、Build Tools 36.0.0、Platform Tools 37.0.0；`adb` 1.0.41 可运行。
- 仓库 `.gitignore` 明确忽略根 `local.properties`；已用该本地文件配置 `sdk.dir=/Users/ctgg/Library/Android/sdk`，不会污染提交差异。
- Gradle Wrapper 9.4.1 已下载到标准 `~/.gradle` 缓存；`./gradlew --version` exit 0，Launcher JVM 21.0.11，Daemon JVM 按仓内条件选择 Java 21，OS 架构为 aarch64。
- 首次沙箱内运行 Wrapper 因不能写 `~/.gradle` lock file 失败；使用获准执行后成功。这是沙箱权限边界，不是工程构建问题。
- 首次 `:app:assembleDebug` 在项目配置期失败，唯一根因链为 Google Maven `aaptcompiler:9.1.0` POM 下载时 TLS handshake 被中断；尚未进入源码编译。
- 本机环境只设置了 `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7897`，无 Gradle `~/.gradle/gradle.properties` 代理配置；curl 在沙箱内也因无法连接该本地代理失败。Git/Homebrew 在获准外部执行中可通过该代理下载，因此当前单一假设是 JVM/Gradle未自动采用环境代理。
- 下一次构建只增加 Java `http/https.proxyHost=127.0.0.1`、`proxyPort=7897`，不修改仓库依赖或版本，以验证该根因。
- 带 JVM proxy properties 的第二次构建尚未启动：外部执行在进程创建前被工具额度限制拒绝，提示 19:51 后再试。该拒绝不是 Gradle/源码失败，不能据此判断代理修复是否生效。
- 阶段性新鲜核验：`competition`、指定 HEAD、origin、干净 tracked diff、`local.properties`、JDK 21、android-36/android.jar、Build Tools aapt2、adb 均存在；APK 输出为空，因此明确不宣称构建通过。
- 2026-07-11 重试时，将 `http/https.proxyHost=127.0.0.1` 与 `proxyPort=7897` 作为一次性 JVM properties 传给 Gradle 后，`aaptcompiler:9.1.0`、AGP 9.1.0、Kotlin Gradle Plugin 2.3.21 等依赖均成功进入标准 `~/.gradle` 缓存，证实此前 TLS 失败源于 JVM 未采用环境代理。
- 最小配置验证 `./gradlew help` 已 `BUILD SUCCESSFUL in 7m 46s`。长时间静默期间线程栈显示 Gradle 正在解压和 instrument classpath，而非死锁；首次缓存建立完成后可继续正式 APK 构建。
- 第一次正式构建已进入 `generateDebugResources`、`packageDebugResources`、`processDebugNavigationResources`，因此 JDK/SDK/AGP/工程配置均已越过初始化阶段；失败发生在运行时依赖下载，不是当前 Android 源码编译报错。
- Gradle 9.4.1 在汇报该解析失败时触发 `ModuleVersionResolveException.getMessage()` 空指针，遮蔽了根因；以 `--info` 单独重跑后确认唯一失败项为 `androidx.activity:activity:1.13.0` AAR 的 TLS EOF，同轮其他大量 Google Maven 依赖已成功。
- 仓库 `gradle.properties` 默认启用 `org.gradle.parallel=true`。当前不修改仓库配置，采用命令行 `--no-parallel --max-workers=1` 串行完成首次缓存，以降低本机代理并发握手压力。
- 串行重跑资源任务后 `BUILD SUCCESSFUL in 2s`；随后正式 `:app:assembleDebug` 在 7 分 22 秒内完成 36 个任务，Kotlin 编译、资源/Manifest、DEX、Debug 签名和 APK 打包均通过。
- 最终按 `verification-before-completion` 做了更强的离线洁净复编译：`clean :app:assembleDebug --offline --no-parallel --max-workers=1`，37 个任务、exit 0，说明原工程可由当前本地 SDK/JDK 与已缓存依赖重复构建。
- 生成 APK 为 22 MiB，SHA-256 `f31bbab68c01ae94ae0a9e7e00d0bf083c1ff3447934aa2377af8adb1ff72966`；`aapt2` 确认包名 `com.example.jetsnack`、min SDK 23、compile/target SDK 36，`apksigner` 确认 v1/v2 Debug 签名通过。
- 嵌套仓工作树仍为干净的 `competition`，HEAD 精确等于指定 commit；远端只有上游分支，没有远端 `competition`，符合“本地分支、不 push”的边界。
- 已新增 `docs/本地基线部署与交付边界.md`：明确当前 Android APK 只是基线验证产物；未来直接在仓库根 `work/` 重构完整鸿蒙仓，根 `INSTRUCTION.md` 在解题交付阶段创建，最终通过 ZIP 交付。
- 目录上移后，旧 Gradle Daemon 一度按历史工程路径创建了 0 字节空 `.gradle/` 目录壳；停止旧 Daemon 并删除空壳后，新 Daemon 从 `work/` 离线 `assembleDebug` 成功，且未再创建旧包装层。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 使用文件路径和原文位置作为关键结论证据 | 便于后续实施阶段快速回查 |
| 将本题定位为“迁移 Agent/Skill + 可编译鸿蒙仓”双层交付 | 同时满足自动化迁移核心与题目特定结果要求 |
| 先建立确定性迁移/验收主链，平台模型做分析与修复增强 | 五次稳定性、无 API 强假设和性能评分共同要求 |
| `work/` 直接作为独立 Git 仓根并保留 `competition` 分支 | 避免最终 ZIP 多包一层，同时精确追溯上游 commit 和后续迁移差异 |
| 原安卓构建优先使用本机 JDK + Android command-line SDK | 与 Gradle Wrapper 最直接，Apple Silicon 上比 Docker Android SDK 更轻且更便于迭代 |
| 使用 JDK 21 运行 Gradle，项目源码仍编译到 Java 17 target | 仓内 `gradle-daemon-jvm.properties` 指定 21，`app/build.gradle.kts` 指定 target 17 |
| 不把 JDK 21 写入全局 PATH | 显式 `JAVA_HOME` 可避免影响用户已有 JDK 25，同时保证 Gradle 使用目标版本 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 首次全量 `rg --files --hidden` 将参考仓库 `.git/objects` 也列出并导致输出截断 | 后续所有清单显式排除 `.git/**`，按目录和文件类型精准读取 |
| 一次计划文件补丁因上下文定位顺序不匹配而失败 | 确认补丁未产生部分写入，改用更小的定点补丁 |
| 综合记录组合补丁再次因跨文件/逆序定位失败 | 按文件和文档顺序拆分补丁，避免回跳 |
| GitHub 网页工具未能读取目标仓 | clone 后以指定 commit 内文件为唯一环境版本依据 |
| clone 中途检查显示无 HEAD | 实际 clone 仍在后台运行；轮询对应 exec session 至 exit 0 后复查成功，无需删除或重下 |
| Homebrew 状态检查无法更新用户缓存 | 对安装/状态命令使用获准外部执行，不绕过系统缓存目录权限 |
| Gradle Wrapper 沙箱内无法创建 `~/.gradle` lock | 使用获准执行写标准 Gradle 缓存；Wrapper 与 JDK 验证成功 |
| `assembleDebug` 下载 Google Maven 依赖时 TLS handshake 中断 | 确认为环境代理未传入 JVM；用一次性 Java proxy system properties 重试 |
| 代理参数重试命令被外部执行额度拒绝 | 不绕过；等待额度恢复后原样重跑，或由用户在本机终端执行同一命令 |

## Resources
- 当前项目：`/Users/ctgg/master/code/learn/01_android_to_harmoneyOS`
- 参考项目：`/Users/ctgg/master/code/learn/ICT_software`

## Visual/Browser Findings
- 本轮暂未查看图片、PDF 或网页。
