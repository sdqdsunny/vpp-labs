#!/usr/bin/env python3
"""
简单的流量监控工具 - 监听 localhost:9080 的连接
"""
import socket
import threading
import time
from datetime import datetime

def monitor_port(port=9080):
    """监听指定端口的连接"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('127.0.0.1', port))
        server.listen(5)
        print(f"✅ 监听 127.0.0.1:{port}")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        connection_count = 0
        while True:
            try:
                client, addr = server.accept()
                connection_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] 连接 #{connection_count}: {addr[0]}:{addr[1]}")
                
                # 接收数据
                data = client.recv(1024)
                if data:
                    # 显示请求的第一行
                    first_line = data.decode('utf-8', errors='ignore').split('\n')[0]
                    print(f"         请求: {first_line}")
                
                client.close()
            except Exception as e:
                print(f"❌ 错误: {e}")
                
    except OSError as e:
        print(f"❌ 无法绑定到端口 {port}: {e}")
        print("   可能原因: 端口已被占用")
    finally:
        server.close()

if __name__ == '__main__':
    print("=" * 60)
    print("简单流量监控工具")
    print("=" * 60)
    print()
    
    try:
        monitor_port(9080)
    except KeyboardInterrupt:
        print("\n\n停止监听")
