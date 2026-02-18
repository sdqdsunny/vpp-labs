"""
Test Dashboard Route - Interactive testing interface for VPP Phase 2 Simulation Framework.

Provides a web-based UI for running tests and viewing results.
"""

import json
import subprocess
import threading
from datetime import datetime
from bottle import Bottle, request, response, static_file
import os

# Store test execution results
test_results = {
    "last_execution": None,
    "status": "idle",
    "output": "",
    "tests_passed": 0,
    "tests_failed": 0,
    "tests_total": 0
}

def create_test_dashboard_routes(app):
    """Create test dashboard routes."""
    
    @app.route("/test-dashboard", method="GET")
    def test_dashboard_page():
        """Serve the test dashboard HTML page."""
        response.content_type = "text/html; charset=utf-8"
        return get_dashboard_html()
    
    @app.route("/api/test/run", method="POST")
    def run_tests():
        """Run tests based on request parameters."""
        data = request.json or {}
        test_type = data.get("test_type", "all")
        
        response.content_type = "application/json"
        
        # Run tests in background
        thread = threading.Thread(
            target=execute_tests,
            args=(test_type,)
        )
        thread.daemon = True
        thread.start()
        
        return json.dumps({
            "status": "started",
            "message": f"Test execution started: {test_type}"
        })
    
    @app.route("/api/test/status", method="GET")
    def get_test_status():
        """Get current test execution status."""
        response.content_type = "application/json"
        return json.dumps(test_results)
    
    @app.route("/api/test/results", method="GET")
    def get_test_results():
        """Get detailed test results."""
        response.content_type = "application/json"
        return json.dumps(test_results)


def execute_tests(test_type):
    """Execute tests based on type."""
    global test_results
    import re
    
    test_results["status"] = "running"
    test_results["output"] = ""
    test_results["last_execution"] = datetime.utcnow().isoformat()
    
    try:
        if test_type == "all":
            cmd = "python3 -m pytest tests/ -v --tb=short"
        elif test_type == "unit":
            cmd = "python3 -m pytest tests/ -v -m 'not integration' --tb=short"
        elif test_type == "integration":
            cmd = "python3 -m pytest tests/test_integration_suite.py -v --tb=short"
        elif test_type == "e2e":
            cmd = "python3 -m pytest tests/test_e2e_scenarios.py -v --tb=short"
        elif test_type == "properties":
            cmd = "python3 -m pytest tests/ -k 'properties' -v --tb=short"
        elif test_type == "metrics":
            cmd = "python3 -m pytest tests/test_metrics_collector.py tests/test_metrics_properties.py -v --tb=short"
        elif test_type == "visualization":
            cmd = "python3 -m pytest tests/test_visualization.py tests/test_visualization_properties.py -v --tb=short"
        else:
            cmd = "python3 -m pytest tests/ -v --tb=short"
        
        # Execute command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        output = result.stdout + result.stderr
        test_results["output"] = output
        
        # Parse results - look for pytest summary line
        # Pattern: "X passed" or "X passed, Y failed" or "X failed"
        passed_match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)
        
        if passed_match:
            test_results["tests_passed"] = int(passed_match.group(1))
        else:
            test_results["tests_passed"] = 0
        
        if failed_match:
            test_results["tests_failed"] = int(failed_match.group(1))
        else:
            test_results["tests_failed"] = 0
        
        test_results["tests_total"] = test_results["tests_passed"] + test_results["tests_failed"]
        
        # If no tests found, check if pytest ran at all
        if test_results["tests_total"] == 0 and "passed" not in output and "failed" not in output:
            test_results["status"] = "error"
            test_results["output"] = f"No tests found or pytest failed to run.\n\nCommand: {cmd}\n\nOutput:\n{output}"
        else:
            test_results["status"] = "completed"
        
    except Exception as e:
        test_results["status"] = "error"
        test_results["output"] = f"Exception occurred: {str(e)}"


