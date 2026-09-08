# Workload Reproduction (Tier 0–3)

**Mandatory read when profiling a phone (physical device or simulator) and the
target workload requires interaction or reproduction.** Before recording, decide
how the workload is reproduced, and keep that mechanism identical across the idle
baseline, pre-optimization, and post-optimization runs.

## Selection & Fallback Process

Reproduction is an active decision at the start of every task, not a fixed
workflow. Follow these rules in order:

1. **Prefer automation.** Never default to manual operation when the workload can
   be reproduced automatically. Tier 0 (manual) is the last resort.
2. **Selection priority** (most preferred to last resort):
   1. **Tier 1 (launch args / deep links)** — if the app exposes a launch/deep-link
      entry and you only need steady-state metrics: most deterministic, cheapest to
      repeat, works on both simulator and device.
   2. **Tier 3 (device UI automation via XCUITest)** — if real gestures are needed
      or device-only metrics matter (energy/thermal/GPU): stable and reliable on
      real hardware.
   3. **Tier 2 (simulator UI automation via idb)** — only for fast CPU-hotspot
      triage on a simulator when no device build is available (capabilities are
      limited; see Simulator Boundaries).
   4. **Tier 0 (manual)** — fallback when nothing above works.
3. **State the choice up front.** Tell the user which tier you are using and why,
   so they can correct or add context.
4. **Switch tier on failure.** If a path fails or produces unusable data (command
   errors, app ignores args, gestures have no effect, results not reproducible),
   do not keep retrying the same path — fall back to the next tier. Switching
   within one task is allowed.
5. **Ask for manual help explicitly.** When no automation works, tell the user
   exactly what to do ("open the X screen, scroll for 30s, stop") and why
   automation failed. Never make the user cooperate blindly.
6. **Respect an explicit manual request.** If the user says up front "I'll do it
   myself", use Tier 0 directly — do not attempt automation.
7. **Keep one mechanism for all runs.** Whatever tier you end up with, baseline /
   pre / post must use the same mechanism for comparable results.

## Tier Comparison

| Tier | Mechanism | Interactive? | Simulator | Device | Energy/Thermal metrics | Measures gesture cost? |
|---|---|---|---|---|---|---|
| 0 | Manual (user triggers the scenario) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 1 | Launch args / deep links (programmatic) | ❌ | ✅ | ✅ | ✅ (on device) | ❌ |
| 2 | Simulator UI automation (idb / XCUITest) | ✅ (idb) | ✅ | ❌ | ❌ | ✅ |
| 3 | Device UI automation (XCUITest) | ❌ (precompiled) | ❌ | ✅ | ✅ | ✅ |

## Simulator Boundaries

The simulator is fast and convenient but has hard limits. Check these before choosing:

- **Energy / thermal / CPU Impact (Power Profiler) is unavailable on the simulator.**
  Instruments reports `Power Profiler is not supported on the Simulator`. Any
  metric involving CPU Impact, energy, or thermal **requires a physical device**
  (Tier 1 on device, or Tier 3).
- **xctrace recording on the simulator can be unstable** (recording may hang at
  startup in some environments). For batch multi-run traces, a device is more
  reliable.
- **Simulator results do not represent device behavior** for power, thermal,
  some GPU, and radio behavior. Use the simulator for CPU-hotspot triage and
  logic issues only; never draw energy/thermal conclusions from it.

## Tier 0 — Manual Triggering (always available)

