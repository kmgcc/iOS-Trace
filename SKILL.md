---
name: ios-trace
description: "Agent-native runbook for evidence-based profiling and optimization of native iOS and iPadOS apps with xctrace and Xcode Instruments on physical devices or simulators. Use for CPU or battery use, memory growth or Jetsam, UI hitches, slow launch, concurrency stalls, audio glitches, or network activity. Choose instruments and workload reproduction to fit the issue; bundled scripts are optional helpers."
compatibility: "macOS with Xcode or Command Line Tools providing xctrace; target support depends on the selected Xcode and device OS; Python 3.8+ only for optional helper scripts"
license: MIT
metadata:
  author: kmgcc
  version: "1.6.0"
---

# iOS-Trace

An agent-native runbook for investigating performance in native iOS and iPadOS apps. Choose tools and reproduction paths based on the reported symptom, device capabilities, and repository instructions. `xctrace` and Instruments provide the measurements; the GUI and CLI are both useful. Bundled scripts are optional helpers for repeatable exports and comparisons, not a required workflow.

## Runbook

1. **Understand the report.** Identify the affected app, user-visible symptom, reproduction steps, target OS/device class, and what evidence would show improvement. Ask only for missing details that materially affect the measurement. Do not impose generic numeric targets or assume every report needs code changes.
2. **Inspect the target and toolchain.** Read repository instructions. Check active Xcode and `xctrace` versions, installed templates, target OS, device/simulator availability, build configuration, app process/bundle identity, and permissions. Use `xcrun xctrace list devices` to distinguish available devices from offline ones. Follow repository device, signing, and test rules.
3. **Choose evidence that answers the question.** Use `references/templates.md` to select the smallest useful instrument or combination. Check the installed help for supported target types and options instead of assuming every Xcode/device pair exposes the same capability. Use Instruments UI when timelines or inspectors aid interpretation; use CLI capture/export when it is clearer and repeatable.
4. **Choose the right target.** Use a physical device for battery, energy, thermal, radio, and device-specific GPU conclusions. A simulator can help with CPU-hotspot, logic, and interaction triage; it cannot establish physical-device energy or thermal behavior. Explain the limit if only simulator evidence is available.
5. **Reproduce the real workload.** Read `references/workload-reproduction.md` when timing or interaction matters. Choose a trustworthy app hook, UI automation, test flow, or user-triggered interaction for the specific question. Verify that the action occurred and that the target app is in the recorded state. An idle trace is an optional control; it does not establish improvement to an active user scenario.
6. **Capture with comparable conditions.** Keep the app foregrounded and the device awake for UI or rendering work. For before/after runs, align device model, OS, build configuration, app content, screen brightness, power state, network conditions, interaction, and capture scope where they affect the result. Record differences and avoid conclusions broader than the evidence. A physical device or Simulator target does not move Instruments' host-side temporary files off the Mac; load `references/storage-and-recovery.md` before a capture when storage is constrained, and after a run if finalization or space recovery is abnormal.
7. **Interpret before editing.** Tie the user-visible symptom to the relevant process, interval, thread, task, allocation, frame, network event, or call tree. Cross-check a suspected hot path against source and call sites. Separate measured results from inference; avoid changes when the trace does not support a concrete hypothesis.
8. **Make a focused change and compare.** Follow repository instructions for code edits, device use, and validation. Re-run the same meaningful scenario with comparable conditions. If results are noisy, thermally constrained, or simulator-only, state that and refine the measurement before claiming success.
9. **Report and preserve.** Summarize the scenario, target/device/OS, instruments, observed bottleneck, change, measured result, and unverified layers. Treat traces and exports as potentially sensitive. Confirm `xctrace` has exited, inspect for deleted-open `.ktrace` handles, and verify free space on the affected Mac volume. Keep or remove artifacts according to the user's and repository's retention rules; never use broad temporary-file or Instruments-cache deletion.

## iOS measurement boundaries

- Power Profiler energy and CPU-impact conclusions require a supported physical device/OS combination. It is not supported by the Simulator. Verify the current Xcode/device help before capture; never infer energy or thermal results from simulator CPU traces.
- Device behavior changes with temperature, battery level, refresh rate, brightness, radio conditions, and foreground state. Repeat comparable runs on the same physical device when the question is about before/after changes.
- A device listed under `== Devices Offline ==` is unavailable for recording. Unlock and trust a physical device, and keep it awake and foregrounded for the scenario.
- Attach may be blocked by signing or OS policy. Use an authorized development build or supported launch mode; do not silently weaken signing or entitlements.
- Recording and export use storage on the Mac running Xcode even when the target is a physical iPhone/iPad. `--output` selects the final trace destination; it does not guarantee that host-side intermediate files use that volume.

## Xcode 27 and Instruments

When Xcode 27 is installed, load `references/templates.md` for new instruments and capture/export improvements. Capabilities depend on the installed Xcode and target OS. Swift Executor names require OS 27; on older systems they may appear as `Unknown executor`. The Foundation Models instrument covers Apple's Foundation Models framework, not arbitrary cloud or third-party model calls.

For optional Xcode project/build/test integration through MCP, load `references/xcode-agent-mcp.md`. MCP complements Instruments profiling; do not enable a host MCP server or widen its permissions as an implicit trace step.

## Optional helpers

- Use bundled scripts only when they fit the question or make a repetitive export/comparison easier. Resolve the skill directory dynamically and inspect a helper's usage before calling it.
- The runner does not own cleanup of shared Instruments files or services. The agent remains responsible for the post-recording checks in `references/storage-and-recovery.md`, whether or not a helper script was used; identify exact candidates and decide whether they are safe to remove, or ask the user when ownership or impact is unclear.
- Never edit scripts inside the installed skill. For a one-off parser adjustment, copy only the relevant helper to a task scratch directory and change the copy.
- If the app already has a project-specific profiling workflow, follow its instructions and device/process/data boundaries before using generic examples here.

## References (load as needed)

- `references/templates.md` — choose instruments by symptom; includes Xcode 27 additions.
- `references/workload-reproduction.md` — selecting and verifying device/simulator workload reproduction.
- `references/device-commands.md` — device discovery, process selection, xctrace capabilities, capture, and export.
- `references/storage-and-recovery.md` — host-side temporary storage, deleted-open `.ktrace` diagnosis, and safe recovery after recording.
- `references/xcode-agent-mcp.md` — optional Xcode 27 MCP integration and safe capability discovery.
- `references/subsystems.md` — optimization patterns for radio, ProMotion, media decoding, audio, and other app subsystems.
