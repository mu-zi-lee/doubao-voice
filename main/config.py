"""中继配置：历史条数等，支持用户目录持久化。"""
import json
import os
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "config.json"
PROMPTS_FILENAME = "prompts.json"
HISTORY_FILENAME = "history.json"

DEFAULT_HISTORY_SIZE = 10
DEFAULT_AI_OPTIMIZE_ENABLED = False
DEFAULT_DEFAULT_MODE = "restore"
DEFAULT_AI_API_KEY = ""
DEFAULT_AI_BASE_URL = ""


def get_user_config_dir() -> Path:
    """返回用户配置目录：Windows %APPDATA%/doubao-voice，Unix ~/.config/doubao-voice。"""
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    path = Path(base) / "doubao-voice"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path() -> Path:
    return get_user_config_dir() / CONFIG_FILENAME


def load_config() -> dict[str, Any]:
    """从用户目录 config.json 读取配置；不存在则用环境变量与默认值。"""
    path = _config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "history_size": int(data.get("history_size", DEFAULT_HISTORY_SIZE)),
                "ai_optimize_enabled": bool(data.get("ai_optimize_enabled", DEFAULT_AI_OPTIMIZE_ENABLED)),
                "default_mode": str(data.get("default_mode", DEFAULT_DEFAULT_MODE)),
                "ai_api_key": str(data.get("ai_api_key", DEFAULT_AI_API_KEY)),
                "ai_base_url": str(data.get("ai_base_url", DEFAULT_AI_BASE_URL)),
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    history_size = int(os.environ.get("RELAY_HISTORY_SIZE", str(DEFAULT_HISTORY_SIZE)))
    return {
        "history_size": max(1, history_size),
        "ai_optimize_enabled": DEFAULT_AI_OPTIMIZE_ENABLED,
        "default_mode": DEFAULT_DEFAULT_MODE,
        "ai_api_key": DEFAULT_AI_API_KEY,
        "ai_base_url": DEFAULT_AI_BASE_URL,
    }


def save_config(config: dict[str, Any]) -> None:
    """将配置写入用户目录 config.json。"""
    path = _config_path()
    path.write_text(
        json.dumps(
            {
                "history_size": config.get("history_size", DEFAULT_HISTORY_SIZE),
                "ai_optimize_enabled": config.get("ai_optimize_enabled", DEFAULT_AI_OPTIMIZE_ENABLED),
                "default_mode": config.get("default_mode", DEFAULT_DEFAULT_MODE),
                "ai_api_key": config.get("ai_api_key", DEFAULT_AI_API_KEY),
                "ai_base_url": config.get("ai_base_url", DEFAULT_AI_BASE_URL),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_history_size() -> int:
    """当前生效的历史条数。"""
    return max(1, load_config()["history_size"])


def get_ai_optimize_enabled() -> bool:
    """是否启用 AI 优化。"""
    return load_config()["ai_optimize_enabled"]


def get_default_mode() -> str:
    """默认粘贴模式。"""
    return load_config()["default_mode"]


def get_ai_api_key() -> str:
    """AI 接口 API Key（可选）。"""
    return load_config().get("ai_api_key", DEFAULT_AI_API_KEY)


def get_ai_base_url() -> str:
    """AI 接口 Base URL（可选）。"""
    return load_config().get("ai_base_url", DEFAULT_AI_BASE_URL)


def _prompts_path() -> Path:
    return get_user_config_dir() / PROMPTS_FILENAME


def load_prompts() -> dict[str, str]:
    """从用户目录 prompts.json 读取提示词；不存在则返回空 dict。"""
    path = _prompts_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {k: str(v) for k, v in data.items()}
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return {}


def save_prompts(prompts: dict[str, str]) -> None:
    """将提示词写入用户目录 prompts.json。"""
    path = _prompts_path()
    path.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")


def _history_path() -> Path:
    return get_user_config_dir() / HISTORY_FILENAME


def load_history(max_size: int) -> list[dict[str, Any]]:
    """从用户目录 history.json 读取历史，最多返回 max_size 条（保留最新）。"""
    path = _history_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        out = []
        for item in data:
            if isinstance(item, dict) and "content" in item:
                out.append({
                    "content": str(item["content"]),
                    "timestamp": int(item.get("timestamp", 0)),
                    "mode": str(item.get("mode", "restore")),
                })
        return out[-max_size:] if len(out) > max_size else out
    except (json.JSONDecodeError, TypeError, ValueError, KeyError):
        return []


def save_history(records: list[dict[str, Any]]) -> None:
    """将历史记录列表写入用户目录 history.json。"""
    path = _history_path()
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


# 启动时历史条数，供 relay 创建 deque；修改配置后需重启生效
HISTORY_SIZE = get_history_size()
