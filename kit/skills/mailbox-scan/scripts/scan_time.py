"""스캔의 시각 — 저장은 UTC ISO 8601(사전순이 시간순이다), 보이기는 서울(+09:00 고정 — `zoneinfo` 는 윈도에서 `tzdata` 가 따로 들어
안 쓴다). 파일 · 프로세스에 안 닿는다.

    import scan_time as tm
    tm.stamp(tm.now()) · tm.parse(text) · tm.seoul(t) · tm.mail_time(date) · tm.KST
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from scan_const import MAIL_DATE, MAIL_DATE_MINUTE, SEOUL_OFFSET_H

KST = timezone(timedelta(hours=SEOUL_OFFSET_H), "KST")


def now() -> datetime:
    """지금(UTC)."""
    return datetime.now(timezone.utc)


def stamp(t: datetime) -> str:
    """저장할 글자 — UTC ISO 8601. 사전순이 시간순이다."""
    if t.tzinfo is None:
        raise ValueError("시간대 없는 시각은 받지 않는다")
    return t.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse(text: str | None) -> datetime | None:
    """저장된 글자 · 시간대가 붙은 ISO 글자(정리 스킬의 기록)를 시각으로. 못 읽거나 시간대가 없으면 None."""
    if not text:
        return None
    try:
        t = datetime.fromisoformat(str(text))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def mail_time(date: str | None) -> datetime | None:
    """메일의 때(서울 글자) → 시각. 그 꼴이 아니면 None — 때를 모르는 메일이다."""
    if not date:
        return None
    for form in (MAIL_DATE, MAIL_DATE_MINUTE):   # 옛 state.json 에 든 분까지인 글자도 푼다
        try:
            return datetime.strptime(date, form).replace(tzinfo=KST)
        except ValueError:
            continue
    return None


def seoul(t: datetime | None, form: str = "%Y-%m-%d %H:%M") -> str:
    """시각을 서울 글자로 — 없으면 빈 글."""
    return t.astimezone(KST).strftime(form) if t else ""
