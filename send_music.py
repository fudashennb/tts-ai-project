import requests
import json
import time
import sys
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入统一的日志配置
import log_config

# 配置日志
_logger = logging.getLogger(__name__)

url = "http://localhost:8800/play"
params_start = {
    "file_path": "music/9.wav",
    "music_text": "开始播放对话",
    "play_interval": 2.0,
    "play_count": 1,
    "replay_interval": 15.0,
    "priority": 2, 
    "mode": "replace",
    "status_command": "play_music",
    "volume": 0.5
}
print(params_start)
while True:
    try:
        response = requests.post(url, json=params_start) 
        print("send music")
        _logger.info(response.json())  
        time.sleep(1)
    except Exception as e:
        _logger.error(f"send music error: {e}")
        time.sleep(1)