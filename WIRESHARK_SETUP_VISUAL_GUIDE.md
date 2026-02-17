# Wireshark 设置可视化指南

## 一句话答案

### ✅ 选择：**bridge0**

这是 Docker 虚拟网桥，所有容器流量都在这里。

---

## 你的 Wireshark 界面中的网卡列表

根据你的截图，这是你看到的网卡列表：

```
WI-Fi: en0                    ← 你的 WiFi 网卡（不选）
utun1024                      ← VPN 隧道（不选）
Loopback: lo0                 ← 本地回环（不选）
ap1                           ← Apple 接口（不选）
awdl0                         ← Apple Wireless（不选）
llw0                          ← Link Local（不选）
utun0                         ← VPN 隧道（不选）
utun1                         ← VPN 隧道（不选）
utun2                         ← VPN 隧道（不选）
utun3                         ← VPN 隧道（不选）
anpi0                         ← Apple 接口（不选）
anpi2                         ← Apple 接口（不选）
anpi1                         ← Apple 接口（不选）
Ethernet Adapter (en4): en4   ← 以太网（不选）
Ethernet Adapter (en5): en5   ← 以太网（不选）
Ethernet Adapter (en6): en6   ← 以太网（不选）
Thunderbolt 1: en1            ← Thunderbolt（不选）
Thunderbolt 2: en2            ← Thunderbolt（不选）
Thunderbolt 3: en3            ← Thunderbolt（不选）
USB 10/100/1000 LAN: en7      ← USB 网卡（不选）
Thunderbolt Bridge: bridge0   ← ✅ 选择这个！
gif0                          ← 隧道接口（不选）
stf0                          ← 隧道接口（不选）
```

---

## 为什么选择 bridge0？

### Docker 流量路径

```
┌─────────────────────────────────────────────────────────┐
│                    macOS (你的电脑)                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Docker Desktop (虚拟机)                 │   │
│  │                                                 │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │  bridge0 (虚拟网桥)                       │  │   │
│  │  │  ← 所有 Docker 容器流量都在这里！        │  │   │
│  │  │                                           │  │   │
│  │  │  ┌─────────────────────────────────────┐  │  │   │
│  │  │  │  Docker 网络 (10.0.1.0/24)          │  │  │   │
│  │  │  │  ├─ vpp-master (10.0.1.10)          │  │  │   │
│  │  │  │  ├─ vpp-phase2-simulation (10.0.1.x)│  │  │   │
│  │  │  │  ├─ vpp-vcc (10.0.1.20)             │  │  │   │
│  │  │  │  ├─ vpp-upf (10.0.1.30)             │  │  │   │
│  │  │  │  ├─ vpp-gen (10.0.1.40)             │  │  │   │
│  │  │  │  └─ vpp-analyzer (10.0.1.50)        │  │  │   │
│  │  │  └─────────────────────────────────────┘  │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  其他网卡（en0, en1, en2 等）                          │
│  ← 这些是你的 WiFi、以太网、Thunderbolt 等            │
│  ← 不会看到 Docker 流量                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 在 Wireshark 中选择 bridge0 的步骤

### 步骤 1：找到 bridge0

在你的网卡列表中，向下滚动找到：

```
Thunderbolt Bridge: bridge0   ← 这个！
```

### 步骤 2：点击蓝色按钮

```
[蓝色圆形按钮] Thunderbolt Bridge: bridge0
                ↑
            点击这里开始抓包
```

### 步骤 3：等待抓包开始

Wireshark 会显示：
```
Capturing on "bridge0"
```

### 步骤 4：应用过滤器

在顶部的 Filter 栏输入：

```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 步骤 5：观察流量

你会看到：

```
时间          源地址        目标地址      协议  长度  信息
07:08:26.123  10.0.1.x      10.0.1.10    HTTP  1024  POST /api/v1/devices/sync
07:08:26.125  10.0.1.10     10.0.1.x     HTTP  256   HTTP/1.1 200 OK
07:08:36.234  10.0.1.x      10.0.1.10    HTTP  1024  POST /api/v1/devices/sync
07:08:36.236  10.0.1.10     10.0.1.x     HTTP  256   HTTP/1.1 200 OK
```

---

## 其他网卡的用途

### ❌ 不要选择这些

| 网卡 | 用途 | 为什么不选 |
|------|------|----------|
| en0 (WiFi) | 你的 WiFi 连接 | 会看到所有系统流量，太杂乱 |
| en1-7 | 以太网、Thunderbolt | Docker 流量不在这里 |
| utun0-3 | VPN 隧道 | 与 Docker 无关 |
| lo0 | 本地回环 | 只有本地流量 |
| awdl0 | Apple Wireless | 与 Docker 无关 |
| anpi0-2 | Apple 接口 | 与 Docker 无关 |
| gif0, stf0 | 隧道接口 | 与 Docker 无关 |

---

## 快速参考

### 选择网卡
```
找到: Thunderbolt Bridge: bridge0
点击: 蓝色按钮
```

### 应用过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 预期结果
```
✓ 每 10 秒一次的 HTTP POST 请求
✓ 来自 10.0.1.x (vpp-phase2-simulation)
✓ 目标 10.0.1.10 (vpp-master)
✓ 包含工控协议数据
```

---

## 如果找不到 bridge0？

### 方案 A：用命令行启动

```bash
# 直接用 bridge0 启动 Wireshark
wireshark -i bridge0 &
```

### 方案 B：检查 Docker 是否运行

```bash
# 确认 Docker 正在运行
docker ps | grep vpp-

# 如果没有输出，启动 Docker Desktop
```

### 方案 C：重启 Wireshark

```bash
# 关闭 Wireshark
# 重新打开
wireshark &
```

---

## 完整的抓包流程

### 1. 打开 Wireshark
```bash
wireshark &
```

### 2. 选择 bridge0
- 在接口列表中找到 **Thunderbolt Bridge: bridge0**
- 点击蓝色按钮

### 3. 应用过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 4. 观察流量
- 等待 10 秒
- 你会看到 HTTP POST 请求

### 5. 分析数据包
- 双击数据包
- 展开 **Hypertext Transfer Protocol**
- 查看 JSON 数据

---

## 数据包颜色含义

| 颜色 | 含义 |
|------|------|
| 🟢 绿色 | TCP SYN (连接建立) |
| 🔵 蓝色 | TCP 数据 (HTTP 请求/响应) |
| 🔴 红色 | TCP RST/FIN (连接关闭) |
| ⚫ 黑色 | TCP ACK (确认) |

---

## 预期看到的数据

### HTTP POST 请求（每 10 秒）

```
POST /api/v1/devices/sync HTTP/1.1
Host: vpp-master:8080
Content-Type: application/json

{
  "devices": [
    {
      "id": "gen-001",
      "type": "solar",
      "state": {
        "power_output": 5000.0,
        "efficiency": 0.95
      }
    },
    {
      "id": "storage-001",
      "type": "battery",
      "state": {
        "soc": 0.75,
        "power": 2000.0
      }
    }
  ]
}
```

### HTTP 响应

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "sync_id": "sync-20260217-070826",
  "devices_processed": 3
}
```

---

## 总结

✅ **选择**: Thunderbolt Bridge: bridge0
✅ **过滤器**: tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
✅ **预期**: 每 10 秒一次的 HTTP POST 请求

---

**现在就试试吧！** 选择 bridge0，你会立即看到通信流量。
