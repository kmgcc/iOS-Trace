# iOS-Trace

[English](README_en.md) | [中文](README.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Install](https://img.shields.io/badge/Install-npx_skills_add-000000.svg)](https://skills.sh/kmgcc/iOS-Trace)
[![Platform](https://img.shields.io/badge/Platform-iOS_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Need profiling for macOS desktop apps? See [macOS-Trace](https://github.com/kmgcc/macOS-Trace).

An agent-native runbook for profiling iOS and iPadOS apps. Choose instruments, workload reproduction, and success evidence based on the actual symptom and target device. Physical devices and simulators have different measurement boundaries. Bundled scripts are optional data-processing helpers, not a required workflow.

## Prerequisites

- A usable Xcode or Command Line Tools installation on macOS. Target support depends on Xcode and device OS. Xcode 27 requires macOS Tahoe 26.6 or later and runs only on Apple silicon.
- A physical device must be online, unlocked, and trusted by the Mac. Attach and UI testing also depend on signing, Developer Mode, and OS support.
- Python 3.8+ only when using optional helper scripts.

## Installation

### Recommended: skills CLI

```bash
npx skills add kmgcc/iOS-Trace
```

Use `-g` for a user-level installation, or `-a` to select an agent supported by the CLI.

### Manual installation

| Agent | User-level global directory |
| :--- | :--- |
| Codex | `~/.agents/skills/ios-trace` |
| Antigravity | `~/.gemini/config/skills/ios-trace` |
| DSH | `~/.dsh/skills/ios-trace` |
| Claude Code | `~/.claude/skills/ios-trace` |
| Cursor | `~/.cursor/skills/ios-trace` |
| OpenCode | `~/.config/opencode/skills/ios-trace` |

Copy the repository contents into the selected directory. Discovery paths can change by agent version; follow the agent's current documentation for project-level installation.

## Use

Ask the agent to use `ios-trace` for a concrete scenario, such as device scrolling hitches, overheating, slow launch, audio dropouts, or memory growth. It will choose a target, profiler, reproduction path, and comparison based on the question; no fixed script sequence is required.

## Documentation map

- `SKILL.md` — core runbook.
- `references/templates.md` — Instruments selection guide and Xcode 27 additions.
- `references/workload-reproduction.md` — choosing a physical-device or simulator path for the question.
- `references/device-commands.md` — device discovery, process verification, xctrace discovery, capture, and export.
- `references/xcode-agent-mcp.md` — optional Xcode MCP workflow and permission boundaries.
- `references/subsystems.md` — radio, ProMotion, media decoding, audio, and other optimization leads.

## Boundaries

- Simulator results can help with some CPU, logic, and UI investigations; they cannot establish physical-device power, radio, or thermal behavior.
- Traces may contain prompts, paths, media metadata, or logs; treat them as sensitive task data.
- MCP is an optional Xcode project/development integration. Runtime performance evidence comes from Instruments.
- Follow project rules for processes, devices, data ownership, builds, tests, and release workflows.

## License

MIT License. See [LICENSE](LICENSE).
