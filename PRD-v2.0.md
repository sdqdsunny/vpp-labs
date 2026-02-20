---

# 《新型电力系统及虚拟电厂通信协议仿真模拟环境》产品需求说明书 (PRD) v2.0

**版本**: 2.0  
**最后更新**: 2026年2月16日  
**状态**: 已通过Brainstorming优化  
**目标用户**: 电力系统安全研究人员

---

## 1. 项目概览

### 1.1 项目背景
随着新型电力系统和虚拟电厂（VPP）的发展，电力工控协议的安全性成为核心挑战。本项目旨在构建一个**全软件定义**的仿真环境，模拟复杂的电力业务场景，用于协议安全评估与漏洞深度分析。

**目标用户**: 电力系统的安全研究人员，需要进行协议漏洞挖掘、复现和深度分析。

### 1.2 核心目标

*   **全软件模拟（协议逻辑层）：** 彻底去硬件化，使用容器技术模拟所有电力终端与网络设备。重点关注**协议逻辑**的准确性，而非物理层时序特性。
*   **安全深度分析：** 支持对电力协议进行手工漏洞挖掘与复现，并实现故障（崩溃）现场的**自动分析、重放和人工验证**三层递进式分析。
*   **5G链路仿真（安全仿真优先）：** 采用Open5GS + UERANSIM模拟5G无线通信过程中的协议封装与加解密流程，重点关注**安全仿真**而非大并发接入。
*   **业务闭环验证：** 构建"主站-协调层-终端侧"完整的虚拟电厂业务链路，支持多协议验证。
*   **确定性延迟保证：** 通过PTP时钟同步、逻辑时间戳校准和CPU绑定，确保电力协议（尤其是IEC 61850 SV/GOOSE）的微秒级同步要求。

---

## 2. 系统总体架构

系统采用四层级联架构，所有组件均运行在 Linux 容器环境下：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: VPP Master (Python + FastAPI)                     │
│  - 业务决策中心                                              │
│  - 控制API与安全监控界面                                     │
│  - Core Dump自动分析与漏洞报告生成                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: VCC (Python + C++)                                │
│  - 协议映射引擎（配置化+插件化）                             │
│  - 逻辑聚合与协议分发                                        │
│  - 时间戳校准与同步                                          │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: 5G Simulation Network                             │
│  - Open5GS (核心网)                                          │
│  - UERANSIM (RAN模拟)                                        │
│  - 安全算法强制配置、网络切片、日志增强                      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Endpoint Simulators (C/C++)                       │
│  - 电源侧 (Source)                                           │
│  - 储能侧 (Storage)                                          │
│  - 需求侧 (Demand)                                           │
│  - 基于lib60870, libiec61850, libmodbus                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                        │
│  - PTP时钟同步 (linuxptp)                                    │
│  - 监控系统 (Prometheus + Grafana)                           │
│  - 日志系统 (EFK: Elasticsearch + Fluent Bit + Kibana)       │
│  - 部署支持 (Docker Compose + Kubernetes)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 功能模块设计

### 3.1 虚拟电厂主站模拟器 (VPP Master)

**技术栈**: Python + FastAPI + SQLAlchemy + Pydantic

#### 3.1.1 业务管理
*   模拟资源准入、调度指令（如调峰、调频）下发
*   支持多种调度策略的配置和执行
*   实时监控各仿真终端存活状态

#### 3.1.2 故障分析接口（三层递进式）

**第一层：自动分析**
*   集成 Core Dump 自动化提取功能
*   当底层协议栈进程崩溃时，主站自动收集内存快照
*   自动分析Core Dump并生成初步漏洞报告
*   包含：崩溃地址、调用栈、寄存器状态等关键信息

**第二层：重放功能**
*   支持Replay（重新执行导致崩溃的操作序列）
*   自动记录导致漏洞的操作序列
*   生成可重放的Python/Shell脚本
*   支持脚本的版本管理和共享

**第三层：人工验证**
*   提供详细的数据收集接口
*   支持研究人员进行深度调试和分析
*   支持对镜像流量的实时展示（对接虚拟交换机）

#### 3.1.3 可视化与报告
*   实时系统状态仪表板
*   漏洞分析报告自动生成
*   支持多协议的验证结果展示

