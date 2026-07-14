# 参赛作品提交规范
## 1. 提交内容
参赛作品统一提交至 **work/** 目录，目录结构不限。

作品形式不限，包括但不限于：
```markdown
CLI 工具
Agent
Skill
MCP Server
Web 服务
Extension
Docker 应用
其他自动化工具
```
本赛题中，参赛作品需要实现的是：迁移安卓代码到鸿蒙代码。

## 2. 平台提供的材料
评测平台会提供 xxx 项目材料，参赛选手不需要提交这些内容。
平台提供路径如下：
```markdown
/app/code/judge-assets/02_01_android_to_harmoneyOS
├── xxx/        # xxx
└── README.md          # 比赛说明、REST API 契约、黑盒用例说明
```

## 3. 必须包含文件
参赛作品根目录至少包含以下内容：
```markdown
├── INSTRUCTION.md
work/
└── ...
└── ...
```
​其中：
**INSTRUCTION.md**：裁判执行说明书，用于指导自动评测系统部署、启动、执行参赛作品并获取修复结果。

## 4. INSTRUCTION.md 编写要求
自动评测系统将依据 INSTRUCTION.md 执行参赛作品。
INSTRUCTION.md 至少应包含以下内容：

### 4.1 环境准备
说明参赛作品运行所需的环境准备步骤，包括但不限于：
```markdown
依赖安装
编译构建
服务启动
Docker 环境准备
MCP、Skill、Agent 等组件安装
```
所有步骤应能够自动完成，不得依赖人工操作。

### 4.2 执行方式
说明如何执行参赛作品，包括但不限于：
```markdown
启动命令
执行命令
参数说明
调用方式
执行顺序
```

### 4.3 执行完成判定
说明如何判断参赛作品执行完成，例如：
```markdown
命令退出
服务返回完成状态
指定文件生成
指定接口返回成功
```

### 4.4 生成结果交付件
说明自动评测系统如何获取最终修复结果：
```markdown
一个完整的鸿蒙代码仓，并给定代码仓位置
```

## 5. 自动评测流程
自动评测系统将按照以下流程执行：
* 阅读 INSTRUCTION.md
* 按照说明完成环境准备
* 等待鸿蒙代码仓生成
* 生成完毕后调度鸿蒙打分 skill 打分。

## 6. 注意事项
以下情况将导致作品无法完成自动评测：
```markdown
缺少 INSTRUCTION.md
INSTRUCTION.md 无法指导自动执行
执行过程需要人工交互
无法判断执行完成
无法生成鸿蒙代码仓
为给定代码仓位置
```
注意，包含 Skill 则路径必须符合 **work/skills/{your-skill-name}/SKILL.md** 规范