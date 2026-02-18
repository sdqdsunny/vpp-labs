# VPP Master与仿真模块联合调试方案 - 第三部分

## 第八部分：测试执行计划

### 8.1 每日测试计划

#### 第1天：环境准备与基础连接

```
09:00-10:00  环境检查与配置
  □ 检查硬件配置
  □ 检查网络连接
  □ 检查软件依赖
  □ 初始化数据库

10:00-11:00  VPP Master启动与验证
  □ 启动VPP Master服务
  □ 验证服务健康状态
  □ 检查API端点
  □ 检查日志输出

11:00-12:00  Phase 2 Simulation启动与验证
  □ 启动Phase 2 Simulation服务
  □ 验证服务健康状态
  □ 检查API端点
  □ 检查日志输出

13:00-14:00  REST API连接测试
  □ 运行test_rest_connection.py
  □ 验证所有端点可访问
  □ 记录响应时间

14:00-15:00  WebSocket连接测试
  □ 运行test_websocket_connection.py
  □ 验证双向通信
  □ 测试消息传递

15:00-16:00  总结与问题排查
  □ 汇总测试结果
  □ 排查发现的问题
  □ 生成第1天报告
```

#### 第2-4天：功能验证

```
09:00-10:00  设备注册测试
  □ 运行test_device_registration.py
  □ 验证设备创建
  □ 验证设备查询

10:00-11:00  VCC功能验证
  □ 运行test_vcc_command_mapping.py
  □ 验证命令映射
  □ 验证响应转换

11:00-12:00  电源侧模块验证
  □ 运行test_power_generation_module.py
  □ 验证太阳能发电
  □ 验证风力发电

13:00-14:00  储能侧模块验证
  □ 测试电池充放电
  □ 验证SOC/SOH计算
  □ 验证可用功率计算

14:00-15:00  需求侧模块验证
  □ 测试负荷模拟
  □ 验证需求响应
  □ 验证负荷预测

15:00-16:00  总结与问题排查
  □ 汇总测试结果
  □ 排查发现的问题
  □ 生成日报告
```

#### 第5-6天：集成与性能测试

```
09:00-10:00  端到端工作流测试
  □ 运行test_e2e_workflow.py
  □ 验证完整场景
  □ 验证多设备协调

10:00-11:00  协议互操作性测试
  □ 运行test_protocol_interoperability.py
  □ 验证协议转换
  □ 验证协议链转换

11:00-12:00  吞吐量测试
  □ 运行test_throughput.py
  □ 记录吞吐量指标
  □ 分析性能瓶颈

13:00-14:00  延迟测试
  □ 运行test_latency.py
  □ 记录延迟指标
  □ 分析延迟分布

14:00-15:00  容错能力测试
  □ 运行test_fault_tolerance.py
  □ 验证故障恢复
  □ 验证网络恢复

15:00-16:00  总结与问题排查
  □ 汇总测试结果
  □ 排查发现的问题
  □ 生成性能报告
```

#### 第7天：生产验证与总结

```
09:00-10:00  生产环境配置
  □ 配置生产参数
  □ 配置监控告警
  □ 配置日志收集

10:00-11:00  生产环境测试
  □ 运行完整测试套件
  □ 验证所有功能
  □ 验证性能指标

11:00-12:00  文档与知识转移
  □ 完成测试文档
  □ 完成操作手册
  □ 完成故障排查指南

13:00-14:00  最终验收
  □ 验收测试结果
  □ 验收性能指标
  □ 签署验收报告

14:00-15:00  总结与建议
  □ 汇总所有测试结果
  □ 提出改进建议
  □ 生成最终报告
```

### 8.2 测试执行脚本

