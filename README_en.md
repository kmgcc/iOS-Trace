# iOS-Trace

[English](README_en.md) | [中文](README.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Install](https://img.shields.io/badge/Install-npx_skills_add-000000.svg)](https://skills.sh/kmgcc/iOS-Trace)
[![Platform](https://img.shields.io/badge/Platform-iOS_15%2B_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Looking for macOS desktop app profiling? See [macOS-Trace](https://github.com/kmgcc/macOS-Trace).

An autonomous, closed-loop performance optimization engine for **iOS / iPadOS apps** built on `xctrace` and Xcode Instruments. Lets AI coding agents (Claude Code, OpenAI Codex, Cursor, Google Antigravity, GitHub Copilot) work without touching the Instruments GUI: goal alignment → headless diagnostic traces → bottleneck isolation → targeted code fixes → differential re-testing → automatic iteration until targets are met.

---

## Prerequisites

- **Host**: macOS 12+, full Xcode or Xcode Command Line Tools (`xcrun xctrace version`).
- **Target**: iOS/iPadOS app on a physical device or simulator. Devices must be unlocked, trusted by the Mac, and listed under `== Devices ==`; debug/development signing (`get-task-allow`) is required for `--attach`.
- **Python**: 3.8+ (standard library only, zero third-party dependencies).

---

## Installation

### Recommended: one command (skills CLI matches each agent's directory)

```bash
npx skills add kmgcc/iOS-Trace
```

Add `-g` for global (all projects), or `-a claude-code -g` to target a single agent.

### Manual installation (directory name must be `ios-trace`)

| Agent | Project scope | Global scope |
| :--- | :--- | :--- |
| Claude Code | `.claude/skills/ios-trace` | `~/.claude/skills/ios-trace` |
| OpenAI Codex | `.agents/skills/ios-trace` | `~/.codex/skills/ios-trace` |
| Cursor | `.agents/skills/ios-trace` | `~/.cursor/skills/ios-trace` |
| OpenCode | `.agents/skills/ios-trace` | `~/.config/opencode/skills/ios-trace` |
| Other agents | `.agents/skills/ios-trace` | `~/.agents/skills/ios-trace` |

```bash
git clone https://github.com/kmgcc/iOS-Trace.git ~/.claude/skills/ios-trace
```

---

## How to Invoke

After installation, the agent auto-triggers from the description's conditions, or you can ask directly: "use iOS-Trace to optimize X". Minimal run:

```bash
SKILL_DIR="$HOME/.claude/skills/ios-trace"
"$SKILL_DIR/scripts/run_trace.sh" --bundle-id "com.example.MyApp" --template power --duration 60s --label "01-baseline"
python3 "$SKILL_DIR/scripts/compare_elements.py" /tmp/ios-traces/01-baseline-power.xml:"Idle" /tmp/ios-traces/02-active-power.xml:"Active"
```

---

## Documentation Map (load on demand)

- **`SKILL.md`** — Core behavior: goal alignment, agent rules, the 4-phase loop.
- **`references/templates.md`** — Instruments template picker (which template for which bottleneck).
- **`references/subsystems.md`** — Per-subsystem optimization patterns (radio / ProMotion / media decoding / audio).
- **`references/workload-reproduction.md`** — How to reproduce the workload (Tier 0–3, including simulator boundaries).
- **`references/device-commands.md`** — Exact `devicectl`/`xctrace` device commands, iOS-version template limits, process matching, and script-copy rules.

---

## Limitations & Notes

- **Energy / thermal / CPU Impact metrics (Power Profiler) are unsupported on the simulator** — a physical device is required.
- **Power Profiler requires iOS 26+**; on older devices use the Time Profiler (hot call-trees) + Activity Monitor (per-process CPU ms/s) pair — see `references/device-commands.md`.
- **Simulator xctrace recording can be unstable**; for batch multi-run traces, a device is more reliable.
- Simulator results do not represent device power / thermal / GPU behavior; use it for CPU-hotspot and logic triage only.
- Processes targeted with `--attach` must be debug/development-signed builds.
- For "AI operating the phone to reproduce a scenario", see `references/workload-reproduction.md`.

---

## License

MIT License. See [LICENSE](LICENSE).
