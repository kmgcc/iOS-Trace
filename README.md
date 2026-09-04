# iOS-Trace

[English](README.md) | [中文](README_zh.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Platform](https://img.shields.io/badge/Platform-iOS_15%2B_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![Python](https://img.shields.io/badge/Python-3.8%2B_(Zero_Deps)-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Looking for macOS desktop application profiling? See [macOS-Trace](https://github.com/kmgcc/macOS-Trace).

Autonomous, closed-loop application performance optimization engine for **iOS and iPadOS applications** running on physical iPhone/iPad devices and iOS Simulators using `xctrace` and Xcode Instruments.

Designed for AI coding agents (Claude Code, OpenAI Codex, Cursor, Google Antigravity, GitHub Copilot) and iOS engineers. It completely eliminates manual Instruments GUI interaction. From a single prompt, an agent can align on optimization goals with the user, capture headless diagnostic traces, implement targeted code fixes, and re-test with differential benchmarking across multiple iterations until the user's requirements are met.

---

## The Autonomous Optimization Loop

```text
+-------------------------------------------------------------------------+
|                  The Autonomous Optimization Loop                        |
|                                                                         |
|  1. Goal Alignment ──> 2. Diagnostic Trace ──> 3. Targeted Code Fix     |
|         ^                                                 │             |
|         │                                                 ▼             |
|         └────── Iterate if Target Not Met <── 4. Re-test Verification   |
+-------------------------------------------------------------------------+
```

1. **Goal Alignment**: The agent queries the user upfront (via interactive questionnaire modal if available, or direct chat) with concrete recommended thresholds.
2. **Diagnostic Profiling**: Headless trace capture under idle baseline and active workload on device/simulator to isolate hot call-frames, allocation spikes, and radio tails.
3. **Code Modification**: The agent implements surgical, source-level optimizations directly in the codebase.
4. **Re-Test Verification**: Automated re-profiling under identical conditions to compute empirical Before vs After deltas.
5. **Iteration Gate**: If the user's targets are met, deliver the final report; if not, initiate the next optimization round automatically.

---

## Upfront Goal Alignment (Pre-Flight Questionnaire)

Before making changes or running traces, agents should align on targets with the user:

- **Interactive Modal / Components**: If the agent platform provides an interactive modal or prompt tool (e.g. `ask_question`), invoke it to present selectable options. Otherwise, ask directly in conversation.
- **Recommended Threshold Presets**:
  - **Battery & CPU**:
    - *Idle Baseline Target*: < 15 M/s instructions, CPU Impact < 0.3.
    - *Active Workload Target*: < 80 M/s instructions (or reduce current CPU by 30% - 50%).
  - **Memory & Jetsam Ceilings**:
    - *Maximum Resident RAM*: Cap at < 150 MB (standard utilities) or < 300 MB (rich media apps).
    - *Allocation Rate*: < 400 events/sec during steady-state execution.
    - *Leaks*: 0 persistent leaks.
  - **UI Smoothness & Hitches**:
    - *Hitch Ratio*: < 5.0 ms/s (acceptable), < 1.0 ms/s (fluid / 120Hz ProMotion grade).
  - **Cold Launch Time**:
    - *Time to First Frame*: < 400 ms (excellent), < 800 ms (acceptable).
  - **Network & Radio Efficiency**:
    - *Radio Standby Overhead*: Batch periodic pings into single burst requests to avoid cellular/WiFi radio tails.

---

## Prerequisites and Scope

Read these requirements and constraints before deploying or invoking this skill:

### Supported Targets
- **iOS & iPadOS Devices Only**: Designed specifically for applications running on physical iPhone/iPad hardware connected via USB or local network, as well as local iOS Simulators.
- **Looking for macOS desktop software?**: Use [macOS-Trace](https://github.com/kmgcc/macOS-Trace).

### Host System and Tooling
- **Host System**: macOS 12.0 (Monterey) or later with full Xcode or Xcode Command Line Tools (`xcrun xctrace`).
- **Device Connection**:
  - The physical iPhone or iPad must be unlocked and trusted by the host Mac.
  - The device must appear under `== Devices ==` when running `xcrun xctrace list devices` (not under `== Devices Offline ==`).
  - Auto-Lock should be set to "Never" or kept awake during recordings to prevent iOS from suspending background processes.
- **Python**: Python 3.8+ on the host Mac (uses standard library only; zero external pip dependencies).
- **Process Entitlements**: Debug builds or developer-signed builds with `com.apple.security.get-task-allow` entitlement are required for process attaching (`--attach <PID>`).

---

## Agent Installation and Integration Guide

This section outlines how an AI coding agent should install, locate, and execute `iOS-Trace` within an automated repository workflow.

### 1. Skill Location Detection

When an agent needs to install this skill into an iOS repository, it should detect the existing skill directory convention:

```bash
# Order of preference for agent skill directories:
# 1. Standard Agent Skills: .agents/skills/
# 2. OpenAI Codex:          .codex/skills/
# 3. Cursor:                 .cursor/skills/
# 4. Claude Code:            .claude/skills/
```

If none exists, default to `.agents/skills/`.

### 2. Installation Commands for Agents

```bash
# Option A: Standard Agent Skills directory (Recommended)
mkdir -p .agents/skills
git clone https://github.com/kmgcc/iOS-Trace.git .agents/skills/ios-trace

# Option B: As a Git Submodule
git submodule add https://github.com/kmgcc/iOS-Trace.git .agents/skills/ios-trace

# Option C: OpenAI Codex specific directory
mkdir -p .codex/skills
git clone https://github.com/kmgcc/iOS-Trace.git .codex/skills/ios-trace

# Option D: User-level global installation
mkdir -p ~/.agents/skills
git clone https://github.com/kmgcc/iOS-Trace.git ~/.agents/skills/ios-trace
```

### 3. Complete Optimization Run Example

```bash
SKILL_DIR=".agents/skills/ios-trace"

# 1. Find device UDID
DEVICE_UDID=$(xcrun xctrace list devices 2>&1 | awk '/== Devices ==/{flag=1; next} /== Devices Offline ==/{flag=0} flag && !/Mac/ && NF {print; exit}' | sed -E 's/.*\(([A-Fa-f0-9-]+)\).*/\1/')

# 2. Record 60s idle baseline (device unlocked, app foregrounded)
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --bundle-id "com.example.MyApp" --template power --duration 60s --label "01-baseline"

# 3. Trigger active workload in app, then record pre-opt active state
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --process "MyApp" --template power --duration 60s --label "02-pre-opt"

# 4. Implement code fixes, rebuild and deploy to device, then record post-opt active state
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --process "MyApp" --template power --duration 60s --label "03-post-opt"

# 5. Compare Pre-Opt vs Post-Opt against Baseline
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"Idle Baseline" \
  /tmp/ios-traces/02-pre-opt-power.xml:"Active Pre-Opt" \
  /tmp/ios-traces/03-post-opt-power.xml:"Active Post-Opt"
```

---

## Quick Start Example

Running the comparison produces an empirical differential report:

```text
Scenario                 Sec  CPU Avg  CPU Max  Display  GPU Avg  Total Instr    Instr M/s   WiFi Tx/Rx
=========================================================================================================
1. Idle Baseline          60     0.12     0.60     0.05     0.00        0.85G         14.2   0.0/0.0MB
2. Active Workload        60     2.40     4.80     1.10     1.80       15.60G        260.0  14.2/1.8MB
---------------------------------------------------------------------------------------------------------
Differential vs Baseline [1. Idle Baseline]:
  2. Active Workload        +245.8 M/s instructions, CPU Avg Delta +2.28, WiFi Tx Delta +14.20MB
```

---

## Included Tooling

All scripts require Python 3.8+ and use the standard library only (`re`, `sys`, `os`, `xml.etree.ElementTree`, `collections`).

| Script | Function | Usage |
| :--- | :--- | :--- |
| `scripts/run_trace.sh` | CLI runner: device discovery, record, export, and parse | `./scripts/run_trace.sh --bundle-id com.example.MyApp --template power` |
| `scripts/compare_elements.py` | Multi-run comparison table with CPU, GPU, and WiFi/Cellular delta | `python3 scripts/compare_elements.py base.xml active.xml` |
| `scripts/parse_power.py` | Single-run breakdown of CPU, GPU, Display, and Network throughput | `python3 scripts/parse_power.py run-power.xml "Workload"` |
| `scripts/top_categories.py` | Allocations ranking by event rate, transient, and persistent bytes | `python3 scripts/top_categories.py alloc.xml 60 10.0` |

---

## Instruments Templates

| Template | Shorthand | Target Metrics & Primary Use Case |
| :--- | :--- | :--- |
| `Power Profiler` | `power` | Instructions/sec (M/s), CPU/GPU/Display/WiFi/Cellular energy impacts (`ProcessSubsystemPowerImpact`). Comprehensive battery drain and A/B testing. |
| `Time Profiler` | `time` | Thread CPU weights, call stack hotspots, main-thread blocking methods. |
| `Animation Hitches` | `hitches` | ProMotion 120Hz scrolling stutter, hitch duration (ms), frame drop ratios. |
| `SwiftUI` | `swiftui` | View body evaluations, State invalidation counts, view update frequency. |
| `Allocations` | `alloc` | Heap allocation rates, transient memory spikes, category event rates (`all-allocations-summary`). |
| `Leaks` | `leaks` | Retained memory leaks outliving parent lifecycle, retain cycles. |
| `Network` | `network` | TCP/UDP connections, DNS latency, packets sent/received, radio state overhead. |
| `App Launch` | `launch` | Time to first frame, `dyld` loading time, static initializers, runloop setup. |
| `Metal System Trace` | `metal` | GPU encoder time, vertex/fragment shader durations, frame latency. |

---

## Subsystem Optimization Notes

Detailed implementation guidance is provided in [SKILL.md](SKILL.md):

1. **Battery & Radio Energy**: Batching periodic network requests to avoid cellular/WiFi radio tails; minimizing wake-locks and background audio/location tasks.
2. **ProMotion 120Hz Displays**: Honoring the 8.33ms frame budget; isolating Commit Hitches (main-thread layout delays) from Render Hitches (GPU compositing bottlenecks).
3. **Image Downsampling & Jetsam Ceilings**: Preventing high-resolution raw bitmaps from exhausting the strict mobile memory ceiling using `CGImageSourceCreateThumbnailAtIndex`.
4. **Real-Time Audio Session**: Zero heap allocations in CoreAudio/AVAudioEngine render callbacks; managing audio interruptions and background transitions.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
