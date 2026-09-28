# Reproducing iOS and iPadOS Workloads

Load when the report depends on a tap, scroll, launch, playback, network request, import, resume, or other timed activity. Choose the reproduction path that preserves the behavior under investigation.

## Choose and verify the path

1. Describe the scenario as observable app state and actions. Identify the time interval, device/OS requirements, content, network or account dependencies, and whether the question concerns the interaction itself or steady-state work after it.
2. Choose a trustworthy path for this app: user-triggered interaction, a supported launch argument or deep link, an existing benchmark/test, or UI automation. Launch hooks are useful only when the app consumes them and they exercise the reported work.
3. Prefer the least intrusive path that retains the scenario. Use the Simulator for quick CPU/logic triage when it faithfully exercises the path. Use a physical device for battery, energy, thermal, radio, device GPU, ProMotion, or other hardware-specific behavior.
4. Verify the action occurred and the target app is in the expected state. Use app state, logs, signposts, UI observation, or the trace as appropriate; a successful command or test launch alone does not prove the intended path ran.
5. For before/after comparisons, repeat the same scenario and reproduction mechanism. Keep device model, OS, build configuration, app content, screen brightness, refresh conditions, battery/power state, network conditions, window/app state, and capture scope comparable where they affect the result. Record differences and narrow the conclusion when a condition could not be held constant.
6. If automation changes timing, cannot reach the required state, or the app does not expose a reliable hook, use a manual interaction or a better-supported path. Ask the user to perform an action only when the required state cannot be established safely or accurately by the agent.

An idle capture may help isolate background cost, but it is optional. It does not establish improvement to an active scroll, playback, launch, network, or other reported scenario.

## Physical-device precautions

- Use `xcrun xctrace list devices` to confirm the intended device is online. Do not record against entries under `== Devices Offline ==`.
- Unlock and trust the device before use. Keep it awake and the app foregrounded for UI/rendering work; backgrounding can suspend or change app behavior.
- For battery/energy comparisons, use the same physical device, control brightness and network conditions, and allow temperature and battery state to be comparable. A warm device or changing radio conditions can dominate short runs.
- Do not reset, erase, re-provision, or clear app data merely to make a scenario repeatable. Follow project and user data-ownership rules.

## Simulator limits

- The Simulator is useful for fast CPU, logic, and UI-interaction triage when its behavior matches the question.
- Power Profiler energy/CPU-impact and thermal conclusions require a supported physical device; the Simulator does not provide them.
- Simulator results do not establish physical-device radio, battery, thermal, or device-GPU behavior. Simulator `xctrace` can also fail or hang in some environments; verify that a useful trace was actually produced before analysis.

## Capture design

Choose duration and repetition from the behavior. Include warm-up if the user experiences it, the trigger and aftermath for transient issues, and repeated lifecycle events for memory growth. Use signposts or existing logs when they materially improve alignment. Keep the target app visible for rendering measurements and note when background operation is itself the scenario.

Align analysis to the verified workload interval. If the device was offline, the app backgrounded, automation missed the interaction, or the wrong process was captured, discard that run as evidence and correct the reproduction before diagnosing code.