---

### 3.2 控制协调中心仿真 (VCC Module)

**技术栈**: Python (协议映射引擎) + C++ (高性能转发)

#### 3.2.1 配置化协议映射

采用**配置化映射**而非硬编码，支持灵活的协议转换规则。

**映射配置示例** (YAML格式):
```yaml
protocol_mappings:
  - name: "IEC104_to_Modbus"
    source_protocol: "IEC104"
    target_protocol: "Modbus"
    rules:
      - source_field: "ASDU_M_ME_NC_1"  # 32-bit float
        target_field: "HOLDING_REGISTER"
        transform: "scale_and_offset"
        params:
          scale: 0.01
          offset: 0
      - source_field: "ASDU_M_SP_NA_1"  # Single point
        target_field: "COIL"
        transform: "direct"
```

**支持的映射类型**:
- 字段级别映射（ASDU → Coil/Register）
- 条件映射（基于业务逻辑的动态转换）
- 聚合映射（多个源字段 → 单个目标字段）
- 拆分映射（单个源字段 → 多个目标字段）

#### 3.2.2 插件化协议适配框架

采用**插件化驱动**架构，支持动态加载新协议。

**架构设计**:
```
VCC Core
├── Protocol Registry
├── Mapping Engine
├── Time Synchronization Module
└── Plugin Loader
    ├── IEC104Adapter
    ├── ModbusAdapter
    ├── MQTTAdapter
    ├── 61850Adapter
    └── [Custom Adapters]
```

**协议适配器接口** (Python SDK):
```python
class ProtocolAdapter:
    def __init__(self, config: Dict):
        pass
    
    def parse_message(self, raw_data: bytes) -> Dict:
        """解析协议报文"""
        pass
    
    def encode_message(self, data: Dict) -> bytes:
        """编码协议报文"""
        pass
    
    def get_supported_types(self) -> List[str]:
        """返回支持的数据类型"""
        pass
```

#### 3.2.3 自定义协议接入

提供**协议注入 SDK/接口**，允许研究人员开发自定义协议适配器。

**SDK特性**:
- 提供Python/C++ SDK供研究人员开发
- 定义标准的Protocol Adapter接口
- 支持热加载（无需重启VCC）
- 提供示例和完整文档

#### 3.2.4 时间戳校准与同步

**系统级时钟共享**:
- 所有容器共享同一个宿主机内核时钟
- 使用 linuxptp (PTP) 在宿主机上运行
- 挂载 `/dev/rtc` 到所有相关容器
- 确保主站、VCC 和终端看到的是同一基准时间

**逻辑时间戳校准**:
- 在协议仿真模块内部，不依赖 5G 链路的传输时间
- 采用逻辑时间戳进行业务校验
- 主站下发指令时附加逻辑时间戳
- 终端执行时使用逻辑时间戳而非实际接收时间

---

### 3.3 5G 仿真网络层

**技术栈**: Open5GS + UERANSIM + 定制化开发

#### 3.3.1 5G核心网仿真 (Open5GS)

**选择理由**:
- 开源、可定制、易于调试
- 完全满足安全仿真的需求
- 支持完整的NAS/RRC信令面和GTP用户面加密
- 社区活跃，文档完善

**部署方案**:
- 优先选择: https://github.com/open5gs/open5gs
- 备选方案: https://github.com/herlesupreeth/docker_open5gs

#### 3.3.2 RAN仿真 (UERANSIM)

**功能**:
- 模拟5G基站和用户设备
- 支持NAS/RRC信令
- 支持GTP用户面

#### 3.3.3 定制化开发需求

**a) 安全算法强制配置 (Security Policy)**
```yaml
security_policy:
  encryption_algorithm: "5G-AES"  # or "ZUC", "SNOW3G"
  integrity_algorithm: "5G-AES"
  key_derivation: "3GPP-KDF"
  force_weak_algorithm: false  # 支持强制使用弱算法进行漏洞测试
```

**b) 网络切片 (Slicing) 模拟**
- 支持创建多个网络切片（eMBB, URLLC, mMTC）
- 每个切片可配置不同的QoS参数
- 支持切片间的隔离和干扰模拟