```python
# run_all_tests.py
import subprocess
import sys
import json
from datetime import datetime

class TestExecutor:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def run_test(self, test_name, test_file):
        """运行单个测试"""
        print(f"\n{'='*60}")
        print(f"运行测试: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.results[test_name] = 'PASS'
                print(f"✅ {test_name} 通过")
            else:
                self.results[test_name] = 'FAIL'
                print(f"❌ {test_name} 失败")
                print(result.stderr)
        except subprocess.TimeoutExpired:
            self.results[test_name] = 'TIMEOUT'
            print(f"⏱️ {test_name} 超时")
        except Exception as e:
            self.results[test_name] = 'ERROR'
            print(f"❌ {test_name} 错误: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        tests = [
            ('环境验证', 'verify_environment.py'),
            ('REST连接', 'test_rest_connection.py'),
            ('WebSocket连接', 'test_websocket_connection.py'),
            ('设备注册', 'test_device_registration.py'),
            ('VCC功能', 'test_vcc_command_mapping.py'),
            ('电源侧模块', 'test_power_generation_module.py'),
            ('端到端工作流', 'test_e2e_workflow.py'),
            ('协议互操作性', 'test_protocol_interoperability.py'),
            ('吞吐量测试', 'test_throughput.py'),
            ('延迟测试', 'test_latency.py'),
            ('容错能力', 'test_fault_tolerance.py'),
        ]
        
        for test_name, test_file in tests:
            self.run_test(test_name, test_file)
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v == 'PASS')
        failed = sum(1 for v in self.results.values() if v == 'FAIL')
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.results.items():
            status = '✅' if result == 'PASS' else '❌'
            print(f"  {status} {test_name}: {result}")
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        print(f"\n总耗时: {elapsed_time:.1f}秒")
        
        # 保存结果
        with open('test_results.json', 'w') as f:
            json.dump({
                'timestamp': self.start_time.isoformat(),
                'results': self.results,
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'pass_rate': passed/total*100
                }
            }, f, indent=2)
        
        print("\n✅ 测试结果已保存到 test_results.json")

# 运行所有测试
if __name__ == '__main__':
    executor = TestExecutor()
    executor.run_all_tests()
```

---

## 第九部分：测试检查清单

### 9.1 环境准备检查清单

```
环境准备阶段检查清单
═══════════════════════════════════════════════════════════

硬件检查:
□ VPP Master服务器CPU ≥ 4核
□ VPP Master服务器内存 ≥ 8GB
□ Phase 2 Simulation服务器CPU ≥ 8核
□ Phase 2 Simulation服务器内存 ≥ 16GB
□ 网络连接正常（延迟 < 10ms）

网络配置:
□ VPP Master IP: 192.168.1.100
□ Phase 2 Simulation IP: 192.168.1.101
□ 测试客户端IP: 192.168.1.102
□ 防火墙规则配置正确
□ 路由配置正确

软件环境:
□ Python 3.8+已安装
□ 所有依赖包已安装
□ 数据库已初始化
□ 配置文件已准备
□ 日志目录已创建

服务启动:
□ VPP Master服务已启动
□ Phase 2 Simulation服务已启动
□ 所有服务健康检查通过
□ 日志输出正常
```

### 9.2 功能验证检查清单

```
功能验证阶段检查清单
═══════════════════════════════════════════════════════════

基础连接:
□ REST API连接正常
□ WebSocket连接正常
□ 数据交互正常
□ 错误处理正确

设备管理:
□ 设备创建成功
□ 设备查询成功
□ 设备更新成功
□ 设备删除成功

VCC协调中心:
□ 命令映射正确
□ 响应转换正确
□ 网络条件模拟正确
□ 消息顺序检查正确

电源侧模块:
□ 太阳能发电模拟正确
□ 风力发电模拟正确
□ 天气数据处理正确
□ 发电预测正确

储能侧模块:
□ 电池充电模拟正确
□ 电池放电模拟正确
□ SOC计算正确
□ SOH计算正确

需求侧模块:
□ 负荷模拟正确
□ 需求响应正确
□ 负荷预测正确
□ 灵活性范围计算正确
```

### 9.3 性能测试检查清单

```
性能测试阶段检查清单
═══════════════════════════════════════════════════════════

吞吐量指标:
□ 设备查询吞吐量 ≥ 100 req/s
□ 命令调度吞吐量 ≥ 50 cmd/s
□ 数据上报吞吐量 ≥ 1000 msg/s

延迟指标:
□ API平均响应延迟 < 100ms
□ API P95响应延迟 < 200ms
□ 命令执行延迟 < 500ms
□ 数据传输延迟 < 100ms

资源使用:
□ CPU使用率 < 80%
□ 内存使用率 < 80%
□ 磁盘使用率 < 80%
□ 网络带宽使用率 < 80%

可靠性指标:
□ 测试通过率 ≥ 99%
□ 故障恢复时间 < 5s
□ 数据一致性 100%
□ 无数据丢失
```

### 9.4 生产验证检查清单

