# DNP3 Web UI 增强 - 攻击检测功能

**状态**: 待实施  
**优先级**: 高  
**预计工作量**: 2-3小时

---

## 概述

为Web界面添加DNP3攻击检测功能的UI组件，包括：
- 攻击检测选项
- 异常分析选项
- 结果显示面板
- 告警状态显示

---

## 实施计划

### 1. HTML UI 组件

在 `vpp-phase2-simulation/static/security_tester.html` 中添加：

```html
<!-- DNP3 Attack Detection Section -->
<div id="dnp3-attack-detection" class="test-section">
    <h3>DNP3 攻击检测</h3>
    
    <div class="form-group">
        <label>检测类型:</label>
        <select id="dnp3-detection-type">
            <option value="detect_attack">攻击检测</option>
            <option value="analyze_anomaly">异常分析</option>
        </select>
    </div>
    
    <div class="form-group">
        <label>数据包参数:</label>
        <div class="packet-params">
            <input type="number" id="control-field" placeholder="控制字段 (0-255)" min="0" max="255" value="128">
            <input type="number" id="function-code" placeholder="功能码 (0-15)" min="0" max="15" value="1">
            <input type="number" id="data-length" placeholder="数据长度 (0-65535)" min="0" max="65535" value="100">
            <input type="number" id="sequence-number" placeholder="序列号 (0-65535)" min="0" max="65535" value="1">
            <input type="number" id="object-type" placeholder="对象类型 (1-123)" min="1" max="123" value="1">
        </div>
    </div>
    
    <button onclick="runDNP3AttackDetection()">执行检测</button>
</div>

<!-- Attack Detection Results -->
<div id="attack-detection-results" class="results-panel" style="display:none;">
    <h4>检测结果</h4>
    <div class="result-content">
        <div class="result-item">
            <span class="label">攻击检测:</span>
            <span id="attack-detected" class="value"></span>
        </div>
        <div class="result-item">
            <span class="label">异常列表:</span>
            <div id="anomalies-list" class="anomalies"></div>
        </div>
        <div class="result-item">
            <span class="label">严重级别:</span>
            <span id="severity-level" class="value"></span>
        </div>
        <div class="result-item">
            <span class="label">告警状态:</span>
            <div id="alarm-state" class="alarm-info"></div>
        </div>
        <div class="result-item">
            <span class="label">统计信息:</span>
            <div id="statistics" class="stats-info"></div>
        </div>
    </div>
</div>
```

### 2. CSS 样式

```css
.packet-params {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
    margin: 10px 0;
}

.packet-params input {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 12px;
}

.anomalies {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 10px;
    margin: 5px 0;
    border-radius: 4px;
}

.anomalies .anomaly-item {
    padding: 5px 0;
    color: #856404;
    font-size: 12px;
}

.alarm-info {
    background: #e7f3ff;
    border-left: 4px solid #2196F3;
    padding: 10px;
    margin: 5px 0;
    border-radius: 4px;
    font-size: 12px;
}

.stats-info {
    background: #f0f0f0;
    border-left: 4px solid #666;
    padding: 10px;
    margin: 5px 0;
    border-radius: 4px;
    font-size: 12px;
}

.severity-high {
    color: #d32f2f;
    font-weight: bold;
}

.severity-medium {
    color: #f57c00;
    font-weight: bold;
}

.severity-low {
    color: #388e3c;
    font-weight: bold;
}
```

### 3. JavaScript 函数

```javascript
async function runDNP3AttackDetection() {
    const detectionType = document.getElementById('dnp3-detection-type').value;
    const packetData = {
        control_field: parseInt(document.getElementById('control-field').value),
        function_code: parseInt(document.getElementById('function-code').value),
        data_length: parseInt(document.getElementById('data-length').value),
        sequence_number: parseInt(document.getElementById('sequence-number').value),
        object_type: parseInt(document.getElementById('object-type').value),
    };
    
    try {
        const response = await fetch('/api/security/dnp3/attack_detection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                test_type: detectionType,
                host: document.getElementById('dnp3-host').value,
                port: parseInt(document.getElementById('dnp3-port').value),
                packet_data: packetData
            })
        });
        
        const result = await response.json();
        displayAttackDetectionResults(result);
    } catch (error) {
        alert('检测失败: ' + error.message);
    }
}

function displayAttackDetectionResults(result) {
    const resultsPanel = document.getElementById('attack-detection-results');
    
    // Display attack detected status
    const attackDetected = result.result_data.attack_detected;
    document.getElementById('attack-detected').textContent = attackDetected ? '是' : '否';
    document.getElementById('attack-detected').className = 
        'value ' + (attackDetected ? 'severity-high' : 'severity-low');
    
    // Display anomalies
    const anomaliesList = document.getElementById('anomalies-list');
    anomaliesList.innerHTML = '';
    if (result.result_data.anomalies.length > 0) {
        result.result_data.anomalies.forEach(anomaly => {
            const item = document.createElement('div');
            item.className = 'anomaly-item';
            item.textContent = '• ' + anomaly;
            anomaliesList.appendChild(item);
        });
    } else {
        anomaliesList.innerHTML = '<div class="anomaly-item">无异常检测</div>';
    }
    
    // Display severity
    const severity = result.result_data.severity;
    const severityEl = document.getElementById('severity-level');
    severityEl.textContent = severity;
    severityEl.className = 'value severity-' + severity;
    
    // Display alarm state
    const alarmState = result.result_data.alarm_state;
    const alarmEl = document.getElementById('alarm-state');
    alarmEl.innerHTML = `
        <div>最后异常: ${alarmState.last_anomaly || '无'}</div>
        <div>异常计数: ${alarmState.anomaly_count}</div>
        <div>告警状态: ${alarmState.is_alarmed ? '已告警' : '正常'}</div>
    `;
    
    // Display statistics
    const stats = result.result_data.statistics;
    const statsEl = document.getElementById('statistics');
    statsEl.innerHTML = `
        <div>总数据包: ${stats.total_packets}</div>
        <div>异常数据包: ${stats.anomalous_packets}</div>
        <div>异常率: ${stats.anomaly_rate.toFixed(1)}%</div>
    `;
    
    resultsPanel.style.display = 'block';
}
```

---

## 集成步骤

1. 在HTML中添加DNP3攻击检测部分
2. 添加相应的CSS样式
3. 实现JavaScript函数
4. 测试UI交互
5. 验证结果显示

---

## 测试清单

- [ ] UI 组件正确显示
- [ ] 表单输入验证
- [ ] API 调用成功
- [ ] 结果正确显示
- [ ] 错误处理正确
- [ ] 响应式设计正确

---

**预计完成时间**: 2-3小时  
**优先级**: 高  
**状态**: 待实施

