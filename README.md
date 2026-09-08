# iOS-Trace

[中文](README.md) | [English](README_en.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Install](https://img.shields.io/badge/Install-npx_skills_add-000000.svg)](https://skills.sh/kmgcc/iOS-Trace)
[![Platform](https://img.shields.io/badge/Platform-iOS_15%2B_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 需要 macOS 桌面应用性能分析？见 [macOS-Trace](https://github.com/kmgcc/macOS-Trace)。

基于 `xctrace` 与 Xcode Instruments 的 **iOS / iPadOS 自主闭环性能优化引擎**。让 AI 编码 Agent（Claude Code、OpenAI Codex、Cursor、Google Antigravity、GitHub Copilot）无需手动操作 Instruments GUI，即可完成：目标对齐 → 无头采样诊断 → 定位瓶颈 → 精准改码 → 复测量化 → 未达标自动迭代。

---

## 前置条件

- **宿主**：macOS 12+，完整 Xcode 或 Xcode 命令行工具（`xcrun xctrace version`）。
- **目标**：iOS/iPadOS App（真机或模拟器）。真机需解锁并信任此 Mac、出现在 `== Devices ==` 列表；调试/开发签名（`get-task-allow`）用于 `--attach`。
- **Python**：3.8+（仅标准库，零第三方依赖）。

---

## 安装

### 推荐：一条命令（skills CLI 自动匹配各 Agent 目录）

```bash
npx skills add kmgcc/iOS-Trace
```

加 `-g` 全局安装（所有项目可用），或 `-a claude-code -g` 指定单个 Agent。

### 手动安装（目录名必须为 `ios-trace`）

| Agent | 项目级 | 用户级全局 |
| :--- | :--- | :--- |
| Claude Code | `.claude/skills/ios-trace` | `~/.claude/skills/ios-trace` |
| OpenAI Codex | `.agents/skills/ios-trace` | `~/.codex/skills/ios-trace` |
| Cursor | `.agents/skills/ios-trace` | `~/.cursor/skills/ios-trace` |
| OpenCode | `.agents/skills/ios-trace` | `~/.config/opencode/skills/ios-trace` |
| 其他 Agent | `.agents/skills/ios-trace` | `~/.agents/skills/ios-trace` |

```bash
git clone https://github.com/kmgcc/iOS-Trace.git ~/.claude/skills/ios-trace
```

---

## 怎么调用

安装后，Agent 会根据 description 里的触发条件自动匹配，或直接要求"用 iOS-Trace 优化 XX"。核心运行示例：

```bash
SKILL_DIR="$HOME/.claude/skills/ios-trace"
"$SKILL_DIR/scripts/run_trace.sh" --bundle-id "com.example.MyApp" --template power --duration 60s --label "01-baseline"
python3 "$SKILL_DIR/scripts/compare_elements.py" /tmp/ios-traces/01-baseline-power.xml:"Idle" /tmp/ios-traces/02-active-power.xml:"Active"
```

---

## 文档地图（按需读取）

- **`SKILL.md`** — 核心行为指令：目标对齐、执行规则、4 阶段闭环协议。
- **`references/templates.md`** — Instruments 模板选择（哪种瓶颈用哪个模板）。
- **`references/subsystems.md`** — 各子系统调优知识（射频/ProMotion/图像/音频）。
- **`references/workload-reproduction.md`** — 负载如何复现（Tier 0–3，含模拟器边界）。

---

## 局限与注意点

- **能耗/发热/CPU Impact 指标（Power Profiler）模拟器不支持**，必须真机。
- **模拟器 xctrace 录制可能不稳定**，批量跑多轮 trace 用真机更可靠。
- 模拟器结果不能代表真机功耗/发热/GPU 行为；模拟器只适合 CPU 热点与逻辑问题的快速定位。
- 需要 `--attach` 的进程必须为 debug/开发签名构建。
- 本 Skill 是测量与调优闭环；若需"AI 自动操作手机复现场景"，见 `references/workload-reproduction.md`。

---

## License

MIT License。见 [LICENSE](LICENSE)。
