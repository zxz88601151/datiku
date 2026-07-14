# 智学系统 SmartStudyOS

SmartStudyOS 是一套面向学习场景的智能操作系统，覆盖学习流程管理、学情采集与可视化分析。后端以 Python 组织多模块业务，前端提供学习流交互界面，旨在将分散的学习行为数据沉淀为可度量的学习画像。

## 功能特性

- 学习流程编排与状态管理（learning_flow）
- 学情数据采集、统计与可视化看板
- 模块化业务组件，便于二次扩展
- 统一参数校验、全局异常处理与日志脱敏

## 技术栈

Python 3.x；UI 层基于 Qt/PySide；数据分析依赖 pandas / numpy 等成熟库；工程包含 SmartStudyOS 主模块。

## 目录结构

```
datiku/
├── .gitignore
├── .workbuddy/
├── BUILD.md
├── CHANGELOG.md
├── LICENSE
├── SmartStudyOS/
```

## 安装与运行

详见仓库根目录 `BUILD.md`（含依赖版本、虚拟环境、启动与打包方式）。

通用步骤：

```bash
# 进入项目目录后，按 BUILD.md 配置依赖并运行
```

## 合规说明

本项目已按统一合规基线完成改造：可见版权头、LICENSE、全局异常与日志脱敏、安全模式审计。详情见 `CHANGELOG.md`。

## 版权与许可

© 中哥  All Rights Reserved

- 本仓库代码仅限项目内部使用，未经授权禁止转载、二次分发或商用。
- 开源许可与版权归属详见仓库根目录 `LICENSE`。
- 合规改造说明见 `CHANGELOG.md`，构建与运行说明见 `BUILD.md`。
