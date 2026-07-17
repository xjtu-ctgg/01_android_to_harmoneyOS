# 实现与验证轨迹

## 1. 输入与目标

| 项目 | 固定内容 |
| --- | --- |
| Android 来源 | `fuxi-artifacts/demo-Jetsnack-android` |
| 固定提交 | `23e1421b72b602d80486777efbf24dd248abf3bb` |
| 目标 | 原生 HarmonyOS Stage / ArkTS / ArkUI Entry HAP |
| 交付仓 | `work/` |
| 主入口 | 根 `INSTRUCTION.md`；平台就绪检查为 `sh work/tools/platform_ready.sh` |

## 2. 工程产物清单

- `work/entry/src/main/ets/`：页面、状态、公共组件、Ability 和 Form Kit 实现。
- `work/entry/src/main/resources/`：颜色、字符串、尺寸、字体、图片、向量和深色资源。
- `work/source-facts/`：指定 Android 提交的离线事实、源码快照、公开测试契约和资源证据。
- `work/migration-manifest.json`：34 项源到目标映射，页面、路由、动作、资源、状态、主题和数据均标记为 `implemented`。
- `work/migration-report.md`：按评测维度索引源码证据，降低评委和评分 Agent 的定位成本。
- `work/journeys/core.yaml`：228 条可机读行为、视觉、接口、边界和配置 Journey。
- `work/skills/android-to-harmonyos/`：自动迁移方法、质量规则、参考资料和 Agent 元数据。
- `work/tools/`：合同检查、静态规则、设备证据、PNG 比较、构建预检和平台就绪门禁。

## 3. 本地可复核门禁

在仓库有 Python 3 和相应 HarmonyOS 工具链时，可从 `work/` 目录执行：

```bash
sh tools/verify.sh --static
sh tools/verify.sh --build
```

最近一次可执行静态门禁结果：

```text
Ran 272 tests in 38.315s
OK
stage=completed
status=passed
mode=static
```

工程构建命令要求 API 20 SDK、Hvigor、Node.js/JDK；成功判定同时检查退出码、`BUILD SUCCESSFUL`、`status=passed` 和非空 Entry HAP。官方 Code Linter 后端、真实设备和签名环境不可用时，记录为待评分环境验证，不用替代脚本伪造结果。

## 4. 覆盖矩阵

| 维度 | 已交付证据 | 代表性检查 |
| --- | --- | --- |
| 功能 | `AppStore.ets`、六个页面、`core.yaml`、事实快照 | 搜索四态、购物车数量/失败/删除、详情展开、Filter 生命周期、Tab/返回/深链 |
| 截图 | 资源快照、主题资源、尺寸合同、视觉 Journey | 明暗主题、字体比例、窄屏/平板、横屏挖孔、系统安全区、Hero/BottomNav/Filter 几何 |
| 接口 | 稳定 ID、无障碍属性、Form Kit、清单和路由配置 | Button/selected 角色、动态 ID 唯一性、冷暖深链、Widget 尺寸和跳转 |
| 规范 | ArkTS 规则扫描、迁移映射合同、路径/凭据/缓存审计 | `any`、空事件、经典循环、非严格比较、绝对路径、符号链接和构建污染 |

## 5. 平台稳定性专项

上一轮平台日志出现“准确性完整、稳定性交集为零”。本轮将评分主路径改为：

```text
作品根目录
  → sh work/tools/platform_ready.sh
  → 固定输出 artifact_status=ready / artifact_path=work
  → 平台自带鸿蒙评分 Skill 读取同一份 work/
```

就绪脚本只读检查以下必要证据：Stage 配置、Entry 页面、迁移报告、迁移清单、Android 事实、Journey 和迁移 Skill。它不会修改交付仓，也不会触发重新生成、联网安装或构建缓存。

独立解压副本验证内容：

- 每个副本均以同名作品目录解压；
- 将仓库标记为只读后执行就绪脚本；
- 输出文本完全一致，且固定使用相对路径 `work`；
- 归档不含 `.git`、`.gradle`、`.hvigor`、构建产物、Node/ohpm 缓存、Python 缓存、HAP、pyc 或符号链接。

该验证能证明交付协议和源码输入是确定性的；隐藏用例最终通过数仍以平台评分为准。

## 6. 归档结果

- 归档文件：`02_01_纯人机，已开智.zip`
- 解压根目录：`02_01_纯人机，已开智/`
- 必选路径：`INSTRUCTION.md`、`work/`、`result/output.md`、`logs/interaction.md`、`logs/trace/`
- ZIP 条目数：328
- 归档审计：UTF-8 文件名、必选路径、禁止项、符号链接和 `unzip -t` 均通过
- 当前包文件指纹由最终打包命令输出；指纹不是平台评分参数。

## 7. 未冒充的验证项

以下项目有实现和执行入口，但当前机器没有足够条件给出官方通过结论：

1. HarmonyOS 专有 SDK 下的正式签名构建；
2. 官方 Code Linter 后端的完整规则报告；
3. 真机/模拟器上的 arkXtest 组件树和原始截图；
4. 评分平台提供的非公开用例及最终准确性/稳定性统计。

日志将上述项目标记为评分环境门禁，避免把公共 API 交叉构建、静态代理或本地截图工具的结果夸大为官方成绩。
