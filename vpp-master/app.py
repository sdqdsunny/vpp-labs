#!/usr/bin/env python3
"""
VPP Master - 虚拟电厂主站程序
基于Bottle.py框架开发

主应用入口文件
"""

import sys
import os

# 添加bottle-framework到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bottle-framework'))

from bottle import Bottle, static_file, request, response
import json
from config import Config
from utils.logger import setup_logger
from middleware.error_handler import setup_error_handling
from middleware.request_logger import setup_request_logging
from middleware.auth import setup_authentication
from middleware.authorization import setup_authorization
from middleware.response_formatter import setup_response_formatting
from middleware.request_validator import setup_request_validation
from middleware.rate_limiter import setup_rate_limiting
from utils.metrics import registry
from prometheus_client import generate_latest
from routes.devices import setup_device_routes
from routes.dispatch import setup_dispatch_routes
from routes.protocol import setup_protocol_routes
from routes.analysis import setup_analysis_routes
from utils.openapi_spec import OPENAPI_SPEC
from utils.swagger_ui import get_swagger_ui_html, get_redoc_html

# 初始化
config = Config()
logger = setup_logger(__name__)
app = Bottle()

# ============================================================================
# 中间件设置
# ============================================================================

# 设置错误处理（必须首先设置）
setup_error_handling(app)

# 设置请求验证
setup_request_validation(app)

# 设置速率限制
setup_rate_limiting(app)

# 设置请求日志
setup_request_logging(app)

# 设置认证（保护 /api/ 路由）
setup_authentication(app, protected_routes=['/api/'])

# 设置授权（保护 /api/ 路由）
setup_authorization(app, protected_routes=['/api/'])

# 设置响应格式化
setup_response_formatting(app)

# ============================================================================
# 路由注册
# ============================================================================

# 设置设备管理路由
setup_device_routes(app)

# 设置调度控制路由
setup_dispatch_routes(app)

# 设置协议转换路由
setup_protocol_routes(app)

# 设置分析功能路由
setup_analysis_routes(app)

# 健康检查（公开路由）
@app.route('/health')
def health_check():
    """系统健康检查"""
    return {
        'status': 'healthy',
        'version': config.VERSION,
        'environment': config.ENVIRONMENT
    }

# Prometheus 指标端点（公开路由）
@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    response.content_type = 'text/plain; version=0.0.4'
    return generate_latest(registry).decode('utf-8')

# OpenAPI 规范端点（公开路由）
@app.route('/api/openapi.json')
def openapi_spec():
    """OpenAPI 3.0 specification endpoint"""
    response.content_type = 'application/json'
    return OPENAPI_SPEC

# Swagger UI 文档端点（公开路由）
@app.route('/api/docs')
def swagger_ui():
    """Swagger UI documentation endpoint"""
    response.content_type = 'text/html'
    return get_swagger_ui_html(spec_url='/api/openapi.json')

# ReDoc 文档端点（公开路由）
@app.route('/api/redoc')
def redoc_ui():
    """ReDoc documentation endpoint"""
    response.content_type = 'text/html'
    return get_redoc_html(spec_url='/api/openapi.json')

# API 文档端点（公开路由）
@app.route('/docs')
def api_docs():
    """API documentation endpoint"""
    response.content_type = 'application/json'
    return {
        'title': 'VPP Master API',
        'version': config.VERSION,
        'description': 'Virtual Power Plant Master Station API',
        'endpoints': {
            'devices': '/api/v1/devices',
            'dispatch': '/api/v1/dispatch',
            'protocol': '/api/v1/protocol',
            'analysis': '/api/v1/analysis'
        },
        'documentation': {
            'swagger_ui': '/api/docs',
            'redoc': '/api/redoc',
            'openapi_spec': '/api/openapi.json'
        }
    }

# 首页
@app.route('/')
def index():
    """返回首页"""
    try:
        return static_file('index.html', root='static')
    except:
        return {
            'message': 'VPP Master API',
            'version': config.VERSION,
            'status': 'running'
        }

# 静态文件
@app.route('/static/<filepath:path>')
def serve_static(filepath):
    """提供静态文件"""
    return static_file(filepath, root='static')

# ============================================================================
# 响应头设置
# ============================================================================

@app.hook('after_request')
def set_response_headers():
    """设置响应头"""
    response.headers['X-Powered-By'] = 'VPP-Master'
    response.headers['X-Version'] = config.VERSION
    response.headers['Content-Type'] = 'application/json'

# ============================================================================
# 主程序
# ============================================================================

def create_app():
    """创建并配置应用"""
    logger.info(f'Initializing VPP Master v{config.VERSION}')
    logger.info(f'Environment: {config.ENVIRONMENT}')
    logger.info(f'Debug mode: {config.DEBUG}')
    return app


if __name__ == '__main__':
    logger.info(f'Starting VPP Master v{config.VERSION}')
    logger.info(f'Environment: {config.ENVIRONMENT}')
    logger.info(f'Listening on {config.HOST}:{config.PORT}')
    logger.info(f'Health check: http://{config.HOST}:{config.PORT}/health')
    logger.info(f'Metrics: http://{config.HOST}:{config.PORT}/metrics')
    logger.info(f'API Docs (JSON): http://{config.HOST}:{config.PORT}/docs')
    logger.info(f'Swagger UI: http://{config.HOST}:{config.PORT}/api/docs')
    logger.info(f'ReDoc: http://{config.HOST}:{config.PORT}/api/redoc')
    logger.info(f'OpenAPI Spec: http://{config.HOST}:{config.PORT}/api/openapi.json')
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        reloader=config.DEBUG,
        quiet=not config.DEBUG
    )
