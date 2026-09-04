---
name: ios-trace
description: "Autonomous closed-loop performance optimization engine for iOS and iPadOS applications using xctrace and Xcode Instruments on physical devices and simulators. Handles the complete lifecycle: aligning optimization targets with the user, headless diagnostic trace capture, isolating bottlenecks, implementing code fixes, re-testing with differential A/B verification, and iterating until performance goals are met without manual GUI intervention. Use when the user reports battery drain or device overheating, high CPU usage, memory spikes or Jetsam OOM crashes, UI hitches or dropped frames (including ProMotion 120Hz stutter), slow cold launch, or excessive network radio overhead in an iOS/iPadOS app, and asks to profile, benchmark, or optimize it."
compatibility: "macOS 12+ host, iOS 15+ physical device or simulator, Xcode Command Line Tools, Python 3.8+"
license: MIT
metadata:
  author: kmgcc
  version: "1.2.1"
---

# iOS-Trace: Autonomous Application Performance Optimization

`iOS-Trace` is a closed-loop performance optimization engine for iOS and iPadOS applications running on physical iPhone/iPad devices and local iOS Simulators (SwiftUI, UIKit, Metal, CoreAudio / AVAudioEngine, and URLSession networking).

The core objective is to eliminate manual Instruments GUI interaction. An AI agent can autonomously diagnose, locate bottlenecks, implement code changes, re-test with differential benchmarking, and iterate until performance targets are verified with empirical data.

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

---

## Phase 1: User Goal Alignment (Pre-Flight Questionnaire)

Before modifying code or collecting traces on mobile devices, the agent must align with the user on optimization targets and success criteria.

### Modal Tool vs Chat Interaction
- **If your agent platform provides an interactive questionnaire/modal tool** (e.g., `ask_question`, input dialogs, or selectable option lists), invoke it to present these choices cleanly to the user.
- **If no modal tool is available**, ask the user directly in the conversation with structured options and concrete recommended values.

### Questions to Ask the User

1. **Primary Optimization Objective**:
   - Option A: Reduce battery drain, CPU utilization, and thermal throttling.
   - Option B: Lower memory footprint, transient allocation spikes, or prevent Jetsam OOM crashes.
   - Option C: Eliminate UI frame stuttering and dropped animation frames (ProMotion 120Hz Hitches).
   - Option D: Accelerate mobile application cold launch time.
   - Option E: Optimize network radio overhead and batch request efficiency.

2. **Specific Performance Targets (Provide Recommended Defaults)**:
   - **Battery & CPU Targets**:
     - *Idle Baseline Target*: < 15 M/s instructions, CPU Impact < 0.3.
     - *Active Workload Target*: < 80 M/s instructions (or specify: reduce by 30% - 50%).
   - **Memory & Jetsam Targets**:
     - *Maximum Resident RAM*: Cap at < 150 MB (standard utilities) or < 300 MB (media/rich interactive apps).
     - *Allocation Event Rate*: < 400 events/sec during steady-state interaction.
     - *Memory Leaks*: Exactly 0 persistent leaks.
   - **UI Smoothness & Frame Rate Targets**:
     - *Hitch Ratio*: < 5.0 ms/s (acceptable), < 1.0 ms/s (fluid / 120Hz ProMotion grade).
     - *Max Hitch Duration*: < 16.6ms (60Hz) or < 8.33ms (120Hz).
   - **Launch Time Targets**:
     - *Time to First Frame*: < 400 ms (excellent), < 800 ms (acceptable).
   - **Network & Radio Targets**:
     - *Radio Overhead*: Batch periodic pings into single burst requests to avoid radio tail standby power.

3. **Benchmark User Scenario**:
   - Ask the user which specific screen, user interaction, physical device, or simulator to benchmark.

Once targets are confirmed, proceed to Phase 2.

---

## Scope and Prerequisites

