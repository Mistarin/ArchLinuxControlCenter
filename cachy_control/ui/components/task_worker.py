"""Small QThread wrapper for read-only work that would otherwise block the UI."""

from typing import Callable, Any
from PyQt6.QtCore import QThread, pyqtSignal


class TaskWorker(QThread):
    result_ready = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, task: Callable[[], Any], parent=None):
        super().__init__(parent)
        self._task = task
        self.finished.connect(self.deleteLater)

    def run(self):
        try:
            self.result_ready.emit(self._task())
        except Exception as exc:
            self.failed.emit(str(exc))