**c) 日志与抓包增强**
- 增强5G信令日志的详细程度
- 支持在GTP隧道层面的报文抓取
- 集成Wireshark插件支持

#### 3.3.4 性能优化

**UERANSIM 性能调优**:
- **CPU 绑定（CPU Pinning）**: 将UERANSIM进程绑定到特定CPU核心
- **实时内核（RT-Kernel）**: 在宿主机上使用实时内核补丁
- **内存锁定**: 使用mlockall()防止内存交换
- 目标: 尽可能模拟电力系统所需的确定性延迟（Deterministic Latency）

---

### 3.4 业务终端侧通信仿真 (Endpoints)

**技术栈**: C/C++ + lib60870 + libiec61850 + libmodbus

#### 3.4.1 分布式电源模拟 (Source)

**遥测参数**:
- 有功/无功功率、三相电压/电流、频率
- 逆变器效率、环境温度、光照/风速

**遥信参数**:
- 并网状态、设备告警位、断路器状态

**遥控指令**:
- 有功限值调节、无功补偿调节、远程并/脱网

#### 3.4.2 储能系统模拟 (Storage)

**遥测参数**:
- SOC（荷电状态）、SOH（健康度）
- 实时充放电功率、电池单体最高/最低电压

**遥信参数**:
- 充放电状态、过温/过充/过放告警、通讯异常状态

**遥控指令**:
- 充放电模式切换、充放电功率给定

#### 3.4.3 需求侧负荷模拟 (Demand)

**通用负荷**:
- 实时有功功率、负荷优先级、在线状态

**EV充电桩**:
- 车辆连接状态（插枪/拔枪）、当前电量、V2G 允许标识

**遥控指令**:
- 负荷削减（LSE）响应指令

---

## 4. 安全测试与漏洞验证

### 4.1 Fuzzer-Friendly 设计

**设计思路**: 我们不开发 Fuzzer，但环境必须**"Fuzzer-Friendly（模糊测试友好）"**

**实现方式**:
- 提供标准化的协议报文接口
- 支持外部Fuzzer工具（如AFL, libFuzzer）的集成
- 提供报文生成和注入的SDK
- 支持结果收集和分析

### 4.2 攻击场景执行

**方案**: 采取"手工探索 + 模板化执行"的结合方案

**攻击场景模板库**:
- IEC 104长度字段异常
- Modbus CRC错误
- 61850 GOOSE时间戳异常
- MQTT QoS违规
- 等等

**攻击场景模板示例** (Python):
```python
attack_template = {
    "name": "IEC104_ASDU_Length_Overflow",
    "protocol": "IEC104",
    "target": "ASDU",
    "mutations": [
        {"field": "length", "operation": "overflow", "value": 65535},
        {"field": "length", "operation": "underflow", "value": 0},
        {"field": "length", "operation": "random", "range": [256, 65535]},
    ]
}
```

### 4.3 漏洞复现脚本生成

**功能**:
- 自动记录导致漏洞的操作序列
- 生成可重放的Python/Shell脚本
- 脚本包含详细的注释和参数说明
- 支持脚本的版本管理和共享

**脚本示例**:
```python
#!/usr/bin/env python3
# 漏洞复现脚本: IEC104_ASDU_Length_Overflow
# 生成时间: 2026-02-16
# 漏洞描述: 发送长度字段为65535的ASDU导致协议栈崩溃

from vpp_client import VPPClient
from attack_templates import IEC104_ASDU_Length_Overflow

client = VPPClient("http://localhost:8000")

# 执行攻击
result = client.execute_attack(
    endpoint="endpoint-1",
    attack_template=IEC104_ASDU_Length_Overflow,
    mutation_value=65535
)

# 验证结果
assert result.crashed == True
assert result.core_dump_generated == True
print(f"漏洞复现成功: {result.core_dump_path}")
```

### 4.4 联调验证流程

#### 4.4.1 指令流
主站 API → VCC 逻辑聚合 → 5G 仿真核心网 → 各终端协议栈（执行指令）

#### 4.4.2 数据流
终端电力参数 → 5G 仿真链路 → VCC → 主站看板

