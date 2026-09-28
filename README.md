# iOS-Trace

[中文](README.md) | [English](README_en.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Install](https://img.shields.io/badge/Install-npx_skills_add-000000.svg)](https://skills.sh/kmgcc/iOS-Trace)
[![Platform](https://img.shields.io/badge/Platform-iOS_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 需要 macOS 桌面应用性能分析？见 [macOS-Trace](https://github.com/kmgcc/macOS-Trace)。

面向 AI 编码 Agent 的 iOS / iPadOS 性能分析 runbook。Agent 根据真实症状和目标设备选择 Instruments、复现路径与验收证据；真机与模拟器各有不同测量边界。附带脚本仅是可选的数据处理工具，不是固定执行流程。

## 前置条件

- macOS 上可用的 Xcode 或 Command Line Tools；目标支持范围由当前 Xcode 与设备 OS 决定。Xcode 27 要求 macOS Tahoe 26.6 或更新版本，并仅支持 Apple silicon Mac。
- 真机需在线、解锁并信任此 Mac；真机 attach 和 UI 测试还受签名、Developer Mode 与系统版本影响。
- Python 3.8+ 仅用于可选脚本。

## 安装

### 推荐：skills CLI

```bash
npx skills add kmgcc/iOS-Trace
```

使用 `-g` 安装到用户级目录；可用 `-a` 选择 CLI 支持的 Agent。

### 手动安装

| Agent | 用户级全局目录 |
| :--- | :--- |
| Codex | `~/.agents/skills/ios-trace` |
| Antigravity | `~/.gemini/config/skills/ios-trace` |
| DSH | `~/.dsh/skills/ios-trace` |
| Claude Code | `~/.claude/skills/ios-trace` |
| Cursor | `~/.cursor/skills/ios-trace` |
| OpenCode | `~/.config/opencode/skills/ios-trace` |

把仓库内容放入对应目录即可。具体发现路径可能随 Agent 版本变化；项目级安装请遵循该 Agent 当前文档。

## 使用

要求 Agent 使用 `ios-trace` 调查明确的用户场景，例如真机滚动掉帧、发热、启动变慢、音频断续或内存增长。Agent 会按目标选择设备、采样器、复现方式和对比方法；不需要先运行固定脚本。

## 文档地图

- `SKILL.md` — 核心执行 runbook。
- `references/templates.md` — Instruments 选择指南与 Xcode 27 增强项。
- `references/workload-reproduction.md` — 按问题选择真机或模拟器的复现路径。
- `references/device-commands.md` — 设备发现、进程确认、xctrace 能力发现、记录与导出。
- `references/storage-and-recovery.md` — Mac 主机临时空间、已删除但仍打开的 `.ktrace` 诊断与安全恢复。
- `references/xcode-agent-mcp.md` — 可选 Xcode MCP 工作流及权限边界。
- `references/subsystems.md` — 射频、ProMotion、媒体解码、音频等优化线索。

## 使用边界

- 模拟器结果适合部分 CPU、逻辑和 UI 排查，不能证明真机功耗、射频或热表现。
- trace 可能包含提示词、路径、媒体或日志信息，按敏感任务数据处理。
- MCP 是可选的 Xcode 项目/开发集成；运行时性能证据来自 Instruments。
- 遵循项目自身的进程、设备、数据所有权、构建、测试和发布规则。

## License

MIT License。见 [LICENSE](LICENSE)。
