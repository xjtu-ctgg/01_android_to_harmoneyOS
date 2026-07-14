> 注：平台整理了一个建议的INSTUCTION.md格式，大家可以参考，可以有效降低token消耗、加快打分进度，生成有效成绩。但重点还是要以有效执行、通过打分平台的测试用例为主要目标

# INSTRUCTION.md 模板说明

## 核心原则

INSTRUCTION.md 是选手提交作品时附带的**使用指导**，告诉使用方：

1. **输入是什么**——启动本作品需要什么前置条件、什么输入数据（概念描述，不绑定平台实现）
2. **执行工作流**——怎么启动、流程步骤、每步做什么
3. **产物是什么**——每步产出放在哪、是什么格式、有什么用途

**不包括**：

- 验证方式和评分规则——那是 SKILL.md 的职责
- 平台实现细节

> 输入和产物用**概念描述**（如"待修复的代码目录"），不用平台路径。Scorer 运行时自行将概念映射到实际路径。这样平台变更后，选手作品无需跟随修改。

## 模板结构

每个 INSTRUCTION.md 必须包含以下章节：

### 1. 作品概述

简要说明作品做了什么。

### 2. 输入

启动本作品需要的前置条件和输入数据，用概念描述，不绑定平台路径：

| 输入项   | 说明     |
| -------- | -------- |
| 概念名称 | 用途说明 |

### 3. 执行工作流

逐步描述启动和运行流程，每步包括：

- 做什么（命令或操作）
- 预期输出（成功标志）
- 本步产物及位置

对于无需编译运行的作品（纯文本分析结果），直接说明"无需执行，读取交付件即可"。

### 4. 产物清单

列出所有输出产物，位置用相对于 INSTRUCTION.md 的相对路径：

| 产物     | 位置     | 格式     | 用途                  |
| -------- | -------- | -------- | --------------------- |
| 概念名称 | 相对路径 | 格式说明 | Scorer 如何使用此产物 |

------

## 样例：02_04 设计实现一致性

~~~markdown
# 设计实现一致性检查与修复 - 参赛作品说明

## 1. 作品概述

本作品对 ShopHub 电商项目的设计与实现不一致问题进行了修复。修复后的项目可通过 Maven 编译和黑盒测试验证。

## 2. 输入

| 输入项 | 说明 |
|--------|------|
| 修复后的项目代码 | 已修复的 Maven 项目，含 pom.xml |
| Maven 镜像配置 | 内网 Maven 仓库配置文件（评分资源提供） |

## 3. 执行工作流

### Step 1：编译项目

```bash
cd code/
mvn clean install -DskipTests -s <maven-settings.xml路径>

~~~

- 预期输出：包含 `BUILD SUCCESS`
- 产物：编译后的 class 文件在 `code/target/` 下

### Step 2：运行测试

```bash
cd code/
mvn test -s <maven-settings.xml路径>

```

- 预期输出：Surefire 报告在 `code/target/surefire-reports/` 下
- 产物：测试结果 XML

## 4. 产物清单

| 产物         | 位置                         | 格式           | 用途                          |
| ------------ | ---------------------------- | -------------- | ----------------------------- |
| 修复后的项目 | `code/`                      | Maven 项目目录 | Scorer 执行编译和测试的主目标 |
| 运行结果摘要 | `result/output.md`           | Markdown       | 修复结果和执行状态摘要        |
| 修复记录     | `logs/trace/fix-record.json` | JSON           | 具体修复的代码变更清单        |
| 推理日志     | `logs/trace/`                | 多文件         | AI 推理详细日志               |

```
---

## 样例：01_02 漏洞挖掘（执行类，无需编译）