#### 4.4.3 安全测试流程
1. **攻击注入**: 在 5G 链路节点使用手工工具或模板注入电力协议畸形报文
2. **崩溃捕获**: 监控系统实时监测终端容器进程，一旦 `Segfault`，自动生成 `core.dump`
3. **自动分析**: 自动分析Core Dump并生成初步漏洞报告
4. **重放验证**: 支持重放导致崩溃的操作序列进行深度调试
5. **人工分析**: 研究人员进行最终的漏洞验证和根因分析

---

## 5. 验收标准

### 5.1 全链路通过性标准

**验收应采用"全链路通过性"作为标准**:

- ✅ 能够稳定复现已知漏洞（可靠性 ≥ 95%）
- ✅ 能够自动化执行漏洞复现脚本
- ✅ 能够生成详细的漏洞分析报告
- ✅ 能够通过Core Dump进行根因分析
- ✅ 能够支持漏洞的重放和调试

### 5.2 多协议验证

**验证范围**:
- IEC 104（北向协议）- 至少1个已知漏洞
- Modbus（南向协议）- 至少1个已知漏洞
- IEC 61850（可选）- 至少1个已知漏洞
- MQTT（可选）- 至少1个已知漏洞

**验证方式**:
- 每个协议验证漏洞的可复现性
- 验证漏洞的自动化程度
- 验证报告生成的完整性

### 5.3 交付验收物

1. **全套仿真环境镜像与部署脚本**
   - Docker Compose配置
   - Kubernetes Helm Chart
   - 部署指南和故障排查文档

2. **VPP 主站模拟器源代码**
   - Python + FastAPI实现
   - 完整的API文档
   - 单元测试和集成测试

3. **《协议仿真安全分析验收报告》**
   - 包含多个协议的漏洞挖掘与复现过程记录
   - 每个漏洞包含：描述、复现步骤、Core Dump分析、修复建议
   - 漏洞复现脚本

4. **《虚拟电厂场景仿真能力建设技术报告》**
   - 系统架构设计文档
   - 协议适配框架设计
   - 时钟同步方案详解
   - 性能测试报告
   - 最佳实践指南

---

## 6. 技术约束与实现方案

### 6.1 技术栈

#### 6.1.1 开发语言

| 组件 | 语言 | 理由 |
|------|------|------|
| VPP主站模拟器 | Python + FastAPI | 快速开发、丰富的数据分析库、易于集成 |
| VCC协调中心 | Python (映射引擎) + C++ (转发) | 灵活性与性能平衡 |
| 终端模拟器 | C/C++ | 性能要求高、复用开源协议栈库 |
| 5G仿真 | C (Open5GS) + C++ (UERANSIM) | 开源项目原生语言 |

#### 6.1.2 开源库与依赖

| 库 | 用途 | 版本 |
|----|------|------|
| lib60870 | IEC 60870-5-104协议栈 | 最新稳定版 |
| libiec61850 | IEC 61850协议栈 | 最新稳定版 |
| libmodbus | Modbus协议栈 | 最新稳定版 |
| Open5GS | 5G核心网仿真 | 最新稳定版 |
| UERANSIM | 5G RAN仿真 | 最新稳定版 |
| Scapy | 报文生成和注入 | 最新稳定版 |
| FastAPI | Web框架 | 最新稳定版 |
| SQLAlchemy | ORM | 最新稳定版 |
| Pydantic | 数据验证 | 最新稳定版 |

### 6.2 容器技术

#### 6.2.1 Docker & Docker Compose
- 用于开发、测试和小规模部署
- 提供完整的docker-compose.yml
- 支持一键启动整个仿真环境

#### 6.2.2 Kubernetes (K8s)
- 用于生产环境和大规模部署
- 提供Helm Chart
- 支持自动扩展和故障恢复
- 支持多节点部署

### 6.3 监控与日志系统

#### 6.3.1 Prometheus + Grafana
- **Prometheus**: 收集系统和应用指标
  - 主站API响应时间
  - 终端连接状态
  - 协议转换延迟
  - 5G仿真网络状态
  - Core Dump生成次数
  - 漏洞检测次数

- **Grafana**: 可视化仪表板
  - 实时系统状态
  - 性能趋势分析
  - 告警规则配置

