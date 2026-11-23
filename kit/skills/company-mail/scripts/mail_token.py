"""지문 — 부분들을 한 꼴(키를 고른 JSON)로 이은 글의 sha256 앞 ``TOKEN_LENGTH`` 자.

이 스킬의 명령이 미리 본 판의 확인 열쇠로, 메일함을 여는 자리(``mail_open``)가 받아 둔 메일함 주소를 묶는 세션의 지문으로 쓴다 —
같은 부분이면 늘 같은 글자다.
"""

from __future__ import annotations

import hashlib
import json

TOKEN_LENGTH = 12


def token(*parts) -> str:
    """부분들의 지문 — 부분이 같으면 같은 ``TOKEN_LENGTH`` 자, 하나라도 다르면 다른 글자다."""
    blob = json.dumps(parts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:TOKEN_LENGTH]
