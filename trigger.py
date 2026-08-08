import random
from .config import PluginConfig
from .constants import TRIGGER_PROBABILITY, TRIGGER_INTERVAL, TRIGGER_MANUAL


class TriggerManager:
    """触发决策器。"""

    def __init__(self, cfg: PluginConfig):
        self.cfg = cfg
        self._counter = 0
        self._last_triggered = -999

    def should_trigger(self, msg_count: int) -> bool:
        """判断是否应该触发生图。"""
        mode = self.cfg.trigger_mode

        if mode == TRIGGER_MANUAL:
            return False

        # 冷却检查
        if msg_count - self._last_triggered < self.cfg.cooldown:
            return False

        if mode == TRIGGER_INTERVAL:
            self._counter += 1
            if self._counter >= self.cfg.interval:
                self._counter = 0
                self._last_triggered = msg_count
                return True
            return False

        if mode == TRIGGER_PROBABILITY:
            if random.random() < self.cfg.probability:
                self._last_triggered = msg_count
                return True
            return False

        return False

    def mark_triggered(self, msg_count: int) -> None:
        self._last_triggered = msg_count