#### 6.3.2 EFK Stack (Elasticsearch + Fluent Bit + Kibana)
- **Fluent Bit**: 轻量级日志收集
- **Elasticsearch**: 日志存储和搜索
- **Kibana**: 日志可视化和分析

### 6.4 时钟同步方案

#### 6.4.1 PTP (Precision Time Protocol)
- 在宿主机上运行 linuxptp
- 挂载 `/dev/rtc` 到所有相关容器
- 确保微秒级精度

#### 6.4.2 CPU绑定与实时内核
- CPU Pinning: 将UERANSIM进程绑定到特定CPU核心
- RT-Kernel: 在宿主机上使用实时内核补丁
- 内存锁定: 使用mlockall()防止内存交换

---

## 7. 部署架构

### 7.1 开发环境 (Docker Compose)

```
单机部署
├── VPP Master (Python)
├── VCC (Python + C++)
├── Open5GS (C)
├── UERANSIM (C++)
├── Endpoint Simulators (C/C++)
├── Prometheus
├── Grafana
└── EFK Stack
```

### 7.2 生产环境 (Kubernetes)

```
多节点部署
├── Node 1: VPP Master + Prometheus + Grafana
├── Node 2: VCC + Open5GS
├── Node 3: UERANSIM + Endpoint Simulators
└── Node 4: EFK Stack
```

### 7.3 分布式部署支持

- **主站层**: 可部署在单独的节点
- **VCC层**: 可部署在单独的节点，支持多副本
- **5G仿真层**: 可部署在单独的节点
- **终端层**: 可分散部署在多个节点

**通信方式**:
- 使用gRPC或REST API进行节点间通信
- 使用消息队列（如RabbitMQ）进行异步通信
- 使用共享存储（如NFS）存储配置和日志

---

## 8. 项目里程碑与交付计划

### 8.1 Phase 1: 基础架构搭建 (4周)
- [ ] Docker Compose环境搭建
- [ ] VPP主站基础框架
- [ ] VCC协议映射引擎
- [ ] 基础监控系统

### 8.2 Phase 2: 协议栈集成 (6周)
- [ ] IEC 104协议栈集成
- [ ] Modbus协议栈集成
- [ ] 5G仿真网络集成
- [ ] 时钟同步方案实现

### 8.3 Phase 3: 故障分析系统 (4周)
- [ ] Core Dump自动分析
- [ ] 重放功能实现
- [ ] 漏洞报告生成

### 8.4 Phase 4: 测试与验证 (4周)
- [ ] 多协议漏洞验证
- [ ] 性能测试
- [ ] 文档完善

### 8.5 Phase 5: 部署与交付 (2周)
- [ ] Kubernetes部署支持
- [ ] 部署指南编写
- [ ] 最终验收

---

## 9. 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 5G仿真性能不足 | 无法模拟实时场景 | 提前进行性能测试，优化CPU绑定和实时内核配置 |
| 时钟同步精度不够 | 电力协议验证失败 | 采用PTP + 逻辑时间戳的双层方案 |
| 协议栈库版本兼容性 | 集成困难 | 提前进行兼容性测试，制定版本管理策略 |
| 漏洞复现不稳定 | 验收困难 | 建立完整的测试用例库，确保可靠性 ≥ 95% |

---

## 10. 参考资源

### 10.1 开源项目
- Open5GS: https://github.com/open5gs/open5gs
- UERANSIM: https://github.com/aligungr/UERANSIM
- lib60870: https://github.com/mz2/lib60870
- libiec61850: https://github.com/mz2/libiec61850
- libmodbus: https://github.com/stephane/libmodbus

### 10.2 标准与规范
- IEC 60870-5-104: 电力系统远动通信协议
- IEC 61850: 电力系统通信和关联设备的接口标准
- Modbus: 工业控制通信协议
- 3GPP TS 24.501: 5G NAS协议

### 10.3 相关文档
- Brainstorming讨论记录: discuss.md
- 系统架构设计文档: (待编写)
- API设计文档: (待编写)
- 部署指南: (待编写)

---

**文档版本历史**:
- v1.0 (2026-02-16): 初始版本
- v2.0 (2026-02-16): 基于Brainstorming优化，增加详细的技术决策和实现方案

**下一步**: 基于本PRD v2.0进行详细的系统架构设计和API设计