```markdown
# 漏洞挖掘 - 参赛作品说明

## 1. 作品概述

本作品对 TensorFlow 项目进行了漏洞挖掘，识别了 6 个安全漏洞。

## 2. 输入

无外部输入。所有分析结果已写入交付件。

## 3. 执行工作流

无需编译或运行。漏洞分析结果已直接写入交付件，Scorer 读取文件即可。

## 4. 产物清单

| 产物 | 位置 | 格式 | 用途 |
|------|------|------|------|
| 漏洞列表 | `work/vulnerability_list.md` | Markdown | 主要评分文件，每项含漏洞类型/严重性/源码路径/成因/危害 |
| 漏洞报告 | `work/vulnerability_report.md` | Markdown | 完整漏洞分析报告 |
| LLM 交互记录 | `work/llm_chat_log.json` | JSON | 与 LLM 的对话记录，证明漏洞由 AI 辅助发现 |

```

------

## 样例：02_01 Android 到鸿蒙移植

```markdown
# Android 到鸿蒙移植 - 参赛作品说明

## 1. 作品概述

本作品将 jetsnack Android 应用移植到 HarmonyOS（ArkTS/ArkUI）。

## 2. 输入

| 输入项 | 说明 |
|--------|------|
| 鸿蒙代码仓 | 移植后的完整鸿蒙项目（.ets 源文件） |
| 意图用例文件 | 描述需验证的产品功能列表（评分资源提供） |

## 3. 执行工作流

无需编译或运行。Scorer 读取鸿蒙代码仓源文件，逐条判定意图用例中描述的功能是否实现。

## 4. 产物清单

| 产物 | 位置 | 格式 | 用途 |
|------|------|------|------|
| 鸿蒙项目 | `jetsnack_harmony/` | ArkTS 项目目录 | Scorer 逐文件读取，判定功能实现情况 |
| 移植说明 | `work/migration-report.md` | Markdown | 移植方案和功能对照表 |

```

------

## 样例：02_02 C-to-Rust 转换

```
# C-to-Rust 转换 - 参赛作品说明

## 1. 作品概述

本作品使用 C2Rust 工具将 FlashDB 的 C 代码转换为 Rust，并确保转换后的 Rust 项目通过原始 C 测试用例。

## 2. 输入

| 输入项 | 说明 |
|--------|------|
| Rust 项目 | c2rust 转换后的 Rust 项目（含 Cargo.toml） |
| 原始 C 项目 | 含 C 源码和测试用例（kvdb_main.c、tsdb_main.c） |

## 3. 执行工作流

### Step 1：编译 Rust 项目

```bash
cd flashDB_rust/
RUSTC_BOOTSTRAP=1 cargo build --release

```

- 预期产物：`flashDB_rust/target/release/librust.a`
- 成功标志：编译无错误，产物文件存在且非空

### Step 2：编译 C 测试并链接 Rust 静态库

```bash
cd FlashDB/tests/
gcc -c kvdb_main.c tsdb_main.c -I../src -o kvdb_main.o tsdb_main.o
gcc -o kvdb_test kvdb_main.o -L../../flashDB_rust/target/release -lrust -lpthread -ldl -lm
gcc -o tsdb_test tsdb_main.o -L../../flashDB_rust/target/release -lrust -lpthread -ldl -lm

```

- 预期产物：`kvdb_test`、`tsdb_test` 可执行文件
- 成功标志：链接无错误

### Step 3：运行测试

```bash
# 清理旧数据
rm -rf fdb_kvdb1/ fdb_tsdb1/ storage_*

# 执行测试
./kvdb_test
./tsdb_test

```

- 预期输出：每个测试用例打印通过/失败
- 成功标志：24 个测试用例全部通过

## 4. 产物清单

| 产物             | 位置                                    | 格式     | 用途               |
| ---------------- | --------------------------------------- | -------- | ------------------ |
| Rust 静态库      | `flashDB_rust/target/release/librust.a` | 静态库   | 供 C 测试链接      |
| C 测试可执行文件 | `FlashDB/tests/kvdb_test`、`tsdb_test`  | 二进制   | 执行测试用例       |
| 转换报告         | `work/conversion-report.md`             | Markdown | 转换方案和问题记录 |
