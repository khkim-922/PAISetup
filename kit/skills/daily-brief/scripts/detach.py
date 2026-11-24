"""떼어 띄우는 인자 — 띄운 것이 부른 손보다 오래 살게 하는 `Popen` 인자의 한 자리. 창을 안 띄우는 몫은 곁의 `proc_base.quiet` 가 들고, 여기는
다른 프로세스 묶음 · 작업 묶음(job) 밖이라는 몫만 더한다. 창 곁의 손을 띄우는 넣는 손(`presses.start_hand`)과 사람 없는 실행(claude ·
맡긴 일의 지킴이)이 다 이것을 쓴다.

    subprocess.Popen(cmd, **detached())            # 창 없이 · 다른 묶음으로 — 부른 쪽이 끝나도 산다
    for kw in detached_tries(): subprocess.Popen(cmd, **kw)   # 작업 묶음 밖으로 먼저, 묶음이 안 놓아 주면 묶음 안에서라도
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import proc_base as P


def detached() -> dict[str, Any]:
    """떼어 띄우는 `Popen` 인자 — 창 없이, 부른 프로세스와 다른 묶음으로 띄워 부른 쪽이 끝나도 띄운 것이 산다."""
    if sys.platform == "win32":
        return {"creationflags": P.quiet()["creationflags"] | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def detached_tries() -> list[dict[str, Any]]:
    """떼어 띄우는 인자를 시도할 차례 — 부른 손이 든 작업 묶음(job)이 닫혀도 살게 묶음 밖으로 먼저, 묶음이 안 놓아 주면(`OSError`) 묶음
    안에서라도 띄운다."""
    base = detached()
    if sys.platform != "win32":
        return [base]
    return [{"creationflags": base["creationflags"] | subprocess.CREATE_BREAKAWAY_FROM_JOB}, base]
