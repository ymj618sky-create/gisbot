"""配置管理模块"""
from pathlib import Path
from typing import Any, Dict, Optional
import json


class Config:
    """配置管理类"""

    # 必需的配置节
    REQUIRED_SECTIONS = ["app", "channels", "agents"]

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.json")
        self._validate_config_path()
        self._config: Optional[Dict[str, Any]] = None

    def _validate_config_path(self) -> None:
        """验证配置路径安全性"""
        try:
            # 解析绝对路径并检查是否为文件
            abs_path = self.config_path.resolve()
            if abs_path.is_dir():
                raise ValueError(f"配置路径必须是文件，不是目录: {abs_path}")
            self.config_path = abs_path
        except (OSError, RuntimeError) as e:
            raise ValueError(f"无效的配置路径: {e}") from e

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"配置文件格式错误: {e}") from e

            self._validate_config_structure()

        return self._config

    def _validate_config_structure(self) -> None:
        """验证配置结构完整性"""
        config = self._config
        if config is None:
            raise ValueError("配置未加载")

        for section in self.REQUIRED_SECTIONS:
            if section not in config:
                raise ValueError(f"配置文件缺少必需的 {section} 部分")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        if not isinstance(key, str):
            raise TypeError(f"配置键必须是字符串，得到 {type(key).__name__}")

        config = self.load()
        return config.get(key, default)

    def get_channel_config(self, channel_name: str, default: Any = None) -> Any:
        """获取渠道配置"""
        if not isinstance(channel_name, str):
            raise TypeError(f"渠道名称必须是字符串，得到 {type(channel_name).__name__}")

        channels = self.get("channels", {})
        return channels.get(channel_name, default)

    def get_agent_defaults(self) -> Dict[str, Any]:
        """获取 Agent 默认配置"""
        agents = self.get("agents", {})
        return agents.get("defaults", {})


# 全局配置实例
_config: Optional[Config] = None


def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置（单例模式）"""
    global _config
    if _config is None:
        _config = Config(config_path)
        _config.load()
    return _config


def reset_config() -> None:
    """重置配置（主要用于测试）"""
    global _config
    _config = None