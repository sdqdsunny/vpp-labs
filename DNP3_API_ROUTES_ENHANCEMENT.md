# DNP3 API 路由增强 - 攻击检测端点

**状态**: 待实施  
**优先级**: 高  
**预计工作量**: 1-2小时

---

## 概述

为 `vpp-phase2-simulation/routes/security_tester.py` 添加新的API端点，支持DNP3攻击检测功能。

---

## 新增API端点

### 1. 攻击检测端点

**端点**: `POST /api/security/dnp3/attack_detection`

**请求体**:
```json
{
    "test_type": "detect_attack",
    "host": "10.0.8.2",
    "port": 20000,
    "packet_data": {
        "control_field": 128,
        "function_code": 1,
        "data_length": 100,
        "sequence_number": 1,
        "object_type": 1
    }
}
```

**响应**:
```json
{
    "test_id": "uuid",
    "test_type": "detect_attack",
    "adapter_name": "dnp3",
    "status": "success",
    "result_data": {
        "attack_detected": false,
        "anomalies": [],
        "severity": "low",
        "timestamp": "2026-02-19T...",
        "alarm_state": {
            "last_anomaly": null,
            "anomaly_count": 0,
            "is_alarmed": false,
            "history_size": 1
        },
        "statistics": {
            "total_packets": 1,
            "anomalous_packets": 0,
            "anomaly_rate": 0.0
        }
    }
}
```

### 2. 异常分析端点

**端点**: `POST /api/security/dnp3/analyze_anomaly`

**请求体**:
```json
{
    "test_type": "analyze_anomaly",
    "host": "10.0.8.2",
    "port": 20000,
    "packet_data": {
        "control_field": 256,
        "function_code": 1,
        "data_length": 100,
        "sequence_number": 1,
        "object_type": 1
    }
}
```

**响应**:
```json
{
    "test_id": "uuid",
    "test_type": "analyze_anomaly",
    "adapter_name": "dnp3",
    "status": "success",
    "result_data": {
        "is_anomalous": true,
        "anomalies": ["Control field out of range: 256"],
        "severity": "high",
        "timestamp": "2026-02-19T...",
        "details": {
            "control_field": 256,
            "function_code": 1,
            "data_length": 100,
            "sequence_number": 1,
            "object_type": 1
        },
        "alarm_state": {
            "last_anomaly": "2026-02-19T...",
            "anomaly_count": 1,
            "is_alarmed": true,
            "history_size": 1
        }
    }
}
```

### 3. 告警状态端点

**端点**: `GET /api/security/dnp3/alarm_state`

**响应**:
```json
{
    "alarm_state": {
        "last_anomaly": "2026-02-19T...",
        "anomaly_count": 5,
        "is_alarmed": true,
        "history_size": 10
    },
    "timestamp": "2026-02-19T..."
}
```

### 4. 统计信息端点

**端点**: `GET /api/security/dnp3/statistics`

**响应**:
```json
{
    "statistics": {
        "total_packets": 100,
        "anomalous_packets": 5,
        "anomaly_rate": 5.0
    },
    "timestamp": "2026-02-19T..."
}
```

---

## 实施代码

在 `vpp-phase2-simulation/routes/security_tester.py` 中添加：

```python
@app.route("/api/security/dnp3/attack_detection", method="POST")
def dnp3_attack_detection():
    """Run DNP3 attack detection"""
    try:
        data = request.json
        test_type = data.get("test_type", "detect_attack")
        host = data.get("host", "localhost")
        port = int(data.get("port", 20000))
        packet_data = data.get("packet_data", {})
        
        manager = get_security_manager()
        result = manager.run_dnp3_test(
            test_type, 
            host, 
            port, 
            packet_data=packet_data
        )
        
        response.content_type = "application/json"
        return json.dumps(result)
    except Exception as e:
        logger.error(f"DNP3 attack detection error: {e}")
        response.status = 400
        return json.dumps({"error": str(e)})


@app.route("/api/security/dnp3/analyze_anomaly", method="POST")
def dnp3_analyze_anomaly():
    """Analyze DNP3 packet for anomalies"""
    try:
        data = request.json
        test_type = data.get("test_type", "analyze_anomaly")
        host = data.get("host", "localhost")
        port = int(data.get("port", 20000))
        packet_data = data.get("packet_data", {})
        
        manager = get_security_manager()
        result = manager.run_dnp3_test(
            test_type, 
            host, 
            port, 
            packet_data=packet_data
        )
        
        response.content_type = "application/json"
        return json.dumps(result)
    except Exception as e:
        logger.error(f"DNP3 anomaly analysis error: {e}")
        response.status = 400
        return json.dumps({"error": str(e)})


@app.route("/api/security/dnp3/alarm_state", method="GET")
def dnp3_alarm_state():
    """Get DNP3 alarm state"""
    try:
        manager = get_security_manager()
        alarm_state = manager.get_dnp3_alarm_state()
        
        response.content_type = "application/json"
        return json.dumps({
            "alarm_state": alarm_state,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting alarm state: {e}")
        response.status = 500
        return json.dumps({"error": str(e)})


@app.route("/api/security/dnp3/statistics", method="GET")
def dnp3_statistics():
    """Get DNP3 detection statistics"""
    try:
        manager = get_security_manager()
        statistics = manager.get_dnp3_statistics()
        
        response.content_type = "application/json"
        return json.dumps({
            "statistics": statistics,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        response.status = 500
        return json.dumps({"error": str(e)})
```

---

## SecurityTestManager 增强

在 `vpp-phase2-simulation/services/security_tester.py` 中添加方法：

```python
def run_dnp3_test(self, test_type, host, port, **kwargs):
    """Run DNP3 test"""
    adapter = self.adapters.get('dnp3')
    if not adapter:
        raise ValueError("DNP3 adapter not available")
    
    request = TestRequest(
        test_type=test_type,
        adapter_name='dnp3',
        target_host=host,
        target_port=port,
        parameters=kwargs
    )
    
    result = adapter.execute_test(request)
    return result.to_dict()


def get_dnp3_alarm_state(self):
    """Get DNP3 alarm state"""
    adapter = self.adapters.get('dnp3')
    if not adapter or not hasattr(adapter, 'attack_detector'):
        return {}
    
    return adapter.attack_detector.get_alarm_state()


def get_dnp3_statistics(self):
    """Get DNP3 statistics"""
    adapter = self.adapters.get('dnp3')
    if not adapter or not hasattr(adapter, 'attack_detector'):
        return {}
    
    return adapter.attack_detector.get_statistics()
```

---

## 错误处理

所有端点都应该处理以下错误：

1. **400 Bad Request** - 请求参数无效
2. **404 Not Found** - 资源不存在
3. **500 Internal Server Error** - 服务器错误

---

## 测试清单

- [ ] 攻击检测端点正常工作
- [ ] 异常分析端点正常工作
- [ ] 告警状态端点正常工作
- [ ] 统计信息端点正常工作
- [ ] 错误处理正确
- [ ] 响应格式正确
- [ ] 性能可接受

---

## 集成步骤

1. 在 `security_tester.py` 中添加新方法
2. 在 `routes/security_tester.py` 中添加新端点
3. 测试所有端点
4. 验证错误处理
5. 文档更新

---

**预计完成时间**: 1-2小时  
**优先级**: 高  
**状态**: 待实施

