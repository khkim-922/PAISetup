"""measure.sh 의 로그인 파일 손 — 두 팔이 로그인 파일의 사본으로 도는 동안 그 PC 의 로그인이 안 끊기게 한다.

부르는 꼴::

    python -X utf8 -I login.py left <로그인 파일>               # 토큰 만료까지 남은 분(정수)을 낸다
    python -X utf8 -I login.py keep <원본> <사본> [<사본> …]    # 원본보다 만료가 늦은 사본이 있으면 가장 늦은 것을 원본에 되돌린다

까닭 — 도는 중에 토큰이 만료되면 먼저 갱신한 팔의 사본만 새 갱신 토큰을 갖고, 원본과 다른 팔의 사본이 든 옛 갱신 토큰은
죽는다. 사본은 끝에 지워지므로 되돌리지 않으면 그 PC 의 로그인이 끊긴다. ``left`` 로 곧 만료될 토큰을 미리 가리고, 그래도
갱신이 났으면 ``keep`` 이 새 사본을 원본에 되돌린다.

값은 찍지 않는다. 못 읽는 사본은 건너뛴다. 종료 값 — 0 됐다 · 1 로그인 파일을 못 읽었다(left).
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time


def expires(path: pathlib.Path) -> float | None:
    """그 로그인 파일의 토큰 만료 시각(초) — 못 읽거나 칸이 없으면 None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return max(float(v["expiresAt"]) for v in data.values() if isinstance(v, dict) and "expiresAt" in v) / 1000
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "left":
        until = expires(pathlib.Path(argv[1]))
        if until is None:
            return 1
        print(int((until - time.time()) // 60))
        return 0
    if len(argv) >= 3 and argv[0] == "keep":
        real = pathlib.Path(argv[1])
        newest, best = None, expires(real) or 0.0
        for copy in map(pathlib.Path, argv[2:]):
            until = expires(copy)
            if until is not None and until > best:
                newest, best = copy, until
        if newest is not None:
            temp = real.with_suffix(f".{os.getpid()}.tmp")
            temp.write_bytes(newest.read_bytes())
            temp.replace(real)                             # 도중에 죽어도 반쯤 쓴 로그인 파일이 안 남는다
            print("도는 중에 토큰이 갱신됐다 — 갱신된 사본을 로그인 파일에 되돌렸다", file=sys.stderr)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
