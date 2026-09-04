# iOS-Trace

[English](README.md) | [中文](README_zh.md)

[![Agent Skills Open Standard](https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet.svg)](https://agentskills.io)
[![Platform](https://img.shields.io/badge/Platform-iOS_15%2B_%2F_iPadOS-black.svg)](https://developer.apple.com/ios/)
[![Tooling](https://img.shields.io/badge/Xcode-Instruments_%2F_xctrace-007AFF.svg)](https://developer.apple.com/xcode/)
[![Python](https://img.shields.io/badge/Python-3.8%2B_(Zero_Deps)-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 如需对 macOS 桌面原生应用进行性能分析，请参考 [macOS-Trace](https://github.com/kmgcc/macOS-Trace)。

基于 `xctrace` 与 Xcode Instruments 的 **iOS 及 iPadOS 应用**（真机与模拟器）无头（Headless）性能诊断与客观 A/B 差值量化工具链。

专为 **AI 编码 Agent**（Claude Code、OpenAI Codex、Cursor、Google Antigravity、GitHub Copilot）及 **iOS 移动端研发工程师** 设计。无需开启 Instruments 图形界面，即可在终端或流水线中自动化采集真机 Trace、提取底层数据表并输出量化报告。

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

### 3. Agent 自主执行协议（5 步闭环）

当 Agent 接到“分析移动端发热/掉电/卡顿”或“验证 iOS 性能优化”的任务时，执行以下 5 步闭环：

```text
第 1 步：探测并校验真机物理连接
   │    运行 xcrun xctrace list devices 确保设备在线且屏幕解锁。
   ▼
第 2 步：采集移动端静置基线（Baseline）
   │    保持屏幕常亮、应用位于前台、被测业务暂停，录制 60 秒作为对照。
   ▼
第 3 步：激活被测业务并采集高负载样本
   │    触发被测音频/网络传输/复杂动效，录制 60 秒作为测试样本。
   ▼
第 4 步：执行多维度差值量化对比
   │    运行 scripts/compare_elements.py 提取并计算：
   │    净开销 Delta = Active - Baseline（含指令增量与网络吞吐）。
   ▼
第 5 步：向用户交付结构化量化结论
        输出多场景横向对比表并说明电池能耗与 CPU 净增量。
```

#### 标准命令序列

```bash
SKILL_DIR=".agents/skills/ios-trace"

# 1. 自动获取已连接的首台物理真机 UDID
DEVICE_UDID=$(xcrun xctrace list devices 2>&1 | awk '/== Devices ==/{flag=1; next} /== Devices Offline ==/{flag=0} flag && !/Mac/ && NF {print; exit}' | sed -E 's/.*\(([A-Fa-f0-9-]+)\).*/\1/')

# 2. 采集 60 秒静置基线（应用在前台，无业务负载）
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --bundle-id "com.example.MyApp" --template power --duration 60s --label "01-baseline"

# 3. 在真机上触发目标功能，采集 60 秒业务负载态
"$SKILL_DIR/scripts/run_trace.sh" --device "$DEVICE_UDID" --process "MyApp" --template power --duration 60s --label "02-active"

# 4. 执行差值对比
python3 "$SKILL_DIR/scripts/compare_elements.py" \
  /tmp/ios-traces/01-baseline-power.xml:"1. 静置基线" \
  /tmp/ios-traces/02-active-power.xml:"2. 业务负载"
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
