# iOS-Trace

[English](README.md) | [中文](README_zh.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Platform](https://img.shields.io/badge/Platform-iOS_15%2B_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![Python](https://img.shields.io/badge/Python-3.8%2B_(Zero_Deps)-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 如需对 macOS 桌面原生应用进行性能分析，请参考 [macOS-Trace](https://github.com/kmgcc/macOS-Trace)。

基于 `xctrace` 与 Xcode Instruments 的 **iOS 及 iPadOS 应用**（真机与模拟器）自主闭环性能优化引擎。

专为 **AI 编码 Agent**（Claude Code、OpenAI Codex、Cursor、Google Antigravity、GitHub Copilot）及 **iOS 移动端研发工程师** 设计。核心目标是**彻底摆脱繁琐的 Instruments 图形界面**。用户只需下达一句话指令，Agent 即可自主完成：前期目标对齐（弹窗问询）、无头采样诊断、定位性能瓶颈、精准修改源码、重新量化测试复盘，并在未达标时自主迭代，直至满足性能目标。

---

## 自主优化闭环流程

```text
+-------------------------------------------------------------------------+
|                         自主性能优化闭环流程                             |
|                                                                         |
|  1. 目标对齐 ──────> 2. 无头采样诊断 ─────> 3. 精准代码优化              |
|         ^                                                 │             |
|         │                                                 ▼             |
|         └────── 未达标则开启下一轮迭代 <─── 4. 复盘量化重测              |
+-------------------------------------------------------------------------+
```

1. **目标对齐（Upfront Questionnaire）**：Agent 在动手前先通过交互式问询组件（或直接在对话中）向用户确认具体性能指标期望与推荐建议值。
2. **无头采样诊断**：自动化采集静置基线与业务负载样本，精准定位热点调用栈、瞬时内存尖峰或射频唤醒消耗。
3. **精准代码优化**：Agent 根据诊断结果直接在移动端源码中实施针对性修复。
4. **复盘量化重测**：在完全一致的设备环境下自动化重新采样，生成 Before vs After 差值对比。
5. **决策门禁（Gate）**：指标达标则输出最终复盘报告并交付；未达标则自动锁定次级瓶颈并开启下一轮迭代循环。

---

## 优化前目标对齐（问询协议与建议值）

在采集 Trace 或修改代码前，Agent 必须先与用户对齐优化目标与验收标准：

- **交互组件调用**：若 Agent 平台提供交互式问询组件（如 `ask_question`、选项卡或弹窗），优先调用组件渲染选项；若无此类工具，则在对话中以结构化选项向用户提问。
- **推荐参考指标预设**：
  - **电池与 CPU 负载**：
    - *静置基线目标*：指令吞吐率 < 15 M/s，CPU 能耗指数 < 0.3。
    - *业务活跃态目标*：指令吞吐率 < 80 M/s（或当前 CPU 整体下降 30% - 50%）。
  - **内存与 Jetsam 阈值**：
    - *常驻内存上限（Resident RAM）*：轻量工具类 < 150 MB，富媒体/复杂交互类 < 300 MB。
    - *内存分配速率*：稳态交互下 < 400 events/sec。
    - *内存泄漏*：严格 0 持续泄漏。
  - **UI 流畅度与掉帧**：
    - *顿挫比（Hitch Ratio）*：< 5.0 ms/s（良好），< 1.0 ms/s（丝滑 / 120Hz ProMotion 极佳）。
  - **冷启动耗时**：
    - *首帧渲染耗时*：< 400 ms（极佳），< 800 ms（良好）。
  - **网络与基带射频开销**：
    - *射频尾部能耗（Radio Tail）*：将周期性独立零散请求合并为单次批量传输，减少基带高功耗唤醒时长。

---

## 前置条件与适用范围

在部署或调用本 Skill 前，请仔细阅读以下系统要求与约束：

### 支持的目标类型
- **仅支持 iOS 与 iPadOS 应用**：专门针对运行在通过 USB 或局域网连接的物理 iPhone/iPad 真机，以及本地运行的 iOS 模拟器。
- **macOS 桌面软件用户**：请前往使用专为 macOS 桌面端优化的 [macOS-Trace](https://github.com/kmgcc/macOS-Trace)。

### 宿主系统与工具链要求
- **宿主系统**：macOS 12.0 (Monterey) 或更高版本，必须安装完整 Xcode 或包含 `xcrun xctrace` 的 Xcode 命令行工具。
- **真机连接准备**：
  - 物理 iPhone 或 iPad 必须处于**解锁状态**，且已在弹窗中选择“信任此电脑”。
  - 运行 `xcrun xctrace list devices` 时，目标设备必须出现在 `== Devices ==` 列表中，**绝不能处于 `== Devices Offline ==` 离线状态**。
  - 建议将真机的“自动锁定”设置为“永不”，或在录制期间保持屏幕常亮，防止 iOS 锁屏导致前台应用转入后台冻结或挂起。
- **Python 环境**：Mac 宿主机需安装 Python 3.8+（系统自带）。所有分析脚本均**仅依赖标准库**（`re`、`sys`、`os`、`xml.etree.ElementTree`、`collections`），零第三方 pip 依赖。
- **签名权限要求**：Debug 构建或包含 `com.apple.security.get-task-allow` 签名的开发版应用支持通过 `--attach <PID>` 附加采样。

---

## AI Agent 安装与集成指南

本节面向 AI Agent 说明如何在移动端项目中引入并自主执行 `iOS-Trace`。

### 1. 技能目录识别规范

当 Agent 需要向当前仓库引入本 Skill 时，应按以下优先级探测项目中已有的技能目录：

```bash
# Agent Skills 目录优先级探测顺序：
# 1. 开放标准目录：  .agents/skills/
# 2. OpenAI Codex：  .codex/skills/
# 3. Cursor：        .cursor/skills/
# 4. Claude Code：   .claude/skills/
```

若当前仓库不存在上述目录，优先创建标准目录 `.agents/skills/`。

### 2. Agent 安装命令

```bash
# 推荐：安装到项目标准 Agent Skills 目录
mkdir -p .agents/skills
git clone https://github.com/kmgcc/iOS-Trace.git .agents/skills/ios-trace

# 方式二：作为 Git Submodule 引入（便于版本跟踪）
git submodule add https://github.com/kmgcc/iOS-Trace.git .agents/skills/ios-trace

# 方式三：安装到 Codex 专用目录
mkdir -p .codex/skills
git clone https://github.com/kmgcc/iOS-Trace.git .codex/skills/ios-trace

# 方式四：用户级全局安装（所有工作区通用）
mkdir -p ~/.agents/skills
git clone https://github.com/kmgcc/iOS-Trace.git ~/.agents/skills/ios-trace
```

### 3. 完整闭环优化运行示例

```bash
SKILL_DIR=".agents/skills/ios-trace"

# 1. 自动获取已连接的首台物理真机 UDID
DEVICE_UDID=$(xcrun xctrace list devices 2>&1 | awk '/== Devices ==/{flag=1; next} /== Devices Offline ==/{flag=0} flag && !/Mac/ && NF {print; exit}' | sed -E 's/.*\(([A-Fa-f0-9-]+)\).*/\1/')

# 2. 采集 60 秒静置基线（应用在前台，无业务负载）
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --bundle-id "com.example.MyApp" --template power --duration 60s --label "01-baseline"

# 3. 在真机上触发目标功能，采集 60 秒优化前高负载态
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --process "MyApp" --template power --duration 60s --label "02-pre-opt"

# 4. 实施源码修改、重新编译并安装到设备后，采集优化后高负载态
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --process "MyApp" --template power --duration 60s --label "03-post-opt"

# 5. 执行多轮客观差值对比
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"静置基线" \
  /tmp/ios-traces/02-pre-opt-power.xml:"优化前业务态" \
  /tmp/ios-traces/03-post-opt-power.xml:"优化后业务态"
```

---

## 快速上手示例

运行差值对比脚本将输出如下客观量化报告（含移动端独有的网络收发统计）：

```text
Scenario                 Sec  CPU Avg  CPU Max  Display  GPU Avg  Total Instr    Instr M/s   WiFi Tx/Rx
=========================================================================================================
1. 静置基线               60     0.12     0.60     0.05     0.00        0.85G         14.2   0.0/0.0MB
2. 业务负载               60     2.40     4.80     1.10     1.80       15.60G        260.0  14.2/1.8MB
---------------------------------------------------------------------------------------------------------
Differential vs Baseline [1. 静置基线]:
  2. 业务负载               +245.8 M/s instructions, CPU Avg Delta +2.28, WiFi Tx Delta +14.20MB
```

---

## 内置工具与脚本

所有脚本要求 Python 3.8+，**仅使用标准库**（`re`、`sys`、`os`、`xml.etree.ElementTree`、`collections`），零任何第三方依赖。

| 脚本 | 功能说明 | 常用命令示例 |
| :--- | :--- | :--- |
| `scripts/run_trace.sh` | 移动端终端入口：支持真机探测、启动 App、XML 导出与解析 | `./scripts/run_trace.sh --bundle-id com.example.MyApp --template power` |
| `scripts/compare_elements.py` | 多场景对比表生成，包含 CPU、GPU 与 WiFi/蜂窝网络吞吐差值 | `python3 scripts/compare_elements.py base.xml active.xml` |
| `scripts/parse_power.py` | 单次 Power Profiler 导出的功耗、GPU、指令速率及网络数据深度解析 | `python3 scripts/parse_power.py run-power.xml "测试场景"` |
| `scripts/top_categories.py` | Allocations 堆内存高频分配速率与常驻/瞬时内存分析 | `python3 scripts/top_categories.py alloc.xml 60 10.0` |

---

## 常用 Instruments 模板

| 模板名称 | 简写参数 | 核心量化指标与适用场景 |
| :--- | :--- | :--- |
| `Power Profiler` | `power` | 每秒指令吞吐（M/s）、CPU/GPU/Display/WiFi/蜂窝能耗 Impact。整机发热、掉电排查与 A/B 对比首选。 |
| `Time Profiler` | `time` | 各线程 CPU 权重占比、调用栈热点（Call-tree）、主线程卡顿耗时。 |
| `Animation Hitches` | `hitches` | ProMotion 120Hz 滚动掉帧、卡顿时长（ms）、Hitch Ratio（ms/s）。区分 Commit 与 Render 延迟。 |
| `SwiftUI` | `swiftui` | View Body 求值次数、State 变更计数、属性修改频次。定位级联重算。 |
| `Allocations` | `alloc` | 堆内存分配事件速率、瞬时内存波峰、分类事件频次（`all-allocations-summary`）。 |
| `Leaks` | `leaks` | 失去父级引用的孤立内存泄漏、循环引用（Retain Cycles）。 |
| `Network` | `network` | TCP/UDP 连接延迟、DNS 耗时、收发包体积、射频休眠状态。 |
| `App Launch` | `launch` | 首帧渲染耗时、`dyld` 动态库加载时间、静态初始化耗时。应用冷启动优化。 |
| `Metal System Trace` | `metal` | GPU Encoder 执行耗时、片元/顶点着色器负载、帧边界渲染延迟。 |

---

## 移动端核心子系统调优实战

完整实操规则详见 [SKILL.md](SKILL.md)：

1. **电池与蜂窝/WiFi 射频管理**：
   - 警惕射频尾随功耗（Radio Tails）：移动端网络芯片从休眠唤醒到高能耗状态后，传输完毕仍会维持数秒高功耗状态。严禁每隔几秒发起碎片化网络 Ping，应将请求聚合（Batching）后突发传输。
2. **ProMotion 120Hz 高刷屏与卡顿分类**：
   - 严格遵循 8.33ms 单帧预算：精准区分 Commit 阶段超时（主线程布局或视图树构造过慢）与 Render 阶段超时（GPU 图层阴影/离屏渲染过载）。
3. **图像降采样与 iOS Jetsam 内存防线**：
   - iOS 拥有严格的 Jetsam 物理内存红线（超出即被系统强杀）。高清原始图直接解码为 `UIImage` 会瞬时暴涨内存，必须使用 `CGImageSourceCreateThumbnailAtIndex` 做解码期降采样。
4. **实时音频 Session 与后台执行**：
   - 音频实时回调内严禁堆内存分配与加锁；正确处理音频路由中断（Interruption）与后台场景切换。

---

## 开源协议

基于 [MIT License](LICENSE) 开源。