The agent records while the user performs the scenario by hand (scrolling,
playing, navigating), coordinated over chat ("start recording now, scroll for
30 s, stop"). Use when the app has no automation hooks and no UI-automation
toolchain is set up. Requires a human in the loop, so fully unattended
multi-iteration loops are not possible; human timing jitter reduces A/B precision
— mitigate with longer, consistent sample windows.

## Tier 1 — Launch Arguments & Deep Links (deterministic, preferred)

Programmatic navigation that lands the app in the target state without any touch
input. The most deterministic tier, best for A/B benchmarking, and works on both
simulator and device.

```bash
# Simulator: launch with arguments
xcrun simctl launch <device> <bundle-id> --scenario <name> --flag

# Physical device: launch with arguments
xcrun devicectl device process launch --device <UDID> <bundle-id> -- --scenario <name>

# Launch and sample in one step (no separate launch needed)
xcrun xctrace record --device <UDID> --template 'Time Profiler' \
  --time-limit 60s --launch -- <bundle-id> --scenario <name>

# Simulator: deep link (open a URL that routes the app)
xcrun simctl openurl <device> "scheme://path?param=value"
```

The app must act on the input: read `ProcessInfo.processInfo.arguments` for launch
arguments, or implement `onOpenURL` / `application(_:open:options:)` for deep
links, and route to the scenario. For performance work, a debug-only
`--scenario <name>` hook is the cleanest contract.

**Best for:** steady-state CPU / memory / energy of a specific screen or feature;
unattended multi-iteration loops; reproducible before/after comparisons.

**Limitations:** it is navigation, not interaction — the touch pipeline is
bypassed, so tap/scroll gesture cost cannot be measured. It requires the app to
implement parsing; passing an argument an app ignores produces a false success.

## Tier 3 — Device UI Automation (XCUITest, preferred on device)

Apple's official XCTest UI-automation framework runs precompiled UI tests on a
real device with true touch events, real hardware metrics, and no user
interaction. Stable and reliable — the primary automation path on a physical
device.

```bash
# Write an XCUITest target (launch app, tap by accessibility identifier, assert
# state), then run it on the device:
xcodebuild -project <proj> -scheme <scheme> -destination 'id=<UDID>' \
  -allowProvisioningUpdates test
```

**Best for:** gesture cost and behavior that only reproduces on real hardware
(ProMotion, radio, thermal); final release verification; stable multi-run trace
batches; cases where simulator results are not trustworthy.

**Limitations:** tests are precompiled — changing the scenario means editing the
test and re-running, not interactive like `idb` on a simulator. Requires
Developer Mode enabled on the device, an Apple Development signing identity with
automatic signing, and the development team's account configured in Xcode
(Accounts settings). The first run installs runner components on the device.

## Tier 2 — Simulator UI Automation (for fast triage)

The iOS Simulator is a macOS window, so the agent can drive it interactively and
generate real touch events. Recommended tool: `idb`.

```bash
# Read the full accessibility tree (labels + frames) — how the agent "sees" the UI
idb ui describe-all

# Interact by element identity when possible (does not drift with layout)
idb ui tap "<element label>"

# Coordinate taps / swipes as a fallback
idb ui tap <x> <y>
idb ui swipe <x1> <y1> <x2> <y2> --duration 0.5

# Capture frames to verify the effect
xcrun simctl io booted screenshot /tmp/frame.png
```

**Best for:** fast CPU-hotspot and logic triage on a simulator; interactive
exploration — agent reads the UI, decides, taps; quick iteration when no device
build is available.

**Limitations:** `idb ui` commands support simulators only. Cannot measure
energy / thermal / CPU Impact. Simulator xctrace recording can be unstable.
Results do not represent device power/thermal/GPU behavior. Requires an
`iphonesimulator` build.

## Common Pitfalls

- Launch arguments reach the process, but the app must actually consume them —
  verify with a log line or a state assertion, or the run silently tests nothing.
- Launch arguments and deep links do not simulate touches; they cannot measure
  tap/scroll cost. Use Tier 3 for gesture-level questions.
- `simctl openurl` works on simulators only; `devicectl` has no equivalent for
  physical devices (use an in-app trigger or a universal link opened on the device).
- `idb ui` commands are simulator-only; do not attempt them on physical devices.
- Some UI-automation frameworks officially support iOS only on simulators, not on
  physical devices — verify driver support before committing to one.
- Physical-device UI testing fails at signing if the development team is not
  configured in Xcode's Accounts — resolve account configuration before anything
  else.
- Energy/thermal conclusions from simulator data are invalid (Power Profiler is
  unsupported); always return to a device for these metrics.
- Keep the scenario fixed across baseline / pre / post runs: same screen, same
  inputs, same duration, same tier combination.
