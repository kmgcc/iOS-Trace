# Instruments Template Reference (iOS)

Load this file when you need to pick the right Instruments template for a specific
bottleneck. Each template is supported via `scripts/run_trace.sh --template <short>`
and headless `xctrace`.

## Compute, Battery & Energy

| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Power Profiler` | `power` | Instructions/sec (M/s), CPU/GPU/Display/WiFi/Cellular energy impacts (`ProcessSubsystemPowerImpact`). | Comprehensive battery drain, thermal throttling, and A/B benchmarking. |
| `Time Profiler` | `time` | CPU sample weights by thread, call-tree hotspots, main-thread blocking methods. | High CPU utilization, runaway worker threads, and hot function paths. |
| `CPU Counters` | `counters` | IPC (instructions per cycle), L1/L2 cache misses, branch mispredictions. | Low-level computational and audio DSP algorithm performance bottlenecks. |

## UI Responsiveness & Smoothness

| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Animation Hitches` | `hitches` | Hitch duration (ms), hitch ratio (ms/s), dropped frames, commit latency. | ProMotion 120Hz scrolling stutter, dropped animation frames, and commit delays. |
| `SwiftUI` | `swiftui` | View body evaluations, State invalidation counts, view update frequency. | Unnecessary view re-evaluations and state invalidation cascades. |
| `Metal System Trace` | `metal` | GPU encoder time, vertex/fragment shader durations, frame boundary latency. | Shader execution bottlenecks, particle FX overhead, and render pipeline stalls. |

## Memory & Allocations

| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Allocations` | `alloc` | Heap allocations, transient vs persistent memory, category event rates (`all-allocations-summary`). | High-frequency temporary allocations, memory spikes, and buffer thrashing. |
| `Leaks` | `leaks` | Retained memory leaks that outlive parent lifecycle, reference cycles. | Abandoned memory, closure capture leaks, and unreleased delegate cycles. |

## Network, Startup & Concurrency

| Template | Short Name | Target Metrics & Export Schema | Use Case |
| :--- | :--- | :--- | :--- |
| `Network` | `network` | TCP/UDP connections, DNS latency, packets sent/received, radio state overhead. | Network request latency, payload bloat, and radio wake-lock drain. |
| `App Launch` | `launch` | Time to first frame, `dyld` loading time, static initializers, runloop setup. | Cold start optimization (`--launch -- <bundle_id>`). |
| `Swift Concurrency` | `concurrency` | Swift Tasks (created/running/suspended), Actor reentrancy, cooperative pool usage. | `async/await` starvation, actor contention, and long-suspended tasks. |
