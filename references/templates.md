# Instruments Template Guide (iOS / iPadOS)

Load when selecting a recording for a specific performance question. Template names, target support, and CLI options depend on the active Xcode and device OS. Start with `xcrun xctrace list templates` and the installed help; use exact names reported there. This guide describes candidates and evidence, not a hardcoded command matrix.

For release-specific changes, check [Apple's Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

| Question or symptom | Candidate instruments | Evidence to inspect |
| --- | --- | --- |
| CPU work, hot functions, or unexpected wakeups | Time Profiler; CPU Profiler where available | Sample weights by thread, call tree, running intervals, and overlap with the reported symptom. |
| Battery, energy, or thermal behavior | Power Profiler on a supported physical device; Time Profiler for code attribution | Per-process subsystem impact and hot work during the active scenario. Check current device/OS support; do not infer physical energy or thermal impact from a Simulator. |
| Scrolling, animation, or touch-response hitches | Animation Hitches; SwiftUI; Metal System Trace when GPU work is implicated | Hitch intervals and frame phases, view/layout work, GPU activity, refresh-rate context, and the interaction that triggers the delay. |
| Memory growth, churn, or Jetsam risk | Allocations; Leaks; device memory or termination diagnostics as appropriate | Live/persistent allocations, allocation backtraces, growth across repeated lifecycles, and whether owners outlive their intended lifecycle. A Leaks result alone does not establish bounded memory use. |
| Slow cold launch or resume | App Launch; Time Profiler or signposts for attribution | Launch phases, dyld work, static initialization, first useful frame, resume path, and the app's readiness signal. Keep launch conditions comparable. |
| Async stalls, actor contention, or executor starvation | Swift Concurrency; Swift Executors; Time Profiler or CPU Profiler; System Trace for scheduling evidence | Tasks and actors, waits/suspensions, executor queues, thread state, and scheduling around the user-visible delay. |
| Network latency, repeated requests, or radio activity | Network; Power Profiler where available; signposts or app logs | Request timing, connections, payloads, retries, and whether radio-active periods overlap the app's work. Use a physical device for radio/energy conclusions. |
| Audio glitches or real-time callback instability | Audio System Trace; Time Profiler; Allocations when allocation is suspected | Audio I/O timing, late or missed work, callback duration, locks, and allocations on real-time paths. |
| GPU or shader cost | Metal System Trace; CPU Counters where supported | GPU encoder/pass timing, frame boundaries, counters, and the target hardware's support. Some data requires opening the trace in Instruments rather than relying on a CLI export. |
| Apple Foundation Models latency or usage | Foundation Models | Instructions, prompts, responses, token usage, tool activity, and inference latency for calls through Apple's Foundation Models framework. Treat captured prompt/response data as sensitive. |

## Xcode 27 additions

- **Swift Executors**: displays the Cooperative Thread Pool, Main Actor, and custom `TaskExecutor` / `SerialExecutor` implementations. Executor names are captured on OS 27; earlier systems may show `Unknown executor`.
- **Swift Concurrency + CPU profiling**: recording Swift Concurrency alongside Time Profiler or CPU Profiler enables `Profile` details with call trees sampled while tasks are running. Use this to connect task/actor timelines to code-level CPU work; justify the extra capture overhead with the question.
- **SwiftUI layout detail**: records more layout-pass information, including reasons a layout computation was not cached. Confirm repeated layout work coincides with the visible hitch or CPU cost.
- **System Trace**: presents system calls, VM faults, and thread states in a unified timeline, with thread-priority context. Follow scheduling around the affected app thread instead of treating broad system activity as an app bottleneck.
- **Foundation Models**: covers Apple's Foundation Models framework. It is not a general profiler for remote APIs, third-party model providers, or every local inference runtime. Prompt and response contents can be sensitive.
- **Capture and export**: `xctrace record --show-recording-options` reports options for the installed template/instrument; pass reviewed JSON through `--recording-options` only when needed. `xctrace export` can restrict the exported time range, and Allocations exports can include captured backtraces. Check current CLI help because options vary by Xcode.
- **Reviewing runs**: use Instruments' run-comparison and summary views when they make a before/after result clearer. Inspect run metadata and keep the same real scenario and target conditions.

## Device and simulator notes

- Power Profiler is not supported on the Simulator. Energy, CPU-impact, and thermal claims require a supported physical device and OS.
- Power Profiler support depends on device OS; this repository has historically required iOS 26 or later. Check current `xctrace` help and the connected device before relying on it. For unsupported devices, choose CPU attribution tools and report the missing energy evidence explicitly.
- Some device- or GPU-specific instruments expose different data in GUI and CLI exports. Open the trace in Instruments when the relevant timeline is not represented in the export.
- Select only instruments that distinguish a plausible cause. Multi-instrument traces can add overhead and produce more sensitive or larger recordings.
