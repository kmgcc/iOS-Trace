# Mobile Subsystem Optimization Notes (iOS)

Load this file when the profile attributes a bottleneck to a specific subsystem
(battery/radio, ProMotion displays, media & large-asset decoding, or real-time
audio). These are battle-tested optimization patterns for iOS.

## Battery & Radio Energy Management

- **Cellular & WiFi radio tails**: Opening a network socket transitions the cellular baseband or WiFi chip from low-power sleep to high-power active state, maintaining high power consumption for several seconds after the transfer finishes (radio tail). Batch network requests into unified bursts rather than firing periodic independent pings every few seconds.
- **Verification**: Run `Power Profiler` and inspect the `WiFi Tx/Rx` and `Network Impact` metrics in `scripts/parse_power.py`.

## ProMotion 120Hz Displays and Hitches

- **Frame budget**: On ProMotion devices (iPhone Pro models), the display refresh interval is 8.33ms (120Hz). Exceeding 8.33ms on either the main thread (view preparation and layout) or render server (CoreAnimation commit) drops frames.
- **Hitches taxonomy**:
  - *Commit Hitches*: Main thread took too long to build view hierarchy or compute geometry before committing to render server.
  - *Render Hitches*: GPU took too long rendering layers (complex shadows, blur effects, offscreen passes).
- **Diagnosis**: Use `Animation Hitches` with `--duration 30s` during UI interactions (scrolling, transitions, gestures).

## Media & Large-Asset Decoding and Memory Spikes

- **Memory spikes on iOS**: iOS jetsam kills background or foreground apps exceeding strict memory ceilings (often ~1.5GB to 2GB on mobile). Materializing large assets at full resolution inflates the heap: decoding raw photos or big bitmaps into `UIImage` costs 4 bytes per pixel uncompressed, decoding video frames into pixel buffers at source resolution is far larger, and loading whole PDF pages or documents into memory is equally wasteful.
- **Decode at display size**: Downsample images at decode time using `CGImageSourceCreateThumbnailAtIndex` with `kCGImageSourceThumbnailMaxPixelSize`, decode video frames at playback resolution, render PDF pages on demand, and stream/parse large documents incrementally instead of buffering them whole.

## Real-Time Audio & Background Execution

- **Audio Session interruptions**: Real-time audio rendering callbacks running on `AVAudioEngine` or RemoteIO unit must never perform heap allocation or file I/O.
- **Background Mode**: If testing background audio or streaming, verify process behavior when transitions to background state occur (`UIApplication.didEnterBackgroundNotification`).
