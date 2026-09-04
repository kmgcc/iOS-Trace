---
name: ios-trace
description: Profile iOS applications headlessly on physical devices and simulators using xctrace and Xcode Instruments. Use when diagnosing iOS device thermal throttling, battery drain, network radio overhead, ProMotion 120Hz frame drops, UI hitches, audio glitches, memory spikes or leaks, or when validating mobile optimizations with differential A/B benchmarks.
compatibility: macOS 12+ host, iOS 15+ physical device or simulator, Xcode Command Line Tools, Python 3.8+
license: MIT
metadata:
  author: kmgcc
  version: "1.0.0"
---

# iOS-Trace: Headless Performance Profiling for iOS

A headless Xcode Instruments profiling toolchain and automation protocol designed specifically for **iOS applications running on physical iPhone/iPad devices and iOS Simulators**.

Use this skill to automate trace collection, extract data from Instruments tables into structured XML, and produce quantitative metrics and A/B comparisons without opening the Instruments GUI.

## Scope and Prerequisites

- **Target platforms**: iOS, iPadOS physical devices connected via USB or local network, and local iOS Simulators. (For macOS desktop applications, use `macOS-Trace` instead).
- **Host system**: macOS 12+ running on Apple Silicon or Intel Mac with full Xcode or Xcode Command Line Tools (`xcode-select -p`, `xcrun xctrace version`).
- **Device readiness**:
  - The physical iPhone/iPad must be unlocked and trusted by the Mac host.
  - The device must appear under `== Devices ==` (not `== Devices Offline ==`) when running `xcrun xctrace list devices`.
  - Auto-Lock should be set to "Never" or display kept awake during recordings to prevent iOS from suspending background processes.
- **Python**: Python 3.8+ on the host Mac (uses standard library only; zero external pip dependencies).
- **Process entitlements**: Debug builds or developer-provisioned builds with `get-task-allow` entitlement are required for `--attach <PID>`.

## Rules for Agents

Follow these constraints when profiling or verifying performance changes on iOS:

1. **Verify device connection state**: Always run `xcrun xctrace list devices` before recording. Never attempt to record against a device listed under `== Devices Offline ==`.
2. **Confirm real workload state**: On mobile devices, an idle app consumes minimal power. Ensure the feature under test is actively running (e.g. active audio stream, active network packets, active touch animation). If testing network features, verify that WiFi or Cellular transmission is actively occurring.
3. **Establish an idle baseline first**: Never record only the active workload. Always capture an idle baseline run (app in foreground, device screen on, workload paused) before recording the active state. Compute: `Delta = Active - Baseline`.
4. **Prevent screen lock and backgrounding**: If the iOS device locks or returns to the home screen, iOS suspends or throttles the process, producing invalid measurements. Keep the device awake and the app in the foreground.
5. **No third-party Python dependencies**: All bundled scripts (`scripts/compare_elements.py`, `scripts/parse_power.py`, `scripts/top_categories.py`) use the Python 3 standard library only.
6. **Save outputs to `/tmp/ios-traces/`**: Store all `.trace` bundles and `.xml` exports in `/tmp/ios-traces/` with timestamped and scenario-tagged filenames.

## Standard Workflow

### 1. Pre-Flight and Device Discovery

```bash
# 1. Verify tooling
xcrun xctrace version
python3 --version

# 2. List connected devices and simulators
xcrun xctrace list devices

# 3. Locate target process PID on device (if app is already running)
DEVICE_UDID="00008140-000C54310E82801C"
xcrun devicectl device info processes --device "$DEVICE_UDID"
```

### 2. Record and Analyze (Using `scripts/run_trace.sh`)

The script wraps `xcrun xctrace record`, `xcrun xctrace export`, and the Python parser into a single command:

```bash
# Step 1: Record 60s idle baseline on physical device
./scripts/run_trace.sh \
  --device "$DEVICE_UDID" \
  --bundle-id "com.example.MyApp" \
  --template power \
  --duration 60s \
  --label "01-idle-base"

# Step 2: Trigger the target feature in the app, then record 60s active state
./scripts/run_trace.sh \
  --device "$DEVICE_UDID" \
  --process "MyApp" \
  --template power \
  --duration 60s \
  --label "02-active-workload"
```

### 3. Compute A/B Differential

Pass the exported XML files to `scripts/compare_elements.py`. The first file is treated as the reference baseline:

```bash
python3 scripts/compare_elements.py \
  /tmp/ios-traces/01-idle-base-power.xml:"1. Idle Baseline" \
  /tmp/ios-traces/02-active-workload-power.xml:"2. Active Workload"
```

Output example:
```text
Scenario                 Sec  CPU Avg  CPU Max  Display  GPU Avg  Total Instr    Instr M/s   WiFi Tx/Rx
=========================================================================================================
1. Idle Baseline          60     0.12     0.60     0.05     0.00        0.85G         14.2   0.0/0.0MB
2. Active Workload        60     2.40     4.80     1.10     1.80       15.60G        260.0  14.2/1.8MB
---------------------------------------------------------------------------------------------------------
Differential vs Baseline [1. Idle Baseline]:
  2. Active Workload        +245.8 M/s instructions, CPU Avg Delta +2.28, WiFi Tx Delta +14.20MB
```

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