- **Target platforms**: iOS and iPadOS applications running on physical iPhone/iPad devices connected via USB or local network, or local iOS Simulators. (For macOS desktop applications, use [macOS-Trace](https://github.com/kmgcc/macOS-Trace)).
- **Host system**: macOS 12+ running on Apple Silicon or Intel Mac with full Xcode or Xcode Command Line Tools (`xcode-select -p`, `xcrun xctrace version`).
- **Device readiness**:
  - The physical iPhone/iPad must be unlocked and trusted by the Mac host.
  - The device must appear under `== Devices ==` (not `== Devices Offline ==`) when running `xcrun xctrace list devices`.
  - Auto-Lock should be set to "Never" or display kept awake during recordings to prevent iOS from suspending background processes.
- **Python**: Python 3.8+ on the host Mac (uses standard library only; zero external pip dependencies).
- **Process entitlements**: Debug builds or developer-provisioned builds with `get-task-allow` entitlement are required for `--attach <PID>`.

---

## Rules for Agents

Follow these non-negotiable rules during automated profiling:

1. **Verify device connection state**: Always run `xcrun xctrace list devices` before recording. Never attempt to record against a device listed under `== Devices Offline ==`.
2. **Prevent screen lock and backgrounding**: If the iOS device locks or returns to the home screen, iOS suspends or throttles the process, producing invalid measurements. Keep the device awake and the app in the foreground.
3. **Establish a baseline first**: Never record only the active workload. Always capture an idle baseline run (app in foreground, device screen on, workload paused) before recording the active state. Compute: `Delta = Active - Baseline`.
4. **Use equal test parameters**: Compare runs with identical sample durations (default: `60s`), identical device battery states (avoid profiling while under 20% battery or Low Power Mode), and identical test input data.
5. **No third-party Python dependencies**: All bundled scripts (`scripts/compare_elements.py`, `scripts/parse_power.py`, `scripts/top_categories.py`) use the Python 3 standard library only.
6. **Save outputs to `/tmp/ios-traces/`**: Store all `.trace` bundles and `.xml` exports in `/tmp/ios-traces/` with timestamped and scenario-tagged filenames.
7. **Protect conversation context budget**: Trace files and raw exported XML documents can be tens or hundreds of megabytes. Never dump raw `.trace` outputs, full call-trees, or unparsed Allocations XML into the agent conversation context. Always use the bundled Python scripts to stream, filter, rank, and summarize the data before reading.
8. **Focus on primary bottlenecks**: Do not scatter micro-optimizations across dozens of innocent utility functions. Profile first to confirm the dominant contributor (e.g. redundant surface instances, high-frequency timer re-evaluations, unbuffered I/O) and focus optimization efforts exclusively on that root cause.
9. **Never silently alter UI, visual effects, or core behavior**: If a performance bottleneck involves visual fidelity (such as blur/materials, frame animations, shadows, layout transitions) or essential software behavior:
   - **Do not unilaterally remove or downgrade the visual feature.**
   - **Formally ask the user for permission first** (using an interactive prompt or explicit chat message).
   - **Clearly articulate the tradeoff**: Describe the visual change before and after, explain why the feature consumes resources, and present the concrete expected performance gain (e.g., "Disabling dynamic shadow and blur on card views will reduce GPU average impact from 1.8 to 0.2 and eliminate 120Hz ProMotion hitches").

---

## The 4-Phase Optimization Protocol

### Phase 2: Diagnostic Profiling & Attribution

Before writing code, measure the current state on the device and isolate the root cause:

```bash
# 1. Confirm the target device is online and unlocked (optional check;
#    run_trace.sh auto-detects the first connected iPhone/iPad when --device is omitted)
xcrun xctrace list devices

BUNDLE_ID="com.example.MyApp"
# SKILL_DIR = this skill's installed directory (adjust if installed elsewhere)
SKILL_DIR="$HOME/.claude/skills/ios-trace"

# 2. Record 60s idle baseline (device unlocked, app foregrounded, workload paused)
"$SKILL_DIR/scripts/run_trace.sh" \
  --bundle-id "$BUNDLE_ID" \
  --template power \
  --duration 60s \
  --label "01-baseline"

# 3. Trigger target workload in app, record active state
"$SKILL_DIR/scripts/run_trace.sh" \
  --process "MyApp" \
  --template power \
  --duration 60s \
  --label "02-pre-opt"

# 4. Compute pre-optimization delta
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"Idle Baseline" \
  /tmp/ios-traces/02-pre-opt-power.xml:"Active Pre-Opt"
```

Use the specialized templates to attribute the bottleneck:
- Run `--template time` to isolate hot call-tree functions on worker threads.
- Run `--template alloc` with `scripts/top_categories.py` to identify thrashing allocations causing memory pressure.
- Run `--template hitches` during scrolling to isolate render vs commit delays on ProMotion displays.
- Run `--template network` to detect continuous unbatched radio wakeups.

### Phase 3: Targeted Code Modification

Apply minimal, surgical fixes based on findings:
- **Memory Spikes & Jetsam**: Adopt downsampling for high-resolution images with `CGImageSourceCreateThumbnailAtIndex` instead of loading full-size `UIImage`.
- **ProMotion Hitches**: Remove complex shadows and offscreen blending passes; offload heavy view layout calculations from the main thread.
- **Radio Energy Overhead**: Batch periodic network requests into unified payload bursts to eliminate radio tail standby power.
- **Real-Time Audio**: Ensure zero heap allocations in CoreAudio render callbacks (`AVAudioEngine` or RemoteIO).

Rebuild the application and deploy to the device.

### Phase 4: Re-Test, Quantitative Review & Decision Gate

Rerun the profile under identical conditions and evaluate the delta:

```bash
# 1. Record post-optimization active workload
"$SKILL_DIR/scripts/run_trace.sh" \
  --process "MyApp" \
  --template power \
  --duration 60s \
  --label "03-post-opt"

# 2. Compare Pre-Opt vs Post-Opt against Baseline
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
Differential vs Baseline [Idle Baseline]:
  Active Pre-Opt            +245.8 M/s instructions, CPU Avg Delta +2.28, WiFi Tx Delta +14.20MB
  Active Post-Opt           +55.8 M/s instructions, CPU Avg Delta +0.43, WiFi Tx Delta +2.10MB

Optimization Delta (Post-Opt vs Pre-Opt):
  Instruction throughput: -73.1% (70.0 vs 260.0 M/s)
  CPU Average Impact:     -77.1% (0.55 vs 2.40)
  GPU Average Impact:     -88.9% (0.20 vs 1.80)
  WiFi Radio Traffic:     -85.2% (2.1MB vs 14.2MB)
```

**Decision Gate Logic**:
- **Target Met**: Present the empirical comparison table to the user and conclude.
- **Target Not Met**: Keep the previous optimization, isolate the next remaining hotspot, and repeat Phase 3 and Phase 4.

---

## Direct CLI Commands

If executing `xctrace` directly without `run_trace.sh`:

### Record

```bash
# Attach to running app on device
xcrun xctrace record \
  --device <DEVICE_UDID> \
  --template 'Power Profiler' \
  --time-limit 60s \
  --output /tmp/ios-traces/power.trace \
  --attach <PID>

# Cold-launch app on device
xcrun xctrace record \
  --device <DEVICE_UDID> \
  --template 'Time Profiler' \
  --time-limit 30s \
  --output /tmp/ios-traces/launch.trace \
  --launch -- com.example.MyApp <LaunchArgs>
```

### Export

```bash
# Export Power Impact table (CPU instructions, energy, GPU, Display, WiFi/Cellular)
xcrun xctrace export \
  --input /tmp/ios-traces/power.trace \
  --xpath "/trace-toc/run[@number='1']/data/table[@schema='ProcessSubsystemPowerImpact']" \
  > /tmp/ios-traces/power.xml

# Export Allocations summary table
xcrun xctrace export \
  --input /tmp/ios-traces/alloc.trace \
  --xpath "/trace-toc/run[@number='1']/data/table[@schema='all-allocations-summary']" \
  > /tmp/ios-traces/alloc.xml
```

## Template Reference

Instruments templates supported on iOS via `scripts/run_trace.sh` and headless `xctrace`:

### Compute, Battery & Energy
| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Power Profiler` | `power` | Instructions/sec (M/s), CPU/GPU/Display/WiFi/Cellular energy impacts (`ProcessSubsystemPowerImpact`). | Comprehensive battery drain, thermal throttling, and A/B benchmarking. |
| `Time Profiler` | `time` | CPU sample weights by thread, call-tree hotspots, main-thread blocking methods. | High CPU utilization, runaway worker threads, and hot function paths. |
| `CPU Counters` | `counters` | IPC (instructions per cycle), L1/L2 cache misses, branch mispredictions. | Low-level computational and audio DSP algorithm performance bottlenecks. |

### UI Responsiveness & Smoothness
| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Animation Hitches` | `hitches` | Hitch duration (ms), hitch ratio (ms/s), dropped frames, commit latency. | ProMotion 120Hz scrolling stutter, dropped animation frames, and commit delays. |
| `SwiftUI` | `swiftui` | View body evaluations, State invalidation counts, view update frequency. | Unnecessary view re-evaluations and state invalidation cascades. |
| `Metal System Trace` | `metal` | GPU encoder time, vertex/fragment shader durations, frame boundary latency. | Shader execution bottlenecks, particle FX overhead, and render pipeline stalls. |

### Memory & Allocations
| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Allocations` | `alloc` | Heap allocations, transient vs persistent memory, category event rates (`all-allocations-summary`). | High-frequency temporary allocations, memory spikes, and buffer thrashing. |
| `Leaks` | `leaks` | Retained memory leaks that outlive parent lifecycle, reference cycles. | Abandoned memory, closure capture leaks, and unreleased delegate cycles. |

### Network, Startup & Concurrency
| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Network` | `network` | TCP/UDP connections, DNS latency, packets sent/received, radio state overhead. | Network request latency, payload bloat, and radio wake-lock drain. |
| `App Launch` | `launch` | Time to first frame, `dyld` loading time, static initializers, runloop setup. | Cold start optimization (`--launch -- <bundle_id>`). |
| `Swift Concurrency` | `concurrency` | Swift Tasks (created/running/suspended), Actor reentrancy, cooperative pool usage. | `async/await` starvation, actor contention, and long-suspended tasks. |

## Mobile Subsystem Optimization Notes

### Battery & Radio Energy Management
- **Cellular & WiFi radio tails**: Opening a network socket transitions the cellular baseband or WiFi chip from low-power sleep to high-power active state, maintaining high power consumption for several seconds after the transfer finishes (radio tail). Batch network requests into unified bursts rather than firing periodic independent pings every few seconds.
- **Verification**: Run `Power Profiler` and inspect the `WiFi Tx/Rx` and `Network Impact` metrics in `scripts/parse_power.py`.

### ProMotion 120Hz Displays and Hitches
- **Frame budget**: On ProMotion devices (iPhone Pro models), the display refresh interval is 8.33ms (120Hz). Exceeding 8.33ms on either the main thread (view preparation and layout) or render server (CoreAnimation commit) drops frames.
- **Hitches taxonomy**:
  - *Commit Hitches*: Main thread took too long to build view hierarchy or compute geometry before committing to render server.
  - *Render Hitches*: GPU took too long rendering layers (complex shadows, blur effects, offscreen passes).
- **Diagnosis**: Use `Animation Hitches` with `--duration 30s` during scrolling interactions.

### Image Downsampling and Low-Memory Warnings
- **Memory spikes on iOS**: iOS jetsam kills background or foreground apps exceeding strict memory ceilings (often ~1.5GB to 2GB on mobile). Decoding raw photos or large bitmaps directly into `UIImage` inflates the heap by 4 bytes per pixel uncompressed.
- **Downsampling**: Always downsample images at decode time using `CGImageSourceCreateThumbnailAtIndex` with `kCGImageSourceThumbnailMaxPixelSize`.

### Real-Time Audio & Background Execution
- **Audio Session interruptions**: Real-time audio rendering callbacks running on `AVAudioEngine` or RemoteIO unit must never perform heap allocation or file I/O.
- **Background Mode**: If testing background audio or streaming, verify process behavior when transitions to background state occur (`UIApplication.didEnterBackgroundNotification`).