```
生产验证阶段检查清单
═══════════════════════════════════════════════════════════

系统配置:
□ 生产参数已配置
□ 监控告警已配置
□ 日志收集已配置
□ 备份策略已配置

功能验证:
□ 所有功能正常工作
□ 所有API端点可访问
□ 所有协议转换正确
□ 所有设备通信正常

性能验证:
□ 吞吐量满足要求
□ 延迟满足要求
□ 资源使用满足要求
□ 可靠性满足要求

安全验证:
□ 认证机制正常
□ 授权机制正常
□ 数据加密正常
□ 日志审计正常

文档完成:
□ 操作手册已完成
□ 故障排查指南已完成
□ API文档已完成
□ 性能报告已完成
```

---

## 第十部分：问题排查指南

### 10.1 常见问题与解决方案

#### 问题1：VPP Master无法连接到Phase 2 Simulation

**症状**: 
- 连接超时
- 连接被拒绝
- 网络不可达

**排查步骤**:
```bash
# 1. 检查网络连接
ping 192.168.1.101

# 2. 检查端口是否开放
telnet 192.168.1.101 5000

# 3. 检查防火墙规则
sudo iptables -L -n | grep 5000

# 4. 检查服务是否运行
curl http://192.168.1.101:5000/health

# 5. 查看服务日志
tail -f vpp-phase2-simulation/logs/app.log
```

**解决方案**:
- 检查网络配置
- 检查防火墙规则
- 重启服务
- 检查服务日志

#### 问题2：API响应缓慢

**症状**:
- 响应时间 > 1秒
- 超时错误
- 连接重置

**排查步骤**:
```bash
# 1. 检查服务器资源
top
free -h
df -h

# 2. 检查网络延迟
ping -c 10 192.168.1.101

# 3. 检查数据库性能
# 查看慢查询日志

# 4. 检查应用日志
tail -f vpp-master/logs/app.log
```

**解决方案**:
- 优化数据库查询
- 增加服务器资源
- 启用缓存
- 优化网络配置

#### 问题3：设备状态不同步

**症状**:
- Master和Simulation中设备状态不一致
- 命令执行后状态未更新
- 数据丢失

**排查步骤**:
```bash
# 1. 检查设备状态
curl http://192.168.1.100:8080/api/v1/devices/solar-001
curl http://192.168.1.101:5000/api/v1/devices/solar-001

# 2. 检查消息队列
# 查看是否有待处理消息

# 3. 检查数据库
# 查看数据库中的设备状态

# 4. 查看应用日志
grep "solar-001" vpp-master/logs/app.log
grep "solar-001" vpp-phase2-simulation/logs/app.log
```

**解决方案**:
- 重新同步设备状态
- 检查消息队列
- 检查数据库一致性
- 重启服务

### 10.2 日志分析

```python
# analyze_logs.py
import re
from datetime import datetime

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.errors = []
        self.warnings = []
        self.info = []
    
    def parse_logs(self):
        """解析日志文件"""
        with open(self.log_file, 'r') as f:
            for line in f:
                if 'ERROR' in line:
                    self.errors.append(line.strip())
                elif 'WARNING' in line:
                    self.warnings.append(line.strip())
                elif 'INFO' in line:
                    self.info.append(line.strip())
    
    def print_summary(self):
        """打印日志总结"""
        print(f"日志文件: {self.log_file}")
        print(f"错误数: {len(self.errors)}")
        print(f"警告数: {len(self.warnings)}")
        print(f"信息数: {len(self.info)}")
        
        if self.errors:
            print("\n最近的错误:")
            for error in self.errors[-5:]:
                print(f"  {error}")
    
    def find_issues(self):
        """查找常见问题"""
        issues = []
        
        for error in self.errors:
            if 'Connection refused' in error:
                issues.append('连接被拒绝')
            elif 'Timeout' in error:
                issues.append('连接超时')
            elif 'Database' in error:
                issues.append('数据库错误')
            elif 'Protocol' in error:
                issues.append('协议错误')
        
        return issues

# 使用示例
if __name__ == '__main__':
    analyzer = LogAnalyzer('vpp-master/logs/app.log')
    analyzer.parse_logs()
    analyzer.print_summary()
    
    issues = analyzer.find_issues()
    if issues:
        print("\n发现的问题:")
        for issue in set(issues):
            print(f"  - {issue}")
```

