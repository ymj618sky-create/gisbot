"""配置管理模块"""
from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging
import os

logger = logging.getLogger(__name__)


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


# ==================== 超时配置管理 ====================

class TimeoutConfig:
    """系统超时配置。

    所有超时值以秒为单位。
    """

    # LLM API调用超时
    llm_request: int = 300  # 5分钟

    # 工具执行超时
    exec_command: int = 600  # 10分钟
    run_python: int = 600  # 10分钟

    # SSE流超时
    sse_queue_wait: int = 600  # 10分钟
    sse_heartbeat: int = 30  # 30秒心跳

    # Agent循环配置
    max_iterations: int = 100

    # Provider重试配置
    provider_max_retries: int = 5
    provider_retry_delay: int = 2  # 秒

    def __init__(self, **kwargs):
        """初始化超时配置，从关键字参数读取值。"""
        self.llm_request = kwargs.get('llm_timeout', kwargs.get('llm_request', 300))
        self.exec_command = kwargs.get('exec_timeout', kwargs.get('exec_command', 600))
        self.run_python = kwargs.get('run_python_timeout', kwargs.get('run_python', 600))
        self.sse_queue_wait = kwargs.get('sse_timeout', kwargs.get('sse_queue_wait', 600))
        self.sse_heartbeat = kwargs.get('sse_heartbeat', 30)
        self.max_iterations = kwargs.get('max_iterations', 100)
        self.provider_max_retries = kwargs.get('provider_max_retries', 5)
        self.provider_retry_delay = kwargs.get('provider_retry_delay', 2)

        self._validate()

    def _validate(self):
        """在初始化后验证配置值。"""
        if self.llm_request < 60:
            logger.warning(f"llm_request {self.llm_request}s is too short, using minimum 60s")
            self.llm_request = 60

        if self.exec_command < 60:
            logger.warning(f"exec_command {self.exec_command}s is too short, using minimum 60s")
            self.exec_command = 60

        if self.run_python < 60:
            logger.warning(f"run_python {self.run_python}s is too short, using minimum 60s")
            self.run_python = 60

        if self.sse_queue_wait < 300:
            logger.warning(f"sse_queue_wait {self.sse_queue_wait}s is too short, using minimum 300s")
            self.sse_queue_wait = 300

        if self.max_iterations < 10:
            logger.warning(f"max_iterations {self.max_iterations} is too small, using minimum 10")
            self.max_iterations = 10

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'TimeoutConfig':
        """从配置字典创建 TimeoutConfig。"""
        return cls(**config)

    @classmethod
    def from_config_file(cls, config_path: Optional[Path] = None) -> 'TimeoutConfig':
        """从配置文件读取超时配置。

        Args:
            config_path: 配置文件路径，默认为 config.json

        Returns:
            TimeoutConfig 实例
        """
        if config_path is None:
            # 尝试找到 config.json
            config_path = Path(__file__).parent.parent / 'config.json'

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 从不同可能的配置路径读取超时值
            timeout_dict: Dict[str, Any] = {}

            # 从 timeout 节读取（优先）
            if 'timeout' in config_data:
                timeout_dict.update(config_data['timeout'])

            # 从 agents.defaults 读取
            if 'agents' in config_data and 'defaults' in config_data['agents']:
                defaults = config_data['agents']['defaults']
                if 'max_iterations' in defaults and 'max_iterations' not in timeout_dict:
                    timeout_dict['max_iterations'] = defaults['max_iterations']

            # 从 tools.system 读取工具超时
            if 'tools' in config_data and 'system' in config_data['tools']:
                system = config_data['tools']['system']
                if 'exec' in system and 'exec_timeout' not in timeout_dict:
                    timeout_dict['exec_timeout'] = system['exec'].get('timeout_seconds', 600)
                if 'run_python' in system and 'run_python_timeout' not in timeout_dict:
                    timeout_dict['run_python_timeout'] = system['run_python'].get('timeout_seconds', 600)

            # 尝试从顶级配置读取
            for key in ['llm_timeout', 'exec_timeout', 'run_python_timeout', 'sse_timeout',
                        'max_iterations', 'provider_max_retries', 'provider_retry_delay']:
                if key in config_data and key not in timeout_dict:
                    timeout_dict[key] = config_data[key]

            # 从环境变量覆盖
            timeout_dict.update(cls._read_env_overrides())

            result = cls.from_dict(timeout_dict)
            logger.info(f"Loaded timeout config from {config_path}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}, using defaults")
            return cls()

    @staticmethod
    def _read_env_overrides() -> Dict[str, Any]:
        """从环境变量读取超时配置覆盖。"""
        overrides: Dict[str, Any] = {}

        env_mapping = {
            'LLM_TIMEOUT': ('llm_timeout', int),
            'EXEC_TIMEOUT': ('exec_timeout', int),
            'RUN_PYTHON_TIMEOUT': ('run_python_timeout', int),
            'SSE_TIMEOUT': ('sse_timeout', int),
            'SSE_HEARTBEAT': ('sse_heartbeat', int),
            'MAX_ITERATIONS': ('max_iterations', int),
            'PROVIDER_MAX_RETRIES': ('provider_max_retries', int),
            'PROVIDER_RETRY_DELAY': ('provider_retry_delay', int),
        }

        for env_key, (config_key, converter) in env_mapping.items():
            env_value = os.environ.get(env_key)
            if env_value:
                try:
                    overrides[config_key] = converter(env_value)
                    logger.debug(f"Override {config_key} from env: {overrides[config_key]}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {env_key}: {env_value}")

        return overrides

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'llm_request': self.llm_request,
            'exec_command': self.exec_command,
            'run_python': self.run_python,
            'sse_queue_wait': self.sse_queue_wait,
            'sse_heartbeat': self.sse_heartbeat,
            'max_iterations': self.max_iterations,
            'provider_max_retries': self.provider_max_retries,
            'provider_retry_delay': self.provider_retry_delay,
        }

    def __str__(self) -> str:
        """返回配置的字符串表示。"""
        return (f"TimeoutConfig(llm={self.llm_request}s, exec={self.exec_command}s, "
                f"run_python={self.run_python}s, sse={self.sse_queue_wait}s, "
                f"max_iter={self.max_iterations})")


# 全局默认配置实例
_default_timeout_config: Optional[TimeoutConfig] = None


def get_timeout_config(config_path: Optional[Path] = None) -> TimeoutConfig:
    """获取全局超时配置实例。

    Args:
        config_path: 可选的配置文件路径

    Returns:
        TimeoutConfig 实例
    """
    global _default_timeout_config
    if _default_timeout_config is None:
        _default_timeout_config = TimeoutConfig.from_config_file(config_path)
    return _default_timeout_config


def reset_timeout_config() -> None:
    """重置全局超时配置。下次调用 get_timeout_config 时会重新加载。"""
    global _default_timeout_config
    _default_timeout_config = None
    logger.info("Timeout config reset")