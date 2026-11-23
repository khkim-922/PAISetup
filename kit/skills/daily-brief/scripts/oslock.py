"""OS 잠금 한 자리 — 파일 하나의 첫 바이트를 잠근다. 넣은 누름의 기록을 고치는 손 하나 · 창 곁의 손 하나를 지킨다. 손이 죽으면 OS 가 푼다 —
시각으로 푸는 잠금과 달리 죽은 손을 「도는 중」으로 잘못 읽지 않는다.
"""

from __future__ import annotations

import os
import pathlib


class OsLock:
    """파일 하나의 첫 바이트를 잠근다 — 못 쥐면 `take` 가 False. 시각으로 푸는 잠금과 달리 죽은 손을 「도는 중」으로 잘못 읽지 않는다."""

    def __init__(self, path: pathlib.Path):
        self.path, self.file = path, None

    def take(self) -> bool:
        """잠금을 쥐어 본다 — 쥐었으면 True, 다른 손이 쥐었거나 파일을 못 열면 False."""
        try:
            f = open(self.path, "a+b")
        except OSError:
            return False
        try:
            f.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            return False
        self.file = f
        return True

    def release(self) -> None:
        """쥔 잠금을 풀고 파일을 닫는다 — 안 쥐었으면 아무것도 안 한다."""
        if self.file is None:
            return
        try:
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        self.file.close()
        self.file = None
