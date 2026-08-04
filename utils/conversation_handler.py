"""对话持久化：自动保存/加载/清空，刷新页面不丢失。

后续升级为账号系统时，只需扩展本模块（如增加 user_id 参数），app.py 无需改动。
"""

import json
import os
from datetime import datetime

from utils.path_tool import get_abs_path

# 对话文件相对于项目根目录的路径
_CONVERSATIONS_DIR = 'conversations'
_CURRENT_FILE = 'current.json'


def _ensure_dir() -> str:
    """确保 conversations 目录存在，返回其绝对路径。"""
    dir_path = get_abs_path(_CONVERSATIONS_DIR)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def _current_path() -> str:
    return os.path.join(_ensure_dir(), _CURRENT_FILE)


def save_conversation(messages: list[dict]) -> None:
    """保存当前对话到磁盘。"""
    data = {
        'updated_at': datetime.now().isoformat(),
        'messages': messages,
    }
    with open(_current_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_conversation() -> list[dict]:
    """从磁盘加载上次对话。若无存档则返回空列表。"""
    path = _current_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('messages', [])
    except (json.JSONDecodeError, KeyError):
        return []


def clear_conversation() -> None:
    """清空磁盘上的当前对话。"""
    path = _current_path()
    if os.path.exists(path):
        os.remove(path)
