# Mobile Subsystem Optimization Notes (iOS)

Load this file when the profile attributes a bottleneck to a specific subsystem
(battery/radio, ProMotion displays, images/memory, or real-time audio). These are
battle-tested optimization patterns for iOS.

## Battery & Radio Energy Management

- **Cellular & WiFi radio tails**: Opening a network socket transitions the cellular baseband or WiFi chip from low-power sleep to high-power active state, maintaining high power consumption for several seconds after the transfer finishes (radio tail). Batch network requests into unified bursts rather than firing periodic independent pings every few seconds.
- **Verification**: Run `Power Profiler` and inspect the `WiFi Tx/Rx` and `Network Impact` metrics in `scripts/parse_power.py`.

## ProMotion 120Hz Displays and Hitches

- **Frame budget**: On ProMotion devices (iPhone Pro models), the display refresh interval is 8.33ms (120Hz). Exceeding 8.33ms on either the main thread (view preparation and layout) or render server (CoreAnimation commit) drops frames.
- **Hitches taxonomy**:
  - *Commit Hitches*: Main thread took too long to build view hierarchy or compute geometry before committing to render server.
  - *Render Hitches*: GPU took too long rendering layers (complex shadows, blur effects, offscreen passes).
- **Diagnosis**: Use `Animation Hitches` with `--duration 30s` during scrolling interactions.

## Image Downsampling and Low-Memory Warnings

- **Memory spikes on iOS**: iOS jetsam kills background or foreground apps exceeding strict memory ceilings (often ~1.5GB to 2GB on mobile). Decoding raw photos or large bitmaps directly into `UIImage` inflates the heap by 4 bytes per pixel uncompressed.
- **Downsampling**: Always downsample images at decode time using `CGImageSourceCreateThumbnailAtIndex` with `kCGImageSourceThumbnailMaxPixelSize`.

## Real-Time Audio & Background Execution

- **Audio Session interruptions**: Real-time audio rendering callbacks running on `AVAudioEngine` or RemoteIO unit must never perform heap allocation or file I/O.
- **Background Mode**: If testing background audio or streaming, verify process behavior when transitions to background state occur (`UIApplication.didEnterBackgroundNotification`).
