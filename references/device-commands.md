# Device & Command Reference (iOS)

Load this file when profiling a **physical iPhone/iPad** and you need the exact
`devicectl` / `xctrace` invocation, or when something about the device/process
does not behave as expected. It captures real pitfalls so you do not have to
re-discover them by trial and error.

## iOS Version & Template Compatibility

| Template | iOS 18 and older | iOS 26 and newer |
|---|---|---|
| `Power Profiler` (power) | ❌ **requires iOS 26** — errors "The Power Profiler instrument requires iOS 26.0" | ✅ |
| `Time Profiler` (time) | ✅ | ✅ |
| `Activity Monitor` (activity) | ✅ | ✅ |
| `Allocations` (alloc) | ✅ | ✅ |
| `Metal System Trace` (metal) | ⚠️ GPU data exports mostly empty headless; needs Instruments GUI | ⚠️ same |

**If the device runs iOS < 26**, do NOT try Power Profiler first. Use the
fallback pair instead:

```bash
# Hot call-trees (which functions burn CPU)
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE" --process "MyApp" --template time --duration 60s

# Per-process CPU load + memory (ms of CPU per second of wall time)
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE" --process "MyApp" --template activity --duration 30s
```

Interpretation: Time Profiler gives **attribution** (hot functions, which thread),
Activity Monitor gives **magnitude** (CPU ms/s; 1000 ms/s ≈ one full core).
Power Profiler's CPU Impact / energy numbers are not available on iOS < 26;
report that limitation honestly instead of inventing energy figures.

## Identifying & Attaching the Correct Process

`xcrun devicectl device info processes` lists **every** process, including app
extensions. A Widget/extension path ends in `.appex/<Name>`; the **main**
executable ends in `<Name>.app/<Name>`:

```text
.../VioRelay.app/PlugIns/VioRelayWidgets.appex/VioRelayWidgets   # widget — skip
.../VioRelay.app/VioRelay                                       # main app — attach here
```

`run_trace.sh --process <Name>` already prefers the `.app/<Name>` main executable.
If you call `xctrace` directly, be explicit:

```bash
PID=$(xcrun devicectl device info processes --device "$DEVICE" \
  | awk '$0 ~ /\/VioRelay\.app\/VioRelay$/ {print $1; exit}')
xcrun xctrace record --device "$DEVICE" --template 'Time Profiler' \
  --time-limit 60s --output /tmp/ios-traces/run.trace --attach "$PID"
```

## Launching with Arguments (Tier 1 reproduction)

Prefer one-shot launch + record over launch-then-attach (the PID changes on every
launch, so attach requires re-querying the PID):

```bash
# One-shot: launch with args and record in a single command
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE" --bundle-id "com.example.MyApp" \
  --template time --duration 60s -- --scenario myState

# Equivalent direct xctrace
xcrun xctrace record --device "$DEVICE" --template 'Time Profiler' --time-limit 60s \
  --output /tmp/ios-traces/run.trace --launch -- com.example.MyApp --scenario myState
```

Any extra arguments after `--` are passed to the app. To terminate and relaunch
cleanly between runs:

```bash
xcrun devicectl device process terminate --device "$DEVICE" --pid "$PID" --kill
xcrun devicectl device process launch --device "$DEVICE" --bundle-id com.example.MyApp
```

(`devicectl process terminate` takes `--pid`, NOT `--bundle-id`.)

## Screenshots & UI State Verification

`xcrun devicectl device screenshot` is **not** a valid subcommand. Capture the
screen from the host with a screenshot tool (e.g. QuickTime / `screencapture` of
the mirrored window), or use `xcrun simctl io booted screenshot` on a simulator.
For verifying app state on a physical device, prefer reading its logs or files.

## Reading Device Logs

There is no `timeout` command on stock macOS. Use a background job with a kill:

```bash
xcrun devicectl device process launch --device "$DEVICE" --terminate-existing \
  --console com.example.MyApp > /tmp/console.log 2>&1 &
CONSOLE_PID=$!
sleep 8
kill "$CONSOLE_PID" 2>/dev/null
cat /tmp/console.log
```

## Pulling Files From the App Container

App-side diagnostics/logs written to `Documents/` are retrievable via
`devicectl device copy`:

```bash
xcrun devicectl device copy from \
  --device "$DEVICE" \
  --source "Documents/Diagnostics" \
  --destination /tmp/app-diagnostics \
  --domain-type appDataContainer \
  --domain "com.example.MyApp"
```

## Install / Rebuild Cycle

```bash
xcodebuild -project YourApp.xcodeproj -scheme YourApp -configuration Debug \
  -destination "id=$DEVICE" -derivedDataPath .build_ios -allowProvisioningUpdates build

xcrun devicectl device install app --device "$DEVICE" \
  .build_ios/Build/Products/Debug-iphoneos/YourApp.app
```

## Adapting Scripts (allowed, with rules)

The bundled scripts are meant to be adapted for specific tasks. Rules:

1. **Never edit files inside the skill directory** (`SKILL_DIR/scripts/…`).
2. **Copy to a temp directory first, then modify the copy**:
   ```bash
   mkdir -p /tmp/my-trace-tools
   cp "$SKILL_DIR"/scripts/*.py /tmp/my-trace-tools/
   # edit /tmp/my-trace-tools/top_time.py, then run:
   python3 /tmp/my-trace-tools/top_time.py ...
   ```
3. Keep the original scripts untouched so every user/run sees the same baseline.
