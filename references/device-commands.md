# Device and xctrace Reference

Load when selecting a physical device or simulator, choosing attach versus launch, or resolving a capture problem. Commands and instrument support vary across Xcode and OS releases; inspect the active tool before recording.

## Discover current capabilities

- Check `xcodebuild -version` and `xcrun xctrace version` to identify the selected toolchain.
- Xcode 27 release notes specify iOS 17+ for on-device debugging. This does not define support for every Instruments template or recording mode; verify the selected template against the target OS.
- Use `xcrun xctrace list devices` to locate the intended device or simulator and distinguish online from offline devices.
- Inspect `xcrun xctrace list templates`, `xcrun xctrace record --help`, `xcrun xctrace export --help`, and the relevant `xcrun devicectl` / `simctl` help. Confirm the chosen template supports the target type and OS.
- For Xcode 27 recording settings, use the `--show-recording-options` form documented by the installed `xctrace` help; review any JSON before passing it with `--recording-options`.
- Do not assume old short aliases or examples work with a different installed helper/Xcode. When an instrument is GUI-only or exports insufficient data, open the trace in Instruments.

## Select and verify the target

- Prefer a physical device for energy, thermal, radio, real refresh-rate, and device-specific GPU measurements. Use the Simulator for suitable CPU, logic, and interaction triage.
- Confirm the bundle ID, app process, and executable. Device process lists can include app extensions and widgets; select the main app process for the question. If multiple instances or extensions match, inspect them instead of choosing the first PID.
- Choose attach for an already-running app when that preserves the scenario. Choose profiler-launched execution when cold launch or startup itself is under study. Follow the project's signing, build, device and data rules.
- Attach may require a development-signed app with the appropriate debugging entitlement and device state. If it fails, identify the signing/OS boundary and use an authorized development build or supported launch path; do not silently weaken signing or entitlements.
- Verify the process and app state during capture. A successful recorder exit does not prove that the intended workload or process was sampled.

## Physical-device readiness

- The device must be online, unlocked, trusted, and available to the selected Xcode. Follow the device's Developer Mode and signing requirements for the chosen action.
- Keep the app in the foreground and display awake for UI or rendering measurements. If that requires changing Auto-Lock or another device setting, follow the user's stated preference or ask before changing it.
- For before/after energy runs, record device model, OS, battery/power state, temperature context if available, brightness, and network conditions. Keep these conditions comparable.

## Record and export

Create an output location appropriate for the task and name traces for the scenario, device/OS, and run phase. Use the CLI when it preserves the question and capture scope; open Instruments for track relationships, inspectors, device-specific detail, or comparisons that are clearer visually.

The recorder and its temporary files run on the Mac, including when the target is a physical device. Check host free space on both the temporary volume and the output volume before long captures. `--time-limit` limits collection time; it does not limit bytes or guarantee prompt finalization. Load `references/storage-and-recovery.md` if disk space falls unexpectedly, `xctrace` remains alive, or space does not return after capture.

Before using custom recording options, inspect the installed template defaults and save only the reviewed changes needed for the question. Before exporting, use current help to restrict the time range, process, table, or fields to the evidence required. Treat traces and exports as potentially sensitive, and keep raw trace bundles and huge exports out of chat.

If recording fails, report the Xcode/OS, target type, template, and relevant diagnostic; then adjust based on the failure. Do not retry with an arbitrary process, broader permissions, a reset device, or a different target that cannot answer the same question.
