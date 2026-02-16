"""
VPP Master 配置管理

支持从环境变量和.env文件读取配置
"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Config:
    """基础配置"""
    
    # 应用信息
    VERSION = '0.1.0'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vpp_master.db')
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 5G仿真配置
    OPEN5GS_HOST = os.getenv('OPEN5GS_HOST', 'localhost')
    OPEN5GS_PORT = int(os.getenv('OPEN5GS_PORT', 3000))
    
    # 监控配置
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))
    
    # 时钟同步配置
    PTP_ENABLED = os.getenv('PTP_ENABLED', 'true').lower() == 'true'
    PTP_INTERFACE = os.getenv('PTP_INTERFACE', 'eth0')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    ENVIRONMENT = 'development'
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    ENVIRONMENT = 'production'
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    ENVIRONMENT = 'testing'
    DATABASE_URL = 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'


# 根据环境变量选择配置
def get_config():
    """获取当前环境的配置"""
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
