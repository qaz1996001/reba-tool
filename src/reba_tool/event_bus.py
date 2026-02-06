#!/usr/bin/env python3
"""
框架無關的事件匯流排 (Framework-Agnostic Event Bus)
取代 Qt Signal/Slot，純 Python callback，線程安全。

事件定義：
- frame_processed: frame, angles, reba_score, risk_level, fps, details
- processing_finished: (無參數)
- error_occurred: message
- progress_updated: current_frame, total_frames
"""

import threading
from typing import Callable, Dict, List, Any


class EventBus:
    """線程安全的事件匯流排"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def on(self, event_name: str, handler: Callable):
        """
        註冊事件處理器

        Args:
            event_name: 事件名稱
            handler: 回調函式
        """
        with self._lock:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)

    def off(self, event_name: str, handler: Callable = None):
        """
        取消事件處理器

        Args:
            event_name: 事件名稱
            handler: 要移除的回調函式，None 則移除該事件所有處理器
        """
        with self._lock:
            if event_name not in self._handlers:
                return
            if handler is None:
                del self._handlers[event_name]
            else:
                try:
                    self._handlers[event_name].remove(handler)
                except ValueError:
                    pass

    def emit(self, event_name: str, **kwargs):
        """
        發送事件

        Args:
            event_name: 事件名稱
            **kwargs: 事件參數
        """
        with self._lock:
            handlers = list(self._handlers.get(event_name, []))

        for handler in handlers:
            handler(**kwargs)
