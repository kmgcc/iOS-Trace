#!/usr/bin/env bash
# iOS-Trace Automation Runner
# Headless Instruments profiling for iOS physical devices and simulators.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="/tmp/ios-traces"
TEMPLATE="Power Profiler"
DURATION="60s"
DEVICE=""
BUNDLE_ID=""
ATTACH_PID=""
PROCESS_NAME=""
LABEL=""
AUTO_ANALYZE=1
EXTRA_LAUNCH_ARGS=()

# Every xctrace recording writes several-GB transient kernel traces (instruments*.ktrace)
# and an Instruments CLI cache into the per-user system temp folder. Remove only that
# user's own transient artifacts; the recorded .trace bundle in OUTPUT_DIR is untouched.
cleanup_recording_artifacts() {
  local TMP_ROOT TMP_CACHE_DIR
  TMP_ROOT="${TMPDIR:-/tmp}"
  find "$TMP_ROOT" -maxdepth 1 -type f -name 'instruments*.ktrace' -delete 2>/dev/null || true
  TMP_CACHE_DIR="$(dirname "$TMP_ROOT")/C/com.apple.dt.InstrumentsCLI"
  case "$TMP_CACHE_DIR" in
    /var/folders/*|/private/var/folders/*|/tmp/*)
      rm -rf -- "$TMP_CACHE_DIR" 2>/dev/null || true ;;
  esac
}
trap cleanup_recording_artifacts EXIT

usage() {
  cat <<EOF
iOS-Trace Automated Runner

Usage:
  $(basename "$0") [options]

Target Device:
  -d, --device <UDID|Name>    Physical iPhone/iPad UDID or Simulator name/UUID.
                              Run 'xcrun xctrace list devices' to list available devices.
                              If omitted, the script checks for the first connected device.

Target Application (Required: choose one):
  -b, --bundle-id <id>        Bundle identifier to launch (e.g. 'com.example.MyApp').
  -a, --attach <PID>          PID of already running app on device.
  -p, --process <name>        Process name to locate on device via devicectl and attach.

Profiling Options:
  -t, --template <name>       Instruments template. Supports shorthands:
                              power       -> 'Power Profiler' (default)
                              time        -> 'Time Profiler'
                              alloc       -> 'Allocations'
                              leaks       -> 'Leaks'
                              metal       -> 'Metal System Trace'
                              hitches     -> 'Animation Hitches'
                              swiftui     -> 'SwiftUI'
                              concurrency -> 'Swift Concurrency'
                              launch      -> 'App Launch'
                              network     -> 'Network'
                              counters    -> 'CPU Counters'
                              Or specify any exact Instruments template name.
  -l, --duration <time>       Recording duration limit (default: 60s, e.g. 30s, 120s)
  -o, --output-dir <path>     Directory to save .trace and exported .xml files (default: /tmp/ios-traces)
  --label <text>              Custom label for run output (default: bundle ID or process name)
  --no-analyze                Skip automatic XML export and Python analysis

Examples:
  # 1. Profile running iOS app on physical device for 60s with Power Profiler:
  $(basename "$0") --device "00008140-000C54310E82801C" --process "MyApp" --template power --duration 60s

  # 2. Launch app cold on device under Power Profiler:
  $(basename "$0") --device "00008140-000C54310E82801C" --bundle-id "com.example.MyApp" --template power

  # 3. Profile UI animation hitches during scrolling on iOS Simulator:
  $(basename "$0") --device "iPhone 17 Pro Max Simulator" --process "MyApp" --template hitches --duration 30s
EOF
  exit 0
}

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--device)
      DEVICE="$2"
      shift 2
      ;;
    -b|--bundle-id)
      BUNDLE_ID="$2"
      shift 2
      ;;
    -a|--attach)
      ATTACH_PID="$2"
      shift 2
      ;;
    -p|--process)
      PROCESS_NAME="$2"
      shift 2
      ;;
    -t|--template)
      case "$2" in
        power)       TEMPLATE="Power Profiler" ;;
        time)        TEMPLATE="Time Profiler" ;;
        alloc)       TEMPLATE="Allocations" ;;
        leaks)       TEMPLATE="Leaks" ;;
        metal)       TEMPLATE="Metal System Trace" ;;
        hitches)     TEMPLATE="Animation Hitches" ;;
        swiftui)     TEMPLATE="SwiftUI" ;;
        concurrency) TEMPLATE="Swift Concurrency" ;;
        launch)      TEMPLATE="App Launch" ;;
        network)     TEMPLATE="Network" ;;
        counters)    TEMPLATE="CPU Counters" ;;
        *)           TEMPLATE="$2" ;;
      esac
      shift 2
      ;;
    -l|--duration)
      DURATION="$2"
      shift 2
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
      shift 2
      ;;
    --no-analyze)
      AUTO_ANALYZE=0
      shift
      ;;
    -h|--help)
      usage
      ;;
    --)
      shift
      EXTRA_LAUNCH_ARGS=("$@")
      break
      ;;
    *)
      echo "[ERROR] Unknown option: $1" >&2
      usage
      ;;
  esac
done

# Check prerequisites
if ! command -v xcrun &>/dev/null; then
  echo "[ERROR] 'xcrun' not found. Install Xcode Command Line Tools via: xcode-select --install" >&2
  exit 1
fi

if ! xcrun xctrace version &>/dev/null; then
  echo "[ERROR] 'xctrace' is not functional. Ensure Xcode is active." >&2
  exit 1
fi

# Device discovery if not provided
if [[ -z "$DEVICE" ]]; then
  echo "[INFO] No device specified. Querying available devices..."
  # Prefer physical iPhone/iPad over other connected device types (e.g. Apple Watch)
  DETECTED_DEVICE=$(xcrun xctrace list devices 2>&1 | awk '/== Devices ==/{flag=1; next} /== Devices Offline ==/{flag=0} flag && !/Mac/ && /iPhone|iPad/ && NF {print; exit}')
  if [[ -z "$DETECTED_DEVICE" ]]; then
    DETECTED_DEVICE=$(xcrun xctrace list devices 2>&1 | awk '/== Devices ==/{flag=1; next} /== Devices Offline ==/{flag=0} flag && !/Mac/ && NF {print; exit}')
  fi
  if [[ -n "$DETECTED_DEVICE" ]]; then
    # Extract device UDID inside parentheses
    DEVICE=$(echo "$DETECTED_DEVICE" | sed -E 's/.*\(([A-Fa-f0-9-]+)\).*/\1/')
    echo "[INFO] Auto-detected connected physical device: $DETECTED_DEVICE (UDID: $DEVICE)"
  else
    echo "[ERROR] No connected physical iOS device detected." >&2
    echo "Please specify a device via --device <UDID|Name>. Run 'xcrun xctrace list devices' to list devices." >&2
    exit 1
  fi
fi

if [[ -z "$BUNDLE_ID" && -z "$ATTACH_PID" && -z "$PROCESS_NAME" ]]; then
  echo "[ERROR] You must specify a target: --bundle-id <id>, --attach <PID>, or --process <name>." >&2
  echo "Run '$(basename "$0") --help' for usage." >&2
  exit 1
fi

# Resolve process name to PID via devicectl if process name was specified
if [[ -n "$PROCESS_NAME" && -z "$ATTACH_PID" ]]; then
  echo "[INFO] Querying processes on device '$DEVICE' for '$PROCESS_NAME'..."
  if command -v xcrun &>/dev/null && xcrun devicectl help &>/dev/null; then
    FOUND_PID=$(xcrun devicectl device info processes --device "$DEVICE" 2>/dev/null | awk -v name="$PROCESS_NAME" '$0 ~ name {print $1; exit}' || true)
    if [[ -n "$FOUND_PID" && "$FOUND_PID" =~ ^[0-9]+$ ]]; then
      ATTACH_PID="$FOUND_PID"
      echo "[INFO] Found PID $ATTACH_PID for process '$PROCESS_NAME'."
    fi
  fi

  if [[ -z "$ATTACH_PID" ]]; then
    echo "[WARN] Could not automatically resolve PID for '$PROCESS_NAME'. Will attempt process attach by name."
  fi
fi

mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
SAFE_TEMPLATE=$(echo "$TEMPLATE" | tr -d ' ' | tr '[:upper:]' '[:lower:]')

if [[ -z "$LABEL" ]]; then
  TARGET_TAG="${BUNDLE_ID:-${PROCESS_NAME:-pid$ATTACH_PID}}"
  LABEL="${TARGET_TAG}-${SAFE_TEMPLATE}"
fi

TRACE_FILE="${OUTPUT_DIR}/${LABEL}-${TIMESTAMP}.trace"

echo "========================================================================"
echo " iOS-Trace Profiling Run"
echo "========================================================================"
echo "  Device:    $DEVICE"
echo "  Template:  $TEMPLATE"
echo "  Duration:  $DURATION"
echo "  Target:    ${BUNDLE_ID:+Launch Bundle '$BUNDLE_ID'}${ATTACH_PID:+Attach PID '$ATTACH_PID'}${PROCESS_NAME:+Process '$PROCESS_NAME'}"
echo "  Output:    $TRACE_FILE"
echo "========================================================================"

# Execution
if [[ -n "$BUNDLE_ID" ]]; then
  xcrun xctrace record \
    --device "$DEVICE" \
    --template "$TEMPLATE" \
    --time-limit "$DURATION" \
    --output "$TRACE_FILE" \
    --launch -- "$BUNDLE_ID" ${EXTRA_LAUNCH_ARGS[@]+"${EXTRA_LAUNCH_ARGS[@]}"}
elif [[ -n "$ATTACH_PID" ]]; then
  xcrun xctrace record \
    --device "$DEVICE" \
    --template "$TEMPLATE" \
    --time-limit "$DURATION" \
    --output "$TRACE_FILE" \
    --attach "$ATTACH_PID"
else
  xcrun xctrace record \
    --device "$DEVICE" \
    --template "$TEMPLATE" \
    --time-limit "$DURATION" \
    --output "$TRACE_FILE" \
    --attach "$PROCESS_NAME"
fi

echo ""
echo "[INFO] Trace recorded successfully: $TRACE_FILE"

# Post-processing / analysis
if [[ $AUTO_ANALYZE -eq 1 ]]; then
  if [[ "$TEMPLATE" == "Power Profiler" ]]; then
    XML_FILE="${OUTPUT_DIR}/${LABEL}-${TIMESTAMP}-power.xml"
    echo "[INFO] Exporting ProcessSubsystemPowerImpact table to XML..."
    xcrun xctrace export \
      --input "$TRACE_FILE" \
      --xpath "/trace-toc/run[@number='1']/data/table[@schema='ProcessSubsystemPowerImpact']" \
      > "$XML_FILE" 2>/dev/null || {
        echo "[WARN] ProcessSubsystemPowerImpact table not present or export returned non-zero."
      }

    if [[ -f "$XML_FILE" && -s "$XML_FILE" ]]; then
      echo "[INFO] Parsing Power Impact metrics..."
      python3 "${SCRIPT_DIR}/parse_power.py" "$XML_FILE" "$LABEL"
    fi

  elif [[ "$TEMPLATE" == "Allocations" ]]; then
    XML_FILE="${OUTPUT_DIR}/${LABEL}-${TIMESTAMP}-alloc.xml"
    echo "[INFO] Exporting all-allocations-summary table to XML..."
    xcrun xctrace export \
      --input "$TRACE_FILE" \
      --xpath "/trace-toc/run[@number='1']/data/table[@schema='all-allocations-summary']" \
      > "$XML_FILE" 2>/dev/null || {
        echo "[WARN] all-allocations-summary table not present or export returned non-zero."
      }

    DURATION_SEC=$(echo "$DURATION" | sed 's/[^0-9]//g')
    if [[ -z "$DURATION_SEC" ]]; then DURATION_SEC=60; fi

    if [[ -f "$XML_FILE" && -s "$XML_FILE" ]]; then
      echo "[INFO] Parsing allocation categories..."
      python3 "${SCRIPT_DIR}/top_categories.py" "$XML_FILE" "$DURATION_SEC" 10.0
    fi
  fi
fi

echo "[INFO] iOS profiling session complete."
