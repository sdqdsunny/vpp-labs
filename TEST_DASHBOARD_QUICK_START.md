# 🚀 测试仪表板快速开始

## 访问仪表板

打开浏览器，访问:
```
http://localhost:8080/test-dashboard
```

## 界面说明

### 左侧 - 测试类型选择
```
📋 测试类型
├─ ▶ 运行所有测试 (479)      ← 执行全部测试
├─ ▶ 单元测试                ← 仅单元测试
├─ ▶ 集成测试                ← 仅集成测试
├─ ▶ 端到端测试              ← 仅 E2E 测试
├─ ▶ 属性测试                ← 仅属性测试
├─ ▶ 指标测试                ← 仅指标测试
└─ ▶ 可视化测试              ← 仅可视化测试
```

### 右侧 - 执行状态
```
📊 执行状态
├─ 状态: 就绪
├─ 最后执行: 未执行
├─ 进度条: [████░░░░░░] 40%
└─ 统计数据:
   ├─ 通过: 0
   ├─ 失败: 0
   └─ 总计: 0
```

### 下方 - 执行输出
```
📝 执行输出
└─ 等待测试执行...
```

## 快速操作

### 1️⃣ 运行全部测试
```
点击 "运行所有测试 (479)" 按钮
↓
等待约 11 秒
↓
查看结果: 479 通过, 0 失败
```

### 2️⃣ 运行特定测试
```
点击对应的测试按钮
↓
等待测试完成
↓
查看输出和统计
```

### 3️⃣ 查看详细输出
```
在下方的黑色输出面板中查看完整日志
↓
自动滚动到最新内容
↓
可复制输出内容
```

## 测试执行时间参考

| 测试类型 | 预期时间 |
|---------|---------|
| 全部测试 | ~11 秒 |
| 单元测试 | ~5 秒 |
| 集成测试 | ~3 秒 |
| 端到端测试 | ~2 秒 |
| 属性测试 | ~4 秒 |
| 指标测试 | ~2 秒 |
| 可视化测试 | ~2 秒 |

## 常见操作

### 查看测试是否通过
```
✅ 通过数 = 总计数 → 所有测试通过
❌ 失败数 > 0 → 有测试失败
```

### 查看失败原因
```
在输出面板中搜索 "FAILED"
查看失败的测试名称和错误信息
```

### 重新运行测试
```
点击同一个按钮再次运行
或选择不同的测试类型
```

## 状态指示

### 执行状态颜色
- 🟢 **就绪** - 可以执行测试
- 🟡 **运行中** - 测试正在执行
- 🟢 **已完成** - 测试执行完成
- 🔴 **错误** - 测试执行出错

### 进度条
- 显示已通过测试的百分比
- 实时更新
- 测试完成时达到 100%

## 快速命令参考

### 通过 API 运行测试
```bash
# 运行所有测试
curl -X POST http://localhost:8080/api/test/run \
  -H "Content-Type: application/json" \
  -d '{"test_type": "all"}'

# 运行单元测试
curl -X POST http://localhost:8080/api/test/run \
  -H "Content-Type: application/json" \
  -d '{"test_type": "unit"}'

# 查看状态
curl http://localhost:8080/api/test/status
```

### 通过命令行运行测试
```bash
# 进入容器
docker exec -it vpp-phase2-simulation bash

# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/test_metrics_collector.py -v

# 运行并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html
```

## 故障排除

### 仪表板无法打开
```
1. 检查容器是否运行
   docker ps | grep vpp-phase2-simulation

2. 检查 API 是否响应
   curl http://localhost:8080/health

3. 查看容器日志
   docker logs vpp-phase2-simulation
```

### 测试无法执行
```
1. 检查输出面板中的错误信息
2. 查看容器日志
3. 尝试在命令行中运行相同的测试
```

### 页面显示不正常
```
1. 刷新页面 (Ctrl+R 或 Cmd+R)
2. 清除浏览器缓存
3. 尝试其他浏览器
```

## 下一步

- 📖 阅读完整指南: [TEST_DASHBOARD_GUIDE.md](TEST_DASHBOARD_GUIDE.md)
- 🧪 查看测试报告: [TEST_EXECUTION_REPORT.md](TEST_EXECUTION_REPORT.md)
- 📊 查看部署状态: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

---

**提示**: 仪表板每 2 秒自动刷新一次状态，无需手动刷新页面。
