---
name: ios-trace
description: "Autonomous closed-loop performance optimization engine for iOS and iPadOS applications using xctrace and Xcode Instruments on physical devices and simulators. Handles the complete lifecycle: aligning optimization targets with the user, headless diagnostic trace capture, isolating bottlenecks, implementing code fixes, re-testing with differential A/B verification, and iterating until performance goals are met without manual GUI intervention. Use when the user reports battery drain or device overheating, high CPU usage, memory spikes or Jetsam OOM crashes, UI hitches or dropped frames (including ProMotion 120Hz stutter), slow cold launch, or excessive network radio overhead in an iOS/iPadOS app, and asks to profile, benchmark, or optimize it."
compatibility: "macOS 12+ host, iOS 15+ physical device or simulator, Xcode Command Line Tools, Python 3.8+"
license: MIT
metadata:
  author: kmgcc
  version: "1.3.0"
---

# iOS-Trace: Autonomous Application Performance Optimization

`iOS-Trace` is a closed-loop performance optimization engine for iOS and iPadOS applications (SwiftUI, UIKit, Metal, CoreAudio / AVAudioEngine, URLSession) on physical devices and simulators. Its core objective is to eliminate manual Instruments GUI interaction: an agent aligns on targets, captures headless traces, isolates bottlenecks, applies code fixes, re-tests with differential benchmarking, and iterates until performance targets are verified with empirical data.

---

## Phase 1: User Goal Alignment (Pre-Flight Questionnaire)

Before modifying code or collecting traces, align with the user on optimization targets and success criteria. Use an interactive modal if available (`ask_question`, option lists); otherwise ask directly with structured options.

1. **Primary Optimization Objective**:
   - A: Reduce battery drain, CPU utilization, and thermal throttling.
   - B: Lower memory footprint / transient allocation spikes / prevent Jetsam OOM.
   - C: Eliminate UI frame stuttering and dropped frames (ProMotion 120Hz Hitches).
   - D: Accelerate cold launch time.
   - E: Optimize network radio overhead / batch request efficiency.

2. **Specific Performance Targets (recommended defaults)**:
   - **Battery & CPU**: idle < 15 M/s instructions, CPU Impact < 0.3; active < 80 M/s (or reduce 30–50%).
   - **Memory & Jetsam**: resident RAM < 150 MB (utilities) / < 300 MB (rich media); allocation rate < 400 events/sec steady-state; 0 persistent leaks.
   - **UI Smoothness**: hitch ratio < 5.0 ms/s (acceptable), < 1.0 ms/s (fluid / 120Hz); max hitch < 16.6 ms (60Hz) / < 8.33 ms (120Hz).
   - **Launch Time**: time to first frame < 400 ms (excellent), < 800 ms (acceptable).
   - **Network & Radio**: batch periodic pings into single burst requests to avoid radio tail standby power.

3. **Benchmark User Scenario**: ask which specific screen, interaction, device, or simulator to benchmark.

Once targets are confirmed, proceed to Phase 2.

---

## Scope and Prerequisites