def get_dashboard_html():
    """Generate the test dashboard HTML."""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPP Phase 2 - 测试仪表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .test-buttons {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .test-btn {
            padding: 12px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            text-align: left;
        }
        
        .test-btn:hover {
            transform: translateX(4px);
        }
        
        .test-btn.all {
            background: #667eea;
            color: white;
        }
        
        .test-btn.all:hover {
            background: #5568d3;
        }
        
        .test-btn.unit {
            background: #48bb78;
            color: white;
        }
        
        .test-btn.unit:hover {
            background: #38a169;
        }
        
        .test-btn.integration {
            background: #ed8936;
            color: white;
        }
        
        .test-btn.integration:hover {
            background: #dd6b20;
        }
        
        .test-btn.e2e {
            background: #f6ad55;
            color: white;
        }
        
        .test-btn.e2e:hover {
            background: #ed8936;
        }
        
        .test-btn.properties {
            background: #9f7aea;
            color: white;
        }
        
        .test-btn.properties:hover {
            background: #805ad5;
        }
        
        .test-btn.metrics {
            background: #4299e1;
            color: white;
        }
        
        .test-btn.metrics:hover {
            background: #3182ce;
        }
        
        .test-btn.visualization {
            background: #38b2ac;
            color: white;
        }
        
        .test-btn.visualization:hover {
            background: #319795;
        }
        
        .test-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status-panel {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .status-label {
            color: #666;
            font-weight: 500;
        }
        
        .status-value {
            color: #333;
            font-weight: 600;
        }
        
        .status-running {
            color: #ed8936;
        }
        
        .status-completed {
            color: #48bb78;
        }
        
        .status-error {
            color: #f56565;
        }
        
        .output-panel {
            background: #1a202c;
            color: #68d391;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.5;
        }
        
        .output-panel.empty {
            color: #a0aec0;
            font-style: italic;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stat-box {
            background: #f7fafc;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
        }
        
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e2e8f0;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 VPP Phase 2 测试仪表板</h1>
            <p>交互式测试执行和结果查看平台</p>
        </div>
        
        <div class="main-grid">
            <div class="card">
                <h2>📋 测试类型</h2>
                <div class="test-buttons">
                    <button class="test-btn all" onclick="runTest('all')">
                        ▶ 运行所有测试 (479)
                    </button>
                    <button class="test-btn unit" onclick="runTest('unit')">
                        ▶ 单元测试
                    </button>
                    <button class="test-btn integration" onclick="runTest('integration')">
                        ▶ 集成测试
                    </button>
                    <button class="test-btn e2e" onclick="runTest('e2e')">
                        ▶ 端到端测试
                    </button>
                    <button class="test-btn properties" onclick="runTest('properties')">
                        ▶ 属性测试
                    </button>
                    <button class="test-btn metrics" onclick="runTest('metrics')">
                        ▶ 指标测试
                    </button>
                    <button class="test-btn visualization" onclick="runTest('visualization')">
                        ▶ 可视化测试
                    </button>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 执行状态</h2>
                <div class="status-panel">
                    <div class="status-item">
                        <span class="status-label">状态:</span>
                        <span class="status-value" id="status">就绪</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">最后执行:</span>
                        <span class="status-value" id="last-execution">未执行</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-number" id="passed-count">0</div>
                        <div class="stat-label">通过</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="failed-count">0</div>
                        <div class="stat-label">失败</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="total-count">0</div>
                        <div class="stat-label">总计</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📝 执行输出</h2>
            <div class="output-panel empty" id="output">
                等待测试执行...
            </div>
        </div>
        
        <div class="footer">
            <p>VPP Phase 2 Simulation Framework | 测试仪表板 v1.0</p>
            <p>实时监控和执行测试 | 自动刷新状态</p>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        async function runTest(testType) {
            if (isRunning) {
                alert('测试正在运行中，请稍候...');
                return;
            }
            
            isRunning = true;
            updateUI('running');
            
            try {
                const response = await fetch('/api/test/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ test_type: testType })
                });
                
                const data = await response.json();
                console.log('Test started:', data);
                
                // Poll for results
                pollResults();
            } catch (error) {
                console.error('Error starting test:', error);
                updateUI('error');
                isRunning = false;
            }
        }
        
        async function pollResults() {
            try {
                const response = await fetch('/api/test/status');
                const data = await response.json();
                
                updateStatus(data);
                
                if (data.status === 'running') {
                    setTimeout(pollResults, 1000);
                } else {
                    isRunning = false;
                }
            } catch (error) {
                console.error('Error polling results:', error);
            }
        }
        
        function updateStatus(data) {
            // Update status
            const statusEl = document.getElementById('status');
            if (data.status === 'running') {
                statusEl.innerHTML = '<span class="spinner"></span>运行中...';
                statusEl.className = 'status-value status-running';
            } else if (data.status === 'completed') {
                statusEl.textContent = '已完成';
                statusEl.className = 'status-value status-completed';
            } else if (data.status === 'error') {
                statusEl.textContent = '错误';
                statusEl.className = 'status-value status-error';
            } else {
                statusEl.textContent = '就绪';
                statusEl.className = 'status-value';
            }
            
            // Update last execution
            if (data.last_execution) {
                const date = new Date(data.last_execution);
                document.getElementById('last-execution').textContent = 
                    date.toLocaleString('zh-CN');
            }
            
            // Update stats
            document.getElementById('passed-count').textContent = data.tests_passed;
            document.getElementById('failed-count').textContent = data.tests_failed;
            document.getElementById('total-count').textContent = data.tests_total;
            
            // Update progress
            if (data.tests_total > 0) {
                const progress = (data.tests_passed / data.tests_total) * 100;
                document.getElementById('progress-fill').style.width = progress + '%';
            }
            
            // Update output
            const outputEl = document.getElementById('output');
            if (data.output) {
                outputEl.textContent = data.output;
                outputEl.className = 'output-panel';
                outputEl.scrollTop = outputEl.scrollHeight;
            }
        }
        
        function updateUI(status) {
            const statusEl = document.getElementById('status');
            if (status === 'running') {
                statusEl.innerHTML = '<span class="spinner"></span>运行中...';
                statusEl.className = 'status-value status-running';
            }
        }
        
        // Initial load
        pollResults();
        
        // Auto-refresh every 2 seconds
        setInterval(pollResults, 2000);
    </script>
</body>
</html>
"""
