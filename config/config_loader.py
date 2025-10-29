"""
统一配置加载器

设计理念：
1. 单一职责：只负责读取CSV
2. 缓存机制：避免重复读取
3. 热加载：支持运行时更新
4. 通用接口：所有模块使用相同方式获取配置

扩展性：
- 添加新配置文件：只需放到 rules/ 目录
- 添加新模块：调用 get_config() 即可
"""

import csv
from pathlib import Path
from typing import Dict, List, Any
import logging
import time

_logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    统一配置加载器
    
    使用示例:
        # 获取实例
        loader = get_config_loader()
        
        # 加载列表型配置
        keywords = loader.get_config('number_identifier_keywords')
        
        # 加载键值型配置
        decimal_places = loader.get_config_value('number_processing_config', 'decimal_places', 2)
        
        # 强制重新加载
        loader.reload_all()
    """
    
    _instance = None  # 单例模式
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_dir = Path(__file__).parent / 'rules'
        self.cache = {}
        self.cache_timeout = 60  # 60秒缓存
        self.last_load_time = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        _logger.info(f"✅ 配置加载器初始化完成: {self.config_dir}")
    
    def get_config(self, config_name: str, force_reload: bool = False) -> List[Dict]:
        """
        获取配置（通用接口）
        
        参数:
            config_name: 配置文件名（不含.csv）
            force_reload: 是否强制重新加载
        
        返回:
            List[Dict]: 配置数据列表
        
        示例:
            # 数字模块
            keywords = loader.get_config('number_identifier_keywords')
            
            # 唤醒词模块
            wake_words = loader.get_config('wake_words')
            
            # 缩写词模块
            abbreviations = loader.get_config('abbreviations')
        """
        # 检查缓存
        if not force_reload and config_name in self.cache:
            elapsed = time.time() - self.last_load_time.get(config_name, 0)
            if elapsed < self.cache_timeout:
                return self.cache[config_name]
        
        # 加载配置
        config_file = self.config_dir / f"{config_name}.csv"
        
        if not config_file.exists():
            _logger.warning(f"⚠️ 配置文件不存在: {config_file}")
            return []
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            # 更新缓存
            self.cache[config_name] = data
            self.last_load_time[config_name] = time.time()
            
            _logger.info(f"📄 加载配置: {config_name}.csv ({len(data)} 条)")
            return data
        
        except Exception as e:
            _logger.error(f"❌ 加载配置失败: {config_name}.csv, 错误: {e}")
            return []
    
    def reload_all(self):
        """重新加载所有配置"""
        _logger.info("🔄 重新加载所有配置...")
        self.cache.clear()
        self.last_load_time.clear()
    
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        获取单个配置值（键值对配置）
        
        适用于 xxx_config.csv 类型的配置
        
        示例:
            decimal_places = loader.get_config_value(
                'number_processing_config', 
                'decimal_places', 
                2
            )
        """
        config = self.get_config(config_name)
        
        for row in config:
            if row.get('config_key') == key:
                value = row.get('config_value', default)
                value_type = row.get('value_type', 'str')
                
                # 类型转换
                try:
                    if value_type == 'int':
                        return int(value)
                    elif value_type == 'float':
                        return float(value)
                    elif value_type == 'bool':
                        return value.upper() in ['TRUE', '1', 'YES']
                    else:
                        return str(value)
                except:
                    return default
        
        return default
    
    def get_enabled_items(self, config_name: str, filter_field: str = 'enabled') -> List[Dict]:
        """
        获取已启用的配置项
        
        参数:
            config_name: 配置文件名
            filter_field: 过滤字段名（默认为'enabled'）
        
        返回:
            List[Dict]: 已启用的配置项列表
        """
        all_items = self.get_config(config_name)
        return [item for item in all_items if item.get(filter_field, '').upper() in ['TRUE', '1', 'YES']]


# 全局单例
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

