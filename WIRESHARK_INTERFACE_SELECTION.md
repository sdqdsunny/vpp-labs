# Wireshark 网卡选择指南

## 你应该选择哪张网卡？

### ✅ 推荐选择：**bridge0**

这是 Docker Desktop 在 macOS 上创建的虚拟网桥，所有 Docker 容器的流量都通过这个接口。

---

## 为什么选择 bridge0？

### Docker 网络架构

```
macOS 主机
    ↓
Docker Desktop VM (Linux)
    ↓
bridge0 (虚拟网桥)
    ↓
Docker 容器网络 (10.0.1.0/24)
    ├─ vpp-master (10.0.1.10)
    ├─ vpp-phase2-simulation (10.0.1.x)
    ├─ vpp-vcc (10.0.1.20)
    ├─ vpp-upf (10.0.1.30)
    ├─ vpp-gen (10.0.1.40)
    └─ vpp-analyzer (10.0.1.50)
```

### 为什么 bridge0 是最佳选择

1. **包含所有 Docker 流量** - 所有容器间的通信都经过这个接口
2. **隔离性好** - 只看到 Docker 网络流量，不会被其他系统流量干扰
3. **性能好** - 虚拟网桥效率高，不会有额外开销
4. **易于过滤** - 可以清晰地看到 10.0.1.0/24 子网的所有流量

---

## 在 Wireshark 中选择 bridge0

### 步骤 1：打开 Wireshark

```bash
wireshark &
```

### 步骤 2：选择网卡

在 Wireshark 的主界面中：

1. 点击 **Capture → Interfaces**
2. 在接口列表中找到 **bridge0**
3. 点击 **bridge0** 前面的蓝色按钮开始抓包

**或者直接点击主界面中的 bridge0**

### 步骤 3：应用过滤器

在 Filter 栏输入：

```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 步骤 4：观察流量

你会看到每 10 秒一次的 HTTP POST 请求

---

## 其他网卡的用途

| 网卡 | 用途 | 是否选择 |
|------|------|--------|
| **bridge0** | Docker 虚拟网桥 | ✅ **选择这个** |
| en0 | 主网络接口（WiFi/有线） | ❌ 会看到所有系统流量 |
| en1, en2, en3 | 其他网络接口 | ❌ 不需要 |
| lo0 | 本地回环 | ❌ 只有本地流量 |
| utun0-3 | VPN 隧道 | ❌ 不需要 |
| awdl0 | Apple Wireless Direct Link | ❌ 不需要 |
| anpi0-2 | Apple Network Processor Interface | ❌ 不需要 |

---

## 快速步骤（3 步）

### 1️⃣ 打开 Wireshark
```bash
wireshark &
```

### 2️⃣ 选择 bridge0
- 在接口列表中找到 **bridge0**
- 点击蓝色按钮开始抓包

### 3️⃣ 应用过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

**完成！** 你会看到每 10 秒一次的 HTTP POST 请求

---

## 预期看到的流量

### 数据包示例

```
时间: 07:08:26.123456
源: 10.0.1.x (vpp-phase2-simulation)
目标: 10.0.1.10 (vpp-master)
协议: HTTP
方法: POST
路径: /api/v1/devices/sync
大小: 1024 字节

↓

时间: 07:08:26.125000
源: 10.0.1.10 (vpp-master)
目标: 10.0.1.x (vpp-phase2-simulation)
协议: HTTP
状态: 200 OK
大小: 256 字节
```

---

## 如果看不到 bridge0？

### 方案 A：用命令行启动 Wireshark

```bash
# 直接指定 bridge0
wireshark -i bridge0 &
```

### 方案 B：用 tcpdump 验证

```bash
# 检查 bridge0 是否有流量
sudo tcpdump -i bridge0 -n 'tcp port 8080' -c 5
```

### 方案 C：用 tshark（命令行版）

```bash
# 实时显示 bridge0 上的 HTTP 流量
tshark -i bridge0 -f 'tcp port 8080' -Y 'http'
```

---

## 常见问题

### Q: 为什么我看不到 bridge0？

**A:** 可能的原因：
1. Docker Desktop 没有运行 - 启动 Docker Desktop
2. 网卡列表没有刷新 - 重启 Wireshark
3. 权限问题 - 用 `sudo wireshark` 运行

### Q: 我选了 en0 但看不到 Docker 流量？

**A:** 这是正常的。en0 是主网络接口，Docker 流量在虚拟网桥 bridge0 上。

### Q: 我应该选择 utun0 吗？

**A:** 不应该。utun0 是 VPN 隧道，与 Docker 无关。

### Q: 如何确认我选对了网卡？

**A:** 
1. 选择 bridge0
2. 应用过滤器 `tcp.port == 8080`
3. 如果看到数据包，说明选对了
4. 如果没看到，尝试移除过滤器看是否有其他流量

---

## 完整的 Wireshark 设置

### 打开 Wireshark
```bash
wireshark &
```

### 选择接口
- 在接口列表中找到 **bridge0**
- 点击蓝色按钮或双击开始抓包

### 应用过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 观察流量
- 绿色数据包 = TCP SYN (连接建立)
- 蓝色数据包 = TCP 数据 (HTTP 请求/响应)
- 红色数据包 = TCP RST/FIN (连接关闭)

### 分析数据包
1. 双击数据包查看详情
2. 展开 **Hypertext Transfer Protocol**
3. 查看 **Request Method**, **Request URI**, **Message Body**

---

## 命令行替代方案

### 用 tcpdump 抓包

```bash
# 从 bridge0 抓包
sudo tcpdump -i bridge0 -n 'tcp port 8080' -A

# 保存到文件
sudo tcpdump -i bridge0 -w capture.pcap 'tcp port 8080'

# 用 Wireshark 打开
open capture.pcap
```

### 用 tshark（命令行 Wireshark）

```bash
# 实时显示
tshark -i bridge0 -f 'tcp port 8080' -Y 'http'

# 保存并分析
tshark -i bridge0 -w capture.pcap -f 'tcp port 8080'
tshark -r capture.pcap -Y 'http' -T json > analysis.json
```

---

## 总结

✅ **选择 bridge0**
- 这是 Docker 虚拟网桥
- 所有容器流量都经过这个接口
- 最干净、最清晰的选择

✅ **应用过滤器**
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

✅ **观察流量**
- 每 10 秒一次的 HTTP POST 请求
- 包含完整的工控协议数据

---

**现在就试试吧！** 选择 bridge0，应用过滤器，你会立即看到通信流量。