- **Target platforms**: iOS/iPadOS apps on physical iPhone/iPad (USB or local network) or local iOS Simulators. For macOS desktop apps, use [macOS-Trace](https://github.com/kmgcc/macOS-Trace).
- **Host**: macOS 12+ with full Xcode or Xcode Command Line Tools (`xcrun xctrace version`).
- **Device readiness**: unlocked and trusted by the Mac; listed under `== Devices ==` (not `== Devices Offline ==`); Auto-Lock "Never" or display kept awake during recordings.
- **Python**: 3.8+ (standard library only; zero pip dependencies).
- **Entitlements**: debug builds or developer-provisioned builds with `get-task-allow` are required for `--attach <PID>`.

---

## Rules for Agents

1. **Verify device connection state**: run `xcrun xctrace list devices` first; never record against a device under `== Devices Offline ==`.
2. **Prevent screen lock/backgrounding**: if the device locks or returns to home, iOS suspends the process and measurements are invalid. Keep the app foregrounded.
3. **Establish a baseline first**: always capture an idle baseline before the active workload; compute `Delta = Active - Baseline`.
4. **Use equal test parameters**: identical durations (default 60s), battery states, and input data across runs.
5. **Zero third-party Python dependencies**: bundled scripts (`compare_elements.py`, `parse_power.py`, `top_categories.py`) use the standard library only.
6. **Save outputs to `/tmp/ios-traces/`**: timestamped, scenario-tagged filenames.
7. **Protect context budget**: never dump raw `.trace` bundles, call-trees, or unparsed XML into the conversation — they can be hundreds of MB. Always stream/filter/rank via the bundled scripts before reading.
8. **Focus on primary bottlenecks**: profile first to confirm the dominant contributor; don't scatter micro-optimizations across innocent utilities.
9. **Never silently alter UI, visual effects, or core behavior**: if an optimization affects visual fidelity or essential behavior, formally ask the user first and articulate the exact before/after tradeoff with quantified expected gain.
10. **Clean up recording artifacts**: `run_trace.sh` auto-cleans the several-GB transient kernel traces (`instruments*.ktrace` in `$TMPDIR`). When running `xctrace` directly, clean them yourself before concluding:
    ```bash
    find "${TMPDIR:-/tmp}" -maxdepth 1 -type f -name 'instruments*.ktrace' -delete 2>/dev/null || true
    ```

---

## The 4-Phase Optimization Protocol

### Phase 2: Diagnostic Profiling & Attribution

```bash
BUNDLE_ID="com.example.MyApp"
SKILL_DIR="$HOME/.claude/skills/ios-trace"

# Idle baseline (device unlocked, app foregrounded, workload paused)
"$SKILL_DIR/scripts/run_trace.sh" --bundle-id "$BUNDLE_ID" --template power --duration 60s --label "01-baseline"

# Active workload (user triggers the scenario in the app while this records)
"$SKILL_DIR/scripts/run_trace.sh" --process "MyApp" --template power --duration 60s --label "02-pre-opt"

# Pre-optimization delta
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"Idle Baseline" \
  /tmp/ios-traces/02-pre-opt-power.xml:"Active Pre-Opt"
```

Attribute the bottleneck with specialized templates: `--template time` for hot call-trees, `alloc` with `top_categories.py` for allocation thrashing, `hitches` during scrolling for render vs commit delays, `network` for unbatched radio wakeups. See `references/templates.md` for the full template reference.

> **If the target workload requires interaction or reproduction** (taps, scrolling, gestures) — on a physical device or simulator — **read `references/workload-reproduction.md` before recording** and decide which reproduction tier to use.

### Phase 3: Targeted Code Modification

Apply minimal, surgical fixes based on findings:
- **Memory spikes & Jetsam**: downsample images at decode time with `CGImageSourceCreateThumbnailAtIndex` instead of loading full-size `UIImage`.
- **ProMotion hitches**: remove complex shadows / offscreen blending; offload heavy layout calculations from the main thread.
- **Radio energy overhead**: batch periodic network requests into unified payload bursts to eliminate radio tail standby power.
- **Real-time audio**: zero heap allocations in CoreAudio render callbacks (`AVAudioEngine` / RemoteIO).

Rebuild and deploy to the device.

### Phase 4: Re-Test, Quantitative Review & Decision Gate

```bash
# Post-optimization active workload
"$SKILL_DIR/scripts/run_trace.sh" --process "MyApp" --template power --duration 60s --label "03-post-opt"

# Compare Pre-Opt vs Post-Opt against Baseline
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"Idle Baseline" \
  /tmp/ios-traces/02-pre-opt-power.xml:"Active Pre-Opt" \
  /tmp/ios-traces/03-post-opt-power.xml:"Active Post-Opt"
```

Example Decision Output:

```text
Scenario                 Sec  CPU Avg  CPU Max  Display  GPU Avg  Total Instr    Instr M/s   WiFi Tx/Rx
=========================================================================================================
Idle Baseline             60     0.12     0.60     0.05     0.00        0.85G         14.2   0.0/0.0MB
Active Pre-Opt            60     2.40     4.80     1.10     1.80       15.60G        260.0  14.2/1.8MB
Active Post-Opt           60     0.55     1.10     0.15     0.20        4.20G         70.0   2.1/0.4MB
---------------------------------------------------------------------------------------------------------
Optimization Delta (Post-Opt vs Pre-Opt):
  Instruction throughput: -73.1% (70.0 vs 260.0 M/s)
  CPU Average Impact:     -77.1% (0.55 vs 2.40)
```

**Decision Gate**: target met → present the comparison table and conclude. Target not met → keep the current optimization, isolate the next hotspot, repeat Phases 3–4.

**Post-Report Cleanup**: after the user accepts the report, delete accumulated `.trace` bundles under `/tmp/ios-traces/` (each can be tens of GB) unless the user asks to keep them.

---

## Direct CLI

You may call `xctrace` directly instead of the bundled scripts. Run `xcrun xctrace record --help` and `xcrun xctrace export --help` for full options. You may also modify the bundled scripts for a specific task — keep the originals intact.

```bash
# Record a cold-launch sample
xcrun xctrace record --device <UDID> --template 'Time Profiler' --time-limit 30s \
  --output /tmp/ios-traces/launch.trace --launch -- com.example.MyApp <LaunchArgs>

# Export the Power Impact table
xcrun xctrace export --input /tmp/ios-traces/power.trace \
  --xpath "/trace-toc/run[@number='1']/data/table[@schema='ProcessSubsystemPowerImpact']" \
  > /tmp/ios-traces/power.xml
```

---

## Reference Documents (load on demand)

- `references/templates.md` — Instruments template picker (which template for which bottleneck).
- `references/subsystems.md` — per-subsystem optimization patterns (radio, ProMotion, images, audio).
- `references/workload-reproduction.md` — **how to reproduce the workload (Tier 0–3), including simulator boundaries; mandatory read when interaction-based scenarios are being profiled.**
