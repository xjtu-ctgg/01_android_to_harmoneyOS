# 自验证结果

## 作品

- 赛题：02_01 Android 到鸿蒙移植
- Android 基线提交：`23e1421b72b602d80486777efbf24dd248abf3bb`
- 最终鸿蒙代码仓：`work/`
- 工程类型：HarmonyOS Stage、ArkTS/ArkUI、Entry HAP
- Bundle 名：`com.example.jetsnack`

## 执行方式

从作品根目录执行：

```bash
cd work
sh tools/verify.sh --build
```

## 最近一次自验证结果

| 检查项 | 结果 |
| --- | --- |
| Android 固定基线与迁移映射校验 | 通过；6 个页面、6 条路由、10 个动作、28 个商品、34 项映射 |
| 仓内合同测试 | 通过；265/265 |
| ArkTS/API 20 兼容构建 | 通过；`BUILD SUCCESSFUL` |
| HAP 产物 | 通过；`entry/build/default/outputs/default/entry-default-unsigned.hap` 非空 |
| 五个独立 Executor 本地复现代理 | 通过；5/5 均为 265/265，源码树一致，输入包只读；完整 HAP 构建见统一验证结果 |
| 交付结构检查 | 通过；必选文件与目录齐全，压缩包无缓存、构建产物和符号链接 |

最近一次主验证输出末尾为：

```text
BUILD SUCCESSFUL
stage=completed
status=passed
mode=build
build_scope=public_api_compatibility
hap=entry/build/default/outputs/default/entry-default-unsigned.hap
```

## 环境边界

本地已完成公共 API 20 兼容编译和仓内规范门禁。官方 HarmonyOS Code Linter 后端、真实 HarmonyOS 设备截图及平台隐藏用例由评分环境执行；本文件不将本地代理结果表述为隐藏用例成绩。
