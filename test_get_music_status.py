#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：调用 /get_music_playing_status 接口
运行一次即可触发一次启动语音提醒
"""

import requests
import sys

# 服务地址和端口
SERVER_URL = "http://localhost:8800"
ENDPOINT = "/get_music_playing_status"

def main():
    """调用接口获取音乐播放状态"""
    try:
        url = f"{SERVER_URL}{ENDPOINT}"
        print(f"📡 正在调用接口: {url}")
        
        # 发送 GET 请求
        response = requests.get(url, timeout=10)
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"   状态: {result.get('status')}")
            print(f"   消息: {result.get('message')}")
            print(f"   是否播放中: {result.get('is_playing')}")
            print(f"\n🎵 启动语音提醒已触发")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器: {SERVER_URL}")
        print(f"   请确保 TTS 语音播放服务已启动")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
